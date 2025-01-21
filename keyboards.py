# src/utils/keyboards.py
from telebot import types

def main_menu():
    """Создание главного меню"""
    markup = types.ReplyKeyboardMarkup(resize_keyboard=True, row_width=2)
    markup.add(
        types.KeyboardButton("🔧 Настроить профиль"),
        types.KeyboardButton("🍽️ Анализ блюда"),
        types.KeyboardButton("📊 Мой прогресс"),
        types.KeyboardButton("💰 Пополнить баланс")
    )
    return markup

def profile_menu():
    """Меню настройки профиля"""
    markup = types.ReplyKeyboardMarkup(resize_keyboard=True)
    markup.add(
        types.KeyboardButton("Возраст"),
        types.KeyboardButton("Рост"),
        types.KeyboardButton("Вес"),
        types.KeyboardButton("Цель"),
        types.KeyboardButton("Назад в меню")
    )
    return markup

def goals_menu():
    """Меню выбора целей"""
    markup = types.ReplyKeyboardMarkup(resize_keyboard=True)
    markup.add(
        types.KeyboardButton("Похудение"),
        types.KeyboardButton("Набор массы"),
        types.KeyboardButton("Поддержание веса"),
        types.KeyboardButton("Назад в меню")
    )
    return markup

def back_to_menu():
    """Кнопка возврата в главное меню"""
    markup = types.ReplyKeyboardMarkup(resize_keyboard=True)
    markup.add(types.KeyboardButton("Назад в меню"))
    return markup