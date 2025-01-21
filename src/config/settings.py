# src/config/settings.py
import os
from dotenv import load_dotenv

# Загружаем переменные из .env файла
load_dotenv()

# Токены и ключи API
TELEGRAM_BOT_TOKEN = os.getenv('TELEGRAM_BOT_TOKEN')
OPENAI_API_KEY = os.getenv('OPENAI_API_KEY')
STATS_CHAT_ID = os.getenv('STATS_CHAT_ID')
YOOKASSA_SHOP_ID = os.getenv('YOOKASSA_SHOP_ID')
YOOKASSA_SECRET_KEY = os.getenv('YOOKASSA_SECRET_KEY')

# Тарифные планы
TARIFF_PLANS = {
    "Базовый": {
        "price": 299,
        "generations": 50
    },
    "Стандартный": {
        "price": 499,
        "generations": 100
    },
    "Премиум": {
        "price": 990,
        "generations": 300
    }
}

# Настройки логирования
LOGGING_CONFIG = {
    'level': 'INFO',
    'format': '%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    'handlers': ['file', 'console']
}

# Пути к файлам
DATABASE_PATH = 'user_profiles.db'
TEMP_DIR = 'temp'