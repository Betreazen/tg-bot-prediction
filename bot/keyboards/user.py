"""User-facing keyboards."""

from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton

from bot.db.models import Prediction


def get_prediction_keyboard(
    prediction: Prediction,
    is_test: bool = False,
) -> InlineKeyboardMarkup:
    """
    Create inline keyboard with 3 prediction buttons.
    
    Args:
        prediction: The prediction to create buttons for
        is_test: Whether this is a test message for admin
    """
    prefix = "test_" if is_test else ""
    
    buttons = [
        [InlineKeyboardButton(
            text=prediction.button_1_initial,
            callback_data=f"{prefix}select:{prediction.id}:1"
        )],
        [InlineKeyboardButton(
            text=prediction.button_2_initial,
            callback_data=f"{prefix}select:{prediction.id}:2"
        )],
        [InlineKeyboardButton(
            text=prediction.button_3_initial,
            callback_data=f"{prefix}select:{prediction.id}:3"
        )],
    ]
    
    return InlineKeyboardMarkup(inline_keyboard=buttons)


def get_selected_keyboard(
    prediction: Prediction,
    selected_button: int,
) -> InlineKeyboardMarkup:
    """
    Create keyboard showing only the selected button with final text.
    
    Args:
        prediction: The prediction
        selected_button: Which button was selected (1, 2, or 3)
    """
    final_text = prediction.get_final_button(selected_button)
    
    # Single button with final text, no callback (disabled)
    buttons = [
        [InlineKeyboardButton(
            text=final_text,
            callback_data=f"selected:{prediction.id}:{selected_button}"
        )],
    ]
    
    return InlineKeyboardMarkup(inline_keyboard=buttons)
