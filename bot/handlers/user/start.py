"""User /start command handler."""

from datetime import datetime

import pytz
from aiogram import Router, F
from aiogram.types import Message
from aiogram.filters import CommandStart
from sqlalchemy.ext.asyncio import AsyncSession

from bot.config.settings import settings
from bot.services.user_service import UserService
from bot.services.prediction_service import PredictionService
from bot.keyboards.user import get_prediction_keyboard
from bot.keyboards.admin import get_admin_menu_keyboard
from bot.db.models import MediaType

router = Router(name="user_start")


@router.message(CommandStart())
async def cmd_start(
    message: Message,
    session: AsyncSession,
    is_admin: bool,
) -> None:
    """Handle /start command."""
    if not message.from_user:
        return

    user_id = message.from_user.id
    
    # Ensure user exists in database
    user_service = UserService(session)
    await user_service.get_or_create_user(user_id)
    
    # Admin gets admin menu
    if is_admin:
        await message.answer(
            "👋 Добро пожаловать в панель администратора!\n\n"
            "Выберите действие:",
            reply_markup=get_admin_menu_keyboard(),
        )
        return
    
    # Regular user flow
    prediction_service = PredictionService(session)
    tz = pytz.timezone(settings.scheduler_timezone)
    now = datetime.now(tz)
    
    # Check if there's an active prediction
    active_prediction = await prediction_service.get_active_prediction()
    
    if not active_prediction:
        await message.answer(
            "🔮 Скоро вы получите новое предсказание.\n\n"
            "Ожидайте!"
        )
        return
    
    # Check if user already chose this month
    has_chosen = await prediction_service.has_user_chosen_this_month(
        telegram_user_id=user_id,
        year=now.year,
        month=now.month,
    )
    
    if has_chosen:
        await message.answer(
            "✨ Вы уже получили своё предсказание в этом месяце.\n\n"
            "Новое предсказание будет доступно в следующем месяце!"
        )
        return
    
    # Send prediction with buttons
    keyboard = get_prediction_keyboard(active_prediction)
    
    try:
        if active_prediction.media_type == MediaType.PHOTO:
            await message.answer_photo(
                photo=active_prediction.media_file_id,
                caption=active_prediction.post_text,
                reply_markup=keyboard,
            )
        elif active_prediction.media_type == MediaType.VIDEO:
            await message.answer_video(
                video=active_prediction.media_file_id,
                caption=active_prediction.post_text,
                reply_markup=keyboard,
            )
        elif active_prediction.media_type in (MediaType.GIF, MediaType.ANIMATION):
            await message.answer_animation(
                animation=active_prediction.media_file_id,
                caption=active_prediction.post_text,
                reply_markup=keyboard,
            )
    except Exception as e:
        await message.answer(
            "❌ Произошла ошибка при отправке предсказания. "
            "Пожалуйста, попробуйте позже."
        )
