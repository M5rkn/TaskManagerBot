"""
Task Manager Bot - Бот для управления задачами с Google Calendar

Запуск бота:
    python main.py

Предварительная настройка:
1. Скопируйте .env.example в .env
2. Заполните BOT_TOKEN в .env
3. Для Google Calendar добавьте credentials.json
4. Установите зависимости: pip install -r requirements.txt
"""

import asyncio
import sys
from pathlib import Path

# Добавляем корень проекта до PATH
sys.path.insert(0, str(Path(__file__).parent))

from bot.main import main

if __name__ == "__main__":
    asyncio.run(main())
