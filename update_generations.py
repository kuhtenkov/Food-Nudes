import sqlite3

# Подключаемся к базе данных
conn = sqlite3.connect('user_profiles.db')
cursor = conn.cursor()

# Выполняем обновление
cursor.execute('UPDATE users SET free_generations = 5 WHERE free_generations > 5')

# Сохраняем изменения
conn.commit()

# Проверяем результат
cursor.execute('SELECT user_id, free_generations FROM users')
results = cursor.fetchall()
print("Обновленные данные пользователей:")
for user_id, free_gens in results:
    print(f"Пользователь {user_id}: {free_gens} генераций")

# Закрываем соединение
conn.close()