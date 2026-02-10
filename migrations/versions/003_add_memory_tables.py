"""
003_add_memory_tables.py - добавление таблиц для системы памяти Елены
"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

revision = '003_add_memory_tables'
down_revision = '002_add_users_table'
branch_labels = None
depends_on = None

def upgrade():
    """Применение миграции"""
    
    # Таблица категорий памяти
    op.create_table('memory_categories',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('name', sa.String(length=100), nullable=False),
        sa.Column('description', sa.Text(), nullable=True),
        sa.Column('priority', sa.Integer(), nullable=True, server_default='1'),
        sa.Column('retention_days', sa.Integer(), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=True, server_default=sa.text('CURRENT_TIMESTAMP')),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('name')
    )
    
    # Вставляем базовые категории
    op.execute("""
        INSERT INTO memory_categories (name, description, priority, retention_days) VALUES
        ('short_term', 'Краткосрочная память', 1, 1),
        ('long_term', 'Долгосрочная память', 2, 365),
        ('procedural', 'Процедурная память (навыки)', 3, NULL),
        ('episodic', 'Эпизодическая память (события)', 4, 30),
        ('semantic', 'Семантическая память (знания)', 5, NULL),
        ('user_specific', 'Пользовательская информация', 6, 90)
    """)
    
    # Таблица памяти
    op.create_table('memories',
        sa.Column('id', sa.String(length=36), nullable=False),
        sa.Column('category_id', sa.Integer(), nullable=True),
        sa.Column('user_id', sa.String(length=36), nullable=True),
        sa.Column('agent_id', sa.String(length=36), nullable=True),
        sa.Column('memory_type', sa.String(length=50), nullable=False),
        sa.Column('content', sa.Text(), nullable=False),
        sa.Column('summary', sa.Text(), nullable=True),
        sa.Column('embedding_vector', postgresql.ARRAY(sa.Float()), nullable=True),
        sa.Column('metadata', sa.JSON(), nullable=True),
        sa.Column('importance_score', sa.Float(), nullable=True, server_default='0.5'),
        sa.Column('access_count', sa.Integer(), nullable=True, server_default='0'),
        sa.Column('last_accessed', sa.DateTime(), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=True, server_default=sa.text('CURRENT_TIMESTAMP')),
        sa.Column('updated_at', sa.DateTime(), nullable=True, server_default=sa.text('CURRENT_TIMESTAMP')),
        sa.Column('expires_at', sa.DateTime(), nullable=True),
        sa.ForeignKeyConstraint(['category_id'], ['memory_categories.id'], ondelete='SET NULL'),
        sa.ForeignKeyConstraint(['user_id'], ['users.id'], ondelete='SET NULL'),
        sa.ForeignKeyConstraint(['agent_id'], ['agents.id'], ondelete='SET NULL'),
        sa.PrimaryKeyConstraint('id')
    )
    
    # Таблица контекста (для поддержания контекста диалога)
    op.create_table('contexts',
        sa.Column('id', sa.String(length=36), nullable=False),
        sa.Column('session_id', sa.String(length=36), nullable=True),
        sa.Column('user_id', sa.String(length=36), nullable=True),
        sa.Column('context_type', sa.String(length=50), nullable=True),
        sa.Column('current_topic', sa.String(length=255), nullable=True),
        sa.Column('context_data', sa.JSON(), nullable=True),
        sa.Column('memory_references', postgresql.ARRAY(sa.String(length=36)), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=True, server_default=sa.text('CURRENT_TIMESTAMP')),
        sa.Column('updated_at', sa.DateTime(), nullable=True, server_default=sa.text('CURRENT_TIMESTAMP')),
        sa.Column('expires_at', sa.DateTime(), nullable=True),
        sa.ForeignKeyConstraint(['session_id'], ['sessions.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['user_id'], ['users.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id')
    )
    
    # Таблица связей между воспоминаниями
    op.create_table('memory_links',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('source_memory_id', sa.String(length=36), nullable=False),
        sa.Column('target_memory_id', sa.String(length=36), nullable=False),
        sa.Column('link_type', sa.String(length=50), nullable=True),
        sa.Column('strength', sa.Float(), nullable=True, server_default='1.0'),
        sa.Column('created_at', sa.DateTime(), nullable=True, server_default=sa.text('CURRENT_TIMESTAMP')),
        sa.ForeignKeyConstraint(['source_memory_id'], ['memories.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['target_memory_id'], ['memories.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('source_memory_id', 'target_memory_id', 'link_type', name='uq_memory_link')
    )
    
    # Индексы
    op.create_index('ix_memories_category_id', 'memories', ['category_id'])
    op.create_index('ix_memories_user_id', 'memories', ['user_id'])
    op.create_index('ix_memories_created_at', 'memories', ['created_at'])
    op.create_index('ix_memories_importance_score', 'memories', ['importance_score'])
    op.create_index('ix_contexts_session_id', 'contexts', ['session_id'])
    op.create_index('ix_memory_links_source', 'memory_links', ['source_memory_id'])
    op.create_index('ix_memory_links_target', 'memory_links', ['target_memory_id'])
    
    # Создаем расширение для векторных операций (PostgreSQL)
    # Для других БД будет другая реализация
    op.execute('CREATE EXTENSION IF NOT EXISTS vector')

def downgrade():
    """Откат миграции"""
    op.drop_table('memory_links')
    op.drop_table('contexts')
    op.drop_table('memories')
    op.drop_table('memory_categories')
    op.execute('DROP EXTENSION IF EXISTS vector')