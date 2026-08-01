import os
from dotenv import load_dotenv

load_dotenv()

BOT_TOKEN = os.getenv("BOT_TOKEN")
ADMIN_ID = 5288817405  # <-- حط رقمك هنا

STYLES_DIR = "styles"
os.makedirs(STYLES_DIR, exist_ok=True)

STARS_PER_IMAGE = 10
MIN_DEPOSIT = 10
