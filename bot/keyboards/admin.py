"""Admin-facing keyboards."""

from datetime import datetime
from typing import Optional

from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton

from bot.db.models import Prediction, PredictionStatus


def get_admin_menu_keyboard() -> InlineKeyboardMarkup:
    """Create main admin menu keyboard."""
    buttons = [
        [InlineKeyboardButton(
            text="📋 Текущее предсказание",
            callback_data="admin:current_prediction"
        )],
        [InlineKeyboardButton(
            text="📊 Статистика",
            callback_data="admin:statistics"
        )],
        [InlineKeyboardButton(
            text="➕ Создать новое предсказание",
            callback_data="admin:create_prediction"
        )],
        [InlineKeyboardButton(
            text="🧪 Отправить тест себе",
            callback_data="admin:test_message"
        )],
    ]
    
    return InlineKeyboardMarkup(inline_keyboard=buttons)


def get_prediction_actions_keyboard(
    prediction: Optional[Prediction],
) -> InlineKeyboardMarkup:
    """Create prediction actions keyboard based on prediction state."""
    buttons = []
    
    if prediction:
        if prediction.status == PredictionStatus.SCHEDULED:
            buttons.append([InlineKeyboardButton(
                text="❌ Отменить",
                callback_data=f"admin:cancel_prediction:{prediction.id}"
            )])
            buttons.append([InlineKeyboardButton(
                text="🔄 Пересоздать",
                callback_data="admin:create_prediction"
            )])
        # For active predictions, no actions available
    else:
        buttons.append([InlineKeyboardButton(
            text="➕ Создать предсказание",
            callback_data="admin:create_prediction"
        )])
    
    buttons.append([InlineKeyboardButton(
        text="🔙 Назад",
        callback_data="admin:menu"
    )])
    
    return InlineKeyboardMarkup(inline_keyboard=buttons)


def get_confirm_keyboard() -> InlineKeyboardMarkup:
    """Create confirmation keyboard for prediction creation."""
    buttons = [
        [InlineKeyboardButton(
            text="✅ Подтвердить",
            callback_data="admin:confirm_creation"
        )],
        [InlineKeyboardButton(
            text="🔄 Пересоздать",
            callback_data="admin:recreate"
        )],
        [InlineKeyboardButton(
            text="❌ Отменить",
            callback_data="admin:cancel_creation"
        )],
    ]
    
    return InlineKeyboardMarkup(inline_keyboard=buttons)


def get_time_selection_keyboard(selected_date: datetime) -> InlineKeyboardMarkup:
    """Create time selection keyboard."""
    times = ["10:00", "11:00", "12:00", "13:00", "14:00", "15:00"]
    date_str = selected_date.strftime("%Y-%m-%d")
    
    buttons = []
    row = []
    for i, time in enumerate(times):
        # Use "-" instead of ":" in callback to avoid parsing issues
        time_callback = time.replace(":", "-")
        row.append(InlineKeyboardButton(
            text=time,
            callback_data=f"admin:time:{date_str}:{time_callback}"
        ))
        if len(row) == 3:
            buttons.append(row)
            row = []
    if row:
        buttons.append(row)
    
    buttons.append([InlineKeyboardButton(
        text="❌ Отменить",
        callback_data="admin:cancel_creation"
    )])
    
    return InlineKeyboardMarkup(inline_keyboard=buttons)


def get_date_selection_keyboard() -> InlineKeyboardMarkup:
    """Create date selection keyboard with next month option."""
    from datetime import date
    from calendar import monthrange
    
    today = date.today()
    
    # Calculate first day of next month
    if today.month == 12:
        next_month_first = date(today.year + 1, 1, 1)
    else:
        next_month_first = date(today.year, today.month + 1, 1)
    
    buttons = [
        [InlineKeyboardButton(
            text=f"📅 {next_month_first.strftime('%d.%m.%Y')} (начало следующего месяца)",
            callback_data=f"admin:date:{next_month_first.isoformat()}"
        )],
        [InlineKeyboardButton(
            text="📅 Сегодня",
            callback_data=f"admin:date:{today.isoformat()}"
        )],
        [InlineKeyboardButton(
            text="❌ Отменить",
            callback_data="admin:cancel_creation"
        )],
    ]
    
    return InlineKeyboardMarkup(inline_keyboard=buttons)


def get_back_keyboard() -> InlineKeyboardMarkup:
    """Create simple back button keyboard."""
    buttons = [
        [InlineKeyboardButton(
            text="🔙 Назад",
            callback_data="admin:menu"
        )],
    ]
    
    return InlineKeyboardMarkup(inline_keyboard=buttons)


def get_cancel_keyboard() -> InlineKeyboardMarkup:
    """Create cancel button keyboard for FSM steps."""
    buttons = [
        [InlineKeyboardButton(
            text="❌ Отменить создание",
            callback_data="admin:cancel_creation"
        )],
    ]
    
    return InlineKeyboardMarkup(inline_keyboard=buttons)
