from aiogram.fsm.state import State, StatesGroup

class AddReviewStates(StatesGroup):
    waiting_for_review = State()
