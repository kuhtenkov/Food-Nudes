import telebot
from telebot import types
import openai
import requests
import base64
import os
import time
import logging
import sqlite3
from yookassa import Configuration, Payment
import uuid
from dotenv import load_dotenv

# Загружаем переменные окружения
load_dotenv()

# Получаем переменные из .env
TELEGRAM_BOT_TOKEN = os.getenv('TELEGRAM_BOT_TOKEN')
OPENAI_API_KEY = os.getenv('OPENAI_API_KEY')
YOOKASSA_SHOP_ID = os.getenv('YOOKASSA_SHOP_ID')
YOOKASSA_SECRET_KEY = os.getenv('YOOKASSA_SECRET_KEY')

# Настройка логирования
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('bot.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

# Настройка ЮKassa
Configuration.configure(YOOKASSA_SHOP_ID, YOOKASSA_SECRET_KEY)

# Создаем клиента OpenAI
client = openai.OpenAI(api_key=OPENAI_API_KEY)

# Инициализация бота
bot = telebot.TeleBot(TELEGRAM_BOT_TOKEN)

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

def init_database():
    """Инициализация базы данных"""
    try:
        conn = sqlite3.connect('user_profiles.db')
        cursor = conn.cursor()
        
        # Создаем таблицы
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS users (
                user_id INTEGER PRIMARY KEY,
                name TEXT,
                age INTEGER,
                height REAL,
                weight REAL,
                goal TEXT,
                daily_calories INTEGER,
                free_generations INTEGER DEFAULT 10,
                total_generations INTEGER DEFAULT 0
            )
        ''')
        
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS payments (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER,
                payment_id TEXT UNIQUE,
                amount REAL,
                plan TEXT,
                generations INTEGER,
                status TEXT,
                created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY(user_id) REFERENCES users(user_id)
            )
        ''')
        
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS meals (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER,
                date TEXT,
                meal_type TEXT,
                calories INTEGER,
                FOREIGN KEY(user_id) REFERENCES users(user_id)
            )
        ''')
        
        conn.commit()
        logger.info("База данных успешно инициализирована")
        
    except Exception as e:
        logger.error(f"Ошибка при инициализации базы данных: {e}")
        raise e
    finally:
        if 'conn' in locals():
            conn.close()

def ensure_user_exists(user_id):
    """Проверка существования пользователя и создание записи если нет"""
    conn = sqlite3.connect('user_profiles.db')
    cursor = conn.cursor()
    try:
        cursor.execute('SELECT 1 FROM users WHERE user_id = ?', (user_id,))
        if not cursor.fetchone():
            cursor.execute('''
                INSERT INTO users (user_id, free_generations, total_generations)
                VALUES (?, 10, 0)
            ''', (user_id,))
            conn.commit()
    except Exception as e:
        logger.error(f"Ошибка при проверке пользователя: {e}")
    finally:
        conn.close()

def check_user_generations(user_id):
    """Проверка баланса генераций пользователя"""
    ensure_user_exists(user_id)
    conn = sqlite3.connect('user_profiles.db')
    cursor = conn.cursor()
    
    try:
        cursor.execute('SELECT free_generations, total_generations FROM users WHERE user_id = ?', 
                      (user_id,))
        result = cursor.fetchone()
        return result[0], result[1]
    except Exception as e:
        logger.error(f"Ошибка проверки генераций: {e}")
        return 0, 0
    finally:
        conn.close()

def update_user_generations(user_id, is_free_generation=True):
    """Обновление счетчика генераций"""
    conn = sqlite3.connect('user_profiles.db')
    cursor = conn.cursor()
    
    try:
        if is_free_generation:
            cursor.execute('''
                UPDATE users 
                SET free_generations = free_generations - 1,
                    total_generations = total_generations + 1
                WHERE user_id = ?
            ''', (user_id,))
        else:
            cursor.execute('''
                UPDATE users 
                SET total_generations = total_generations + 1
                WHERE user_id = ?
            ''', (user_id,))
        
        conn.commit()
    except Exception as e:
        logger.error(f"Ошибка обновления генераций: {e}")
    finally:
        conn.close()

def create_payment(user_id, plan_name):
    """Создание платежа в ЮKassa"""
    plan_name = plan_name.split(" (")[0]  # Очищаем название плана от цены
    try:
        tariff = TARIFF_PLANS[plan_name]
        
        idempotence_key = str(uuid.uuid4())
        payment = Payment.create({
            "amount": {
                "value": str(tariff["price"]) + ".00",
                "currency": "RUB"
            },
            "payment_method_data": {
                "type": "bank_card"
            },
            "confirmation": {
                "type": "redirect",
                "return_url": f"https://t.me/YourBotUsername?start=payment_success_{user_id}"
            },
            "description": f"Тариф: {plan_name} ({tariff['generations']} генераций)"
        }, idempotence_key)

        conn = sqlite3.connect('user_profiles.db')
        cursor = conn.cursor()
        cursor.execute('''
            INSERT INTO payments 
            (user_id, payment_id, amount, plan, generations, status) 
            VALUES (?, ?, ?, ?, ?, ?)
        ''', (user_id, payment.id, tariff["price"], plan_name, tariff["generations"], 'pending'))
        conn.commit()
        conn.close()

        return payment.confirmation.confirmation_url
    except Exception as e:
        logger.error(f"Ошибка создания платежа: {e}")
        return None

def encode_image(image_path):
    """Кодирование изображения в base64"""
    with open(image_path, "rb") as image_file:
        return base64.b64encode(image_file.read()).decode('utf-8')

def show_balance_menu(message):
    """Показ баланса генераций и тарифов"""
    free_gens, total_gens = check_user_generations(message.from_user.id)
    
    markup = types.ReplyKeyboardMarkup(resize_keyboard=True)
    
    # Добавляем кнопки с ценами
    markup.add(
        types.KeyboardButton(f"Базовый план ({TARIFF_PLANS['Базовый']['price']} руб.)"),
        types.KeyboardButton(f"Стандартный план ({TARIFF_PLANS['Стандартный']['price']} руб.)"),
        types.KeyboardButton(f"Премиум план ({TARIFF_PLANS['Премиум']['price']} руб.)"),
        types.KeyboardButton("Назад в меню")
    )
    
    text = (
        f"🔢 Баланс генераций:\n"
        f"- Бесплатные генерации: {free_gens}\n"
        f"- Всего использовано: {total_gens}\n\n"
        "📊 Доступные тарифы:\n"
        f"1. Базовый план: {TARIFF_PLANS['Базовый']['price']} руб. "
        f"({TARIFF_PLANS['Базовый']['generations']} генераций)\n"
        f"2. Стандартный план: {TARIFF_PLANS['Стандартный']['price']} руб. "
        f"({TARIFF_PLANS['Стандартный']['generations']} генераций)\n"
        f"3. Премиум план: {TARIFF_PLANS['Премиум']['price']} руб. "
        f"({TARIFF_PLANS['Премиум']['generations']} генераций)\n\n"
        "Выберите план для пополнения:"
    )
    
    bot.send_message(message.chat.id, text, reply_markup=markup)

def main_menu():
    """Создание главного меню"""
    markup = types.ReplyKeyboardMarkup(resize_keyboard=True, row_width=2)
    markup.add(
        types.KeyboardButton("🔧 Настроить профиль"),
        types.KeyboardButton("🍽️ Анализ блюда"),
        types.KeyboardButton("📊 Мой прогресс"),
        types.KeyboardButton("💰 Пополнить баланс")
    )
    return markup

@bot.message_handler(commands=['start'])
def send_welcome(message):
    """Обработчик команды /start"""
    ensure_user_exists(message.from_user.id)
    text = ("Привет! 🥗 Я твой помощник по питанию.\n"
            "Я помогу тебе анализировать блюда и следить за питанием.")
    bot.send_message(message.chat.id, text, reply_markup=main_menu())

@bot.message_handler(func=lambda message: message.text == "🍽️ Анализ блюда")
def start_meal_analysis(message):
    """Начало анализа блюда"""
    free_gens, _ = check_user_generations(message.from_user.id)
    
    if free_gens > 0:
        bot.send_message(
            message.chat.id,
            "Пожалуйста, отправьте фото блюда для анализа.",
            reply_markup=types.ReplyKeyboardRemove()
        )
    else:
        bot.send_message(
            message.chat.id,
            "У вас закончились бесплатные генерации. Пополните баланс.",
            reply_markup=main_menu()
        )

@bot.message_handler(func=lambda message: message.text == "🍽️ Анализ блюда")
def start_meal_analysis(message):
    bot.send_message(
        message.chat.id,
        "Пожалуйста, отправьте фото блюда для анализа.",
        reply_markup=types.ReplyKeyboardRemove()
    )

@bot.message_handler(content_types=['photo'])
def handle_photo(message):
    try:
        # Получение информации о фото
        file_info = bot.get_file(message.photo[-1].file_id)
        downloaded_file = bot.download_file(file_info.file_path)

        # Сохранение изображения
        os.makedirs("temp", exist_ok=True)
        file_path = f"temp/{message.photo[-1].file_id}.jpg"
        with open(file_path, "wb") as file:
            file.write(downloaded_file)

        logger.info("Фото успешно сохранено локально.")

        # Кодируем изображение в base64
        base64_image = encode_image(file_path)

        # Удаляем локальный файл
        os.remove(file_path)
        logger.info("Локальный файл удален.")

        # Отправляем запрос в OpenAI с использованием base64
        response = client.chat.completions.create(
            model="gpt-4o",
            messages=[
                {
                    "role": "system", 
                    "content": "Ты эксперт по питанию. Проанализируй блюдо на изображении, определи ингредиенты, калорийность и дай nutritional advice."
                },
                {
                    "role": "user",
                    "content": [
                        {"type": "text", "text": "Детально опиши и проанализируй это блюдо"},
                        {"type": "image_url", "image_url": {"url": f"data:image/jpeg;base64,{base64_image}"}}
                    ]
                }
            ]
        )

        # Отправляем результат
        bot.send_message(
            message.chat.id,
            f"Результат анализа:\n{response.choices[0].message.content}",
            reply_markup=main_menu()
        )
    except Exception as e:
        bot.send_message(message.chat.id, "Ошибка при обработке изображения. Попробуйте снова.")
        logger.error(f"Ошибка обработки фото: {e}")

@bot.message_handler(func=lambda message: message.text == "💰 Пополнить баланс")
def handle_balance_replenish(message):
    """Обработка запроса на пополнение баланса"""
    show_balance_menu(message)

@bot.message_handler(func=lambda message: any(message.text.startswith(f"{plan} план") for plan in TARIFF_PLANS.keys()))
def handle_plan_selection(message):
    """Обработка выбора тарифного плана"""
    plan_name = message.text.split(" (")[0]  # Получаем название плана без цены
    payment_url = create_payment(message.from_user.id, plan_name)
    
    if payment_url:
        bot.send_message(
            message.chat.id,
            f"Для оплаты тарифа '{plan_name}' перейдите по ссылке:\n{payment_url}",
            reply_markup=main_menu()
        )
    else:
        bot.send_message(
            message.chat.id,
            "Произошла ошибка при создании платежа. Попробуйте позже.",
            reply_markup=main_menu()
        )

@bot.message_handler(func=lambda message: message.text == "🔧 Настроить профиль")
def configure_profile(message):
    """Настройка профиля пользователя"""
    ensure_user_exists(message.from_user.id)
    markup = types.ReplyKeyboardMarkup(resize_keyboard=True)
    markup.add(
        types.KeyboardButton("Возраст"),
        types.KeyboardButton("Рост"),
        types.KeyboardButton("Вес"),
        types.KeyboardButton("Цель"),
        types.KeyboardButton("Назад в меню")
    )
    bot.send_message(
        message.chat.id,
        "Выберите, что хотите изменить в профиле:",
        reply_markup=markup
    )

@bot.message_handler(func=lambda message: message.text == "Назад в меню")
def back_to_main_menu(message):
    """Возврат в главное меню"""
    bot.send_message(
        message.chat.id,
        "Возвращаемся в главное меню:",
        reply_markup=main_menu()
    )

@bot.message_handler(func=lambda message: message.text == "Имя")
def set_name(message):
    """Установка имени пользователя"""
    msg = bot.send_message(message.chat.id, "Введите ваше имя:")
    bot.register_next_step_handler(msg, save_name)

def save_name(message):
    """Сохранение имени пользователя"""
    try:
        conn = sqlite3.connect('user_profiles.db')
        cursor = conn.cursor()
        cursor.execute('''
            INSERT INTO users (user_id, name, free_generations, total_generations) 
            VALUES (?, ?, 10, 0)
            ON CONFLICT(user_id) 
            DO UPDATE SET name = excluded.name
        ''', (message.from_user.id, message.text))
        conn.commit()
        bot.send_message(
            message.chat.id,
            f"Имя сохранено: {message.text}",
            reply_markup=main_menu()
        )
    except Exception as e:
        logger.error(f"Ошибка сохранения имени: {e}")
        bot.send_message(message.chat.id, "Произошла ошибка при сохранении имени.")
    finally:
        conn.close()

@bot.message_handler(func=lambda message: message.text == "Возраст")
def set_age(message):
    """Установка возраста пользователя"""
    msg = bot.send_message(message.chat.id, "Введите ваш возраст:")
    bot.register_next_step_handler(msg, save_age)

def save_age(message):
    """Сохранение возраста пользователя"""
    try:
        age = int(message.text)
        if age < 0 or age > 120:
            raise ValueError("Некорректный возраст")
            
        conn = sqlite3.connect('user_profiles.db')
        cursor = conn.cursor()
        cursor.execute('UPDATE users SET age = ? WHERE user_id = ?', 
                      (age, message.from_user.id))
        conn.commit()
        bot.send_message(
            message.chat.id,
            f"Возраст сохранен: {age}",
            reply_markup=main_menu()
        )
    except ValueError:
        bot.send_message(message.chat.id, "Пожалуйста, введите корректный возраст (0-120).")
    except Exception as e:
        logger.error(f"Ошибка сохранения возраста: {e}")
        bot.send_message(message.chat.id, "Произошла ошибка при сохранении возраста.")
    finally:
        if 'conn' in locals():
            conn.close()

@bot.message_handler(func=lambda message: message.text == "Рост")
def set_height(message):
    """Установка роста пользователя"""
    msg = bot.send_message(message.chat.id, "Введите ваш рост (в см):")
    bot.register_next_step_handler(msg, save_height)

def save_height(message):
    """Сохранение роста пользователя"""
    try:
        height = float(message.text)
        if height < 50 or height > 250:
            raise ValueError("Некорректный рост")
            
        conn = sqlite3.connect('user_profiles.db')
        cursor = conn.cursor()
        cursor.execute('UPDATE users SET height = ? WHERE user_id = ?', 
                      (height, message.from_user.id))
        conn.commit()
        bot.send_message(
            message.chat.id,
            f"Рост сохранен: {height} см",
            reply_markup=main_menu()
        )
    except ValueError:
        bot.send_message(message.chat.id, "Пожалуйста, введите корректный рост (50-250 см).")
    except Exception as e:
        logger.error(f"Ошибка сохранения роста: {e}")
        bot.send_message(message.chat.id, "Произошла ошибка при сохранении роста.")
    finally:
        if 'conn' in locals():
            conn.close()

@bot.message_handler(func=lambda message: message.text == "Вес")
def set_weight(message):
    """Установка веса пользователя"""
    msg = bot.send_message(message.chat.id, "Введите ваш вес (в кг):")
    bot.register_next_step_handler(msg, save_weight)

def save_weight(message):
    """Сохранение веса пользователя"""
    try:
        weight = float(message.text)
        if weight < 30 or weight > 300:
            raise ValueError("Некорректный вес")
            
        conn = sqlite3.connect('user_profiles.db')
        cursor = conn.cursor()
        cursor.execute('UPDATE users SET weight = ? WHERE user_id = ?', 
                      (weight, message.from_user.id))
        conn.commit()
        bot.send_message(
            message.chat.id,
            f"Вес сохранен: {weight} кг",
            reply_markup=main_menu()
        )
    except ValueError:
        bot.send_message(message.chat.id, "Пожалуйста, введите корректный вес (30-300 кг).")
    except Exception as e:
        logger.error(f"Ошибка сохранения веса: {e}")
        bot.send_message(message.chat.id, "Произошла ошибка при сохранении веса.")
    finally:
        if 'conn' in locals():
            conn.close()

@bot.message_handler(func=lambda message: message.text == "Цель")
def set_goal(message):
    """Установка цели пользователя"""
    markup = types.ReplyKeyboardMarkup(resize_keyboard=True)
    markup.add(
        types.KeyboardButton("Похудение"),
        types.KeyboardButton("Набор массы"),
        types.KeyboardButton("Поддержание веса"),
        types.KeyboardButton("Назад в меню")
    )
    msg = bot.send_message(message.chat.id, "Выберите вашу цель:", reply_markup=markup)
    bot.register_next_step_handler(msg, save_goal)

def save_goal(message):
    """Сохранение цели пользователя"""
    try:
        if message.text == "Назад в меню":
            bot.send_message(message.chat.id, "Возвращаемся в главное меню", 
                           reply_markup=main_menu())
            return
            
        goal = message.text
        if goal not in ["Похудение", "Набор массы", "Поддержание веса"]:
            raise ValueError("Некорректная цель")
        
        conn = sqlite3.connect('user_profiles.db')
        cursor = conn.cursor()
        cursor.execute('UPDATE users SET goal = ? WHERE user_id = ?', 
                      (goal, message.from_user.id))
        conn.commit()
        bot.send_message(message.chat.id, f"Цель сохранена: {goal}", 
                        reply_markup=main_menu())
    except ValueError:
        bot.send_message(message.chat.id, "Пожалуйста, выберите цель из списка.")
    except Exception as e:
        logger.error(f"Ошибка сохранения цели: {e}")
        bot.send_message(message.chat.id, "Произошла ошибка при сохранении цели.")
    finally:
        if 'conn' in locals():
            conn.close()

@bot.message_handler(func=lambda message: message.text == "📊 Мой прогресс")
def show_progress(message):
    """Отображение прогресса пользователя"""
    conn = sqlite3.connect('user_profiles.db')
    cursor = conn.cursor()
    
    try:
        cursor.execute('SELECT * FROM users WHERE user_id = ?', (message.from_user.id,))
        user = cursor.fetchone()
        
        if not user:
            bot.send_message(message.chat.id, "Сначала настройте профиль!", reply_markup=main_menu())
            return
        
        free_gens, total_gens = check_user_generations(message.from_user.id)
        
        # Получаем статистику приема пищи
        cursor.execute('''
            SELECT meal_type, COUNT(*) as meal_count, SUM(calories) as total_calories 
            FROM meals 
            WHERE user_id = ? 
            GROUP BY meal_type
        ''', (message.from_user.id,))
        meal_stats = cursor.fetchall()
        
        progress_message = (
            f"👤 Профиль пользователя:\n"
            f"Имя: {user[1] or 'Не указано'}\n"
            f"Возраст: {user[2] or 'Не указан'}\n"
            f"Рост: {user[3] or 'Не указан'} см\n"
            f"Вес: {user[4] or 'Не указан'} кг\n"
            f"Цель: {user[5] or 'Не указана'}\n\n"
            f"🔢 Баланс генераций:\n"
            f"- Бесплатные генерации: {free_gens}\n"
            f"- Всего использовано: {total_gens}\n\n"
        )
        
        if meal_stats:
            progress_message += "📊 Статистика питания:\n"
            for stat in meal_stats:
                progress_message += f"- {stat[0]}: {stat[1]} приемов, {stat[2]} калорий\n"
        else:
            progress_message += "Пока нет записей о приемах пищи.\n"
        
        bot.send_message(message.chat.id, progress_message, reply_markup=main_menu())
        
    except Exception as e:
        logger.error(f"Ошибка отображения прогресса: {e}")
        bot.send_message(
            message.chat.id,
            "Произошла ошибка при получении данных профиля.",
            reply_markup=main_menu()
        )
    finally:
        conn.close()

@bot.message_handler(func=lambda message: True)
def handle_text(message):
    """Обработчик всех остальных текстовых сообщений"""
    bot.send_message(
        message.chat.id,
        "Пожалуйста, используйте меню для взаимодействия с ботом.",
        reply_markup=main_menu()
    )

if __name__ == "__main__":
    # Инициализируем базу данных при запуске
    init_database()
    
    # Запускаем бота
    while True:
        try:
            logger.info("Запуск бота...")
            bot.polling(none_stop=True)
        except Exception as e:
            logger.error(f"Ошибка: {e}")
            time.sleep(5)
