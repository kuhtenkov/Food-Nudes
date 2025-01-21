import os
import logging
from datetime import datetime
from logging.handlers import RotatingFileHandler
from telebot import TeleBot, types
from database.db_manager import DatabaseManager
from utils.keyboards import main_menu

# Создаем директорию для логов, если её нет
log_directory = 'logs'
if not os.path.exists(log_directory):
    os.makedirs(log_directory)

# Настраиваем логирование
def setup_logging():
    # Создаем форматтер для логов
    formatter = logging.Formatter(
        '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    
    # Настраиваем файловый обработчик с ротацией
    file_handler = RotatingFileHandler(
        filename=f'{log_directory}/payment_bot.log',
        maxBytes=10*1024*1024,  # 10MB
        backupCount=5,
        encoding='utf-8'
    )
    file_handler.setFormatter(formatter)
    
    # Настраиваем вывод в консоль
    console_handler = logging.StreamHandler()
    console_handler.setFormatter(formatter)
    
    # Получаем корневой логгер
    logger = logging.getLogger('PaymentBot')
    logger.setLevel(logging.INFO)
    
    # Очищаем существующие обработчики
    logger.handlers = []
    
    # Добавляем обработчики к логгеру
    logger.addHandler(file_handler)
    logger.addHandler(console_handler)
    
    return logger

# Инициализируем логгер
logger = setup_logging()

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

class PaymentHandler:
    def __init__(self, bot: TeleBot, db_manager: DatabaseManager):
        self.bot = bot
        self.db_manager = db_manager
        self.provider_token = os.getenv('PAYMENT_PROVIDER_TOKEN')
        if not self.provider_token:
            logger.error("PAYMENT_PROVIDER_TOKEN не найден в переменных окружения")
            raise ValueError("Токен платежной системы не настроен")
        logger.info("PaymentHandler успешно инициализирован")

    def show_tariff_plans(self, message):
        """Показ доступных тарифных планов"""
        logger.info(f"Показ тарифов для пользователя {message.from_user.id}")
        try:
            markup = types.ReplyKeyboardMarkup(resize_keyboard=True)
            
            for plan_name, plan_info in TARIFF_PLANS.items():
                button_text = f"{plan_name} ({plan_info['price']} ₽)"
                markup.add(types.KeyboardButton(button_text))
            
            markup.add(types.KeyboardButton("Назад в меню"))

            free_gens, total_gens = self.db_manager.check_user_generations(message.from_user.id)
            
            text = (
                f"🔢 Ваш баланс:\n"
                f"- Бесплатные генерации: {free_gens}\n"
                f"- Всего использовано: {total_gens}\n\n"
                "📊 Доступные тарифы:\n"
            )
            
            for plan_name, plan_info in TARIFF_PLANS.items():
                text += (
                    f"• {plan_name}:\n"
                    f"  - {plan_info['generations']} генераций\n"
                    f"  - {plan_info['price']} ₽\n"
                )

            self.bot.send_message(message.chat.id, text, reply_markup=markup)
            logger.info(f"Тарифы успешно показаны пользователю {message.from_user.id}")
            
        except Exception as e:
            logger.error(f"Ошибка при показе тарифов пользователю {message.from_user.id}: {str(e)}", 
                        exc_info=True)
            self.bot.send_message(
                message.chat.id,
                "Произошла ошибка при загрузке тарифов. Попробуйте позже.",
                reply_markup=main_menu()
            )

    def create_invoice(self, message, plan_name):
        """Создание счета на оплату"""
        logger.info(f"Создание счета для пользователя {message.from_user.id}, план: {plan_name}")
        try:
            clean_plan_name = plan_name.split(" (")[0]
            if clean_plan_name not in TARIFF_PLANS:
                logger.error(f"Попытка создать счет с неверным планом: {clean_plan_name}")
                raise ValueError(f"Неверный тарифный план: {clean_plan_name}")
                
            plan = TARIFF_PLANS[clean_plan_name]
            
            prices = [
                types.LabeledPrice(
                    label=f'Тариф {clean_plan_name}', 
                    amount=plan["price"] * 100
                )
            ]
            
            invoice_data = {
                'chat_id': message.chat.id,
                'title': f"Тариф {clean_plan_name}",
                'description': f"Тариф {clean_plan_name} на {plan['generations']} генераций",
                'invoice_payload': f"tariff_{clean_plan_name}",
                'provider_token': self.provider_token,
                'currency': "RUB",
                'prices': prices,
                'start_parameter': "payment"
            }
            
            logger.info(f"Отправка инвойса с данными: {invoice_data}")
            self.bot.send_invoice(**invoice_data)
            logger.info(f"Инвойс успешно отправлен пользователю {message.from_user.id}")
            
        except Exception as e:
            logger.error(f"Ошибка создания счета для пользователя {message.from_user.id}: {str(e)}", 
                        exc_info=True)
            self.bot.send_message(
                message.chat.id,
                "Произошла ошибка при создании счета. Пожалуйста, попробуйте позже или обратитесь в поддержку.",
                reply_markup=main_menu()
            )

    def handle_plan_selection(self, message):
        """Обработка выбора тарифного плана"""
        logger.info(f"Обработка выбора тарифа для пользователя {message.from_user.id}")
        try:
            plan_name = message.text.split(" (")[0]
            logger.info(f"Пользователь {message.from_user.id} выбрал тариф: {plan_name}")
            self.create_invoice(message, plan_name)
            
        except Exception as e:
            logger.error(f"Ошибка обработки выбора тарифа: {str(e)}", exc_info=True)
            self.bot.send_message(
                message.chat.id,
                "Произошла ошибка при выборе тарифа. Попробуйте позже.",
                reply_markup=main_menu()
            )

    def handle_pre_checkout(self, pre_checkout_query):
        """Обработка предварительной проверки платежа"""
        logger.info(f"Обработка pre-checkout для query_id: {pre_checkout_query.id}")
        try:
            # Проверяем валидность payload
            payload = pre_checkout_query.invoice_payload
            plan_name = payload.split('_')[1]
            
            logger.info(f"Pre-checkout данные: plan_name={plan_name}, "
                       f"amount={pre_checkout_query.total_amount}, "
                       f"user_id={pre_checkout_query.from_user.id}")
            
            if plan_name not in TARIFF_PLANS:
                logger.error(f"Неверный тарифный план в pre-checkout: {plan_name}")
                self.bot.answer_pre_checkout_query(
                    pre_checkout_query.id,
                    ok=False,
                    error_message="Неверный тарифный план"
                )
                return

            # Проверяем сумму платежа
            expected_amount = TARIFF_PLANS[plan_name]["price"] * 100
            if pre_checkout_query.total_amount != expected_amount:
                logger.error(
                    f"Несоответствие суммы: ожидается {expected_amount}, "
                    f"получено {pre_checkout_query.total_amount}"
                )
                self.bot.answer_pre_checkout_query(
                    pre_checkout_query.id,
                    ok=False,
                    error_message="Несоответствие суммы платежа"
                )
                return

            # Если все проверки пройдены, подтверждаем платеж
            logger.info(f"Pre-checkout успешно пройден для query_id: {pre_checkout_query.id}")
            self.bot.answer_pre_checkout_query(pre_checkout_query.id, ok=True)
            
        except Exception as e:
            logger.error(f"Ошибка pre-checkout: {str(e)}", exc_info=True)
            self.bot.answer_pre_checkout_query(
                pre_checkout_query.id,
                ok=False,
                error_message="Произошла ошибка при обработке платежа"
            )

    def handle_successful_payment(self, message):
        """Обработка успешного платежа"""
        logger.info(f"Обработка успешного платежа от пользователя {message.from_user.id}")
        try:
            payment = message.successful_payment
            plan_name = payment.invoice_payload.split('_')[1]
            plan = TARIFF_PLANS[plan_name]
            
            # Сохраняем информацию о транзакции
            payment_info = {
                'user_id': message.from_user.id,
                'amount': payment.total_amount / 100,
                'currency': payment.currency,
                'provider_payment_charge_id': payment.provider_payment_charge_id,
                'telegram_payment_charge_id': payment.telegram_payment_charge_id,
                'plan_name': plan_name,
                'generations_added': plan['generations'],
                'payment_date': datetime.now()
            }
            
            logger.info(f"Информация о платеже: {payment_info}")
            
            # Сохраняем информацию о платеже
            self.db_manager.save_payment(payment_info)
            logger.info(f"Платёж сохранен в базе данных")
            
            # Начисляем генерации пользователю
            self.db_manager.add_generations(message.from_user.id, plan['generations'])
            logger.info(f"Генерации начислены пользователю {message.from_user.id}")
            
            success_message = (
                f"✅ Оплата успешно проведена!\n\n"
                f"Тариф: {plan_name}\n"
                f"Начислено генераций: {plan['generations']}\n"
                f"Номер транзакции: {payment.provider_payment_charge_id}"
            )
            
            self.bot.send_message(
                message.chat.id,
                success_message,
                reply_markup=main_menu()
            )
            logger.info(f"Успешное завершение обработки платежа для пользователя {message.from_user.id}")
            
        except Exception as e:
            logger.error(f"Ошибка обработки успешного платежа: {str(e)}", exc_info=True)
            self.bot.send_message(
                message.chat.id,
                "Произошла ошибка при обработке платежа. Пожалуйста, обратитесь в поддержку.",
                reply_markup=main_menu()
            )

    def register_handlers(self):
        """Регистрация обработчиков платежей"""
        logger.info("Регистрация обработчиков платежей")
        
        @self.bot.message_handler(func=lambda message: message.text == "💰 Пополнить баланс")
        def show_plans(message):
            self.show_tariff_plans(message)

        @self.bot.message_handler(func=lambda message: any(
            message.text.startswith(f"{plan} (") for plan in TARIFF_PLANS.keys()
        ))
        def process_plan_selection(message):
            plan_name = message.text.split(" (")[0]
            logger.info(f"Выбран тарифный план: {plan_name}")
            self.handle_plan_selection(message)

        @self.bot.pre_checkout_query_handler(func=lambda query: True)
        def pre_checkout(pre_checkout_query):
            self.handle_pre_checkout(pre_checkout_query)

        @self.bot.message_handler(content_types=['successful_payment'])
        def successful_payment(message):
            self.handle_successful_payment(message)
            
        logger.info("Обработчики платежей успешно зарегистрированы")