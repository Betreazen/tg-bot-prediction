"""Admin prediction creation FSM handler."""

import logging
from datetime import datetime, date

import pytz
from aiogram import Router, F, Bot
from aiogram.types import CallbackQuery, Message
from aiogram.fsm.context import FSMContext
from sqlalchemy.ext.asyncio import AsyncSession

from bot.config.settings import settings
from bot.services.prediction_service import PredictionService
from bot.services.user_service import UserService
from bot.keyboards.admin import (
    get_admin_menu_keyboard,
    get_confirm_keyboard,
    get_date_selection_keyboard,
    get_time_selection_keyboard,
    get_cancel_keyboard,
)
from bot.db.models import MediaType
from bot.states.admin import CreatePredictionState

logger = logging.getLogger(__name__)
router = Router(name="admin_create_prediction")


# Step 1: Start creation - ask for media
@router.callback_query(F.data == "admin:create_prediction")
async def start_prediction_creation(
    callback: CallbackQuery,
    state: FSMContext,
) -> None:
    """Start the prediction creation flow."""
    await state.clear()
    await state.set_state(CreatePredictionState.waiting_for_media)
    
    await callback.message.edit_text(
        "📷 <b>Шаг 1/7: Загрузка медиа</b>\n\n"
        "Отправьте фото, видео, GIF или анимацию для предсказания.",
        reply_markup=get_cancel_keyboard(),
        parse_mode="HTML",
    )
    await callback.answer()


@router.message(CreatePredictionState.waiting_for_media)
async def process_media(
    message: Message,
    state: FSMContext,
) -> None:
    """Process uploaded media."""
    media_type = None
    file_id = None
    
    if message.photo:
        media_type = MediaType.PHOTO
        file_id = message.photo[-1].file_id
    elif message.video:
        media_type = MediaType.VIDEO
        file_id = message.video.file_id
    elif message.animation:
        media_type = MediaType.ANIMATION
        file_id = message.animation.file_id
    elif message.document and message.document.mime_type and "gif" in message.document.mime_type:
        media_type = MediaType.GIF
        file_id = message.document.file_id
    
    if not media_type or not file_id:
        await message.answer(
            "❌ Пожалуйста, отправьте фото, видео, GIF или анимацию.",
            reply_markup=get_cancel_keyboard(),
        )
        return
    
    await state.update_data(media_type=media_type.value, media_file_id=file_id)
    await state.set_state(CreatePredictionState.waiting_for_text)
    
    await message.answer(
        "✅ Медиа получено!\n\n"
        "📝 <b>Шаг 2/7: Текст предсказания</b>\n\n"
        "Отправьте текст для предсказания.",
        reply_markup=get_cancel_keyboard(),
        parse_mode="HTML",
    )


# Step 2: Post text
@router.message(CreatePredictionState.waiting_for_text)
async def process_text(
    message: Message,
    state: FSMContext,
) -> None:
    """Process prediction text."""
    if not message.text:
        await message.answer(
            "❌ Пожалуйста, отправьте текстовое сообщение.",
            reply_markup=get_cancel_keyboard(),
        )
        return
    
    await state.update_data(post_text=message.text)
    await state.set_state(CreatePredictionState.waiting_for_button_1_initial)
    
    await message.answer(
        "✅ Текст сохранён!\n\n"
        "🔘 <b>Шаг 3/7: Исходные тексты кнопок</b>\n\n"
        "Отправьте текст для <b>кнопки 1</b> (исходный).",
        reply_markup=get_cancel_keyboard(),
        parse_mode="HTML",
    )


# Step 3: Initial button texts
@router.message(CreatePredictionState.waiting_for_button_1_initial)
async def process_button_1_initial(
    message: Message,
    state: FSMContext,
) -> None:
    """Process button 1 initial text."""
    if not message.text:
        await message.answer("❌ Отправьте текст.", reply_markup=get_cancel_keyboard())
        return
    
    await state.update_data(button_1_initial=message.text)
    await state.set_state(CreatePredictionState.waiting_for_button_2_initial)
    
    await message.answer(
        f"✅ Кнопка 1: {message.text}\n\n"
        "Отправьте текст для <b>кнопки 2</b> (исходный).",
        reply_markup=get_cancel_keyboard(),
        parse_mode="HTML",
    )


