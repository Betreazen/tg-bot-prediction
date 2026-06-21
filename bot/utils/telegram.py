"""Helpers for safely editing Telegram messages from callback queries.

``callback.message`` is optional and may be an ``InaccessibleMessage`` (e.g. the
original message is older than 48h or was deleted). Editing it then raises
``TelegramBadRequest``. These helpers centralise that handling so individual
handlers don't crash with ``AttributeError`` / unhandled exceptions.
"""

import logging
from typing import Optional

from aiogram.exceptions import TelegramBadRequest
from aiogram.types import CallbackQuery, InlineKeyboardMarkup

logger = logging.getLogger(__name__)


async def safe_edit_text(
    callback: CallbackQuery,
    text: str,
    reply_markup: Optional[InlineKeyboardMarkup] = None,
) -> None:
    """Edit the callback message text, falling back to a new message."""
    message = callback.message
    if message is not None:
        try:
            await message.edit_text(text, reply_markup=reply_markup)
            return
        except TelegramBadRequest as e:
            # "message is not modified" is harmless; for anything else fall back.
            if "message is not modified" in str(e):
                return
            logger.debug("edit_text failed, sending new message: %s", e)

    if callback.from_user:
        try:
            await callback.bot.send_message(
                chat_id=callback.from_user.id,
                text=text,
                reply_markup=reply_markup,
            )
        except TelegramBadRequest as e:
            logger.warning("Failed to send fallback message: %s", e)


async def safe_edit_reply_markup(
    callback: CallbackQuery,
    reply_markup: Optional[InlineKeyboardMarkup] = None,
) -> bool:
    """Edit only the reply markup. Returns True on success."""
    message = callback.message
    if message is None:
        return False
    try:
        await message.edit_reply_markup(reply_markup=reply_markup)
        return True
    except TelegramBadRequest as e:
        logger.debug("edit_reply_markup failed: %s", e)
        return False
