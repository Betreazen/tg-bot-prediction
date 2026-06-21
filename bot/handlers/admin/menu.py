"""Admin menu and general handlers."""

import logging

from aiogram import Router, F, Bot
from aiogram.types import CallbackQuery
from aiogram.fsm.context import FSMContext
from sqlalchemy.ext.asyncio import AsyncSession

from bot.services.prediction_service import PredictionService
from bot.services.statistics_service import StatisticsService
from bot.services.broadcast_service import BroadcastService
from bot.keyboards.admin import (
    get_admin_menu_keyboard,
    get_prediction_actions_keyboard,
    get_back_keyboard,
)
from bot.keyboards.user import get_prediction_keyboard
from bot.db.models import PredictionStatus
from bot.utils.timezone import get_tz
from bot.utils.telegram import safe_edit_text

logger = logging.getLogger(__name__)
router = Router(name="admin_menu")


@router.callback_query(F.data == "admin:menu")
async def show_admin_menu(
    callback: CallbackQuery,
    state: FSMContext,
) -> None:
    """Show main admin menu."""
    await state.clear()

    await safe_edit_text(
        callback,
        "👋 Панель администратора\n\n"
        "Выберите действие:",
        reply_markup=get_admin_menu_keyboard(),
    )
    await callback.answer()


@router.callback_query(F.data == "admin:current_prediction")
async def show_current_prediction(
    callback: CallbackQuery,
    session: AsyncSession,
) -> None:
    """Show current or scheduled prediction."""
    prediction_service = PredictionService(session)
    
    active = await prediction_service.get_active_prediction()
    scheduled = await prediction_service.get_scheduled_prediction()
    
    text_parts = ["📋 <b>Текущие предсказания</b>\n"]
    
    if active:
        tz = get_tz()
        activated_str = active.activated_at.astimezone(tz).strftime("%d.%m.%Y %H:%M") if active.activated_at else "N/A"
        text_parts.append(
            f"\n<b>🟢 Активное предсказание (ID: {active.id})</b>\n"
            f"Статус: {active.status.value}\n"
            f"Активировано: {activated_str}\n"
            f"Текст: {active.post_text[:100]}...\n"
            f"\n<b>Кнопки (исходные):</b>\n"
            f"1️⃣ {active.button_1_initial}\n"
            f"2️⃣ {active.button_2_initial}\n"
            f"3️⃣ {active.button_3_initial}\n"
            f"\n<b>Кнопки (после выбора):</b>\n"
            f"1️⃣ {active.button_1_final}\n"
            f"2️⃣ {active.button_2_final}\n"
            f"3️⃣ {active.button_3_final}\n"
        )
    
    if scheduled:
        tz = get_tz()
        scheduled_str = scheduled.scheduled_at.astimezone(tz).strftime("%d.%m.%Y %H:%M")
        text_parts.append(
            f"\n<b>🕐 Запланированное предсказание (ID: {scheduled.id})</b>\n"
            f"Статус: {scheduled.status.value}\n"
            f"Запланировано на: {scheduled_str}\n"
            f"Текст: {scheduled.post_text[:100]}...\n"
            f"\n<b>Кнопки (исходные):</b>\n"
            f"1️⃣ {scheduled.button_1_initial}\n"
            f"2️⃣ {scheduled.button_2_initial}\n"
            f"3️⃣ {scheduled.button_3_initial}\n"
            f"\n<b>Кнопки (после выбора):</b>\n"
            f"1️⃣ {scheduled.button_1_final}\n"
            f"2️⃣ {scheduled.button_2_final}\n"
            f"3️⃣ {scheduled.button_3_final}\n"
        )
    
    if not active and not scheduled:
        text_parts.append("\n❌ Нет активных или запланированных предсказаний.")
    
    prediction_for_actions = scheduled if scheduled else (active if active and active.status == PredictionStatus.SCHEDULED else None)

    await safe_edit_text(
        callback,
        "".join(text_parts),
        reply_markup=get_prediction_actions_keyboard(prediction_for_actions),
    )
    await callback.answer()


@router.callback_query(F.data == "admin:statistics")
async def show_statistics(
    callback: CallbackQuery,
    session: AsyncSession,
) -> None:
    """Show current month statistics."""
    stats_service = StatisticsService(session)
    stats = await stats_service.get_current_month_statistics()
    
    month_names = {
        1: "Январь", 2: "Февраль", 3: "Март", 4: "Апрель",
        5: "Май", 6: "Июнь", 7: "Июль", 8: "Август",
        9: "Сентябрь", 10: "Октябрь", 11: "Ноябрь", 12: "Декабрь"
    }
    
    text = (
        f"📊 <b>Статистика за {month_names[stats.month]} {stats.year}</b>\n\n"
        f"👥 Всего пользователей: <b>{stats.total_users}</b>\n"
        f"✅ Сделали выбор: <b>{stats.active_users}</b>\n\n"
        f"<b>Распределение по кнопкам:</b>\n"
        f"1️⃣ Кнопка 1: <b>{stats.button_1_count}</b>\n"
        f"2️⃣ Кнопка 2: <b>{stats.button_2_count}</b>\n"
        f"3️⃣ Кнопка 3: <b>{stats.button_3_count}</b>\n"
    )
    
    await safe_edit_text(callback, text, reply_markup=get_back_keyboard())
    await callback.answer()


@router.callback_query(F.data == "admin:test_message")
async def send_test_message(
    callback: CallbackQuery,
    session: AsyncSession,
    bot: Bot,
) -> None:
    """Send test prediction to admin."""
    if not callback.from_user:
        await callback.answer("❌ Ошибка")
        return
    
    prediction_service = PredictionService(session)
    prediction = await prediction_service.get_current_or_scheduled_prediction()
    
    if not prediction:
        await callback.answer(
            "❌ Нет активного или запланированного предсказания для тестирования",
            show_alert=True,
        )
        return
    
    # Send test prediction with test_ prefix for callback data
    keyboard = get_prediction_keyboard(prediction, is_test=True)
    broadcast_service = BroadcastService(bot)
    
    success = await broadcast_service.send_test_prediction(
        chat_id=callback.from_user.id,
        prediction=prediction,
        keyboard=keyboard,
    )
    
    if success:
        await callback.answer("🧪 Тестовое сообщение отправлено!")
    else:
        await callback.answer("❌ Ошибка отправки", show_alert=True)


@router.callback_query(F.data.startswith("admin:cancel_prediction:"))
async def cancel_prediction(
    callback: CallbackQuery,
    session: AsyncSession,
) -> None:
    """Cancel a scheduled prediction."""
    if not callback.data:
        await callback.answer("❌ Ошибка")
        return
    
    try:
        prediction_id = int(callback.data.split(":")[-1])
    except ValueError:
        await callback.answer("❌ Ошибка данных")
        return
    
    prediction_service = PredictionService(session)
    prediction = await prediction_service.get_prediction_by_id(prediction_id)
    
    if not prediction:
        await callback.answer("❌ Предсказание не найдено", show_alert=True)
        return
    
    if prediction.status != PredictionStatus.SCHEDULED:
        await callback.answer(
            "❌ Можно отменить только запланированное предсказание",
            show_alert=True,
        )
        return
    
    await prediction_service.cancel_prediction(prediction)
    
    await callback.answer("✅ Предсказание отменено")
    
    # Refresh the view
    await show_current_prediction(callback, session)
