import logging
from aiogram import Router, types, F, Bot
from aiogram.filters import Command
from aiogram.fsm.context import FSMContext
from aiogram.exceptions import TelegramAPIError
from keyboards.admin_keyboards import get_admin_main_menu_keyboard, get_edit_provider_keyboard, get_toggle_confirmation_keyboard, get_review_approval_keyboard, get_category_selection_keyboard
from keyboards.shared_keyboards import get_cancel_keyboard, get_confirmation_keyboard

from states.admin_states import AddProviderStates, SearchProviderStates, EditProviderStates
from strings import strings
from database.connection import AsyncSessionLocal
from database.crud import add_service_provider, get_service_provider, update_provider_display_name, update_provider_category, toggle_provider_active_status, get_oldest_pending_review, update_review_status
from core.utils import track_message, delete_tracked_messages
from core.config import ADMIN_IDS, CATEGORIES_LIST

admin_router = Router()

# Checks if the message sender is an admin.
# Trigger: Message filter.
# Args: message (types.Message)
# Returns: bool
def is_admin(message: types.Message) -> bool:
    user = message.from_user
    if not user:
        return False
    return (user.id in ADMIN_IDS)

# Checks if the callback sender is an admin.
# Trigger: Callback query filter.
# Args: callback (types.CallbackQuery)
# Returns: bool
def is_admin_callback(callback: types.CallbackQuery) -> bool:
    user = callback.from_user
    if not user:
        return False
    return (user.id in ADMIN_IDS)

# Apply the admin filter to all messages handled by this router
admin_router.message.filter(is_admin)
admin_router.callback_query.filter(is_admin_callback)

# Displays the main admin panel menu.
# Trigger: "/admin" command.
# Args: message (types.Message)
# Returns: None
@admin_router.message(Command("admin"))
async def show_admin_panel(message: types.Message, state: FSMContext):
    try:
        await delete_tracked_messages(message.bot, message.chat.id, state)
        await state.clear()
        keyboard = get_admin_main_menu_keyboard()
        msg = await message.answer(strings.ADMIN_PANEL_TITLE, reply_markup=keyboard)
        await track_message(state, msg.message_id)
    except TelegramAPIError as e:
        logging.error(f"Telegram API Error in show_admin_panel: {e}")
    except Exception as e:
        logging.error(f"Unexpected error in show_admin_panel: {e}")

# Cancels the current state and returns to idle.
# Trigger: "cancel_action" callback data.
# Args: callback (types.CallbackQuery), state (FSMContext)
# Returns: None
@admin_router.callback_query(F.data == "cancel_action")
async def cancel_action_handler(callback: types.CallbackQuery, state: FSMContext):
    try:
        await delete_tracked_messages(callback.message.bot, callback.message.chat.id, state)
        await state.clear()
        await callback.message.answer(strings.ACTION_CANCELLED)
        await show_admin_panel(callback.message, state)
        await callback.answer()
    except TelegramAPIError as e:
        logging.error(f"API Error in cancel_action_handler: {e}")


# Returns to the main admin menu.
# Trigger: "return_to_main_menu" callback data.
# Args: callback (types.CallbackQuery), state (FSMContext)
# Returns: None
@admin_router.callback_query(F.data == "return_to_main_menu")
async def return_to_main_menu_handler(callback: types.CallbackQuery, state: FSMContext):
    try:
        await delete_tracked_messages(callback.message.bot, callback.message.chat.id, state)
        await state.clear()
        await show_admin_panel(callback.message, state)
        await callback.answer()
    except TelegramAPIError as e:
        logging.error(f"API Error in return_to_main_menu_handler: {e}")


# Starts the process of adding a new service provider.
# Trigger: "add_provider_btn" callback data.
# Args: callback (types.CallbackQuery), state (FSMContext)
# Returns: None
@admin_router.callback_query(F.data == "add_provider_btn")
async def start_add_provider_flow(callback: types.CallbackQuery, state: FSMContext):
    try:
        await track_message(state, callback.message.message_id)
        await state.set_state(AddProviderStates.waiting_for_user_id)
        await callback.message.edit_text(strings.ENTER_PROVIDER_ID, reply_markup=get_cancel_keyboard())
        await callback.answer()
    except TelegramAPIError as e:
        logging.error(f"API Error in start_add_provider_flow: {e}")

