from dataclasses import dataclass
from datetime import datetime
from typing import Optional


@dataclass
class Task:
    """Модель задачи"""
    id: Optional[int] = None
    user_id: Optional[int] = None
    title: str = ""
    description: str = ""
    priority: str = "medium"  # low, medium, high
    status: str = "pending"  # pending, in_progress, completed, cancelled
    due_date: Optional[datetime] = None
    google_event_id: Optional[str] = None
    reminder_enabled: bool = False
    reminder_time: Optional[datetime] = None
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None
    
    def to_dict(self) -> dict:
        """Конвертация задачи в словарь"""
        return {
            'id': self.id,
            'user_id': self.user_id,
            'title': self.title,
            'description': self.description,
            'priority': self.priority,
            'status': self.status,
            'due_date': self.due_date.isoformat() if self.due_date else None,
            'google_event_id': self.google_event_id,
            'reminder_enabled': self.reminder_enabled,
            'reminder_time': self.reminder_time.isoformat() if self.reminder_time else None,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None,
        }
    
    @classmethod
    def from_row(cls, row) -> 'Task':
        """Создание задачи из строки базы данных"""
        return cls(
            id=row['id'],
            user_id=row['user_id'],
            title=row['title'],
            description=row['description'],
            priority=row['priority'],
            status=row['status'],
            due_date=datetime.fromisoformat(row['due_date']) if row['due_date'] else None,
            google_event_id=row['google_event_id'],
            reminder_enabled=bool(row['reminder_enabled']),
            reminder_time=datetime.fromisoformat(row['reminder_time']) if row['reminder_time'] else None,
            created_at=datetime.fromisoformat(row['created_at']) if row['created_at'] else None,
            updated_at=datetime.fromisoformat(row['updated_at']) if row['updated_at'] else None,
        )


@dataclass
class User:
    """Модель пользователя"""
    id: Optional[int] = None
    telegram_id: Optional[int] = None
    username: Optional[str] = None
    first_name: Optional[str] = None
    created_at: Optional[datetime] = None
    
    def to_dict(self) -> dict:
        """Конвертация пользователя в словарь"""
        return {
            'id': self.id,
            'telegram_id': self.telegram_id,
            'username': self.username,
            'first_name': self.first_name,
            'created_at': self.created_at.isoformat() if self.created_at else None,
        }
    
    @classmethod
    def from_row(cls, row) -> 'User':
        """Создание пользователя из строки базы данных"""
        return cls(
            id=row['id'],
            telegram_id=row['telegram_id'],
            username=row['username'],
            first_name=row['first_name'],
            created_at=datetime.fromisoformat(row['created_at']) if row['created_at'] else None,
        )


@dataclass
class Reminder:
    """Модель напоминания"""
    id: Optional[int] = None
    task_id: Optional[int] = None
    user_id: Optional[int] = None
    reminder_time: Optional[datetime] = None
    is_sent: bool = False
    created_at: Optional[datetime] = None
    
    def to_dict(self) -> dict:
        """Конвертация напоминания в словарь"""
        return {
            'id': self.id,
            'task_id': self.task_id,
            'user_id': self.user_id,
            'reminder_time': self.reminder_time.isoformat() if self.reminder_time else None,
            'is_sent': self.is_sent,
            'created_at': self.created_at.isoformat() if self.created_at else None,
        }
    
    @classmethod
    def from_row(cls, row) -> 'Reminder':
        """Создание напоминания из строки базы данных"""
        return cls(
            id=row['id'],
            task_id=row['task_id'],
            user_id=row['user_id'],
            reminder_time=datetime.fromisoformat(row['reminder_time']) if row['reminder_time'] else None,
            is_sent=bool(row['is_sent']),
            created_at=datetime.fromisoformat(row['created_at']) if row['created_at'] else None,
        )
