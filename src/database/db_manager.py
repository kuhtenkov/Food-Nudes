import sqlite3
import logging
from datetime import datetime

logger = logging.getLogger(__name__)

class DatabaseManager:
    def __init__(self, db_path="/root/new_telegram_bot/src/user_profiles.db"):
        self.connection = sqlite3.connect(db_path, check_same_thread=False)
        self.cursor = self.connection.cursor()
        self.init_db()

    def init_db(self):
        """Инициализация базы данных."""
        # Создаем основную таблицу пользователей
        self.cursor.execute("""
        CREATE TABLE IF NOT EXISTS users (
            user_id INTEGER PRIMARY KEY,
            age INTEGER,
            height REAL,
            weight REAL,
            goal TEXT,
            daily_calories INTEGER,
            activity_level TEXT DEFAULT 'Не указан',
            free_generations INTEGER DEFAULT 5,
            total_generations INTEGER DEFAULT 0,
            paid_generations INTEGER DEFAULT 0
        )
        """)
        
        # Добавляем колонку last_activity, если её ещё нет
        try:
            self.cursor.execute("ALTER TABLE users ADD COLUMN last_activity DATETIME DEFAULT CURRENT_TIMESTAMP")
            self.connection.commit()
            logger.info("Колонка last_activity успешно добавлена в таблицу users")
        except sqlite3.OperationalError:
            # Колонка уже существует, игнорируем ошибку
            pass
        
        # Создаем таблицу платежей
        self.cursor.execute("""
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
        """)
        
        self.connection.commit()

    def get_user_profile(self, user_id):
        """Получение профиля пользователя."""
        try:
            query = """
            SELECT age, height, weight, goal, daily_calories, activity_level
            FROM users
            WHERE user_id = ?
            """
            self.cursor.execute(query, (user_id,))
            return self.cursor.fetchone()
        except sqlite3.Error as e:
            logger.error(f"Ошибка получения профиля пользователя: {e}")
            return None

    def update_user_profile(self, user_id, field, value):
        """Обновление поля профиля пользователя."""
        try:
            query = f"UPDATE users SET {field} = ?, last_activity = CURRENT_TIMESTAMP WHERE user_id = ?"
            self.cursor.execute(query, (value, user_id))
            self.connection.commit()
            logger.info(f"Обновлено поле {field} для пользователя {user_id}")
        except sqlite3.Error as e:
            logger.error(f"Ошибка обновления профиля пользователя: {e}")

    def ensure_user_exists(self, user_id):
        """Проверяет, существует ли пользователь, и добавляет его, если нет."""
        try:
            query = "SELECT 1 FROM users WHERE user_id = ?"
            self.cursor.execute(query, (user_id,))
            if not self.cursor.fetchone():
                query = """
                INSERT INTO users (user_id, age, height, weight, goal, daily_calories, activity_level, free_generations, last_activity)
                VALUES (?, NULL, NULL, NULL, NULL, NULL, 'Не указан', 5, CURRENT_TIMESTAMP)
                """
                self.cursor.execute(query, (user_id,))
                self.connection.commit()
                logger.info(f"Создан профиль для нового пользователя {user_id} с 5 бесплатными генерациями")
            else:
                self.update_last_activity(user_id)
        except sqlite3.Error as e:
            logger.error(f"Ошибка создания профиля пользователя: {e}")

    def update_last_activity(self, user_id):
        """Обновляет время последней активности пользователя."""
        try:
            query = "UPDATE users SET last_activity = CURRENT_TIMESTAMP WHERE user_id = ?"
            self.cursor.execute(query, (user_id,))
            self.connection.commit()
        except sqlite3.Error as e:
            logger.error(f"Ошибка обновления времени последней активности: {e}")

    def get_total_users(self):
        """Возвращает общее количество пользователей."""
        try:
            self.cursor.execute("SELECT COUNT(*) FROM users")
            return self.cursor.fetchone()[0]
        except sqlite3.Error as e:
            logger.error(f"Ошибка получения общего количества пользователей: {e}")
            return 0

    def get_total_generations(self):
        """Возвращает общее количество генераций."""
        try:
            self.cursor.execute("SELECT SUM(total_generations) FROM users")
            return self.cursor.fetchone()[0] or 0
        except sqlite3.Error as e:
            logger.error(f"Ошибка получения общего количества генераций: {e}")
            return 0

    def get_active_users_last_week(self):
        """Возвращает количество активных пользователей за последнюю неделю."""
        try:
            query = """
            SELECT COUNT(DISTINCT user_id) 
            FROM users 
            WHERE last_activity > datetime('now', '-7 days')
            """
            self.cursor.execute(query)
            return self.cursor.fetchone()[0]
        except sqlite3.Error as e:
            logger.error(f"Ошибка получения количества активных пользователей: {e}")
            return 0

    def check_user_generations(self, user_id):
        """Проверка количества бесплатных и общих генераций пользователя."""
        try:
            query = """
            SELECT free_generations, total_generations
            FROM users
            WHERE user_id = ?
            """
            self.cursor.execute(query, (user_id,))
            result = self.cursor.fetchone()
            if result:
                return result  # Возвращаем (free_generations, total_generations)
            else:
                # Если пользователь не найден, возвращаем значения по умолчанию
                return 0, 0
        except sqlite3.Error as e:
            logger.error(f"Ошибка проверки генераций пользователя: {e}")
            return 0, 0

    def save_payment(self, payment_info):
        """Сохранение информации о платеже."""
        logger.info(f"Начало сохранения платежа: {payment_info}")
        try:
            # Проверка наличия всех необходимых ключей
            required_keys = [
                'user_id', 'telegram_payment_charge_id', 'amount', 'plan_name',
                'generations_added', 'payment_date'
            ]
            for key in required_keys:
                if key not in payment_info:
                    logger.error(f"Отсутствует обязательный ключ: {key}")
                    raise ValueError(f"Отсутствует обязательный ключ: {key}")

            # Вставляем информацию о платеже в таблицу платежей
            insert_query = """
            INSERT INTO payments (user_id, payment_id, amount, plan, generations, status, created_at)
            VALUES (?, ?, ?, ?, ?, ?, ?)
            """
            self.cursor.execute(insert_query, (
                payment_info['user_id'],
                payment_info['telegram_payment_charge_id'],
                payment_info['amount'],
                payment_info['plan_name'],
                payment_info['generations_added'],
                'completed',
                payment_info['payment_date']
            ))

            # Обновляем количество оплаченных генераций для пользователя
            update_query = """
            UPDATE users
            SET paid_generations = COALESCE(paid_generations, 0) + ?,
                total_generations = COALESCE(total_generations, 0) + ?,
                last_activity = CURRENT_TIMESTAMP
            WHERE user_id = ?
            """
            self.cursor.execute(update_query, (
                payment_info['generations_added'],
                payment_info['generations_added'],
                payment_info['user_id']
            ))

            self.connection.commit()
            logger.info(f"Платеж для пользователя {payment_info['user_id']} сохранен успешно")
        except sqlite3.IntegrityError as e:
            self.connection.rollback()
            logger.error(f"Ошибка целостности данных при сохранении платежа: {e}")
            raise
        except sqlite3.OperationalError as e:
            self.connection.rollback()
            logger.error(f"Операционная ошибка базы данных: {e}")
            raise
        except ValueError as e:
            logger.error(f"Ошибка валидации данных: {e}")
            raise
        except Exception as e:
            self.connection.rollback()
            logger.error(f"Непредвиденная ошибка при сохранении платежа: {e}")
            raise

    def add_generations(self, user_id, generations):
        """Добавление количества генераций пользователю."""
        try:
            query = """
            UPDATE users
            SET free_generations = COALESCE(free_generations, 0) + ?,
                total_generations = COALESCE(total_generations, 0) + ?,
                last_activity = CURRENT_TIMESTAMP
            WHERE user_id = ?
            """
            self.cursor.execute(query, (generations, generations, user_id))
            self.connection.commit()
            logger.info(f"Добавлено {generations} генераций пользователю {user_id}")
        except sqlite3.Error as e:
            self.connection.rollback()
            logger.error(f"Ошибка добавления генераций: {e}")
            raise

    def use_generation(self, user_id):
        """Списывание одной генерации у пользователя."""
        try:
            # Сначала пытаемся списать из бесплатных
            free_query = """
            UPDATE users 
            SET free_generations = CASE 
                WHEN free_generations > 0 THEN free_generations - 1 
                ELSE free_generations 
            END,
            total_generations = total_generations + 1,
            last_activity = CURRENT_TIMESTAMP
            WHERE user_id = ?
            """
            self.cursor.execute(free_query, (user_id,))
            
            # Если не осталось бесплатных, списываем из оплаченных
            paid_query = """
            UPDATE users 
            SET paid_generations = CASE 
                WHEN paid_generations > 0 THEN paid_generations - 1 
                ELSE paid_generations 
            END,
            total_generations = total_generations + 1,
            last_activity = CURRENT_TIMESTAMP
            WHERE user_id = ? AND free_generations = 0
            """
            self.cursor.execute(paid_query, (user_id,))
            
            self.connection.commit()
            logger.info(f"Использована одна генерация пользователем {user_id}")
            
            # Возвращаем остаток генераций
            generations_query = """
            SELECT free_generations, paid_generations 
            FROM users 
            WHERE user_id = ?
            """
            self.cursor.execute(generations_query, (user_id,))
            return self.cursor.fetchone()
    
        except sqlite3.Error as e:
            self.connection.rollback()
            logger.error(f"Ошибка списания генерации: {e}")
            raise

