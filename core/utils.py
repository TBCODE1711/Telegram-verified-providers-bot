import logging
from aiogram import Bot
from aiogram.fsm.context import FSMContext
from aiogram.exceptions import TelegramAPIError

# Tracks a message ID in the FSM context for later deletion.
# Args: state (FSMContext), message_id (int)
# Returns: None
async def track_message(state: FSMContext, message_id: int):
    data = await state.get_data()
    tracked = data.get('tracked_messages', [])
    if message_id not in tracked:
        tracked.append(message_id)
        await state.update_data(tracked_messages=tracked)

# Deletes all tracked messages from the chat and clears the tracking list.
# Args: bot (Bot), chat_id (int), state (FSMContext)
# Returns: None
async def delete_tracked_messages(bot: Bot, chat_id: int, state: FSMContext):
    data = await state.get_data()
    tracked = data.get('tracked_messages', [])
    if tracked:
        try:
            await bot.delete_messages(chat_id=chat_id, message_ids=tracked)
        except TelegramAPIError as e:
            logging.error(f"Error deleting tracked messages: {e}")
        await state.update_data(tracked_messages=[])