# Validates and stores the provider's user ID.
# Trigger: Message in AddProviderStates.waiting_for_user_id state.
# Args: message (types.Message), state (FSMContext)
# Returns: None
@admin_router.message(AddProviderStates.waiting_for_user_id)
async def process_provider_id(message: types.Message, state: FSMContext):
    try:
        await track_message(state, message.message_id)
        if not message.text.isdigit():
            msg = await message.answer(strings.INVALID_ID_FORMAT, reply_markup=get_cancel_keyboard())
            await track_message(state, msg.message_id)
            return
            
        await state.update_data(provider_id=int(message.text))
        await state.set_state(AddProviderStates.waiting_for_username)
        msg = await message.answer(strings.ENTER_USERNAME, reply_markup=get_cancel_keyboard())
        await track_message(state, msg.message_id)
    except TelegramAPIError as e:
        logging.error(f"API Error in process_provider_id: {e}")

# Stores the provider's username or skips if requested.
# Trigger: Message in AddProviderStates.waiting_for_username state.
# Args: message (types.Message), state (FSMContext)
# Returns: None
@admin_router.message(AddProviderStates.waiting_for_username)
async def process_provider_username(message: types.Message, state: FSMContext):
    try:
        await track_message(state, message.message_id)
        username = None if message.text.strip().lower() == strings.SKIP_COMMAND else message.text.strip()
        await state.update_data(username=username)
        await state.set_state(AddProviderStates.waiting_for_display_name)
        msg = await message.answer(strings.ENTER_DISPLAY_NAME, reply_markup=get_cancel_keyboard())
        await track_message(state, msg.message_id)
    except TelegramAPIError as e:
        logging.error(f"API Error in process_provider_username: {e}")

# Stores the provider's display name.
# Trigger: Message in AddProviderStates.waiting_for_display_name state.
# Args: message (types.Message), state (FSMContext)
# Returns: None
@admin_router.message(AddProviderStates.waiting_for_display_name)
async def process_provider_display_name(message: types.Message, state: FSMContext):
    try:
        await track_message(state, message.message_id)
        await state.update_data(display_name=message.text.strip())
        await state.set_state(AddProviderStates.waiting_for_category)
        msg = await message.answer(strings.CHOOSE_CATEGORY, reply_markup=get_category_selection_keyboard(CATEGORIES_LIST))
        await track_message(state, msg.message_id)
    except TelegramAPIError as e:
        logging.error(f"API Error in process_provider_display_name: {e}")

# Stores the provider's category and asks for final confirmation.
# Trigger: Callback query in AddProviderStates.waiting_for_category state.
# Args: callback (types.CallbackQuery), state (FSMContext)
# Returns: None
@admin_router.callback_query(AddProviderStates.waiting_for_category)
async def process_provider_category(callback: types.CallbackQuery, state: FSMContext):
    try:
        category = callback.data.split("_", 2)[2]
        await state.update_data(category=category)
        data = await state.get_data()
        
        confirmation_msg = strings.CONFIRM_PROVIDER_DETAILS.format(
            provider_id=data.get('provider_id'),
            username=data.get('username'),
            display_name=data.get('display_name'),
            category=category
        )
        
        await state.set_state(AddProviderStates.waiting_for_confirmation)
        msg = await callback.message.answer(confirmation_msg, reply_markup=get_confirmation_keyboard())
        await track_message(state, msg.message_id)
        await callback.answer()
    except TelegramAPIError as e:
        logging.error(f"API Error in process_provider_category: {e}")

# Saves the new provider to the database or aborts based on admin choice.
# Trigger: Callback query in AddProviderStates.waiting_for_confirmation state.
# Args: callback (types.CallbackQuery), state (FSMContext)
# Returns: None
@admin_router.callback_query(AddProviderStates.waiting_for_confirmation)
async def process_provider_confirmation(callback: types.CallbackQuery, state: FSMContext):
    try:
        await delete_tracked_messages(callback.message.bot, callback.message.chat.id, state)
        if callback.data == "confirm_add":
            data = await state.get_data()
            async with AsyncSessionLocal() as session:
                await add_service_provider(
                    session=session,
                    provider_id=data.get('provider_id'),
                    username=data.get('username'),
                    display_name=data.get('display_name'),
                    category=data.get('category')
                )
            await callback.message.answer(strings.PROVIDER_ADDED_SUCCESS)
        else:
            await callback.message.answer(strings.PROVIDER_ADD_ABORTED)
            
        await state.clear()
        await show_admin_panel(callback.message, state)
        await callback.answer()
    except ValueError as e:
        logging.error(f"ValueError in process_provider_confirmation: {e}")
        await callback.answer(strings.PROVIDER_ALREADY_EXISTS, show_alert=True)
        await delete_tracked_messages(callback.message.bot, callback.message.chat.id, state)
        await state.clear()
        await show_admin_panel(callback.message, state)
    except Exception as e:
        logging.error(f"Error in process_provider_confirmation: {e}")
        await callback.answer(strings.API_ERROR_MSG, show_alert=True)
        await delete_tracked_messages(callback.message.bot, callback.message.chat.id, state)
        await state.clear()



