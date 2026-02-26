"""Broadcast service for sending predictions to all users."""

import asyncio
import logging
from typing import List, Optional, Callable, Any

from aiogram import Bot
from aiogram.exceptions import TelegramRetryAfter, TelegramForbiddenError, TelegramBadRequest
from aiogram.types import InlineKeyboardMarkup

from bot.db.models import Prediction, MediaType

logger = logging.getLogger(__name__)


class BroadcastService:
    """Service for broadcasting predictions to users."""

    # Rate limiting settings
    BATCH_SIZE = 25
    BATCH_DELAY = 1.0  # seconds between batches
    MAX_RETRIES = 3
    RETRY_DELAY = 5.0  # base delay for retries

    def __init__(self, bot: Bot):
        self.bot = bot

    async def broadcast_prediction(
        self,
        prediction: Prediction,
        user_ids: List[int],
        keyboard: InlineKeyboardMarkup,
        on_progress: Optional[Callable[[int, int], Any]] = None,
    ) -> dict:
        """
        Broadcast a prediction to all users.
        
        Returns dict with success_count, failure_count, and errors list.
        """
        success_count = 0
        failure_count = 0
        errors: List[dict] = []

        total_users = len(user_ids)
        
        for i in range(0, total_users, self.BATCH_SIZE):
            batch = user_ids[i:i + self.BATCH_SIZE]
            
            for user_id in batch:
                success = await self._send_to_user(
                    user_id=user_id,
                    prediction=prediction,
                    keyboard=keyboard,
                )
                
                if success:
                    success_count += 1
                else:
                    failure_count += 1
                    errors.append({"user_id": user_id})
            
            # Report progress
            if on_progress:
                try:
                    await on_progress(i + len(batch), total_users)
                except Exception as e:
                    logger.warning(f"Progress callback error: {e}")
            
            # Delay between batches
            if i + self.BATCH_SIZE < total_users:
                await asyncio.sleep(self.BATCH_DELAY)

        logger.info(
            f"Broadcast completed: {success_count} success, {failure_count} failed "
            f"out of {total_users} total"
        )

        return {
            "success_count": success_count,
            "failure_count": failure_count,
            "errors": errors,
        }

    async def _send_to_user(
        self,
        user_id: int,
        prediction: Prediction,
        keyboard: InlineKeyboardMarkup,
        retry_count: int = 0,
    ) -> bool:
        """Send prediction to a single user with retry logic."""
        try:
            await self._send_media_message(
                chat_id=user_id,
                prediction=prediction,
                keyboard=keyboard,
            )
            return True

        except TelegramRetryAfter as e:
            # Respect Telegram's retry-after
            if retry_count < self.MAX_RETRIES:
                logger.warning(f"Rate limited for user {user_id}, waiting {e.retry_after}s")
                await asyncio.sleep(e.retry_after)
                return await self._send_to_user(
                    user_id=user_id,
                    prediction=prediction,
                    keyboard=keyboard,
                    retry_count=retry_count + 1,
                )
            logger.error(f"Max retries exceeded for user {user_id}")
            return False

        except TelegramForbiddenError:
            # User blocked the bot - log but don't remove
            logger.info(f"User {user_id} blocked the bot")
            return False

        except TelegramBadRequest as e:
            # Bad request - user may have deleted chat
            logger.warning(f"Bad request for user {user_id}: {e}")
            return False

        except Exception as e:
            # Other errors - retry with backoff
            if retry_count < self.MAX_RETRIES:
                delay = self.RETRY_DELAY * (2 ** retry_count)
                logger.warning(f"Error for user {user_id}, retrying in {delay}s: {e}")
                await asyncio.sleep(delay)
                return await self._send_to_user(
                    user_id=user_id,
                    prediction=prediction,
                    keyboard=keyboard,
                    retry_count=retry_count + 1,
                )
            logger.error(f"Failed to send to user {user_id} after {self.MAX_RETRIES} retries: {e}")
            return False

    async def _send_media_message(
        self,
        chat_id: int,
        prediction: Prediction,
        keyboard: InlineKeyboardMarkup,
    ) -> None:
        """Send the appropriate media message based on prediction type."""
        caption = prediction.post_text

        if prediction.media_type == MediaType.PHOTO:
            await self.bot.send_photo(
                chat_id=chat_id,
                photo=prediction.media_file_id,
                caption=caption,
                reply_markup=keyboard,
            )
        elif prediction.media_type == MediaType.VIDEO:
            await self.bot.send_video(
                chat_id=chat_id,
                video=prediction.media_file_id,
                caption=caption,
                reply_markup=keyboard,
            )
        elif prediction.media_type in (MediaType.GIF, MediaType.ANIMATION):
            await self.bot.send_animation(
                chat_id=chat_id,
                animation=prediction.media_file_id,
                caption=caption,
                reply_markup=keyboard,
            )

    async def send_test_prediction(
        self,
        chat_id: int,
        prediction: Prediction,
        keyboard: InlineKeyboardMarkup,
    ) -> bool:
        """Send a test prediction to a single user (admin)."""
        try:
            await self._send_media_message(
                chat_id=chat_id,
                prediction=prediction,
                keyboard=keyboard,
            )
            return True
        except Exception as e:
            logger.error(f"Failed to send test prediction to {chat_id}: {e}")
            return False
