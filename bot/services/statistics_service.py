"""Statistics service for generating reports."""

from dataclasses import dataclass
from typing import Dict

from sqlalchemy import select, func, and_
from sqlalchemy.ext.asyncio import AsyncSession

from bot.db.models import User, UserPredictionChoice
from bot.utils.timezone import now as tz_now


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

    async def _count_by_button(self, *conditions) -> Dict[int, int]:
        """Aggregate choices per button in the database (no rows pulled into Python)."""
        result = await self.session.execute(
            select(
                UserPredictionChoice.selected_button,
                func.count(),
            )
            .where(and_(*conditions))
            .group_by(UserPredictionChoice.selected_button)
        )
        return {button: count for button, count in result.all()}

    async def get_current_month_statistics(self) -> MonthlyStatistics:
        """Get statistics for the current month."""
        now = tz_now()
        year = now.year
        month = now.month

        total_users_result = await self.session.execute(select(func.count(User.id)))
        total_users = total_users_result.scalar() or 0

        counts = await self._count_by_button(
            UserPredictionChoice.year == year,
            UserPredictionChoice.month == month,
            UserPredictionChoice.is_test.is_(False),
        )

        return MonthlyStatistics(
            year=year,
            month=month,
            total_users=total_users,
            active_users=sum(counts.values()),
            button_1_count=counts.get(1, 0),
            button_2_count=counts.get(2, 0),
            button_3_count=counts.get(3, 0),
        )

    async def get_prediction_statistics(self, prediction_id: int) -> dict:
        """Get statistics for a specific prediction."""
        counts = await self._count_by_button(
            UserPredictionChoice.prediction_id == prediction_id,
            UserPredictionChoice.is_test.is_(False),
        )

        return {
            "total_choices": sum(counts.values()),
            "button_1_count": counts.get(1, 0),
            "button_2_count": counts.get(2, 0),
            "button_3_count": counts.get(3, 0),
        }
