from aiogram import Router, F
from aiogram.types import Message, CallbackQuery
from aiogram.fsm.context import FSMContext
from datetime import datetime, timedelta
import pytz

from bot.states import TaskStates, EditTaskStates
from bot.keyboards import (
    get_main_menu, get_priority_keyboard,
    get_reminder_keyboard, get_cancel_keyboard,
    get_task_actions_keyboard, get_task_list_keyboard
)
from db.repositories import TaskRepository, UserRepository
from db.database import db
from services.google_calendar import google_calendar
from models.task import Task
from config.settings import TIMEZONE

router = Router()


# ==================== СОЗДАНИЕ ЗАДАЧИ ====================

@router.message(TaskStates.waiting_for_title)
async def process_task_title(message: Message, state: FSMContext):
    """Обработка названия задачи"""
    await state.update_data(title=message.text)
    await state.set_state(TaskStates.waiting_for_description)
    await message.answer(
        "📝 Введите <b>описание</b> задачи (или нажмите 'Пропустить'):",
        parse_mode="HTML",
        reply_markup=get_cancel_keyboard()
    )


@router.message(TaskStates.waiting_for_description, F.text.lower() != "пропустить")
async def process_task_description(message: Message, state: FSMContext):
    """Обработка описания задачи"""
    await state.update_data(description=message.text)
    await state.set_state(TaskStates.waiting_for_priority)
    await message.answer(
        "🎯 Выберите <b>приоритет</b> задачи:",
        reply_markup=get_priority_keyboard(),
        parse_mode="HTML"
    )


@router.message(TaskStates.waiting_for_description, F.text.lower() == "пропустить")
async def skip_task_description(message: Message, state: FSMContext):
    """Пропуск описания задачи"""
    await state.update_data(description="")
    await state.set_state(TaskStates.waiting_for_priority)
    await message.answer(
        "🎯 Выберите <b>приоритет</b> задачи:",
        reply_markup=get_priority_keyboard(),
        parse_mode="HTML"
    )


@router.callback_query(F.data.startswith("priority_"))
async def process_task_priority(callback: CallbackQuery, state: FSMContext):
    """Обработка выбора приоритета"""
    priority = callback.data.split("_")[1]
    await state.update_data(priority=priority)
    await state.set_state(TaskStates.waiting_for_due_date)
    
    await callback.message.edit_text(
        "📅 Введите <b>дедлайн</b> в формате:\n"
        "ДД.ММ.ГГГГ ЧЧ:ММ\n\n"
        "Пример: 20.02.2026 15:00\n\n"
        "Или нажмите 'Пропустить' если нет дедлайна:",
        reply_markup=get_cancel_keyboard(),
        parse_mode="HTML"
    )
    await callback.answer()


@router.message(TaskStates.waiting_for_due_date, F.text.lower() != "пропустить")
async def process_task_due_date(message: Message, state: FSMContext):
    """Обработка дедлайна задачи"""
    try:
        due_date = datetime.strptime(message.text, "%d.%m.%Y %H:%M")
        due_date = pytz.timezone(TIMEZONE).localize(due_date)
        await state.update_data(due_date=due_date.isoformat())
        await state.set_state(TaskStates.waiting_for_reminder)
        await message.answer(
            "🔔 Хотите ли вы получать <b>напоминания</b>?",
            reply_markup=get_reminder_keyboard(),
            parse_mode="HTML"
        )
    except ValueError:
        await message.answer(
            "❌ Неверный формат даты. Попробуйте еще раз:\n"
            "Формат: ДД.ММ.ГГГГ ЧЧ:ММ\n"
            "Пример: 20.02.2026 15:00"
        )


@router.message(TaskStates.waiting_for_due_date, F.text.lower() == "пропустить")
async def skip_task_due_date(message: Message, state: FSMContext):
    """Пропуск дедлайна"""
    await state.update_data(due_date=None)
    await state.set_state(TaskStates.waiting_for_reminder)
    await message.answer(
        "🔔 Хотите ли вы получать <b>напоминания</b>?",
        reply_markup=get_reminder_keyboard(),
        parse_mode="HTML"
    )


@router.callback_query(F.data == "reminder_enable")
async def enable_reminder(callback: CallbackQuery, state: FSMContext):
    """Включение напоминания"""
    await state.set_state(TaskStates.waiting_for_reminder_time)
    await callback.message.edit_text(
        "⏰ Введите время <b>напоминания</b> в формате:\n"
        "ДД.ММ.ГГГГ ЧЧ:ММ\n\n"
        "Или нажмите 'Отмена' чтобы вернуться:",
        reply_markup=get_cancel_keyboard(),
        parse_mode="HTML"
    )
    await callback.answer()


@router.callback_query(F.data == "reminder_disable")
async def disable_reminder(callback: CallbackQuery, state: FSMContext):
    """Выключение напоминания"""
    await state.update_data(reminder_enabled=False, reminder_time=None)
    await finalize_task_creation(callback.message, state)
    await callback.answer()


@router.message(TaskStates.waiting_for_reminder_time)
async def process_reminder_time(message: Message, state: FSMContext):
    """Обработка времени напоминания"""
    try:
        reminder_time = datetime.strptime(message.text, "%d.%m.%Y %H:%M")
        reminder_time = pytz.timezone(TIMEZONE).localize(reminder_time)
        await state.update_data(reminder_enabled=True, reminder_time=reminder_time.isoformat())
        await finalize_task_creation(message, state)
    except ValueError:
        await message.answer(
            "❌ Неверный формат времени. Попробуйте еще раз:\n"
            "Формат: ДД.ММ.ГГГГ ЧЧ:ММ"
        )


