import sqlite3
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def update_database():
    conn = sqlite3.connect('/root/telegram_bot/src/user_profiles.db')
    cursor = conn.cursor()

    try:
        cursor.execute("ALTER TABLE users ADD COLUMN last_activity DATETIME DEFAULT CURRENT_TIMESTAMP")
        conn.commit()
        logger.info("Колонка last_activity успешно добавлена")
    except sqlite3.OperationalError:
        logger.info("Колонка last_activity уже существует")

    conn.close()

if __name__ == "__main__":
    update_database()
