"""User prediction button selection handler."""

from aiogram import Router, F
from aiogram.types import CallbackQuery
from sqlalchemy.ext.asyncio import AsyncSession

from bot.services.prediction_service import PredictionService
from bot.keyboards.user import get_selected_keyboard
from bot.utils.timezone import now as tz_now
from bot.utils.telegram import safe_edit_reply_markup

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
    now = tz_now()

    # Fast-path UX check (the atomic insert below is the real guard).
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

    # Atomically record the choice. Returns False if a concurrent click (or a
    # previous choice this month) already won — closes the race condition.
    recorded = await prediction_service.record_user_choice(
        telegram_user_id=user_id,
        prediction_id=prediction_id,
        selected_button=button_number,
        is_test=False,
    )

    if not recorded:
        await callback.answer(
            "Вы уже сделали свой выбор в этом месяце!",
            show_alert=True,
        )
        return

    # Update keyboard to show only selected button with final text
    selected_keyboard = get_selected_keyboard(prediction, button_number)
    await safe_edit_reply_markup(callback, selected_keyboard)
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
    is_admin: bool,
) -> None:
    """Handle admin test button selection (not counted in stats)."""
    if not callback.from_user or not callback.data:
        await callback.answer()
        return

    # Test selections are admin-only; reject crafted callbacks from regular users.
    if not is_admin:
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
    await safe_edit_reply_markup(callback, selected_keyboard)
    await callback.answer("🧪 Тестовый выбор (не учитывается в статистике)")
