# src/services/image_service.py
import os
import base64
import logging
from telebot import TeleBot

logger = logging.getLogger(__name__)

class ImageService:
    @staticmethod
    def save_photo(bot: TeleBot, photo):
        """Сохранение фото локально"""
        try:
            file_info = bot.get_file(photo.file_id)
            downloaded_file = bot.download_file(file_info.file_path)
            
            os.makedirs('temp', exist_ok=True)
            file_path = f"temp/{photo.file_id}.jpg"
            
            with open(file_path, "wb") as file:
                file.write(downloaded_file)
                
            logger.info("Фото успешно сохранено локально")
            return file_path
            
        except Exception as e:
            logger.error(f"Ошибка сохранения фото: {e}")
            raise e

    @staticmethod
    def encode_image(image_path):
        """Кодирование изображения в base64"""
        try:
            with open(image_path, "rb") as image_file:
                return base64.b64encode(image_file.read()).decode('utf-8')
        except Exception as e:
            logger.error(f"Ошибка кодирования изображения: {e}")
            raise e

    @staticmethod
    def cleanup(file_path):
        """Удаление временного файла"""
        try:
            if os.path.exists(file_path):
                os.remove(file_path)
                logger.info("Временный файл удален")
        except Exception as e:
            logger.error(f"Ошибка удаления файла: {e}")