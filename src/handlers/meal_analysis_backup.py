import os
import logging
from telebot import TeleBot, types
import openai
import base64
from utils.keyboards import main_menu

logger = logging.getLogger(__name__)

class MealAnalysisHandler:
    def __init__(self, bot: TeleBot):
        self.bot = bot
        openai.api_key = os.getenv('OPENAI_API_KEY')  # Убедитесь, что ключ доступен в окружении

    def encode_image(self, image_data):
        """Кодирование изображения в base64."""
        return base64.b64encode(image_data).decode('utf-8')

    def handle_start_analysis(self, message):
        """Начало анализа блюда."""
        self.bot.send_message(
            message.chat.id,
            "Пожалуйста, отправьте фото блюда для анализа.",
            reply_markup=types.ReplyKeyboardRemove()
        )

    def handle_photo(self, message):
        """Обработка полученного фото."""
        try:
            # Получение информации о фото
            file_info = self.bot.get_file(message.photo[-1].file_id)
            downloaded_file = self.bot.download_file(file_info.file_path)

            # Кодируем изображение в base64
            base64_image = self.encode_image(downloaded_file)

            # Отправляем запрос в OpenAI
            response = openai.ChatCompletion.create(
                model="gpt-4",
                messages=[
                    {"role": "system", "content": "Ты эксперт по питанию. Проанализируй блюдо на изображении, определи ингредиенты, калорийность и дай советы."},
                    {"role": "user", "content": f"Детально опиши и проанализируй это блюдо: data:image/jpeg;base64,{base64_image}"}
                ]
            )

            # Отправляем результат анализа
            result = response.choices[0].message.content
            self.bot.send_message(
                message.chat.id,
                f"Результат анализа:\n{result}",
                reply_markup=main_menu()
            )

        except Exception as e:
            logger.error(f"Ошибка обработки фото: {e}")
            self.bot.send_message(
                message.chat.id,
                "Ошибка при обработке изображения. Попробуйте снова.",
                reply_markup=main_menu()
            )

    def register_handlers(self):
        """Регистрация обработчиков сообщений."""
        @self.bot.message_handler(func=lambda message: message.text == "🍽️ Анализ блюда")
        def start_analysis(message):
            self.handle_start_analysis(message)

        @self.bot.message_handler(content_types=['photo'])
        def process_photo(message):
            self.handle_photo(message)

