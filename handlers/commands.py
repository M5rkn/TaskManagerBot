from aiogram import Router, F
from aiogram.types import Message, CallbackQuery
from aiogram.filters import Command
from aiogram.fsm.context import FSMContext
from datetime import datetime
import pytz

from bot.keyboards import get_main_menu, get_task_list_keyboard, get_cancel_keyboard
from db.repositories import UserRepository
from config.settings import TIMEZONE
from bot.states import TaskStates

router = Router()


@router.message(Command("start"))
async def cmd_start(message: Message):
    """Обработчик команды /start"""
    user = await UserRepository.create_or_update(
        telegram_id=message.from_user.id,
        username=message.from_user.username,
        first_name=message.from_user.first_name
    )
    
    await message.answer(
        f"👋 Приветствую, {message.from_user.first_name}!\n\n"
        f"Я бот для управления задачами с интеграцией Google Calendar.\n\n"
        f"📋 <b>Мои возможности:</b>\n"
        f"• Создание и управление задачами\n"
        f"• Синхронизация с Google Calendar\n"
        f"• Напоминания о дедлайнах\n"
        f"• Просмотр статистики\n\n"
        f"Выберите действие в меню ниже 👇",
        reply_markup=get_main_menu(),
        parse_mode="HTML"
    )


@router.message(Command("help"))
@router.callback_query(F.data == "help")
async def cmd_help(callback: CallbackQuery | Message):
    """Обработчик команды /help"""
    help_text = """
📖 <b>Справка по боту</b>

<b>Основные команды:</b>
/start - Запуск бота
/help - Показать справку
/tasks - Список задач
/add - Добавить задачу
/stats - Статистика

<b>Как создать задачу:</b>
1. Нажмите "➕ Добавить задачу"
2. Введите название задачи
3. Введите описание (или пропустите)
4. Выберите приоритет
5. Укажите дедлайн
6. Настройте напоминание

<b>Интеграция с Google Calendar:</b>
Для синхронизации с календарем необходимо настроить credentials.json

<b>Вопросы?</b>
Обращайтесь к разработчику.
"""
    
    if isinstance(callback, CallbackQuery):
        await callback.message.edit_text(help_text, reply_markup=get_main_menu(), parse_mode="HTML")
        await callback.answer()
    else:
        await callback.answer(help_text, reply_markup=get_main_menu(), parse_mode="HTML")


@router.callback_query(F.data == "main_menu")
async def main_menu_handler(callback: CallbackQuery):
    """Возврат к главному меню"""
    await callback.message.edit_text(
        "📋 <b>Главное меню</b>\n\nВыберите действие:",
        reply_markup=get_main_menu(),
        parse_mode="HTML"
    )
    await callback.answer()


@router.callback_query(F.data == "tasks_list")
async def tasks_list_handler(callback: CallbackQuery):
    """Просмотр списка задач"""
    await callback.message.edit_text(
        "📝 <b>Управление задачами</b>\n\nВыберите фильтр:",
        reply_markup=get_task_list_keyboard(),
        parse_mode="HTML"
    )
    await callback.answer()


@router.callback_query(F.data == "task_create")
async def task_create_handler(callback: CallbackQuery, state: FSMContext):
    """Начало создания новой задачи"""
    await state.set_state(TaskStates.waiting_for_title)
    await callback.message.edit_text(
        "➕ <b>Создание новой задачи</b>\n\n"
        "Введите <b>название</b> задачи:",
        reply_markup=get_cancel_keyboard(),
        parse_mode="HTML"
    )
    await callback.answer()


@router.callback_query(F.data == "calendar_view")
async def calendar_view_handler(callback: CallbackQuery):
    """Просмотр календаря"""
    from services.google_calendar import google_calendar
    
    events = await google_calendar.get_events()
    
    if not events:
        text = "📅 <b>Календарь</b>\n\nНа ближайшие 7 дней событий нет."
    else:
        text = "📅 <b>Календарь на ближайшие 7 дней:</b>\n\n"
        for event in events[:10]:
            start = event.get('start', {})
            date_str = start.get('dateTime', start.get('date', ''))[:10]
            time_str = start.get('dateTime', '')[11:16] if start.get('dateTime') else ''
            text += f"📌 <b>{event.get('summary', 'Без названия')}</b>\n"
            text += f"   🕐 {date_str} {time_str}\n\n"
    
    await callback.message.edit_text(
        text,
        reply_markup=get_main_menu(),
        parse_mode="HTML"
    )
    await callback.answer()


@router.callback_query(F.data == "reminders_view")
async def reminders_view_handler(callback: CallbackQuery):
    """Просмотр напоминаний"""
    from db.repositories import ReminderRepository
    from db.database import db
    
    await db.connect()
    reminders = await ReminderRepository.get_pending()
    
    if not reminders:
        text = "⏰ <b>Напоминания</b>\n\nНет активных напоминаний."
    else:
        text = "⏰ <b>Активные напоминания:</b>\n\n"
        for reminder in reminders[:10]:
            text += f"🔔 Напоминание #{reminder.id}\n"
            text += f"   🕐 {reminder.reminder_time.strftime('%d.%m.%Y %H:%M')}\n\n"
    
    await callback.message.edit_text(
        text,
        reply_markup=get_main_menu(),
        parse_mode="HTML"
    )
    await callback.answer()


@router.callback_query(F.data == "stats_view")
async def stats_view_handler(callback: CallbackQuery):
    """Просмотр статистики"""
    from db.repositories import TaskRepository
    from db.database import db
    
    await db.connect()
    user_id = callback.from_user.id
    
    all_tasks = await TaskRepository.get_all(user_id)
    pending = await TaskRepository.get_all(user_id, status='pending')
    completed = await TaskRepository.get_all(user_id, status='completed')
    overdue = await TaskRepository.get_overdue(user_id)
    
    text = f"""
📊 <b>Статистика задач</b>

📋 Всего задач: <b>{len(all_tasks)}</b>
⏳ В ожидании: <b>{len(pending)}</b>
✅ Завершенные: <b>{len(completed)}</b>
🔥 Просроченные: <b>{len(overdue)}</b>

"""
    
    if all_tasks:
        completion_rate = len(completed) / len(all_tasks) * 100
        text += f"📈 Процент выполнения: <b>{completion_rate:.1f}%</b>"
    
    await callback.message.edit_text(
        text,
        reply_markup=get_main_menu(),
        parse_mode="HTML"
    )
    await callback.answer()
