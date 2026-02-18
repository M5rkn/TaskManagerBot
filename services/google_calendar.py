import asyncio
from datetime import datetime, timedelta
from typing import Optional, List
from google.oauth2.credentials import Credentials
from google.oauth2 import service_account
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError
from config.settings import GOOGLE_CREDENTIALS_FILE, GOOGLE_CALENDAR_ID, TIMEZONE


class GoogleCalendarService:
    """Сервис для интеграции с Google Calendar API"""
    
    def __init__(self):
        self.service = None
        self.calendar_id = GOOGLE_CALENDAR_ID
        self._initialize_service()
    
    def _initialize_service(self):
        """Инициализация сервиса Google Calendar"""
        try:
            # Попытка загрузить учетные данные сервисного аккаунта
            credentials = service_account.Credentials.from_service_account_file(
                GOOGLE_CREDENTIALS_FILE,
                scopes=['https://www.googleapis.com/auth/calendar']
            )
            self.service = build('calendar', 'v3', credentials=credentials)
        except FileNotFoundError:
            print(f"Файл {GOOGLE_CREDENTIALS_FILE} не найден. Google Calendar интеграция будет недоступна.")
        except Exception as e:
            print(f"Ошибка инициализации Google Calendar: {e}")
    
    async def create_event(
        self,
        title: str,
        description: str = "",
        start_time: datetime = None,
        end_time: datetime = None,
        reminder_minutes: int = 15
    ) -> Optional[str]:
        """
        Создание события в Google Calendar
        
        Returns:
            ID созданного события или None в случае ошибки
        """
        if not self.service:
            return None
        
        try:
            # Время по умолчанию
            if start_time is None:
                start_time = datetime.now()
            if end_time is None:
                end_time = start_time + timedelta(hours=1)
            
            event = {
                'summary': title,
                'description': description,
                'start': {
                    'dateTime': start_time.isoformat(),
                    'timeZone': TIMEZONE,
                },
                'end': {
                    'dateTime': end_time.isoformat(),
                    'timeZone': TIMEZONE,
                },
                'reminders': {
                    'useDefault': False,
                    'overrides': [
                        {'method': 'popup', 'minutes': reminder_minutes},
                        {'method': 'email', 'minutes': reminder_minutes * 2},
                    ],
                },
            }
            
            # Выполнение запроса в отдельном потоке (блокирующая операция)
            loop = asyncio.get_event_loop()
            created_event = await loop.run_in_executor(
                None,
                lambda: self.service.events().insert(
                    calendarId=self.calendar_id,
                    body=event
                ).execute()
            )
            
            return created_event.get('id')
        
        except HttpError as error:
            print(f"Ошибка создания события: {error}")
            return None
        except Exception as e:
            print(f"Неизвестная ошибка создания события: {e}")
            return None
    
    async def update_event(
        self,
        event_id: str,
        title: str = None,
        description: str = None,
        start_time: datetime = None,
        end_time: datetime = None
    ) -> bool:
        """Обновление события в Google Calendar"""
        if not self.service:
            return False
        
        try:
            # Получение текущего события
            loop = asyncio.get_event_loop()
            event = await loop.run_in_executor(
                None,
                lambda: self.service.events().get(
                    calendarId=self.calendar_id,
                    eventId=event_id
                ).execute()
            )
            
            # Обновление полей
            if title:
                event['summary'] = title
            if description:
                event['description'] = description
            if start_time:
                event['start']['dateTime'] = start_time.isoformat()
            if end_time:
                event['end']['dateTime'] = end_time.isoformat()
            
            # Сохранение изменений
            await loop.run_in_executor(
                None,
                lambda: self.service.events().update(
                    calendarId=self.calendar_id,
                    eventId=event_id,
                    body=event
                ).execute()
            )
            
            return True
        
        except HttpError as error:
            print(f"Ошибка обновления события: {error}")
            return False
        except Exception as e:
            print(f"Неизвестная ошибка обновления события: {e}")
            return False
    
    async def delete_event(self, event_id: str) -> bool:
        """Удаление события из Google Calendar"""
        if not self.service:
            return False
        
        try:
            loop = asyncio.get_event_loop()
            await loop.run_in_executor(
                None,
                lambda: self.service.events().delete(
                    calendarId=self.calendar_id,
                    eventId=event_id
                ).execute()
            )
            return True
        
        except HttpError as error:
            print(f"Ошибка удаления события: {error}")
            return False
        except Exception as e:
            print(f"Неизвестная ошибка удаления события: {e}")
            return False
    
    async def get_events(
        self,
        start_date: datetime = None,
        end_date: datetime = None,
        max_results: int = 10
    ) -> List[dict]:
        """Получение списка событий из календаря"""
        if not self.service:
            return []
        
        try:
            if start_date is None:
                start_date = datetime.now()
            if end_date is None:
                end_date = start_date + timedelta(days=7)
            
            loop = asyncio.get_event_loop()
            events_result = await loop.run_in_executor(
                None,
                lambda: self.service.events().list(
                    calendarId=self.calendar_id,
                    timeMin=start_date.isoformat() + 'Z',
                    timeMax=end_date.isoformat() + 'Z',
                    maxResults=max_results,
                    singleEvents=True,
                    orderBy='startTime'
                ).execute()
            )
            
            events = events_result.get('items', [])
            
            return [
                {
                    'id': event.get('id'),
                    'summary': event.get('summary'),
                    'description': event.get('description'),
                    'start': event.get('start'),
                    'end': event.get('end'),
                }
                for event in events
            ]
        
        except HttpError as error:
            print(f"Ошибка получения событий: {error}")
            return []
        except Exception as e:
            print(f"Неизвестная ошибка получения событий: {e}")
            return []


# Глобальный экземпляр сервиса
google_calendar = GoogleCalendarService()
