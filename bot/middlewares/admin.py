"""Admin check middleware."""

from typing import Any, Awaitable, Callable, Dict

from aiogram import BaseMiddleware
from aiogram.types import TelegramObject, Message, CallbackQuery

from bot.config.settings import settings


class AdminMiddleware(BaseMiddleware):
    """Middleware that checks if user is admin and adds flag to data."""

    async def __call__(
        self,
        handler: Callable[[TelegramObject, Dict[str, Any]], Awaitable[Any]],
        event: TelegramObject,
        data: Dict[str, Any],
    ) -> Any:
        user_id = None
        
        if isinstance(event, Message) and event.from_user:
            user_id = event.from_user.id
        elif isinstance(event, CallbackQuery) and event.from_user:
            user_id = event.from_user.id
        
        data["is_admin"] = user_id in settings.admin_ids_list if user_id else False
        
        return await handler(event, data)
