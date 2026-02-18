import aiosqlite
from config.settings import DATABASE_PATH


class Database:
    """Класс для управления подключением к SQLite базе данных"""
    
    def __init__(self, db_path: str = DATABASE_PATH):
        self.db_path = db_path
        self.connection: aiosqlite.Connection | None = None
    
    async def connect(self):
        """Установка подключения к базе данных"""
        self.connection = await aiosqlite.connect(self.db_path)
        self.connection.row_factory = aiosqlite.Row
        await self.create_tables()
    
    async def disconnect(self):
        """Закрытие подключения к базе данных"""
        if self.connection:
            await self.connection.close()
    
    async def create_tables(self):
        """Создание таблиц базы данных"""
        await self.connection.execute('''
            CREATE TABLE IF NOT EXISTS users (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                telegram_id INTEGER UNIQUE NOT NULL,
                username TEXT,
                first_name TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        
        await self.connection.execute('''
            CREATE TABLE IF NOT EXISTS tasks (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER NOT NULL,
                title TEXT NOT NULL,
                description TEXT,
                priority TEXT DEFAULT 'medium',
                status TEXT DEFAULT 'pending',
                due_date TIMESTAMP,
                google_event_id TEXT,
                reminder_enabled BOOLEAN DEFAULT 0,
                reminder_time TIMESTAMP,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (user_id) REFERENCES users (telegram_id)
            )
        ''')
        
        await self.connection.execute('''
            CREATE TABLE IF NOT EXISTS reminders (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                task_id INTEGER NOT NULL,
                user_id INTEGER NOT NULL,
                reminder_time TIMESTAMP NOT NULL,
                is_sent BOOLEAN DEFAULT 0,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (task_id) REFERENCES tasks (id),
                FOREIGN KEY (user_id) REFERENCES users (telegram_id)
            )
        ''')
        
        await self.connection.commit()
    
    async def execute(self, query: str, params: tuple = ()):
        """Выполнение SQL запроса"""
        cursor = await self.connection.execute(query, params)
        await self.connection.commit()
        return cursor
    
    async def fetchone(self, query: str, params: tuple = ()):
        """Получение одной строки результата"""
        cursor = await self.connection.execute(query, params)
        return await cursor.fetchone()
    
    async def fetchall(self, query: str, params: tuple = ()):
        """Получение всех строк результата"""
        cursor = await self.connection.execute(query, params)
        return await cursor.fetchall()


# Глобальный экземпляр базы данных
db = Database()
