#!/bin/bash

# Создаем директорию для бэкапа с текущей датой
BACKUP_DATE=$(date +%Y%m%d_%H%M%S)
mkdir -p backups/backup_$BACKUP_DATE

# Копируем основные компоненты бота
cp -r src/ backups/backup_$BACKUP_DATE/
cp bot.py backups/backup_$BACKUP_DATE/
cp requirements.txt backups/backup_$BACKUP_DATE/
cp text_prompts.py backups/backup_$BACKUP_DATE/
cp keyboards.py backups/backup_$BACKUP_DATE/

# Сохраняем базу данных
cp user_profiles.db backups/backup_$BACKUP_DATE/

# Сохраняем логи
cp bot.log backups/backup_$BACKUP_DATE/

# Создаем архив из всего бэкапа
cd backups
tar -czf telegram_bot_$BACKUP_DATE.tar.gz backup_$BACKUP_DATE/
rm -rf backup_$BACKUP_DATE/

echo "Бэкап создан: backups/telegram_bot_$BACKUP_DATE.tar.gz"
