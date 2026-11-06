from aiogram import Bot, Dispatcher
from handlers.admin_handlers import admin_router
from handlers.user_handlers import user_router
from core.config import BOT_TOKEN
from core.telegram_bot_webhook import start_webhook_server
from database.database_manager import init_models

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
    bot, dp = setup_bot()
    start_webhook_server(bot, dp)
