from datetime import datetime
from typing import Optional, List
from db.database import db
from models.task import Task, User, Reminder


class TaskRepository:
    """Репозиторий для работы с задачами"""
    
    @staticmethod
    async def create(task: Task) -> Task:
        """Создание новой задачи"""
        cursor = await db.execute('''
            INSERT INTO tasks (user_id, title, description, priority, status, due_date, reminder_enabled, reminder_time)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        ''', (
            task.user_id,
            task.title,
            task.description,
            task.priority,
            task.status,
            task.due_date.isoformat() if task.due_date else None,
            task.reminder_enabled,
            task.reminder_time.isoformat() if task.reminder_time else None,
        ))
        
        task.id = cursor.lastrowid
        return task
    
    @staticmethod
    async def get_by_id(task_id: int, user_id: int) -> Optional[Task]:
        """Получение задачи по ID"""
        row = await db.fetchone('''
            SELECT * FROM tasks WHERE id = ? AND user_id = ?
        ''', (task_id, user_id))
        
        return Task.from_row(row) if row else None
    
    @staticmethod
    async def get_all(user_id: int, status: Optional[str] = None) -> List[Task]:
        """Получение всех задач пользователя"""
        if status:
            rows = await db.fetchall('''
                SELECT * FROM tasks WHERE user_id = ? AND status = ?
                ORDER BY due_date ASC, created_at DESC
            ''', (user_id, status))
        else:
            rows = await db.fetchall('''
                SELECT * FROM tasks WHERE user_id = ?
                ORDER BY due_date ASC, created_at DESC
            ''', (user_id,))
        
        return [Task.from_row(row) for row in rows]
    
    @staticmethod
    async def update(task: Task) -> Task:
        """Обновление задачи"""
        await db.execute('''
            UPDATE tasks 
            SET title = ?, description = ?, priority = ?, status = ?, 
                due_date = ?, reminder_enabled = ?, reminder_time = ?, updated_at = ?
            WHERE id = ? AND user_id = ?
        ''', (
            task.title,
            task.description,
            task.priority,
            task.status,
            task.due_date.isoformat() if task.due_date else None,
            task.reminder_enabled,
            task.reminder_time.isoformat() if task.reminder_time else None,
            datetime.now().isoformat(),
            task.id,
            task.user_id,
        ))
        
        task.updated_at = datetime.now()
        return task
    
    @staticmethod
    async def delete(task_id: int, user_id: int) -> bool:
        """Удаление задачи"""
        cursor = await db.execute('''
            DELETE FROM tasks WHERE id = ? AND user_id = ?
        ''', (task_id, user_id))
        
        return cursor.rowcount > 0
    
    @staticmethod
    async def get_overdue(user_id: int) -> List[Task]:
        """Получение просроченных задач"""
        now = datetime.now().isoformat()
        rows = await db.fetchall('''
            SELECT * FROM tasks 
            WHERE user_id = ? AND due_date < ? AND status NOT IN ('completed', 'cancelled')
            ORDER BY due_date ASC
        ''', (user_id, now))
        
        return [Task.from_row(row) for row in rows]
    
    @staticmethod
    async def get_upcoming(user_id: int, days: int = 7) -> List[Task]:
        """Получение задач на ближайшие N дней"""
        from datetime import timedelta
        now = datetime.now()
        future = (now + timedelta(days=days)).isoformat()
        
        rows = await db.fetchall('''
            SELECT * FROM tasks 
            WHERE user_id = ? AND due_date >= ? AND due_date <= ? AND status NOT IN ('completed', 'cancelled')
            ORDER BY due_date ASC
        ''', (user_id, now.isoformat(), future))
        
        return [Task.from_row(row) for row in rows]
    
    @staticmethod
    async def set_google_event_id(task_id: int, user_id: int, event_id: str):
        """Установка ID события Google Calendar"""
        await db.execute('''
            UPDATE tasks SET google_event_id = ?, updated_at = ?
            WHERE id = ? AND user_id = ?
        ''', (event_id, datetime.now().isoformat(), task_id, user_id))


class UserRepository:
    """Репозиторий для работы с пользователями"""
    
    @staticmethod
    async def create_or_update(telegram_id: int, username: str = None, first_name: str = None) -> User:
        """Создание или обновление пользователя"""
        # Проверка существует ли пользователь
        existing = await UserRepository.get_by_telegram_id(telegram_id)
        
        if existing:
            await db.execute('''
                UPDATE users SET username = ?, first_name = ? WHERE telegram_id = ?
            ''', (username, first_name, telegram_id))
            return existing
        
        # Создание нового пользователя
        cursor = await db.execute('''
            INSERT INTO users (telegram_id, username, first_name)
            VALUES (?, ?, ?)
        ''', (telegram_id, username, first_name))
        
        return User(id=cursor.lastrowid, telegram_id=telegram_id, username=username, first_name=first_name)
    
    @staticmethod
    async def get_by_telegram_id(telegram_id: int) -> Optional[User]:
        """Получение пользователя по Telegram ID"""
        row = await db.fetchone('''
            SELECT * FROM users WHERE telegram_id = ?
        ''', (telegram_id,))
        
        return User.from_row(row) if row else None
    
    @staticmethod
    async def get_all() -> List[User]:
        """Получение всех пользователей"""
        rows = await db.fetchall('SELECT * FROM users ORDER BY created_at DESC')
        return [User.from_row(row) for row in rows]


class ReminderRepository:
    """Репозиторий для работы с напоминаниями"""
    
    @staticmethod
    async def create(reminder: Reminder) -> Reminder:
        """Создание напоминания"""
        cursor = await db.execute('''
            INSERT INTO reminders (task_id, user_id, reminder_time)
            VALUES (?, ?, ?)
        ''', (
            reminder.task_id,
            reminder.user_id,
            reminder.reminder_time.isoformat() if reminder.reminder_time else None,
        ))
        
        reminder.id = cursor.lastrowid
        return reminder
    
    @staticmethod
    async def get_pending() -> List[Reminder]:
        """Получение всех ненаправленных напоминаний"""
        rows = await db.fetchall('''
            SELECT * FROM reminders WHERE is_sent = 0 AND reminder_time <= ?
            ORDER BY reminder_time ASC
        ''', (datetime.now().isoformat(),))
        
        return [Reminder.from_row(row) for row in rows]
    
    @staticmethod
    async def mark_as_sent(reminder_id: int):
        """Отметка напоминания как отправленного"""
        await db.execute('''
            UPDATE reminders SET is_sent = 1 WHERE id = ?
        ''', (reminder_id,))
    
    @staticmethod
    async def delete(reminder_id: int):
        """Удаление напоминания"""
        await db.execute('DELETE FROM reminders WHERE id = ?', (reminder_id,))
