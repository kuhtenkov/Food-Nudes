import os
import logging
from dotenv import load_dotenv
from telebot import TeleBot
from database.db_manager import DatabaseManager
from handlers.meal_analysis import MealAnalysisHandler
from handlers.profile import ProfileHandler
from handlers.progress import ProgressHandler
from handlers.payment import PaymentHandler
from utils.keyboards import main_menu

# Настройка путей и загрузка переменных окружения
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
ENV_PATH = os.path.join(BASE_DIR, '.env')
load_dotenv(ENV_PATH)

# Настройка логирования
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler(os.path.join(BASE_DIR, 'bot.log')),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

# Определение токена бота и ID администратора
TELEGRAM_BOT_TOKEN = os.getenv('TELEGRAM_BOT_TOKEN')
ADMIN_ID = 6916276950  # Замените на ваш реальный Telegram ID

if not TELEGRAM_BOT_TOKEN:
    logger.critical("Telegram токен не найден в .env файле")
    exit(1)

# Инициализация бота
bot = TeleBot(TELEGRAM_BOT_TOKEN)

# Инициализация базы данных
db_path = os.path.join(BASE_DIR, "user_profiles.db")
db_manager = DatabaseManager(db_path)
db_manager.init_db()

# Инициализация обработчиков
meal_handler = MealAnalysisHandler(bot, db_manager)
profile_handler = ProfileHandler(bot, db_manager)
progress_handler = ProgressHandler(bot, db_manager)
payment_handler = PaymentHandler(bot, db_manager)

@bot.message_handler(commands=['start'])
def send_welcome(message):
    """Обработчик команды /start"""
    try:
        db_manager.ensure_user_exists(message.from_user.id)
        text = "🍓 *Привет, гурман!*\nДобро пожаловать в FoodNudes — место, где еда раскрывает свои *самые сокровенные секреты*.\nОтправь фото блюда, и я расскажу, из чего оно состоит, сколько в нем калорий и насколько оно горячо. 😉"
        bot.send_message(message.chat.id, text, reply_markup=main_menu(), parse_mode='Markdown')
        logger.info(f"Пользователь {message.from_user.id} запустил бота")
    except Exception as e:
        logger.error(f"Ошибка в команде start: {e}")
        bot.send_message(message.chat.id, "Произошла ошибка. Попробуйте позже.")

@bot.message_handler(func=lambda message: message.text == "Назад в меню")
def back_to_main_menu(message):
    """Возврат в главное меню"""
    try:
        bot.send_message(
            message.chat.id,
            "Выберите действие:",
            reply_markup=main_menu()
        )
    except Exception as e:
        logger.error(f"Ошибка возврата в меню: {e}")
        bot.send_message(message.chat.id, "Произошла ошибка. Попробуйте позже.")

@bot.message_handler(commands=['stats'])
def send_stats(message):
    """Отправка статистики использования бота"""
    if message.from_user.id != ADMIN_ID:
        bot.reply_to(message, "У вас нет прав для просмотра статистики.")
        return
    
    total_users = db_manager.get_total_users()
    total_generations = db_manager.get_total_generations()
    active_users = db_manager.get_active_users_last_week()
    
    stats_message = f"📊 Статистика бота:\n\n" \
                    f"👤 Всего пользователей: {total_users}\n" \
                    f"🏃 Активных пользователей за неделю: {active_users}\n" \
                    f"🔢 Всего генераций: {total_generations}\n"
    
    bot.reply_to(message, stats_message)

def register_handlers():
    """Регистрация всех обработчиков сообщений"""
    try:
        meal_handler.register_handlers()
        profile_handler.register_handlers()
        progress_handler.register_handlers()
        payment_handler.register_handlers()
        logger.info("Все обработчики успешно зарегистрированы")
    except Exception as e:
        logger.error(f"Ошибка регистрации обработчиков: {e}")

if __name__ == "__main__":
    try:
        # Регистрируем обработчики
        register_handlers()
        
        # Запускаем бота
        logger.info("Бот запущен и ожидает сообщений...")
        bot.polling(none_stop=True)
    except Exception as e:
        logger.error(f"Критическая ошибка: {e}")
