"""User prediction button selection handler."""

from datetime import datetime

import pytz
from aiogram import Router, F
from aiogram.types import CallbackQuery
from sqlalchemy.ext.asyncio import AsyncSession

from bot.config.settings import settings
from bot.services.prediction_service import PredictionService
from bot.keyboards.user import get_selected_keyboard

router = Router(name="user_prediction")


@router.callback_query(F.data.startswith("select:"))
async def handle_button_selection(
    callback: CallbackQuery,
    session: AsyncSession,
) -> None:
    """Handle user button selection."""
    if not callback.from_user or not callback.data:
        await callback.answer()
        return

    # Parse callback data: select:{prediction_id}:{button_number}
    parts = callback.data.split(":")
    if len(parts) != 3:
        await callback.answer("❌ Ошибка данных")
        return
    
    try:
        prediction_id = int(parts[1])
        button_number = int(parts[2])
    except ValueError:
        await callback.answer("❌ Ошибка данных")
        return
    
    if button_number not in (1, 2, 3):
        await callback.answer("❌ Неверный номер кнопки")
        return
    
    user_id = callback.from_user.id
    prediction_service = PredictionService(session)
    tz = pytz.timezone(settings.scheduler_timezone)
    now = datetime.now(tz)
    
    # Check if user already chose this month
    has_chosen = await prediction_service.has_user_chosen_this_month(
        telegram_user_id=user_id,
        year=now.year,
        month=now.month,
    )
    
    if has_chosen:
        await callback.answer(
            "Вы уже сделали свой выбор в этом месяце!",
            show_alert=True,
        )
        return
    
    # Get prediction
    prediction = await prediction_service.get_prediction_by_id(prediction_id)
    if not prediction:
        await callback.answer("❌ Предсказание не найдено")
        return
    
    # Record the choice
    await prediction_service.record_user_choice(
        telegram_user_id=user_id,
        prediction_id=prediction_id,
        selected_button=button_number,
        is_test=False,
    )
    
    # Update keyboard to show only selected button with final text
    selected_keyboard = get_selected_keyboard(prediction, button_number)
    
    try:
        await callback.message.edit_reply_markup(reply_markup=selected_keyboard)
        await callback.answer("✨ Ваш выбор сохранён!")
    except Exception:
        await callback.answer("✨ Ваш выбор сохранён!")


@router.callback_query(F.data.startswith("selected:"))
async def handle_already_selected(
    callback: CallbackQuery,
) -> None:
    """Handle click on already selected button."""
    await callback.answer(
        "Вы уже сделали свой выбор!",
        show_alert=False,
    )


@router.callback_query(F.data.startswith("test_select:"))
async def handle_test_button_selection(
    callback: CallbackQuery,
    session: AsyncSession,
) -> None:
    """Handle admin test button selection (not counted in stats)."""
    if not callback.from_user or not callback.data:
        await callback.answer()
        return

    # Parse callback data: test_select:{prediction_id}:{button_number}
    parts = callback.data.split(":")
    if len(parts) != 3:
        await callback.answer("❌ Ошибка данных")
        return
    
    try:
        prediction_id = int(parts[1])
        button_number = int(parts[2])
    except ValueError:
        await callback.answer("❌ Ошибка данных")
        return
    
    prediction_service = PredictionService(session)
    prediction = await prediction_service.get_prediction_by_id(prediction_id)
    
    if not prediction:
        await callback.answer("❌ Предсказание не найдено")
        return
    
    # Update keyboard to show only selected button with final text
    selected_keyboard = get_selected_keyboard(prediction, button_number)
    
    try:
        await callback.message.edit_reply_markup(reply_markup=selected_keyboard)
        await callback.answer("🧪 Тестовый выбор (не учитывается в статистике)")
    except Exception:
        await callback.answer("🧪 Тестовый выбор")
