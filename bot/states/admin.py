"""FSM states for admin flows."""

from aiogram.fsm.state import State, StatesGroup


class CreatePredictionState(StatesGroup):
    """States for prediction creation flow."""
    
    # Step 1: Upload media
    waiting_for_media = State()
    
    # Step 2: Enter post text
    waiting_for_text = State()
    
    # Step 3: Initial button texts
    waiting_for_button_1_initial = State()
    waiting_for_button_2_initial = State()
    waiting_for_button_3_initial = State()
    
    # Step 4: Final button texts
    waiting_for_button_1_final = State()
    waiting_for_button_2_final = State()
    waiting_for_button_3_final = State()
    
    # Step 5: Date/time selection
    waiting_for_date = State()
    waiting_for_time = State()
    
    # Step 6: Preview and confirmation
    waiting_for_confirmation = State()
