import os
from dotenv import load_dotenv

load_dotenv()

BOT_TOKEN = os.getenv("BOT_TOKEN")
ADMIN_ID = 5288817405  # Replace with your Telegram ID

STYLES_DIR = "styles"
os.makedirs(STYLES_DIR, exist_ok=True)

COMFYUI_URL = "http://127.0.0.1:8188"