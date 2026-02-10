
---

## 🔧 **Интеграция с основным кодом**:

```python
# src/core/database/__init__.py
"""
Модуль базы данных для Елены
"""
from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker, scoped_session
import logging

logger = logging.getLogger(__name__)

# Базовый класс для моделей
Base = declarative_base()

class DatabaseManager:
    """Менеджер базы данных"""
    
    def __init__(self, database_url: str = None):
        from src.config import settings
        
        self.database_url = database_url or settings.DATABASE_URL
        
        # Создаем движок
        self.engine = create_engine(
            self.database_url,
            echo=settings.DEBUG,
            pool_pre_ping=True,
            pool_recycle=3600
        )
        
        # Создаем фабрику сессий
        self.SessionLocal = sessionmaker(
            autocommit=False,
            autoflush=False,
            bind=self.engine
        )
        
        # Scoped session для многопоточности
        self.ScopedSession = scoped_session(self.SessionLocal)
        
        logger.info(f"Инициализирован менеджер БД: {self.database_url}")
    
    def get_session(self):
        """Получение сессии БД"""
        return self.ScopedSession()
    
    def close_session(self):
        """Закрытие сессии"""
        self.ScopedSession.remove()
    
    def create_tables(self):
        """Создание всех таблиц (для разработки)"""
        Base.metadata.create_all(bind=self.engine)
        logger.info("Таблицы базы данных созданы")
    
    def drop_tables(self):
        """Удаление всех таблиц (для тестирования)"""
        Base.metadata.drop_all(bind=self.engine)
        logger.info("Таблицы базы данных удалены")
    
    def run_migrations(self):
        """Запуск миграций через Alembic"""
        import subprocess
        import os
        
        project_root = os.path.dirname(os.path.dirname(os.path.dirname(__file__)))
        os.chdir(project_root)
        
        try:
            result = subprocess.run(
                ["alembic", "upgrade", "head"],
                capture_output=True,
                text=True
            )
            
            if result.returncode == 0:
                logger.info("Миграции успешно применены")
                return True
            else:
                logger.error(f"Ошибка миграции: {result.stderr}")
                return False
                
        except Exception as e:
            logger.error(f"Ошибка запуска миграций: {e}")
            return False

# Глобальный экземпляр менеджера БД
db_manager = None

def init_database(database_url: str = None):
    """Инициализация базы данных"""
    global db_manager
    db_manager = DatabaseManager(database_url)
    return db_manager

def get_db():
    """Зависимость для FastAPI"""
    db = db_manager.get_session()
    try:
        yield db
    finally:
        db_manager.close_session()