# Starts the process of searching for a service provider.
# Trigger: "search_provider_btn" callback data.
# Args: callback (types.CallbackQuery), state (FSMContext)
# Returns: None
@admin_router.callback_query(F.data == "search_provider_btn")
async def start_search_provider_flow(callback: types.CallbackQuery, state: FSMContext):
    try:
        await state.clear()
        await track_message(state, callback.message.message_id)
        await state.set_state(SearchProviderStates.waiting_for_search_query)
        await callback.message.edit_text(strings.ENTER_SEARCH_QUERY, reply_markup=get_cancel_keyboard())
        await callback.answer()
    except TelegramAPIError as e:
        logging.error(f"API Error in start_search_provider_flow: {e}")

# Searches for a provider by ID or username and displays the edit menu if found.
# Trigger: Message in SearchProviderStates.waiting_for_search_query state.
# Args: message (types.Message), state (FSMContext)
# Returns: None
@admin_router.message(SearchProviderStates.waiting_for_search_query)
async def process_search_query(message: types.Message, state: FSMContext):
    try:
        await track_message(state, message.message_id)
        query = message.text.strip()
        provider_id = int(query) if query.isdigit() else None
        username = query if not query.isdigit() else None
        
        async with AsyncSessionLocal() as session:
            provider = await get_service_provider(session, user_id=provider_id, username=username)
            
        if provider:
            await state.update_data(provider_id=provider.user_id, is_active=provider.is_active)
            await state.set_state(None)
            keyboard = get_edit_provider_keyboard()
            status_text = "Active" if provider.is_active else "Inactive"
            details_text = strings.PROVIDER_DETAILS_DISPLAY.format(
                provider_id=provider.user_id,
                username=provider.username or "N/A",
                display_name=provider.display_name,
                category=provider.category,
                status=status_text
            )
            msg = await message.answer(details_text, reply_markup=keyboard)
            await track_message(state, msg.message_id)
        else:
            msg = await message.answer(strings.PROVIDER_NOT_FOUND, reply_markup=get_cancel_keyboard())
            await track_message(state, msg.message_id)
    except Exception as e:
        logging.error(f"Error in process_search_query: {e}")
        await message.answer(strings.API_ERROR_MSG)
        await state.clear()



# Starts the process of editing a provider's display name.
# Trigger: "edit_display_name" callback data.
# Args: callback (types.CallbackQuery), state (FSMContext)
# Returns: None
@admin_router.callback_query(F.data == "edit_display_name")
async def start_edit_display_name_flow(callback: types.CallbackQuery, state: FSMContext):
    try:
        await state.set_state(EditProviderStates.waiting_for_new_display_name)
        await callback.message.edit_text(strings.ENTER_NEW_DISPLAY_NAME, reply_markup=get_cancel_keyboard())
        await callback.answer()
    except Exception as e:
        logging.error(f"Error in start_edit_display_name_flow: {e}")
        await callback.answer(strings.API_ERROR_MSG, show_alert=True)
        await state.clear()

