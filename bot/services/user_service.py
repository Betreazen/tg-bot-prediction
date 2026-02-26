"""User service for managing users."""

from typing import Optional, List

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from bot.db.models import User
from bot.config.settings import settings


class UserService:
    """Service for user-related operations."""

    def __init__(self, session: AsyncSession):
        self.session = session

    async def get_or_create_user(self, telegram_user_id: int) -> User:
        """Get existing user or create new one."""
        user = await self.get_user_by_telegram_id(telegram_user_id)
        if user:
            return user

        # Create new user
        is_admin = telegram_user_id in settings.admin_ids_list
        user = User(
            telegram_user_id=telegram_user_id,
            is_admin=is_admin,
        )
        self.session.add(user)
        await self.session.flush()
        return user

    async def get_user_by_telegram_id(self, telegram_user_id: int) -> Optional[User]:
        """Get user by Telegram ID."""
        result = await self.session.execute(
            select(User).where(User.telegram_user_id == telegram_user_id)
        )
        return result.scalar_one_or_none()

    async def get_user_by_id(self, user_id: int) -> Optional[User]:
        """Get user by internal ID."""
        result = await self.session.execute(
            select(User).where(User.id == user_id)
        )
        return result.scalar_one_or_none()

    async def get_all_users(self) -> List[User]:
        """Get all users."""
        result = await self.session.execute(select(User))
        return list(result.scalars().all())

    async def get_all_user_telegram_ids(self) -> List[int]:
        """Get all user Telegram IDs for broadcasting."""
        result = await self.session.execute(
            select(User.telegram_user_id)
        )
        return [row[0] for row in result.all()]

    async def get_total_users_count(self) -> int:
        """Get total number of users."""
        from sqlalchemy import func
        result = await self.session.execute(
            select(func.count(User.id))
        )
        return result.scalar() or 0

    def is_admin(self, telegram_user_id: int) -> bool:
        """Check if user is admin by Telegram ID."""
        return telegram_user_id in settings.admin_ids_list
