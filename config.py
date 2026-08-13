import os
from dotenv import load_dotenv

load_dotenv()

BOT_TOKEN = os.getenv("BOT_TOKEN")
if not BOT_TOKEN:
    raise ValueError("BOT_TOKEN environment variable is not set.")

DATABASE_URL = os.getenv("DATABASE_URL")
if not DATABASE_URL:
    raise ValueError("DATABASE_URL environment variable is not set.")

WEBHOOK_HOST = os.getenv("WEBHOOK_HOST")
PORT = int(os.getenv("PORT", 8080))

ADMIN_IDS_STR = os.getenv("ADMIN_IDS", "")
ADMIN_IDS = [int(admin_id.strip()) for admin_id in ADMIN_IDS_STR.split(",") if admin_id.strip().isdigit()]

CATEGORIES_STR = os.getenv("CATEGORIES", "Programmers,Exchangers,Marketers,Graphic Designers")
CATEGORIES_LIST = [category.strip() for category in CATEGORIES_STR.split(",") if category.strip()]

MAIN_PIC_ID = os.getenv("MAIN_PIC_ID", "")