# Updates the provider's display name in the database.
# Trigger: Message in EditProviderStates.waiting_for_new_display_name state.
# Args: message (types.Message), state (FSMContext)
# Returns: None
@admin_router.message(EditProviderStates.waiting_for_new_display_name)
async def process_new_display_name(message: types.Message, state: FSMContext):
    try:
        await track_message(state, message.message_id)
        new_display_name = message.text.strip()
        data = await state.get_data()
        provider_id = data.get('provider_id')
        
        async with AsyncSessionLocal() as session:
            success = await update_provider_display_name(session, new_display_name=new_display_name, user_id=provider_id)
            
        if success:
            await delete_tracked_messages(message.bot, message.chat.id, state)
            await state.set_state(None)
            msg1 = await message.answer(strings.EDIT_SUCCESS)
            keyboard = get_edit_provider_keyboard()
            msg2 = await message.answer(strings.PROVIDER_FOUND_EDIT_MENU, reply_markup=keyboard)
            await track_message(state, msg1.message_id)
            await track_message(state, msg2.message_id)
        else:
            msg = await message.answer(strings.EDIT_FAILED_RETRY, reply_markup=get_cancel_keyboard())
            await track_message(state, msg.message_id)
            
    except Exception as e:
        logging.error(f"Error in process_new_display_name: {e}")
        msg = await message.answer(strings.EDIT_FAILED_RETRY, reply_markup=get_cancel_keyboard())
        await track_message(state, msg.message_id)

# Starts the process of editing a provider's category.
# Trigger: "edit_category" callback data.
# Args: callback (types.CallbackQuery), state (FSMContext)
# Returns: None
@admin_router.callback_query(F.data == "edit_category")
async def start_edit_category_flow(callback: types.CallbackQuery, state: FSMContext):
    try:
        await state.set_state(EditProviderStates.waiting_for_new_category)
        await callback.message.edit_text(strings.ENTER_NEW_CATEGORY, reply_markup=get_category_selection_keyboard(CATEGORIES_LIST))
        await callback.answer()
    except Exception as e:
        logging.error(f"Error in start_edit_category_flow: {e}")
        await callback.answer(strings.API_ERROR_MSG, show_alert=True)
        await state.clear()

# Updates the provider's category in the database.
# Trigger: Callback query in EditProviderStates.waiting_for_new_category state.
# Args: callback (types.CallbackQuery), state (FSMContext)
# Returns: None
@admin_router.callback_query(EditProviderStates.waiting_for_new_category)
async def process_new_category(callback: types.CallbackQuery, state: FSMContext):
    try:
        new_category = callback.data.split("_", 2)[2]
        data = await state.get_data()
        provider_id = data.get('provider_id')
        
        async with AsyncSessionLocal() as session:
            success = await update_provider_category(session, new_category=new_category, user_id=provider_id)
            
        if success:
            await delete_tracked_messages(callback.message.bot, callback.message.chat.id, state)
            await state.set_state(None)
            msg1 = await callback.message.answer(strings.EDIT_SUCCESS)
            keyboard = get_edit_provider_keyboard()
            msg2 = await callback.message.answer(strings.PROVIDER_FOUND_EDIT_MENU, reply_markup=keyboard)
            await track_message(state, msg1.message_id)
            await track_message(state, msg2.message_id)
            await callback.answer()
        else:
            await callback.answer(strings.EDIT_FAILED_RETRY, show_alert=True)
    except Exception as e:
        logging.error(f"Error in process_new_category: {e}")
        await callback.answer(strings.EDIT_FAILED_RETRY, show_alert=True)

# Starts the process of toggling a service provider's status.
# Trigger: "toggle_status" callback data.
# Args: callback (types.CallbackQuery), state (FSMContext)
# Returns: None
@admin_router.callback_query(F.data == "toggle_status")
async def start_toggle_status_flow(callback: types.CallbackQuery, state: FSMContext):
    try:
        data = await state.get_data()
        is_active = data.get('is_active', True)
        await state.set_state(EditProviderStates.waiting_for_delete_confirmation)
        msg = strings.CONFIRM_DEACTIVATE if is_active else strings.CONFIRM_ACTIVATE
        await callback.message.edit_text(msg, reply_markup=get_toggle_confirmation_keyboard())
        await callback.answer()
    except Exception as e:
        logging.error(f"Error in start_toggle_status_flow: {e}")
        await callback.answer(strings.API_ERROR_MSG, show_alert=True)
        await state.clear()