@router.message(CreatePredictionState.waiting_for_button_2_initial)
async def process_button_2_initial(
    message: Message,
    state: FSMContext,
) -> None:
    """Process button 2 initial text."""
    if not message.text:
        await message.answer("❌ Отправьте текст.", reply_markup=get_cancel_keyboard())
        return
    
    await state.update_data(button_2_initial=message.text)
    await state.set_state(CreatePredictionState.waiting_for_button_3_initial)
    
    await message.answer(
        f"✅ Кнопка 2: {message.text}\n\n"
        "Отправьте текст для <b>кнопки 3</b> (исходный).",
        reply_markup=get_cancel_keyboard(),
        parse_mode="HTML",
    )


@router.message(CreatePredictionState.waiting_for_button_3_initial)
async def process_button_3_initial(
    message: Message,
    state: FSMContext,
) -> None:
    """Process button 3 initial text."""
    if not message.text:
        await message.answer("❌ Отправьте текст.", reply_markup=get_cancel_keyboard())
        return
    
    await state.update_data(button_3_initial=message.text)
    await state.set_state(CreatePredictionState.waiting_for_button_1_final)
    
    await message.answer(
        f"✅ Кнопка 3: {message.text}\n\n"
        "🔘 <b>Шаг 4/7: Финальные тексты кнопок</b>\n\n"
        "Теперь отправьте текст для <b>кнопки 1</b> (после выбора).",
        reply_markup=get_cancel_keyboard(),
        parse_mode="HTML",
    )


# Step 4: Final button texts
@router.message(CreatePredictionState.waiting_for_button_1_final)
async def process_button_1_final(
    message: Message,
    state: FSMContext,
) -> None:
    """Process button 1 final text."""
    if not message.text:
        await message.answer("❌ Отправьте текст.", reply_markup=get_cancel_keyboard())
        return
    
    await state.update_data(button_1_final=message.text)
    await state.set_state(CreatePredictionState.waiting_for_button_2_final)
    
    await message.answer(
        f"✅ Финальный текст кнопки 1: {message.text}\n\n"
        "Отправьте текст для <b>кнопки 2</b> (после выбора).",
        reply_markup=get_cancel_keyboard(),
        parse_mode="HTML",
    )


@router.message(CreatePredictionState.waiting_for_button_2_final)
async def process_button_2_final(
    message: Message,
    state: FSMContext,
) -> None:
    """Process button 2 final text."""
    if not message.text:
        await message.answer("❌ Отправьте текст.", reply_markup=get_cancel_keyboard())
        return
    
    await state.update_data(button_2_final=message.text)
    await state.set_state(CreatePredictionState.waiting_for_button_3_final)
    
    await message.answer(
        f"✅ Финальный текст кнопки 2: {message.text}\n\n"
        "Отправьте текст для <b>кнопки 3</b> (после выбора).",
        reply_markup=get_cancel_keyboard(),
        parse_mode="HTML",
    )


@router.message(CreatePredictionState.waiting_for_button_3_final)
async def process_button_3_final(
    message: Message,
    state: FSMContext,
) -> None:
    """Process button 3 final text."""
    if not message.text:
        await message.answer("❌ Отправьте текст.", reply_markup=get_cancel_keyboard())
        return
    
    await state.update_data(button_3_final=message.text)
    await state.set_state(CreatePredictionState.waiting_for_date)
    
    await message.answer(
        f"✅ Финальный текст кнопки 3: {message.text}\n\n"
        "📅 <b>Шаг 5/7: Дата публикации</b>\n\n"
        "Выберите дату публикации:",
        reply_markup=get_date_selection_keyboard(),
        parse_mode="HTML",
    )


# Step 5: Date/Time selection
@router.callback_query(F.data.startswith("admin:date:"), CreatePredictionState.waiting_for_date)
async def process_date_selection(
    callback: CallbackQuery,
    state: FSMContext,
) -> None:
    """Process date selection."""
    if not callback.data:
        await callback.answer("❌ Ошибка")
        return
    
    date_str = callback.data.split(":")[-1]
    try:
        selected_date = datetime.strptime(date_str, "%Y-%m-%d")
    except ValueError:
        await callback.answer("❌ Неверная дата")
        return
    
    await state.update_data(selected_date=date_str)
    await state.set_state(CreatePredictionState.waiting_for_time)
    
    await callback.message.edit_text(
        f"✅ Дата: {selected_date.strftime('%d.%m.%Y')}\n\n"
        "🕐 <b>Шаг 5/7: Время публикации</b>\n\n"
        "Выберите время публикации (GMT+3):",
        reply_markup=get_time_selection_keyboard(selected_date),
        parse_mode="HTML",
    )
    await callback.answer()


