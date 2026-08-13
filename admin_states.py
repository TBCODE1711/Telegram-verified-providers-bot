from aiogram.fsm.state import State, StatesGroup

class AddProviderStates(StatesGroup):
    waiting_for_user_id = State()
    waiting_for_username = State()
    waiting_for_display_name = State()
    waiting_for_category = State()
    waiting_for_confirmation = State()

class SearchProviderStates(StatesGroup):
    waiting_for_search_query = State()

class EditProviderStates(StatesGroup):
    waiting_for_new_display_name = State()
    waiting_for_new_category = State()
    waiting_for_delete_confirmation = State()