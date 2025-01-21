import logging
from telebot import TeleBot, types
from database.db_manager import DatabaseManager
from utils.keyboards import main_menu, profile_menu, goals_menu, activity_menu

logger = logging.getLogger(__name__)

class ProfileHandler:
    def __init__(self, bot: TeleBot, db_manager: DatabaseManager):
        self.bot = bot
        self.db_manager = db_manager

    # Остальной код класса остается без изменений
    
    def calculate_daily_calories(self, weight, height, age, activity_level, goal):
        """Расчет дневной нормы калорий"""
        # Базовый обмен веществ (формула Миффлина-Сан Жеора)
        bmr = 10 * weight + 6.25 * height - 5 * age + 5

        # Коэффициент активности
        activity_multipliers = {
            "Малоподвижный": 1.2,
            "Умеренно активный": 1.375,
            "Активный": 1.55,
            "Очень активный": 1.725,
            "Экстремально активный": 1.9
        }
        
        # Учитываем уровень активности
        maintenance = bmr * activity_multipliers.get(activity_level, 1.2)
        
        # Корректировка на основе цели
        if goal == "Похудение":
            return int(maintenance - 500)  # Дефицит 500 ккал
        elif goal == "Набор массы":
            return int(maintenance + 500)  # Профицит 500 ккал
        else:
            return int(maintenance)  # Поддержание веса

    def handle_profile_settings(self, message):
        """Обработка нажатия кнопки настройки профиля"""
        self.bot.send_message(
            message.chat.id,
            "Что вы хотите настроить?",
            reply_markup=profile_menu()
        )

    def handle_age(self, message):
        """Запрос возраста пользователя"""
        msg = self.bot.send_message(
            message.chat.id,
            "Введите ваш возраст:",
            reply_markup=types.ReplyKeyboardRemove()
        )
        self.bot.register_next_step_handler(msg, self.save_age)

    def save_age(self, message):
        """Сохранение возраста пользователя"""
        try:
            age = int(message.text)
            if 0 <= age <= 120:
                self.db_manager.update_user_profile(message.from_user.id, "age", age)
                self.bot.send_message(
                    message.chat.id,
                    f"Возраст {age} лет успешно сохранен!",
                    reply_markup=profile_menu()
                )
                self.update_daily_calories(message.from_user.id)
            else:
                self.bot.send_message(
                    message.chat.id,
                    "Пожалуйста, введите корректный возраст (от 0 до 120 лет)",
                    reply_markup=profile_menu()
                )
        except ValueError:
            self.bot.send_message(
                message.chat.id,
                "Пожалуйста, введите число",
                reply_markup=profile_menu()
            )

    def handle_height(self, message):
        """Запрос роста пользователя"""
        msg = self.bot.send_message(
            message.chat.id,
            "Введите ваш рост в сантиметрах:",
            reply_markup=types.ReplyKeyboardRemove()
        )
        self.bot.register_next_step_handler(msg, self.save_height)

    def save_height(self, message):
        """Сохранение роста пользователя"""
        try:
            height = float(message.text)
            if 50 <= height <= 250:
                self.db_manager.update_user_profile(message.from_user.id, "height", height)
                self.bot.send_message(
                    message.chat.id,
                    f"Рост {height} см успешно сохранен!",
                    reply_markup=profile_menu()
                )
                self.update_daily_calories(message.from_user.id)
            else:
                self.bot.send_message(
                    message.chat.id,
                    "Пожалуйста, введите корректный рост (от 50 до 250 см)",
                    reply_markup=profile_menu()
                )
        except ValueError:
            self.bot.send_message(
                message.chat.id,
                "Пожалуйста, введите число",
                reply_markup=profile_menu()
            )

    def handle_weight(self, message):
        """Запрос веса пользователя"""
        msg = self.bot.send_message(
            message.chat.id,
            "Введите ваш вес в килограммах:",
            reply_markup=types.ReplyKeyboardRemove()
        )
        self.bot.register_next_step_handler(msg, self.save_weight)

    def save_weight(self, message):
        """Сохранение веса пользователя"""
        try:
            weight = float(message.text)
            if 3 <= weight <= 300:
                self.db_manager.update_user_profile(message.from_user.id, "weight", weight)
                self.bot.send_message(
                    message.chat.id,
                    f"Вес {weight} кг успешно сохранен!",
                    reply_markup=profile_menu()
                )
                self.update_daily_calories(message.from_user.id)
            else:
                self.bot.send_message(
                    message.chat.id,
                    "Пожалуйста, введите корректный вес (от 3 до 300 кг)",
                    reply_markup=profile_menu()
                )
        except ValueError:
            self.bot.send_message(
                message.chat.id,
                "Пожалуйста, введите число",
                reply_markup=profile_menu()
            )

    def handle_goal(self, message):
        """Запрос цели пользователя"""
        self.bot.send_message(
            message.chat.id,
            "Выберите вашу цель:",
            reply_markup=goals_menu()
        )

    def save_goal(self, message):
        """Сохранение цели пользователя"""
        goal = message.text
        if goal in ["Похудение", "Набор массы", "Поддержание веса"]:
            self.db_manager.update_user_profile(message.from_user.id, "goal", goal)
            self.bot.send_message(
                message.chat.id,
                f"Цель \"{goal}\" успешно сохранена!",
                reply_markup=profile_menu()
            )
            self.update_daily_calories(message.from_user.id)
        else:
            self.bot.send_message(
                message.chat.id,
                "Пожалуйста, выберите цель из предложенных вариантов",
                reply_markup=goals_menu()
            )

    def handle_activity(self, message):
        """Запрос уровня активности пользователя"""
        self.bot.send_message(
            message.chat.id,
            "Выберите ваш уровень физической активности:",
            reply_markup=activity_menu()
        )

    def save_activity(self, message):
        """Сохранение уровня активности пользователя"""
        activity = message.text
        valid_activities = ["Малоподвижный", "Умеренно активный", "Активный", 
                          "Очень активный", "Экстремально активный"]
        
        if activity in valid_activities:
            self.db_manager.update_user_profile(message.from_user.id, "activity_level", activity)
            self.bot.send_message(
                message.chat.id,
                f"Уровень активности \"{activity}\" успешно сохранен!",
                reply_markup=profile_menu()
            )
            self.update_daily_calories(message.from_user.id)
        else:
            self.bot.send_message(
                message.chat.id,
                "Пожалуйста, выберите уровень активности из предложенных вариантов",
                reply_markup=activity_menu()
            )

    def update_daily_calories(self, user_id):
        """Обновление дневной нормы калорий"""
        try:
            profile = self.db_manager.get_user_profile(user_id)
            if profile and all(x is not None for x in profile):
                age = profile[0]      # возраст
                height = profile[1]   # рост
                weight = profile[2]   # вес
                goal = profile[3]     # цель
                activity = profile[5] # уровень активности
                
                if all(isinstance(x, (int, float, str)) for x in [weight, height, age, activity, goal]):
                    daily_calories = self.calculate_daily_calories(
                        float(weight), 
                        float(height), 
                        int(age), 
                        str(activity), 
                        str(goal)
                    )
                    self.db_manager.update_user_profile(user_id, "daily_calories", daily_calories)
                    logger.info(f"Обновлены калории для пользователя {user_id}: {daily_calories}")
                else:
                    logger.error(f"Некорректные типы данных: weight={type(weight)}, height={type(height)}, "
                               f"age={type(age)}, activity={type(activity)}, goal={type(goal)}")
        except Exception as e:
            logger.error(f"Ошибка обновления калорий: {e}")

    def register_handlers(self):
        """Регистрация всех обработчиков профиля"""
        @self.bot.message_handler(func=lambda message: message.text == "🔧 Настроить профиль")
        def profile_settings(message):
            self.handle_profile_settings(message)

        @self.bot.message_handler(func=lambda message: message.text == "Возраст")
        def age(message):
            self.handle_age(message)

        @self.bot.message_handler(func=lambda message: message.text == "Рост")
        def height(message):
            self.handle_height(message)

        @self.bot.message_handler(func=lambda message: message.text == "Вес")
        def weight(message):
            self.handle_weight(message)

        @self.bot.message_handler(func=lambda message: message.text == "Цель")
        def goal(message):
            self.handle_goal(message)

        @self.bot.message_handler(func=lambda message: message.text == "Уровень активности")
        def activity(message):
            self.handle_activity(message)

        @self.bot.message_handler(func=lambda message: message.text in 
            ["Малоподвижный", "Умеренно активный", "Активный", "Очень активный", "Экстремально активный"])
        def save_activity_handler(message):
            self.save_activity(message)

        @self.bot.message_handler(func=lambda message: message.text in ["Похудение", "Набор массы", "Поддержание веса"])
        def save_goal_handler(message):
            self.save_goal(message)