async def finalize_task_creation(message: Message, state: FSMContext):
    """Завершение создания задачи"""
    data = await state.get_data()
    user_id = message.from_user.id
    
    # Создание задачи
    task = await TaskRepository.create(Task(
        user_id=user_id,
        title=data['title'],
        description=data.get('description', ''),
        priority=data.get('priority', 'medium'),
        due_date=datetime.fromisoformat(data['due_date']) if data.get('due_date') else None,
        reminder_enabled=data.get('reminder_enabled', False),
        reminder_time=datetime.fromisoformat(data['reminder_time']) if data.get('reminder_time') else None,
    ))
    
    # Синхронизация с Google Calendar
    if task.due_date:
        event_id = await google_calendar.create_event(
            title=task.title,
            description=task.description,
            start_time=task.due_date,
            end_time=task.due_date + timedelta(hours=1) if task.due_date else None
        )
        if event_id:
            await TaskRepository.set_google_event_id(task.id, user_id, event_id)
    
    await state.clear()
    
    await message.answer(
        f"✅ <b>Задача создана!</b>\n\n"
        f"📌 Название: {task.title}\n"
        f"🎯 Приоритет: {get_priority_emoji(task.priority)} {task.priority}\n"
        f"📅 Дедлайн: {format_datetime(task.due_date)}\n"
        f"🔔 Напоминание: {'✅' if task.reminder_enabled else '❌'}",
        reply_markup=get_main_menu(),
        parse_mode="HTML"
    )


# ==================== СПИСОК ЗАДАЧ ====================

@router.callback_query(F.data.startswith("tasks_"))
async def show_tasks(callback: CallbackQuery):
    """Показ списка задач"""
    filter_type = callback.data.split("_")[1]
    user_id = callback.from_user.id
    
    if filter_type == "all":
        tasks = await TaskRepository.get_all(user_id)
        title = "📋 Все задачи"
    elif filter_type == "pending":
        tasks = await TaskRepository.get_all(user_id, status='pending')
        title = "⏳ Задачи в ожидании"
    elif filter_type == "completed":
        tasks = await TaskRepository.get_all(user_id, status='completed')
        title = "✅ Завершенные задачи"
    elif filter_type == "overdue":
        tasks = await TaskRepository.get_overdue(user_id)
        title = "🔥 Просроченные задачи"
    else:
        return
    
    if not tasks:
        text = f"{title}\n\nЗадач не найдено."
    else:
        text = f"{title}\n\n"
        for i, task in enumerate(tasks[:10], 1):
            status_emoji = get_status_emoji(task.status)
            priority_emoji = get_priority_emoji(task.priority)
            text += f"{i}. {status_emoji} <b>{task.title}</b>\n"
            text += f"   {priority_emoji} Приоритет: {task.priority}\n"
            text += f"   📅 Дедлайн: {format_datetime(task.due_date)}\n\n"
        
        if len(tasks) > 10:
            text += f"... и еще {len(tasks) - 10} задач\n"
    
    await callback.message.edit_text(
        text,
        reply_markup=get_task_list_keyboard() if len(tasks) > 0 else get_main_menu(),
        parse_mode="HTML"
    )
    await callback.answer()


# ==================== ДЕЙСТВИЯ С ЗАДАЧАМИ ====================

@router.callback_query(F.data.startswith("task_complete_"))
async def complete_task(callback: CallbackQuery):
    """Завершение задачи"""
    task_id = int(callback.data.split("_")[-1])
    user_id = callback.from_user.id
    
    task = await TaskRepository.get_by_id(task_id, user_id)
    if task:
        task.status = 'completed'
        await TaskRepository.update(task)
        
        await callback.message.edit_text(
            f"✅ <b>Задача завершена!</b>\n\n{task.title}",
            reply_markup=get_main_menu(),
            parse_mode="HTML"
        )
    
    await callback.answer()


@router.callback_query(F.data.startswith("task_delete_"))
async def delete_task(callback: CallbackQuery):
    """Удаление задачи"""
    task_id = int(callback.data.split("_")[-1])
    user_id = callback.from_user.id
    
    task = await TaskRepository.get_by_id(task_id, user_id)
    if task:
        # Удаление события из Google Calendar
        if task.google_event_id:
            await google_calendar.delete_event(task.google_event_id)
        
        await TaskRepository.delete(task_id, user_id)
        
        await callback.message.edit_text(
            f"🗑️ <b>Задача удалена!</b>\n\n{task.title}",
            reply_markup=get_main_menu(),
            parse_mode="HTML"
        )
    
    await callback.answer()


# ==================== ВСПОМОГАТЕЛЬНЫЕ ФУНКЦИИ ====================

def get_priority_emoji(priority: str) -> str:
    """Получение эмодзи приоритета"""
    emojis = {
        'low': '🟢',
        'medium': '🟡',
        'high': '🔴'
    }
    return emojis.get(priority, '🟡')


def get_status_emoji(status: str) -> str:
    """Получение эмодзи статуса"""
    emojis = {
        'pending': '⏳',
        'in_progress': '🔄',
        'completed': '✅',
        'cancelled': '❌'
    }
    return emojis.get(status, '⏳')


def format_datetime(dt: datetime) -> str:
    """Форматирование даты и времени"""
    if not dt:
        return "Не указано"
    return dt.strftime("%d.%m.%Y %H:%M")