@router.callback_query(F.data.startswith("admin:time:"), CreatePredictionState.waiting_for_time)
async def process_time_selection(
    callback: CallbackQuery,
    state: FSMContext,
) -> None:
    """Process time selection and show preview."""
    if not callback.data:
        await callback.answer("❌ Ошибка")
        return
    
    parts = callback.data.split(":")
    if len(parts) < 4:
        await callback.answer("❌ Ошибка данных")
        return
    
    date_str = parts[2]
    # Time was stored with "-" instead of ":" to avoid split issues
    time_str = parts[3].replace("-", ":")
    
    # Combine date and time
    tz = pytz.timezone(settings.scheduler_timezone)
    try:
        dt = datetime.strptime(f"{date_str} {time_str}", "%Y-%m-%d %H:%M")
        scheduled_at = tz.localize(dt)
    except ValueError:
        await callback.answer("❌ Ошибка даты/времени")
        return
    
    await state.update_data(scheduled_at=scheduled_at.isoformat())
    await state.set_state(CreatePredictionState.waiting_for_confirmation)
    
    # Show preview
    data = await state.get_data()
    
    preview_text = (
        "📋 <b>Шаг 6/7: Предварительный просмотр</b>\n\n"
        f"<b>Текст:</b>\n{data['post_text'][:200]}...\n\n"
        f"<b>Кнопки (исходные):</b>\n"
        f"1️⃣ {data['button_1_initial']}\n"
        f"2️⃣ {data['button_2_initial']}\n"
        f"3️⃣ {data['button_3_initial']}\n\n"
        f"<b>Кнопки (после выбора):</b>\n"
        f"1️⃣ {data['button_1_final']}\n"
        f"2️⃣ {data['button_2_final']}\n"
        f"3️⃣ {data['button_3_final']}\n\n"
        f"📅 <b>Публикация:</b> {scheduled_at.strftime('%d.%m.%Y %H:%M')} (GMT+3)\n\n"
        "Подтвердите создание предсказания:"
    )
    
    await callback.message.edit_text(
        preview_text,
        reply_markup=get_confirm_keyboard(),
        parse_mode="HTML",
    )
    await callback.answer()


# Step 7: Confirmation
@router.callback_query(F.data == "admin:confirm_creation", CreatePredictionState.waiting_for_confirmation)
async def confirm_creation(
    callback: CallbackQuery,
    state: FSMContext,
    session: AsyncSession,
) -> None:
    """Confirm and create the prediction."""
    if not callback.from_user:
        await callback.answer("❌ Ошибка")
        return
    
    data = await state.get_data()
    
    # Get admin user
    user_service = UserService(session)
    admin_user = await user_service.get_or_create_user(callback.from_user.id)
    
    # Parse scheduled_at
    tz = pytz.timezone(settings.scheduler_timezone)
    scheduled_at = datetime.fromisoformat(data["scheduled_at"])
    
    # Create prediction
    prediction_service = PredictionService(session)
    prediction = await prediction_service.create_prediction(
        media_type=MediaType(data["media_type"]),
        media_file_id=data["media_file_id"],
        post_text=data["post_text"],
        button_1_initial=data["button_1_initial"],
        button_2_initial=data["button_2_initial"],
        button_3_initial=data["button_3_initial"],
        button_1_final=data["button_1_final"],
        button_2_final=data["button_2_final"],
        button_3_final=data["button_3_final"],
        scheduled_at=scheduled_at,
        created_by_admin_id=admin_user.id,
    )
    
    await state.clear()
    
    await callback.message.edit_text(
        f"✅ <b>Предсказание создано!</b>\n\n"
        f"ID: {prediction.id}\n"
        f"Статус: {prediction.status.value}\n"
        f"Запланировано на: {scheduled_at.strftime('%d.%m.%Y %H:%M')} (GMT+3)\n\n"
        "Предсказание будет автоматически отправлено всем пользователям в указанное время.",
        reply_markup=get_admin_menu_keyboard(),
        parse_mode="HTML",
    )
    await callback.answer("✅ Предсказание создано!")


@router.callback_query(F.data == "admin:recreate")
async def recreate_prediction(
    callback: CallbackQuery,
    state: FSMContext,
) -> None:
    """Restart the creation flow."""
    await state.clear()
    await start_prediction_creation(callback, state)


@router.callback_query(F.data == "admin:cancel_creation")
async def cancel_creation(
    callback: CallbackQuery,
    state: FSMContext,
) -> None:
    """Cancel the creation flow."""
    await state.clear()
    
    await callback.message.edit_text(
        "❌ Создание предсказания отменено.\n\n"
        "Выберите действие:",
        reply_markup=get_admin_menu_keyboard(),
    )
    await callback.answer()