# Confirms and executes the status toggle of a provider.
# Trigger: Callback query in EditProviderStates.waiting_for_delete_confirmation state.
# Args: callback (types.CallbackQuery), state (FSMContext)
# Returns: None
@admin_router.callback_query(EditProviderStates.waiting_for_delete_confirmation)
async def process_toggle_confirmation(callback: types.CallbackQuery, state: FSMContext):
    try:
        if callback.data == "confirm_toggle_btn":
            data = await state.get_data()
            provider_id = data.get('provider_id')
            is_active = data.get('is_active', True)
            
            async with AsyncSessionLocal() as session:
                await toggle_provider_active_status(session, user_id=provider_id)
                
            await state.update_data(is_active=not is_active)
            await delete_tracked_messages(callback.message.bot, callback.message.chat.id, state)
            msg1 = await callback.message.answer(strings.STATUS_UPDATE_SUCCESS)
            msg2 = await callback.message.answer(strings.PROVIDER_FOUND_EDIT_MENU, reply_markup=get_edit_provider_keyboard())
            await track_message(state, msg1.message_id)
            await track_message(state, msg2.message_id)
        elif callback.data == "not_confirm_toggle_btn":
            await delete_tracked_messages(callback.message.bot, callback.message.chat.id, state)
            msg1 = await callback.message.answer(strings.ACTION_CANCELLED)
            msg2 = await callback.message.answer(strings.PROVIDER_FOUND_EDIT_MENU, reply_markup=get_edit_provider_keyboard())
            await track_message(state, msg1.message_id)
            await track_message(state, msg2.message_id)
            
        await state.set_state(None)
        await callback.answer()
    except Exception as e:
        logging.error(f"Error in process_toggle_confirmation: {e}")
        await callback.answer(strings.API_ERROR_MSG, show_alert=True)
        await state.clear()



# Fetches and displays the oldest pending review, or a message if none exist.
# Trigger: Called internally by other review management handlers.
# Args: callback (types.CallbackQuery)
# Returns: None
async def send_next_pending_review(callback: types.CallbackQuery, state: FSMContext):
    async with AsyncSessionLocal() as session:
        review = await get_oldest_pending_review(session)
        
        if review:
            text = strings.REVIEW_DISPLAY.format(
                sender_username=review.sender_username or "Unknown User",
                review_text=review.review_text
            )
            keyboard = get_review_approval_keyboard(review.review_id)
            await callback.message.edit_text(text, reply_markup=keyboard)
        else:
            await callback.message.edit_text(strings.NO_PENDING_REVIEWS)
            msg = await callback.message.answer(strings.ADMIN_PANEL_TITLE, reply_markup=get_admin_main_menu_keyboard())
            await track_message(state, msg.message_id)

# Starts the pending reviews management flow.
# Trigger: "manage_pending_reviews_btn" callback data.
# Args: callback (types.CallbackQuery)
# Returns: None
@admin_router.callback_query(F.data == "manage_pending_reviews_btn")
async def start_manage_reviews_flow(callback: types.CallbackQuery, state: FSMContext):
    try:
        await send_next_pending_review(callback, state)
        await callback.answer()
    except Exception as e:
        logging.error(f"Error in start_manage_reviews_flow: {e}")
        await callback.answer(strings.API_ERROR_MSG, show_alert=True)

# Updates the status of a pending review (APPROVED/REJECTED).
# Trigger: Callback data starting with "confirm_review_" or "reject_review_".
# Args: callback (types.CallbackQuery)
# Returns: None
@admin_router.callback_query(F.data.startswith("confirm_review_") | F.data.startswith("reject_review_"))
async def process_review_action(callback: types.CallbackQuery, state: FSMContext):
    try:
        action = callback.data.split("_")[0]  # Extracts "confirm" or "reject"
        review_id = int(callback.data.split("_")[-1])
        new_status = "APPROVED" if action == "confirm" else "REJECTED"
        
        async with AsyncSessionLocal() as session:
            await update_review_status(session, review_id=review_id, new_status=new_status)
            
        msg = strings.REVIEW_APPROVED if action == "confirm" else strings.REVIEW_REJECTED
        
        await send_next_pending_review(callback, state)
        await callback.answer(msg)
    except Exception as e:
        logging.error(f"Error in process_review_action: {e}")
        await callback.answer(strings.API_ERROR_MSG, show_alert=True)


# Extracts and logs the file_id of the highest resolution photo sent by an admin.
# Trigger: Message containing a photo.
# Args: message (types.Message)
# Returns: None
@admin_router.message(F.photo)
async def log_photo_file_id(message: types.Message):
    try:
        file_id = message.photo[-1].file_id
        logging.warning(f"Photo sent by admin, request not handled. File ID: {file_id}")
    except TelegramAPIError as e:
        logging.error(f"Telegram API Error in log_photo_file_id: {e}")
    except Exception as e:
        logging.error(f"Unexpected error in log_photo_file_id: {e}")
