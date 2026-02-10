"""
001_initial_migration.py - начальная миграция базы данных
Создает базовую структуру таблиц для ИИ-агента Елена
"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic
revision = '001_initial_migration'
down_revision = None
branch_labels = None
depends_on = None

def upgrade():
    """Применение миграции"""
    
    # Таблица конфигураций
    op.create_table('configurations',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('key', sa.String(length=255), nullable=False),
        sa.Column('value', sa.Text(), nullable=True),
        sa.Column('value_type', sa.String(length=50), nullable=True),
        sa.Column('description', sa.Text(), nullable=True),
        sa.Column('category', sa.String(length=100), nullable=True),
        sa.Column('is_encrypted', sa.Boolean(), nullable=True, server_default='false'),
        sa.Column('created_at', sa.DateTime(), nullable=True, server_default=sa.text('CURRENT_TIMESTAMP')),
        sa.Column('updated_at', sa.DateTime(), nullable=True, server_default=sa.text('CURRENT_TIMESTAMP')),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('key')
    )
    
    # Таблица системных логов
    op.create_table('system_logs',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('timestamp', sa.DateTime(), nullable=True, server_default=sa.text('CURRENT_TIMESTAMP')),
        sa.Column('level', sa.String(length=20), nullable=False),
        sa.Column('module', sa.String(length=100), nullable=True),
        sa.Column('message', sa.Text(), nullable=False),
        sa.Column('details', sa.JSON(), nullable=True),
        sa.Column('user_id', sa.String(length=100), nullable=True),
        sa.Column('session_id', sa.String(length=100), nullable=True),
        sa.Column('execution_time_ms', sa.Integer(), nullable=True),
        sa.PrimaryKeyConstraint('id')
    )
    
    # Индексы для логов
    op.create_index('ix_system_logs_timestamp', 'system_logs', ['timestamp'])
    op.create_index('ix_system_logs_level', 'system_logs', ['level'])
    op.create_index('ix_system_logs_module', 'system_logs', ['module'])
    
    # Таблица агентов (для управления разными инстансами)
    op.create_table('agents',
        sa.Column('id', sa.String(length=36), nullable=False),
        sa.Column('name', sa.String(length=255), nullable=False),
        sa.Column('version', sa.String(length=50), nullable=True),
        sa.Column('type', sa.String(length=50), nullable=True),
        sa.Column('status', sa.String(length=20), nullable=True, server_default='active'),
        sa.Column('configuration', sa.JSON(), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=True, server_default=sa.text('CURRENT_TIMESTAMP')),
        sa.Column('updated_at', sa.DateTime(), nullable=True, server_default=sa.text('CURRENT_TIMESTAMP')),
        sa.Column('last_active', sa.DateTime(), nullable=True),
        sa.PrimaryKeyConstraint('id')
    )
    
    # Вставляем базового агента Елена
    op.execute("""
        INSERT INTO agents (id, name, version, type, status, configuration) 
        VALUES (
            'elena_main',
            'Елена',
            '1.0.0',
            'main',
            'active',
            '{"language": "ru", "voice_gender": "female", "personality": "friendly"}'
        )
    """)

def downgrade():
    """Откат миграции"""
    op.drop_table('agents')
    op.drop_table('system_logs')
    op.drop_table('configurations')