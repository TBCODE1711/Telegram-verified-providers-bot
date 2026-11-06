import os
from dotenv import load_dotenv

load_dotenv()

BOT_TOKEN = os.getenv("BOT_TOKEN")
if not BOT_TOKEN:
    raise ValueError("BOT_TOKEN environment variable is not set.")

DATABASE_URL = os.getenv("DATABASE_URL")
if not DATABASE_URL:
    raise ValueError("DATABASE_URL environment variable is not set.")

DB_POOL_SIZE = int(os.getenv("DB_POOL_SIZE", 2))
DB_MAX_OVERFLOW = int(os.getenv("DB_MAX_OVERFLOW", 3))
DB_ECHO = os.getenv("DB_ECHO", "False").lower() == "true"

WEBHOOK_HOST = os.getenv("WEBHOOK_HOST")
WEBHOOK_SECRET = os.getenv("WEBHOOK_SECRET")
if not WEBHOOK_SECRET:
    raise ValueError("WEBHOOK_SECRET environment variable is not set.")
PORT = int(os.getenv("PORT", 8080))
LOG_LEVEL = os.getenv("LOG_LEVEL", "INFO").upper()

ADMIN_IDS_STR = os.getenv("ADMIN_IDS", "")
ADMIN_IDS = [int(admin_id.strip()) for admin_id in ADMIN_IDS_STR.split(",") if admin_id.strip().isdigit()]

CATEGORIES_STR = os.getenv("CATEGORIES", "Programmers,Exchangers,Marketers,Graphic Designers")
CATEGORIES_LIST = [category.strip() for category in CATEGORIES_STR.split(",") if category.strip()]

MAIN_PIC_ID = os.getenv("MAIN_PIC_ID", "")
REVIEWS_PER_PAGE = int(os.getenv("REVIEWS_PER_PAGE", 5))
