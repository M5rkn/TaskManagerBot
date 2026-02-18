import asyncio
import logging
import pytz
from aiogram import Bot, Dispatcher
from aiogram.client.default import DefaultBotProperties
from aiogram.enums import ParseMode
from aiogram.filters import CommandStart
from aiogram.types import Message
from datetime import datetime, timedelta

from config.settings import BOT_TOKEN, TIMEZONE
from db.database import db
from db.repositories import TaskRepository, ReminderRepository, UserRepository
from services.reminder_service import reminder_service
from services.google_calendar import google_calendar

from handlers.commands import router as commands_router
from handlers.tasks import router as tasks_router
from handlers.cancel import router as cancel_router

# Настройка логирования
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)

logger = logging.getLogger(__name__)


async def check_reminders(bot: Bot):
    """
    Периодическая проверка напоминаний
    
    Запускается каждые 30 секунд для проверки
    напоминаний, которые настало время отправить
    """
    while True:
        try:
            await asyncio.sleep(30)  # Проверка каждые 30 секунд
            
            # Получаем напоминания, которые настало время отправить
            due_reminders = await reminder_service.get_due_reminders()
            
            for reminder_data in due_reminders:
                user_id = reminder_data.get('user_id')
                reminder_id = reminder_data.get('reminder_id')
                task_id = reminder_data.get('task_id')
                
                # Получаем задачу для напоминания
                task = await TaskRepository.get_by_id(task_id, user_id)
                
                if task:
                    # Отправляем напоминание
                    try:
                        await bot.send_message(
                            chat_id=user_id,
                            text=(
                                f"🔔 <b>Напоминание о задаче!</b>\n\n"
                                f"📌 <b>{task.title}</b>\n"
                                f"📝 {task.description if task.description else 'Без описания'}\n\n"
                                f"📅 Дедлайн: {format_datetime(task.due_date)}\n"
                                f"🎯 Приоритет: {get_priority_emoji(task.priority)} {task.priority}"
                            ),
                            parse_mode="HTML"
                        )
                        
                        # Отмечаем напоминание как отправленное
                        await ReminderRepository.mark_as_sent(reminder_id)
                        
                        # Удаляем из очереди Redis
                        await reminder_service.remove_reminder(reminder_id)
                        
                        logger.info(f"Напоминание #{reminder_id} отправлено пользователю {user_id}")
                    
                    except Exception as e:
                        logger.error(f"Ошибка отправки напоминания: {e}")
        
        except Exception as e:
            logger.error(f"Ошибка в check_reminders: {e}")


async def check_overdue_tasks(bot: Bot):
    """
    Периодическая проверка просроченных задач
    
    Запускается каждые 5 минут
    """
    while True:
        try:
            await asyncio.sleep(300)  # Проверка каждые 5 минут
            
            # Получаем всех пользователей
            users = await UserRepository.get_all()
            
            for user in users:
                # Получаем просроченные задачи пользователя
                overdue_tasks = await TaskRepository.get_overdue(user.telegram_id)
                
                for task in overdue_tasks:
                    # Проверяем не было ли уже напоминания
                    if task.due_date:
                        tz = pytz.timezone(TIMEZONE)
                        time_since_due = datetime.now(tz) - task.due_date
                        
                        # Напоминаем если просрочено не больше чем на 1 час
                        if timedelta(0) < time_since_due < timedelta(hours=1):
                            try:
                                await bot.send_message(
                                    chat_id=user.telegram_id,
                                    text=(
                                        f"⚠️ <b>Просроченная задача!</b>\n\n"
                                        f"📌 <b>{task.title}</b>\n"
                                        f"📝 {task.description if task.description else 'Без описания'}\n\n"
                                        f"📅 Дедлайн был: {format_datetime(task.due_date)}\n"
                                        f"🎯 Приоритет: {get_priority_emoji(task.priority)} {task.priority}\n\n"
                                        f"Время выполнить! 💪"
                                    ),
                                    parse_mode="HTML"
                                )
                                
                                logger.info(f"Напоминание о просроченной задаче #{task.id} отправлено")
                            
                            except Exception as e:
                                logger.error(f"Ошибка отправки напоминания о просроченной задаче: {e}")
        
        except Exception as e:
            logger.error(f"Ошибка в check_overdue_tasks: {e}")


def format_datetime(dt: datetime) -> str:
    """Форматирование даты и времени"""
    if not dt:
        return "Не указано"
    return dt.strftime("%d.%m.%Y %H:%M")


def get_priority_emoji(priority: str) -> str:
    """Получение эмодзи приоритета"""
    emojis = {
        'low': '🟢',
        'medium': '🟡',
        'high': '🔴'
    }
    return emojis.get(priority, '🟡')


async def on_startup(bot: Bot):
    """Действия при запуске бота"""
    logger.info("🚀 Запуск бота...")
    
    # Подключение к базе данных
    await db.connect()
    logger.info("✅ Подключено к базе данных SQLite")
    
    # Подключение к Redis
    await reminder_service.connect()
    
    # Запуск фоновых задач
    asyncio.create_task(check_reminders(bot))
    asyncio.create_task(check_overdue_tasks(bot))
    
    logger.info("✅ Фоновые задачи запущены")
    
    # Информация о боте
    bot_info = await bot.get_me()
    logger.info(f"✅ Бот запущен: @{bot_info.username}")


async def on_shutdown(bot: Bot):
    """Действия при остановке бота"""
    logger.info("🛑 Остановка бота...")
    
    # Отключение от базы данных
    await db.disconnect()
    logger.info("✅ Отключено от базы данных")
    
    # Отключение от Redis
    await reminder_service.disconnect()
    logger.info("✅ Отключено от Redis")


async def main():
    """Главная функция"""
    # Создание бота и диспетчера
    bot = Bot(token=BOT_TOKEN, default=DefaultBotProperties(parse_mode=ParseMode.HTML))
    dp = Dispatcher()
    
    # Регистрация роутеров
    dp.include_router(commands_router)
    dp.include_router(tasks_router)
    dp.include_router(cancel_router)
    
    # Регистрация хендлеров запуска/остановки
    dp.startup.register(on_startup)
    dp.shutdown.register(on_shutdown)
    
    # Запуск polling
    logger.info("🤖 Бот запущен в режиме polling...")
    await dp.start_polling(bot)


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\n👋 Бот остановлен пользователем")
