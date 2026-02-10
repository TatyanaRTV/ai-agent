#!/bin/bash
# create_migrations_structure.sh

MIGRATIONS_DIR="/mnt/ai_data/ai-agent/migrations"

echo "Создание структуры миграций базы данных..."

# Создаем основную структуру
mkdir -p "$MIGRATIONS_DIR/versions"

# Создаем основные файлы
create_file() {
    local file="$1"
    local content="$2"
    
    echo "$content" > "$MIGRATIONS_DIR/$file"
    echo "Создан файл: $file"
}

# __init__.py для versions
create_file "versions/__init__.py" "# Пакет миграций базы данных"

# Создаем файлы миграций
migrations=(
    "001_initial_migration.py"
    "002_add_users_table.py"
    "003_add_memory_tables.py"
    "004_add_vector_storage.py"
    "005_add_learning_tables.py"
    "006_add_interactions.py"
    "007_add_media_tables.py"
    "008_add_obsidian_sync.py"
    "009_add_performance_indexes.py"
    "010_add_audit_logging.py"
    "011_update_vector_schema.py"
    "012_add_self_improvement.py"
)

# Создаем заглушки для миграций
for migration in "${migrations[@]}"; do
    create_file "versions/$migration" "$(cat << 'EOF'
"""
$(basename "$migration" .py) - описание миграции
"""
from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic
revision = '$(basename "$migration" .py)'
down_revision = None
branch_labels = None
depends_on = None

def upgrade():
    """Применение миграции"""
    # Реализация будет добавлена позже
    pass

def downgrade():
    """Откат миграции"""
    # Реализация будет добавлена позже
    pass
EOF
)"
done

# Alembic.ini
create_file "alembic.ini" "$(cat << 'EOF'
[alembic]
script_location = migrations
sqlalchemy.url = sqlite:///./elena.db
file_template = %%(year)d_%%(month).2d_%%(day).2d_%%(rev)s_%%(slug)s

[post_write_hooks]
# black = black

[loggers]
keys = root,sqlalchemy,alembic

[handlers]
keys = console

[formatters]
keys = generic

[logger_root]
level = WARN
handlers = console

[logger_sqlalchemy]
level = WARN
handlers =
qualname = sqlalchemy.engine

[logger_alembic]
level = INFO
handlers =
qualname = alembic

[handler_console]
class = StreamHandler
args = (sys.stderr,)
level = NOTSET
formatter = generic

[formatter_generic]
format = %(levelname)-5.5s [%(name)s] %(message)s
datefmt = %H:%M:%S
EOF
)"

# env.py
create_file "env.py" "$(cat << 'EOF'
import os
import sys
from logging.config import fileConfig
from alembic import context

sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))

from src.core.database import Base

config = context.config
fileConfig(config.config_file_name)
target_metadata = Base.metadata

def run_migrations_offline():
    url = config.get_main_option("sqlalchemy.url")
    context.configure(url=url, target_metadata=target_metadata, literal_binds=True)
    with context.begin_transaction():
        context.run_migrations()

def run_migrations_online():
    from sqlalchemy import engine_from_config
    from sqlalchemy import pool
    
    connectable = engine_from_config(
        config.get_section(config.config_ini_section),
        prefix="sqlalchemy.",
        poolclass=pool.NullPool,
    )

    with connectable.connect() as connection:
        context.configure(connection=connection, target_metadata=target_metadata)
        with context.begin_transaction():
            context.run_migrations()

if context.is_offline_mode():
    run_migrations_offline()
else:
    run_migrations_online()
EOF
)"

# script.py.mako (шаблон для создания миграций)
create_file "script.py.mako" "$(cat << 'EOF'
"""${message}

Revision ID: ${up_revision}
Revises: ${down_revision | comma,n}
Create Date: ${create_date}

"""
from alembic import op
import sqlalchemy as sa
${imports if imports else ""}

# revision identifiers, used by Alembic
revision = ${repr(up_revision)}
down_revision = ${repr(down_revision)}
branch_labels = ${repr(branch_labels)}
depends_on = ${repr(depends_on)}


def upgrade():
    ${upgrades if upgrades else "pass"}


def downgrade():
    ${downgrades if downgrades else "pass"}
EOF
)"

# README.md для миграций
create_file "README.md" "$(cat << 'EOF'
# 📊 Миграции базы данных

Эта папка содержит миграции базы данных для ИИ-агента "Елена" с использованием Alembic.

## Структура

- `alembic.ini` - Конфигурация Alembic
- `env.py` - Окружение миграций
- `script.py.mako` - Шаблон для новых миграций
- `versions/` - Файлы миграций

## Использование

### Инициализация Alembic (если еще не сделано)
```bash
cd /mnt/ai_data/ai-agent
alembic init migrations