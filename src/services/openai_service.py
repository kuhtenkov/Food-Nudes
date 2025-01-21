# src/services/openai_service.py
import os
import logging
from openai import OpenAI

logger = logging.getLogger(__name__)

class OpenAIService:
    def __init__(self):
        self.client = OpenAI(api_key=os.getenv('OPENAI_API_KEY'))

    def analyze_meal(self, base64_image):
        """Анализ блюда через OpenAI API"""
        try:
            response = self.client.chat.completions.create(
                model="gpt-4-vision-preview",
                messages=[
                    {
                        "role": "system",
                        "content": "Ты эксперт по питанию. Проанализируй блюдо на изображении и предоставь следующую информацию:\n"
                                 "1. Название блюда\n"
                                 "2. Основные ингредиенты\n"
                                 "3. Приблизительная калорийность\n"
                                 "4. Пищевая ценность (белки, жиры, углеводы)\n"
                                 "5. Рекомендации по здоровому питанию"
                    },
                    {
                        "role": "user",
                        "content": [
                            {"type": "text", "text": "Проанализируй это блюдо"},
                            {"type": "image_url", "image_url": {"url": f"data:image/jpeg;base64,{base64_image}"}}
                        ]
                    }
                ],
                max_tokens=1000
            )
            return response.choices[0].message.content
        except Exception as e:
            logger.error(f"Ошибка анализа блюда: {e}")
            raise e