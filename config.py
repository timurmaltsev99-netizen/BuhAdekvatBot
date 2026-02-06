import os
from dotenv import load_dotenv

load_dotenv()  # Загружаем переменные из .env

BOT_TOKEN = os.getenv("BOT_TOKEN")
ADMIN_ID = int(os.getenv("ADMIN_ID"))
YANDEX_API_KEY = os.getenv("YANDEX_API_KEY")
YANDEX_FOLDER_ID = os.getenv("YANDEX_FOLDER_ID")

# Проверка
if not all([BOT_TOKEN, ADMIN_ID, YANDEX_API_KEY, YANDEX_FOLDER_ID]):
    print("⚠️ Внимание: не все переменные окружения заданы!")  
