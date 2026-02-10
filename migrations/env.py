"""
env.py - конфигурация окружения Alembic
"""
import os
import sys
from logging.config import fileConfig
from alembic import context
from sqlalchemy import engine_from_config, pool

# Добавляем путь к проекту
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))

# Импортируем модели SQLAlchemy
from src.core.database import Base
from src.core.database.models import *
from src.core.memory.models import *
from src.core.learning.models import *
from src.interfaces.models import *

# Конфигурация Alembic
config = context.config

# Настройка логгера
if config.config_file_name is not None:
    fileConfig(config.config_file_name)

# Метаданные для миграций
target_metadata = Base.metadata

# Получение URL БД из конфигурации или переменных окружения
def get_database_url():
    """Получение URL базы данных"""
    # Пробуем получить из alembic.ini
    alembic_url = config.get_main_option("sqlalchemy.url")
    
    if alembic_url and alembic_url != "driver://user:pass@localhost/dbname":
        return alembic_url
    
    # Пробуем получить из переменных окружения
    env_url = os.environ.get("DATABASE_URL")
    if env_url:
        return env_url
    
    # Пробуем получить из конфига проекта
    try:
        from src.config import settings
        return settings.DATABASE_URL
    except ImportError:
        pass
    
    # Используем SQLite по умолчанию
    project_root = os.path.dirname(os.path.dirname(__file__))
    return f"sqlite:///{project_root}/elena.db"

def run_migrations_offline():
    """Запуск миграций в оффлайн режиме"""
    url = get_database_url()
    context.configure(
        url=url,
        target_metadata=target_metadata,
        literal_binds=True,
        dialect_opts={"paramstyle": "named"},
    )

    with context.begin_transaction():
        context.run_migrations()

def run_migrations_online():
    """Запуск миграций в онлайн режиме"""
    configuration = config.get_section(config.config_ini_section)
    configuration["sqlalchemy.url"] = get_database_url()
    
    connectable = engine_from_config(
        configuration,
        prefix="sqlalchemy.",
        poolclass=pool.NullPool,
    )

    with connectable.connect() as connection:
        context.configure(
            connection=connection,
            target_metadata=target_metadata,
            compare_type=True,
            compare_server_default=True,
        )

        with context.begin_transaction():
            context.run_migrations()

if context.is_offline_mode():
    run_migrations_offline()
else:
    run_migrations_online()