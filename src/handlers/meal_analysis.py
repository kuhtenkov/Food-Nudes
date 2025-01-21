import os
import logging
import random
from telebot import TeleBot, types
from openai import OpenAI
import base64
from utils.keyboards import main_menu

logger = logging.getLogger(__name__)

class MealAnalysisHandler:
    def __init__(self, bot: TeleBot, db_manager):
        self.bot = bot
        self.db_manager = db_manager
        self.current_rename_context = {}
        
        try:
            self.client = OpenAI(api_key=os.getenv('OPENAI_API_KEY'))
            logger.info("OpenAI client successfully initialized")
        except Exception as e:
            logger.error(f"Failed to initialize OpenAI client: {e}")
            raise

        # Коллекция провокационных фраз для разнообразия
        self.spicy_intros = [
            "Ну что, раздеваем твою тарелку?",
            "Время обнажить кулинарную правду!",
            "Голая правда о твоей еде incoming...",
            "Сейчас узнаем, что прячется под соусом!",
            "Внимание, будет горячо... и не только от блюда!"
        ]

        self.calorie_comments = [
            "Калории не прячутся, детка!",
            "Честно? Эта порция - целый роман с последствиями.",
            "Твоя тарелка врёт, я вижу насквозь!",
            "Осторожно, углеводы раздеваются!",
            "Калорийность? Считай, как интимные encounter'ы!"
        ]

        self.follow_up_phrases = [
            "Ну что, проголодался? Я готов раздеть твою следующую тарелку! 😏🍽️",
            "Один анализ позади, но моя страсть к кулинарным тайнам не утолена. Следующее блюдо, пожалуйста! 🔥",
            "Аппетит приходит во время еды... и во время моего анализа. Что там у тебя next? 😉",
            "Это было горячо, но я только разогрелся! Твоя следующая порция ждёт своего разоблачения. 🌶️",
            "Один culinary striptease окончен, но шоу продолжается! Какое блюдо раздетое ждёт меня? 👀"
        ]

    def generate_correction_keyboard(self, message_id, current_dish):
        """Создание клавиатуры для коррекции блюда"""
        markup = types.InlineKeyboardMarkup()
        markup.row(
            types.InlineKeyboardButton("Всё верно ✅", callback_data=f"meal_correct:{message_id}"),
            types.InlineKeyboardButton("Указать название 🍽️", callback_data=f"meal_rename:{message_id}:{current_dish}")
        )
        return markup

    def encode_image(self, image_path):
        """Кодирование изображения в base64"""
        try:
            with open(image_path, "rb") as image_file:
                return base64.b64encode(image_file.read()).decode('utf-8')
        except Exception as e:
            logger.error(f"Ошибка при кодировании изображения: {e}")
            raise

    def handle_start_analysis(self, message):
        """Начало анализа блюда с новым характером"""
        try:
            free_gens, paid_gens = self.db_manager.check_user_generations(message.from_user.id)
            
            if free_gens + paid_gens <= 0:
                self.bot.send_message(
                    message.chat.id,
                    "⚠️ Упс, твои бесплатные свидания с едой закончились. Пополни баланс, красавчик! 💸",
                    reply_markup=main_menu()
                )
                return

            self.bot.send_message(
                message.chat.id,
                "Готов узнать всю правду о своей тарелке? Присылай фото – я не боюсь никаких кулинарных тайн! 🍽️",
                reply_markup=types.ReplyKeyboardRemove()
            )
        except Exception as e:
            logger.error(f"Ошибка при отправке стартового сообщения: {e}")
            self.bot.send_message(
                message.chat.id,
                "Произошла интригующая ошибка. Попробуй соблазнить меня фото еще раз 😉",
                reply_markup=main_menu()
            )

    def handle_photo(self, message):
        """Обработка полученного фото с возможностью коррекции"""
        try:
            free_gens, paid_gens = self.db_manager.check_user_generations(message.from_user.id)
            
            if free_gens + paid_gens <= 0:
                self.bot.send_message(
                    message.chat.id,
                    "⚠️ Твои бесплатные свидания с едой окончены. Пополни баланс, красавчик! 💸",
                    reply_markup=main_menu()
                )
                return

            processing_msg = self.bot.send_message(
                message.chat.id,
                "Раздеваю твою тарелку... Анализирую со страстью к деталям! 🔍"
            )

            file_info = self.bot.get_file(message.photo[-1].file_id)
            downloaded_file = self.bot.download_file(file_info.file_path)

            os.makedirs("temp", exist_ok=True)
            file_path = f"temp/{message.photo[-1].file_id}.jpg"
            
            try:
                with open(file_path, "wb") as file:
                    file.write(downloaded_file)

                base64_image = self.encode_image(file_path)
            finally:
                if os.path.exists(file_path):
                    os.remove(file_path)

            # Первичный анализ для определения блюда
            dish_response = self.client.chat.completions.create(
                model="gpt-4o",
                messages=[
                    {
                        "role": "system",
                        "content": "Определи название блюда максимально точно. Назови его одним словом."
                    },
                    {
                        "role": "user",
                        "content": [
                            {"type": "text", "text": "Что это за блюдо?"},
                            {"type": "image_url", "image_url": {"url": f"data:image/jpeg;base64,{base64_image}"}}
                        ]
                    }
                ],
                max_tokens=20
            )

            detected_dish = dish_response.choices[0].message.content.strip()

            # Полный анализ блюда
            response = self.client.chat.completions.create(
                model="gpt-4o",
                messages=[
                    {
                        "role": "system",
                        "content": f"{random.choice(self.spicy_intros)}\n\n"
                        "Ты эксперт по питанию с острым языком в стиле FoodNudes. "
                        "Твоя задача - провести максимально честный и дерзкий анализ блюда:\n\n"
                        "🔥 Правила:\n"
                        "1. Определи ингредиенты с язвительным комментарием\n"
                        "2. Укажи калорийность с provокационным намёком\n"
                        "3. Оцени пищевую ценность с легким флиртом\n"
                        "4. Дай совет по употреблению в стиле злого диетолога\n\n"
                        f"{random.choice(self.calorie_comments)}"
                    },
                    {
                        "role": "user",
                        "content": [
                            {"type": "text", "text": f"Это блюдо '{detected_dish}'"},
                            {"type": "image_url", "image_url": {"url": f"data:image/jpeg;base64,{base64_image}"}}
                        ]
                    }
                ],
                max_tokens=300
            )

            self.bot.delete_message(message.chat.id, processing_msg.message_id)

            generations_left = self.db_manager.use_generation(message.from_user.id)
            logger.info(f"Остаток генераций: {generations_left}")

            analysis_result = response.choices[0].message.content

            # Добавляем клавиатуру для коррекции
            correction_message = self.bot.send_message(
                message.chat.id,
                f"🍽️ Анализ блюда '{detected_dish}':\n\n"
                f"{analysis_result}\n\n"
                f"🔍 Я правильно определил блюдо?",
                reply_markup=self.generate_correction_keyboard(message.message_id, detected_dish),
                parse_mode='Markdown'
            )

            # Сохраняем контекст для возможной коррекции
            self.current_rename_context = {
                'user_id': message.from_user.id,
                'image_base64': base64_image,
                'original_analysis': analysis_result,
                'original_dish': detected_dish,
                'message_id': correction_message.message_id
            }

        except Exception as e:
            logger.error(f"Ошибка обработки фото: {e}")
            error_message = ("Упс, что-то пошло не так. " 
                             "Возможно, твоя еда слишком горяча для моего анализа 😏 " 
                             "Попробуй прислать фото еще раз, возможно дело в формате изображения нужен jpeg..")
            self.bot.send_message(
                message.chat.id,
                error_message,
                reply_markup=main_menu()
            )

    def register_handlers(self):
        """Регистрация обработчиков сообщений"""
        @self.bot.message_handler(func=lambda message: message.text == "🍽️ Анализ блюда")
        def start_analysis(message):
            self.handle_start_analysis(message)

        @self.bot.message_handler(content_types=['photo'])
        def process_photo(message):
            self.handle_photo(message)

        @self.bot.callback_query_handler(func=lambda call: call.data.startswith('meal_rename:'))
        def handle_meal_rename(call):
            try:
                _, message_id, current_dish = call.data.split(':')
                self.bot.answer_callback_query(call.id)
                
                rename_msg = self.bot.send_message(
                    call.message.chat.id, 
                    f"Текущее определение блюда: *{current_dish}*\n"
                    "Введите точное название блюда:",
                    parse_mode='Markdown'
                )
                
                # Регистрируем следующий шаг
                self.bot.register_next_step_handler(rename_msg, self.process_meal_rename)
            except Exception as e:
                logger.error(f"Ошибка в callback обработки переименования: {e}")

        @self.bot.callback_query_handler(func=lambda call: call.data.startswith('meal_correct:'))
        def handle_meal_correct(call):
            try:
                # Удаляем инлайн-клавиатуру
                self.bot.edit_message_reply_markup(
                    chat_id=call.message.chat.id, 
                    message_id=call.message.message_id, 
                    reply_markup=None
                )
                
                # Отправляем провокационное сообщение
                self.bot.send_message(
                    call.message.chat.id, 
                    random.choice(self.follow_up_phrases),
                    reply_markup=main_menu()
                )
                
                # Подтверждаем callback
                self.bot.answer_callback_query(call.id, "Анализ подтвержден!")
            
            except Exception as e:
                logger.error(f"Ошибка при подтверждении анализа: {e}")
                self.bot.answer_callback_query(call.id, "Произошла ошибка.")

    def process_meal_rename(self, message):
        """Обработка нового названия блюда"""
        try:
            # Проверяем, что есть активный контекст
            if not hasattr(self, 'current_rename_context') or \
               self.current_rename_context.get('user_id') != message.from_user.id:
                return

            new_dish_name = message.text.strip()
            context = self.current_rename_context

            # Повторный анализ с новым названием
            response = self.client.chat.completions.create(
                model="gpt-4o",
                messages=[
                    {
                        "role": "system",
                        "content": f"{random.choice(self.spicy_intros)}\n\n"
                        "Ты эксперт по питанию с острым языком в стиле FoodNudes. "
                        "Твоя задача - провести максимально честный и дерзкий анализ блюда:\n\n"
                        "🔥 Правила:\n"
                        "1. Определи ингредиенты с язвительным комментарием\n"
                        "2. Укажи калорийность с provокационным намёком\n"
                        "3. Оцени пищевую ценность с легким флиртом\n"
                        "4. Дай совет по употреблению в стиле злого диетолога\n\n"
                        f"{random.choice(self.calorie_comments)}"
                    },
                    {
                        "role": "user",
                        "content": [
                            {"type": "text", "text": f"Это блюдо '{new_dish_name}'"},
                            {"type": "image_url", "image_url": {"url": f"data:image/jpeg;base64,{context['image_base64']}"}}
                        ]
                    }
                ],
                max_tokens=300
            )

            updated_analysis = response.choices[0].message.content

            # Отправляем обновленный анализ
            self.bot.send_message(
                message.chat.id,
                f"🍽️ Уточненный анализ блюда '{new_dish_name}':\n\n{updated_analysis}",
                reply_markup=main_menu(),
                parse_mode='Markdown'
            )

            # Очищаем контекст
            del self.current_rename_context

        except Exception as e:
            logger.error(f"Ошибка при переименовании блюда: {e}")
            self.bot.send_message(
            message.chat.id, 
                "Упс, что-то пошло не так. Попробуйте еще раз.",
                reply_markup=main_menu()
            )
