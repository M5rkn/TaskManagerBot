from aiogram.fsm.state import State, StatesGroup


class TaskStates(StatesGroup):
    """Состояния для создания/редактирования задачи"""
    waiting_for_title = State()
    waiting_for_description = State()
    waiting_for_priority = State()
    waiting_for_due_date = State()
    waiting_for_reminder = State()
    waiting_for_reminder_time = State()


class EditTaskStates(StatesGroup):
    """Состояния для редактирования задачи"""
    waiting_for_new_title = State()
    waiting_for_new_description = State()
    waiting_for_new_priority = State()
    waiting_for_new_due_date = State()
