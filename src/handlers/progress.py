
import logging
from telebot import TeleBot
from database.db_manager import DatabaseManager
from utils.keyboards import main_menu

logger = logging.getLogger(__name__)

def calculate_daily_calories(age, height, weight, goal, activity_level):
    """Расчёт дневной нормы калорий."""
    bmr = 10 * weight + 6.25 * height - 5 * age + 5  # Для мужчин (+5), для женщин (-161)
    
    activity_multiplier = {
        'Малоподвижный': 1.2,
        'Умеренно активный': 1.55,
        'Активный': 1.75,
        'Очень активный': 2.0
    }.get(activity_level, 1.2)
    
    daily_calories = bmr * activity_multiplier
    
    if goal == 'Похудение':
        daily_calories -= 500
    elif goal == 'Набор массы':
        daily_calories += 500

    return int(daily_calories)

class ProgressHandler:
    def __init__(self, bot: TeleBot, db_manager: DatabaseManager):
        self.bot = bot
        self.db_manager = db_manager

    def show_progress(self, message):
        """Отображение прогресса пользователя."""
        try:
            profile = self.db_manager.get_user_profile(message.from_user.id)

            # Проверяем, что профиль существует
            if not profile or len(profile) < 6:
                raise ValueError("Неполные данные профиля пользователя")

            # Распаковываем профиль
            age, height, weight, goal, daily_calories, activity_level = profile

            # Рассчитываем daily_calories, если оно отсутствует
            if not daily_calories:
                daily_calories = calculate_daily_calories(
                    age=age or 30,  # Значение по умолчанию
                    height=height or 170,  # Значение по умолчанию
                    weight=weight or 70,  # Значение по умолчанию
                    goal=goal or 'Поддержание веса',  # Значение по умолчанию
                    activity_level=activity_level or 'Малоподвижный'  # Значение по умолчанию
                )
                self.db_manager.update_user_profile(message.from_user.id, 'daily_calories', daily_calories)

            # Формируем текст профиля
            goal_recommendation = {
                "Похудение": "Для достижения цели рекомендуется придерживаться дефицита калорий и регулярно заниматься спортом.",
                "Набор массы": "Для набора массы важно обеспечить профицит калорий и уделять внимание силовым тренировкам.",
                "Поддержание веса": "Для поддержания веса важно соблюдать баланс между потреблением и расходом калорий."
            }.get(goal, "Нет рекомендаций по данной цели.")

            profile_text = (
                f"Ваш профиль:\n"
                f"Возраст: {age or 'Не указан'}\n"
                f"Рост: {height or 'Не указан'} см\n"
                f"Вес: {weight or 'Не указан'} кг\n"
                f"Цель: {goal or 'Не указана'}\n"
                f"Уровень активности: {activity_level or 'Не указан'}\n\n"
                f"Ваш план питания:\n"
                f"Рекомендуемое количество калорий: {daily_calories or 'Не рассчитано'} ккал/день\n"
                f"{goal_recommendation}\n\n"
            )

            free_gens, total_gens = self.db_manager.check_user_generations(message.from_user.id)
            profile_text += (
                f"Статистика использования:\n"
                f"Бесплатные генерации: {free_gens}\n"
                f"Всего использовано генераций: {total_gens}\n"
            )

            self.bot.send_message(message.chat.id, profile_text, reply_markup=main_menu())

        except ValueError as ve:
            logger.error(f"Ошибка данных профиля: {ve}")
            self.bot.send_message(
                message.chat.id,
                "Ваш профиль заполнен не полностью. Пожалуйста, настройте профиль.",
                reply_markup=main_menu()
            )
        except Exception as e:
            logger.error(f"Ошибка при отображении прогресса: {e}")
            self.bot.send_message(
                message.chat.id,
                "Произошла ошибка при получении данных. Попробуйте позже.",
                reply_markup=main_menu()
            )

    def register_handlers(self):
        """Регистрация обработчиков прогресса."""
        @self.bot.message_handler(func=lambda message: message.text == "📊 Мой прогресс")
        def progress(message):
            self.show_progress(message)

