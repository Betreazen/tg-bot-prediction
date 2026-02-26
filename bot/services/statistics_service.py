"""Statistics service for generating reports."""

from dataclasses import dataclass
from datetime import datetime
from typing import Optional

import pytz
from sqlalchemy import select, func, and_
from sqlalchemy.ext.asyncio import AsyncSession

from bot.db.models import User, UserPredictionChoice, Prediction, PredictionStatus
from bot.config.settings import settings


@dataclass
class MonthlyStatistics:
    """Statistics for the current month."""

    year: int
    month: int
    total_users: int
    active_users: int  # Users who made a choice this month
    button_1_count: int
    button_2_count: int
    button_3_count: int


class StatisticsService:
    """Service for statistics operations."""

    def __init__(self, session: AsyncSession):
        self.session = session
        self.tz = pytz.timezone(settings.scheduler_timezone)

    async def get_current_month_statistics(self) -> MonthlyStatistics:
        """Get statistics for the current month."""
        now = datetime.now(self.tz)
        year = now.year
        month = now.month

        # Total users
        total_users_result = await self.session.execute(
            select(func.count(User.id))
        )
        total_users = total_users_result.scalar() or 0

        # Choices this month (excluding test choices)
        choices_query = select(UserPredictionChoice).where(
            and_(
                UserPredictionChoice.year == year,
                UserPredictionChoice.month == month,
                UserPredictionChoice.is_test == False,  # noqa: E712
            )
        )
        choices_result = await self.session.execute(choices_query)
        choices = list(choices_result.scalars().all())

        # Count active users and button selections
        active_users = len(choices)
        button_1_count = sum(1 for c in choices if c.selected_button == 1)
        button_2_count = sum(1 for c in choices if c.selected_button == 2)
        button_3_count = sum(1 for c in choices if c.selected_button == 3)

        return MonthlyStatistics(
            year=year,
            month=month,
            total_users=total_users,
            active_users=active_users,
            button_1_count=button_1_count,
            button_2_count=button_2_count,
            button_3_count=button_3_count,
        )

    async def get_prediction_statistics(
        self, prediction_id: int
    ) -> Optional[dict]:
        """Get statistics for a specific prediction."""
        choices_query = select(UserPredictionChoice).where(
            and_(
                UserPredictionChoice.prediction_id == prediction_id,
                UserPredictionChoice.is_test == False,  # noqa: E712
            )
        )
        choices_result = await self.session.execute(choices_query)
        choices = list(choices_result.scalars().all())

        if not choices:
            return {
                "total_choices": 0,
                "button_1_count": 0,
                "button_2_count": 0,
                "button_3_count": 0,
            }

        return {
            "total_choices": len(choices),
            "button_1_count": sum(1 for c in choices if c.selected_button == 1),
            "button_2_count": sum(1 for c in choices if c.selected_button == 2),
            "button_3_count": sum(1 for c in choices if c.selected_button == 3),
        }
