"""Tests for inline keyboard construction."""

from bot.db.models import Prediction
from bot.keyboards.user import get_prediction_keyboard, get_selected_keyboard


def _prediction() -> Prediction:
    return Prediction(
        id=42,
        button_1_initial="A1",
        button_2_initial="B1",
        button_3_initial="C1",
        button_1_final="A2",
        button_2_final="B2",
        button_3_final="C2",
    )


def test_prediction_keyboard_callback_data():
    kb = get_prediction_keyboard(_prediction())
    rows = kb.inline_keyboard
    assert [b[0].callback_data for b in rows] == [
        "select:42:1",
        "select:42:2",
        "select:42:3",
    ]
    assert rows[0][0].text == "A1"


def test_prediction_keyboard_test_prefix():
    kb = get_prediction_keyboard(_prediction(), is_test=True)
    assert kb.inline_keyboard[0][0].callback_data == "test_select:42:1"


def test_selected_keyboard_shows_final_text_only():
    kb = get_selected_keyboard(_prediction(), 2)
    assert len(kb.inline_keyboard) == 1
    button = kb.inline_keyboard[0][0]
    assert button.text == "B2"
    assert button.callback_data == "selected:42:2"
