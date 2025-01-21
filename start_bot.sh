#!/bin/bash
cd /root/food_naked
source new_venv/bin/activate

# Более агрессивная очистка процессов
cleanup() {
    # Завершаем все процессы, связанные с ботом
    pkill -9 -f "python3 src/main.py"
    pkill -9 -f "start_bot.sh"
    pkill -9 -f "telegram"
    pkill -9 -f "telebot"
}

# Обработка сигналов завершения
trap cleanup SIGINT SIGTERM

# Первоначальная очистка
cleanup

# Основной цикл запуска
while true; do
    # Проверяем, нет ли уже запущенных процессов
    if ! pgrep -f "python3 src/main.py" > /dev/null; then
        echo "Запуск бота $(date)" >> /root/food_naked/bot_start.log
        python3 src/main.py > bot.log 2>&1
    else
        echo "Бот уже запущен $(date)" >> /root/food_naked/bot_start.log
    fi
    
    # Пауза перед возможным перезапуском
    sleep 5
done
