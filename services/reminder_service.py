import asyncio
import json
import redis.asyncio as redis
from datetime import datetime
from typing import Optional, List
from config.settings import REDIS_HOST, REDIS_PORT, REDIS_DB


class ReminderService:
    """Сервис для управления напоминаниями через Redis"""
    
    def __init__(self):
        self.redis: Optional[redis.Redis] = None
        self.host = REDIS_HOST
        self.port = REDIS_PORT
        self.db = REDIS_DB
    
    async def connect(self):
        """Подключение к Redis"""
        try:
            self.redis = redis.Redis(
                host=self.host,
                port=self.port,
                db=self.db,
                decode_responses=True
            )
            await self.redis.ping()
            print(f"✅ Подключено к Redis: {self.host}:{self.port}")
        except Exception as e:
            print(f"❌ Ошибка подключения к Redis: {e}")
            self.redis = None
    
    async def disconnect(self):
        """Отключение от Redis"""
        if self.redis:
            await self.redis.close()
    
    async def add_reminder(self, reminder_id: int, user_id: int, task_id: int, reminder_time: datetime):
        """
        Добавление напоминания в Redis
        
        Сохраняет напоминание в sorted set с timestamp как score
        для возможности эффективного поиска напоминаний по времени
        """
        if not self.redis:
            return
        
        reminder_data = {
            'reminder_id': reminder_id,
            'user_id': user_id,
            'task_id': task_id,
            'reminder_time': reminder_time.isoformat(),
        }
        
        # Добавляем в sorted set с timestamp как score
        timestamp = reminder_time.timestamp()
        await self.redis.zadd(
            'reminders_queue',
            {json.dumps(reminder_data): timestamp}
        )
        
        print(f"🔔 Напоминание #{reminder_id} добавлено в очередь на {reminder_time}")
    
    async def get_due_reminders(self) -> List[dict]:
        """
        Получение напоминаний, которые настало время отправить
        
        Возвращает все напоминания с временем <= текущего времени
        """
        if not self.redis:
            return []
        
        now = datetime.now().timestamp()
        
        # Получаем все напоминания с временем <= сейчас
        reminders = await self.redis.zrangebyscore(
            'reminders_queue',
            '-inf',
            now
        )
        
        return [json.loads(reminder) for reminder in reminders]
    
    async def remove_reminder(self, reminder_id: int):
        """Удаление напоминания из очереди"""
        if not self.redis:
            return
        
        # Находим напоминание по reminder_id
        reminders = await self.redis.zrange('reminders_queue', 0, -1, withscores=True)
        
        for reminder_json, score in reminders:
            reminder_data = json.loads(reminder_json)
            if reminder_data.get('reminder_id') == reminder_id:
                await self.redis.zrem('reminders_queue', reminder_json)
                print(f"🗑️ Напоминание #{reminder_id} удалено из очереди")
                break
    
    async def get_reminders_count(self) -> int:
        """Получение количества напоминаний в очереди"""
        if not self.redis:
            return 0
        
        return await self.redis.zcard('reminders_queue')
    
    async def clear_sent_reminders(self, reminder_ids: List[int]):
        """Очистка отправленных напоминаний из очереди"""
        if not self.redis:
            return
        
        reminders = await self.redis.zrange('reminders_queue', 0, -1, withscores=True)
        
        for reminder_json, score in reminders:
            reminder_data = json.loads(reminder_json)
            if reminder_data.get('reminder_id') in reminder_ids:
                await self.redis.zrem('reminders_queue', reminder_json)


# Глобальный экземпляр сервиса
reminder_service = ReminderService()
