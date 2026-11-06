import logging
from aiogram import Bot, Dispatcher
from handlers.admin_handlers import admin_router
from handlers.user_handlers import user_router
from core.config import BOT_TOKEN, LOG_LEVEL
from core.telegram_bot_webhook import start_webhook_server
from database.connection import init_models

async def on_db_startup(*args, **kwargs):
    await init_models()

def setup_bot():
    bot = Bot(token=BOT_TOKEN)
    dp = Dispatcher()
    
    dp.startup.register(on_db_startup)
    dp.include_router(user_router)
    dp.include_router(admin_router)
    
    return bot, dp

if __name__ == "__main__":
    logging.basicConfig(level=getattr(logging, LOG_LEVEL, logging.INFO))
    bot, dp = setup_bot()
    start_webhook_server(bot, dp)
