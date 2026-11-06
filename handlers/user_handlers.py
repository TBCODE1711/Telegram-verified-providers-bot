import logging
from aiogram import Router, types, F
from aiogram.filters import CommandStart
from aiogram.fsm.context import FSMContext
from aiogram.exceptions import TelegramAPIError
from keyboards.user_keyboards import get_providers_keyboard, get_provider_actions_keyboard, get_back_to_provider_actions_keyboard, get_back_to_main_menu_keyboard, get_category_selection_keyboard
from strings import user_strings
from database.database_manager import AsyncSessionLocal, get_active_providers_by_category, get_approved_reviews, add_review
from core.utils import track_message, delete_tracked_messages
from states.user_states import AddReviewStates
from core.config import CATEGORIES_LIST, MAIN_PIC_ID

user_router = Router()

@user_router.message(CommandStart())
async def show_start_menu(message: types.Message, state: FSMContext):
    try:
        await delete_tracked_messages(message.bot, message.chat.id, state)
        await state.clear()
        
        if MAIN_PIC_ID:
            msg = await message.answer_photo(photo=MAIN_PIC_ID, caption=user_strings.WELCOME_MESSAGE, reply_markup=get_category_selection_keyboard(CATEGORIES_LIST))
        else:
            msg = await message.answer(text=user_strings.WELCOME_MESSAGE, reply_markup=get_category_selection_keyboard(CATEGORIES_LIST))
        await track_message(state, msg.message_id)
    except TelegramAPIError as e:
        logging.error(f"Telegram API Error in show_start_menu: {e}")
    except Exception as e:
        logging.error(f"Unexpected error in show_start_menu: {e}")

# Returns the user to the main menu from any state.
# Trigger: Callback data "/back_to_user_main".
# Args: callback (types.CallbackQuery), state (FSMContext)
# Returns: None
@user_router.callback_query(F.data == "/back_to_user_main")
async def back_to_main_menu_callback(callback: types.CallbackQuery, state: FSMContext):
    try:
        await delete_tracked_messages(callback.message.bot, callback.message.chat.id, state)
        await state.clear()
        await show_start_menu(callback.message, state)
        await callback.answer()
    except TelegramAPIError as e:
        logging.error(f"Telegram API Error in back_to_main_menu_callback: {e}")
    except Exception as e:
        logging.error(f"Unexpected error in back_to_main_menu_callback: {e}")

# Formats a list of ServiceProvider objects into a list of tuples for keyboard generation.
# Args: providers (list)
# Returns: list[tuple[str, str]]
def format_providers_for_keyboard(providers: list) -> list[tuple[str, str]]:
    formatted_list = []
    for provider in providers:
        callback_data = f"provider_{provider.user_id}_{provider.category}_{provider.display_name}"
        formatted_list.append((provider.display_name, callback_data))
    return formatted_list

# Displays a list of active providers for the selected category.
# Trigger: Callback data matching a category in CATEGORIES_LIST.
# Args: callback (types.CallbackQuery)
# Returns: None
@user_router.callback_query(F.data.in_(CATEGORIES_LIST))
async def show_providers_for_category(callback: types.CallbackQuery, state: FSMContext):
    try:
        category = callback.data
        async with AsyncSessionLocal() as session:
            providers = await get_active_providers_by_category(session, category)
            
        formatted_providers = format_providers_for_keyboard(providers)
        await delete_tracked_messages(callback.message.bot, callback.message.chat.id, state)
        msg = await callback.message.answer(text=user_strings.CHOOSE_PROVIDER, reply_markup=get_providers_keyboard(formatted_providers))
        await track_message(state, msg.message_id)
        await callback.answer()
    except TelegramAPIError as e:
        logging.error(f"Telegram API Error in show_providers_for_category: {e}")
    except Exception as e:
        logging.error(f"Unexpected error in show_providers_for_category: {e}")

# Displays the available actions for a specific service provider.
# Trigger: Callback data starting with "provider_".
# Args: callback (types.CallbackQuery)
# Returns: None
@user_router.callback_query(F.data.startswith("provider_"))
async def show_provider_actions(callback: types.CallbackQuery, state: FSMContext):
    try:
        await state.set_state(None)
        
        parts = callback.data.split("_", 3)

        provider_id = int(parts[1])
        category = parts[2]
        display_name = parts[3]
        
        text = user_strings.PROVIDER_ACTION_PROMPT.format(display_name=display_name)
        keyboard = get_provider_actions_keyboard(provider_id, display_name, category)
        
        await callback.message.edit_text(text=text, reply_markup=keyboard)
        await callback.answer()
    except TelegramAPIError as e:
        logging.error(f"Telegram API Error in show_provider_actions: {e}")
    except Exception as e:
        logging.error(f"Unexpected error in show_provider_actions: {e}")

