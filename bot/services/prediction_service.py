"""Prediction service for managing predictions."""

from datetime import datetime
from typing import Optional

import pytz
from sqlalchemy import select, and_
from sqlalchemy.ext.asyncio import AsyncSession

from bot.db.models import Prediction, PredictionStatus, MediaType, UserPredictionChoice
from bot.config.settings import settings


class PredictionService:
    """Service for prediction-related operations."""

    def __init__(self, session: AsyncSession):
        self.session = session
        self.tz = pytz.timezone(settings.scheduler_timezone)

    async def get_active_prediction(self) -> Optional[Prediction]:
        """Get the currently active prediction."""
        result = await self.session.execute(
            select(Prediction).where(Prediction.status == PredictionStatus.ACTIVE)
        )
        return result.scalar_one_or_none()

    async def get_scheduled_prediction(self) -> Optional[Prediction]:
        """Get the scheduled prediction."""
        result = await self.session.execute(
            select(Prediction).where(Prediction.status == PredictionStatus.SCHEDULED)
        )
        return result.scalar_one_or_none()

    async def get_prediction_by_id(self, prediction_id: int) -> Optional[Prediction]:
        """Get prediction by ID."""
        result = await self.session.execute(
            select(Prediction).where(Prediction.id == prediction_id)
        )
        return result.scalar_one_or_none()

    async def create_prediction(
        self,
        media_type: MediaType,
        media_file_id: str,
        post_text: str,
        button_1_initial: str,
        button_2_initial: str,
        button_3_initial: str,
        button_1_final: str,
        button_2_final: str,
        button_3_final: str,
        scheduled_at: datetime,
        created_by_admin_id: Optional[int] = None,
    ) -> Prediction:
        """Create a new scheduled prediction."""
        # Cancel any existing scheduled prediction
        existing_scheduled = await self.get_scheduled_prediction()
        if existing_scheduled:
            existing_scheduled.status = PredictionStatus.CANCELLED
            await self.session.flush()

        prediction = Prediction(
            status=PredictionStatus.SCHEDULED,
            media_type=media_type,
            media_file_id=media_file_id,
            post_text=post_text,
            button_1_initial=button_1_initial,
            button_2_initial=button_2_initial,
            button_3_initial=button_3_initial,
            button_1_final=button_1_final,
            button_2_final=button_2_final,
            button_3_final=button_3_final,
            scheduled_at=scheduled_at,
            created_by_admin_id=created_by_admin_id,
        )
        self.session.add(prediction)
        await self.session.flush()
        return prediction

    async def activate_prediction(self, prediction: Prediction) -> None:
        """Activate a scheduled prediction."""
        # Archive any existing active prediction
        active = await self.get_active_prediction()
        if active:
            active.status = PredictionStatus.ARCHIVED
            await self.session.flush()

        # Activate this prediction
        prediction.status = PredictionStatus.ACTIVE
        prediction.activated_at = datetime.now(self.tz)
        prediction.broadcast_started = True
        await self.session.flush()

    async def mark_broadcast_completed(self, prediction: Prediction) -> None:
        """Mark prediction broadcast as completed."""
        prediction.broadcast_completed = True
        await self.session.flush()

    async def cancel_prediction(self, prediction: Prediction) -> None:
        """Cancel a prediction."""
        prediction.status = PredictionStatus.CANCELLED
        await self.session.flush()

    async def has_user_chosen_this_month(
        self, telegram_user_id: int, year: int, month: int
    ) -> bool:
        """Check if user has already made a choice this month."""
        result = await self.session.execute(
            select(UserPredictionChoice).where(
                and_(
                    UserPredictionChoice.telegram_user_id == telegram_user_id,
                    UserPredictionChoice.year == year,
                    UserPredictionChoice.month == month,
                    UserPredictionChoice.is_test == False,  # noqa: E712
                )
            )
        )
        return result.scalar_one_or_none() is not None

    async def get_user_choice(
        self, telegram_user_id: int, prediction_id: int
    ) -> Optional[UserPredictionChoice]:
        """Get user's choice for a specific prediction."""
        result = await self.session.execute(
            select(UserPredictionChoice).where(
                and_(
                    UserPredictionChoice.telegram_user_id == telegram_user_id,
                    UserPredictionChoice.prediction_id == prediction_id,
                    UserPredictionChoice.is_test == False,  # noqa: E712
                )
            )
        )
        return result.scalar_one_or_none()

    async def record_user_choice(
        self,
        telegram_user_id: int,
        prediction_id: int,
        selected_button: int,
        is_test: bool = False,
    ) -> UserPredictionChoice:
        """Record user's button selection."""
        now = datetime.now(self.tz)

        choice = UserPredictionChoice(
            telegram_user_id=telegram_user_id,
            prediction_id=prediction_id,
            selected_button=selected_button,
            year=now.year,
            month=now.month,
            is_test=is_test,
        )
        self.session.add(choice)
        await self.session.flush()
        return choice

    async def get_current_or_scheduled_prediction(self) -> Optional[Prediction]:
        """Get current active or scheduled prediction for admin view."""
        active = await self.get_active_prediction()
        if active:
            return active
        return await self.get_scheduled_prediction()
