from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
from aiogram.utils.keyboard import InlineKeyboardBuilder


def get_main_menu() -> InlineKeyboardMarkup:
    """Главное меню бота"""
    builder = InlineKeyboardBuilder()
    builder.button(text="📝 Мои задачи", callback_data="tasks_list")
    builder.button(text="➕ Добавить задачу", callback_data="task_create")
    builder.button(text="📅 Календарь", callback_data="calendar_view")
    builder.button(text="⏰ Напоминания", callback_data="reminders_view")
    builder.button(text="📊 Статистика", callback_data="stats_view")
    builder.button(text="❓ Помощь", callback_data="help")
    builder.adjust(2, 2, 2)
    return builder.as_markup()


def get_task_list_keyboard() -> InlineKeyboardMarkup:
    """Клавиатура списка задач"""
    builder = InlineKeyboardBuilder()
    builder.button(text="🔄 Все задачи", callback_data="tasks_all")
    builder.button(text="⏳ В ожидании", callback_data="tasks_pending")
    builder.button(text="✅ Завершенные", callback_data="tasks_completed")
    builder.button(text="🔥 Просроченные", callback_data="tasks_overdue")
    builder.button(text="🔙 Назад", callback_data="main_menu")
    builder.adjust(2, 2, 1)
    return builder.as_markup()


def get_task_actions_keyboard(task_id: int) -> InlineKeyboardMarkup:
    """Клавиатура действий с задачей"""
    builder = InlineKeyboardBuilder()
    builder.button(text="✅ Завершить", callback_data=f"task_complete_{task_id}")
    builder.button(text="✏️ Редактировать", callback_data=f"task_edit_{task_id}")
    builder.button(text="🗑️ Удалить", callback_data=f"task_delete_{task_id}")
    builder.button(text="🔙 Назад к списку", callback_data="tasks_list")
    builder.adjust(2, 2)
    return builder.as_markup()


def get_priority_keyboard() -> InlineKeyboardMarkup:
    """Выбор приоритета задачи"""
    builder = InlineKeyboardBuilder()
    builder.button(text="🟢 Низкий", callback_data="priority_low")
    builder.button(text="🟡 Средний", callback_data="priority_medium")
    builder.button(text="🔴 Высокий", callback_data="priority_high")
    builder.button(text="❌ Отмена", callback_data="task_cancel")
    builder.adjust(2, 2)
    return builder.as_markup()


def get_reminder_keyboard() -> InlineKeyboardMarkup:
    """Клавиатура настройки напоминаний"""
    builder = InlineKeyboardBuilder()
    builder.button(text="🔔 Включить", callback_data="reminder_enable")
    builder.button(text="🔕 Выключить", callback_data="reminder_disable")
    builder.button(text="❌ Отмена", callback_data="task_cancel")
    builder.adjust(2, 1)
    return builder.as_markup()


def get_yes_no_keyboard() -> InlineKeyboardMarkup:
    """Клавиатура Да/Нет"""
    builder = InlineKeyboardBuilder()
    builder.button(text="✅ Да", callback_data="yes")
    builder.button(text="❌ Нет", callback_data="no")
    builder.adjust(2)
    return builder.as_markup()


def get_cancel_keyboard() -> InlineKeyboardMarkup:
    """Клавиатура отмены"""
    builder = InlineKeyboardBuilder()
    builder.button(text="❌ Отмена", callback_data="cancel")
    return builder.as_markup()