# Provides a direct contact link to the chosen service provider.
# Trigger: Callback data starting with "talk_to_".
# Args: callback (types.CallbackQuery)
# Returns: None
@user_router.callback_query(F.data.startswith("talk_to_"))
async def contact_provider(callback: types.CallbackQuery):
    try:
        parts = callback.data.split("_")
        provider_id = int(parts[2])
        
        text = user_strings.CONTACT_PROVIDER_MSG.format(provider_id=provider_id)
        
        await callback.message.edit_text(text=text, reply_markup=get_back_to_main_menu_keyboard(), parse_mode="HTML")
        await callback.answer()
    except TelegramAPIError as e:
        logging.error(f"Telegram API Error in contact_provider: {e}")
    except Exception as e:
        logging.error(f"Unexpected error in contact_provider: {e}")

# Displays the approved reviews for a specific service provider.
# Trigger: Callback data starting with "read_reviews_".
# Args: callback (types.CallbackQuery)
# Returns: None
@user_router.callback_query(F.data.startswith("read_reviews_"))
async def show_provider_reviews(callback: types.CallbackQuery):
    try:
        parts = callback.data.split("_", 4)
        provider_id = int(parts[2])
        category = parts[3]
        display_name = parts[4]
        
        async with AsyncSessionLocal() as session:
            reviews = await get_approved_reviews(session, provider_id)
            
        if not reviews:
            text = user_strings.NO_REVIEWS_TEXT
        else:
            text = format_reviews_display(reviews)
            
        keyboard = get_back_to_provider_actions_keyboard(provider_id, category, display_name)
        
        await callback.message.edit_text(text=text, reply_markup=keyboard, parse_mode="HTML")
        await callback.answer()
    except TelegramAPIError as e:
        logging.error(f"Telegram API Error in show_provider_reviews: {e}")
    except Exception as e:
        logging.error(f"Unexpected error in show_provider_reviews: {e}")

# Formats a list of approved reviews into a display string.
# Args: reviews (list)
# Returns: str
def format_reviews_display(reviews: list) -> str:
    text = "<b>Approved Reviews:</b>\n\n"
    for review in reviews:
        username = review.sender_username if review.sender_username else "Unknown User"
        text += f"<b>{username}:</b>\n\"{review.review_text}\"\n\n-------------------\n\n"
    return text


# Starts the FSM flow for adding a new review.
# Trigger: Callback data starting with "add_review_".
# Args: callback (types.CallbackQuery), state (FSMContext)
# Returns: None
@user_router.callback_query(F.data.startswith("add_review_"))
async def start_add_review_flow(callback: types.CallbackQuery, state: FSMContext):
    try:
        parts = callback.data.split("_", 4)
        provider_id = int(parts[2])
        category = parts[3]
        display_name = parts[4] if len(parts) > 4 else "the provider"
        
        await state.update_data(provider_id=provider_id, display_name=display_name, category=category)
        await state.set_state(AddReviewStates.waiting_for_review)
        
        text = user_strings.ENTER_REVIEW_PROMPT.format(display_name=display_name)
        msg = await callback.message.edit_text(text=text, reply_markup=get_back_to_provider_actions_keyboard(provider_id, category, display_name))
        
        await track_message(state, msg.message_id)
        await callback.answer()
    except TelegramAPIError as e:
        logging.error(f"Telegram API Error in start_add_review_flow: {e}")
    except Exception as e:
        logging.error(f"Unexpected error in start_add_review_flow: {e}")

# Processes the user's review text and saves it to the database.
# Trigger: Message in AddReviewStates.waiting_for_review state.
# Args: message (types.Message), state (FSMContext)
# Returns: None
@user_router.message(AddReviewStates.waiting_for_review)
async def process_review_text(message: types.Message, state: FSMContext):
    try:
        await track_message(state, message.message_id)
        data = await state.get_data()
        provider_id = data.get("provider_id")
        display_name = data.get("display_name")
        category = data.get("category")
        
        async with AsyncSessionLocal() as session:
            await add_review(
                session=session,
                provider_id=provider_id,
                sender_id=message.from_user.id,
                sender_username=message.from_user.username,
                review_text=message.text.strip()
            )
            
        await delete_tracked_messages(message.bot, message.chat.id, state)
        msg1 = await message.answer(user_strings.REVIEW_SUBMITTED_SUCCESS)
        await track_message(state, msg1.message_id)
        
        text = user_strings.PROVIDER_ACTION_PROMPT.format(display_name=display_name)
        keyboard = get_provider_actions_keyboard(provider_id, display_name, category)
        msg2 = await message.answer(text=text, reply_markup=keyboard)
        await track_message(state, msg2.message_id)
        
        await state.set_state(None)
    except TelegramAPIError as e:
        logging.error(f"Telegram API Error in process_review_text: {e}")
    except Exception as e:
        logging.error(f"Unexpected error in process_review_text: {e}")
        await state.set_state(None)
