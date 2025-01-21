from telebot import types

def main_menu():
    """Главное меню"""
    markup = types.ReplyKeyboardMarkup(resize_keyboard=True)
    markup.add(types.KeyboardButton("🔧 Настроить профиль"))
    markup.add(types.KeyboardButton("🍽️ Анализ блюда"))
    markup.add(types.KeyboardButton("📊 Мой прогресс"))
    markup.add(types.KeyboardButton("💰 Пополнить баланс"))
    return markup

def profile_menu():
    """Меню настройки профиля"""
    markup = types.ReplyKeyboardMarkup(resize_keyboard=True)
    markup.add(types.KeyboardButton("Возраст"))
    markup.add(types.KeyboardButton("Рост"))
    markup.add(types.KeyboardButton("Вес"))
    markup.add(types.KeyboardButton("Цель"))
    markup.add(types.KeyboardButton("Уровень активности"))
    markup.add(types.KeyboardButton("Назад в меню"))
    return markup

def goals_menu():
    """Меню выбора цели"""
    markup = types.ReplyKeyboardMarkup(resize_keyboard=True)
    markup.add(types.KeyboardButton("Похудение"))
    markup.add(types.KeyboardButton("Набор массы"))
    markup.add(types.KeyboardButton("Поддержание веса"))
    markup.add(types.KeyboardButton("Назад в меню"))
    return markup

def activity_menu():
    """Меню выбора уровня активности"""
    markup = types.ReplyKeyboardMarkup(resize_keyboard=True)
    markup.add(types.KeyboardButton("Малоподвижный"))
    markup.add(types.KeyboardButton("Умеренно активный"))
    markup.add(types.KeyboardButton("Активный"))
    markup.add(types.KeyboardButton("Очень активный"))
    markup.add(types.KeyboardButton("Экстремально активный"))
    markup.add(types.KeyboardButton("Назад в меню"))
    return markup
