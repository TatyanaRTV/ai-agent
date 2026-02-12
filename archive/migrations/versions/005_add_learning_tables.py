"""
005_add_learning_tables.py - добавление таблиц для системы обучения
"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

revision = '005_add_learning_tables'
down_revision = '004_add_vector_storage'
branch_labels = None
depends_on = None

def upgrade():
    """Применение миграции"""
    
    # Таблица учебных данных
    op.create_table('training_data',
        sa.Column('id', sa.String(length=36), nullable=False),
        sa.Column('data_type', sa.String(length=50), nullable=False),
        sa.Column('content', sa.Text(), nullable=False),
        sa.Column('source', sa.String(length=255), nullable=True),
        sa.Column('labels', sa.JSON(), nullable=True),
        sa.Column('metadata', sa.JSON(), nullable=True),
        sa.Column('quality_score', sa.Float(), nullable=True, server_default='1.0'),
        sa.Column('usage_count', sa.Integer(), nullable=True, server_default='0'),
        sa.Column('created_at', sa.DateTime(), nullable=True, server_default=sa.text('CURRENT_TIMESTAMP')),
        sa.Column('updated_at', sa.DateTime(), nullable=True, server_default=sa.text('CURRENT_TIMESTAMP')),
        sa.PrimaryKeyConstraint('id')
    )
    
    # Таблица обучающих сессий
    op.create_table('training_sessions',
        sa.Column('id', sa.String(length=36), nullable=False),
        sa.Column('model_name', sa.String(length=100), nullable=False),
        sa.Column('session_type', sa.String(length=50), nullable=False),
        sa.Column('status', sa.String(length=20), nullable=True, server_default='pending'),
        sa.Column('parameters', sa.JSON(), nullable=True),
        sa.Column('dataset_ids', postgresql.ARRAY(sa.String(length=36)), nullable=True),
        sa.Column('metrics', sa.JSON(), nullable=True),
        sa.Column('start_time', sa.DateTime(), nullable=True),
        sa.Column('end_time', sa.DateTime(), nullable=True),
        sa.Column('duration_seconds', sa.Integer(), nullable=True),
        sa.Column('error_message', sa.Text(), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=True, server_default=sa.text('CURRENT_TIMESTAMP')),
        sa.PrimaryKeyConstraint('id')
    )
    
    # Таблица результатов обучения
    op.create_table('training_results',
        sa.Column('id', sa.String(length=36), nullable=False),
        sa.Column('session_id', sa.String(length=36), nullable=False),
        sa.Column('epoch', sa.Integer(), nullable=False),
        sa.Column('train_loss', sa.Float(), nullable=True),
        sa.Column('val_loss', sa.Float(), nullable=True),
        sa.Column('train_accuracy', sa.Float(), nullable=True),
        sa.Column('val_accuracy', sa.Float(), nullable=True),
        sa.Column('learning_rate', sa.Float(), nullable=True),
        sa.Column('metrics', sa.JSON(), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=True, server_default=sa.text('CURRENT_TIMESTAMP')),
        sa.ForeignKeyConstraint(['session_id'], ['training_sessions.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('session_id', 'epoch', name='uq_training_epoch')
    )
    
    # Таблица чекпоинтов моделей
    op.create_table('model_checkpoints',
        sa.Column('id', sa.String(length=36), nullable=False),
        sa.Column('model_name', sa.String(length=100), nullable=False),
        sa.Column('checkpoint_name', sa.String(length=255), nullable=False),
        sa.Column('session_id', sa.String(length=36), nullable=True),
        sa.Column('epoch', sa.Integer(), nullable=True),
        sa.Column('file_path', sa.String(length=500), nullable=False),
        sa.Column('file_size_bytes', sa.BigInteger(), nullable=True),
        sa.Column('metrics', sa.JSON(), nullable=True),
        sa.Column('is_best', sa.Boolean(), nullable=True, server_default='false'),
        sa.Column('created_at', sa.DateTime(), nullable=True, server_default=sa.text('CURRENT_TIMESTAMP')),
        sa.ForeignKeyConstraint(['session_id'], ['training_sessions.id'], ondelete='SET NULL'),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('model_name', 'checkpoint_name', name='uq_model_checkpoint')
    )
    
    # Таблица метрик производительности
    op.create_table('performance_metrics',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('metric_name', sa.String(length=100), nullable=False),
        sa.Column('metric_value', sa.Float(), nullable=False),
        sa.Column('metric_type', sa.String(length=50), nullable=True),
        sa.Column('agent_id', sa.String(length=36), nullable=True),
        sa.Column('user_id', sa.String(length=36), nullable=True),
        sa.Column('context', sa.JSON(), nullable=True),
        sa.Column('recorded_at', sa.DateTime(), nullable=True, server_default=sa.text('CURRENT_TIMESTAMP')),
        sa.ForeignKeyConstraint(['agent_id'], ['agents.id'], ondelete='SET NULL'),
        sa.ForeignKeyConstraint(['user_id'], ['users.id'], ondelete='SET NULL'),
        sa.PrimaryKeyConstraint('id')
    )
    
    # Индексы
    op.create_index('ix_training_data_data_type', 'training_data', ['data_type'])
    op.create_index('ix_training_data_quality', 'training_data', ['quality_score'])
    op.create_index('ix_training_sessions_model', 'training_sessions', ['model_name'])
    op.create_index('ix_training_sessions_status', 'training_sessions', ['status'])
    op.create_index('ix_training_results_session', 'training_results', ['session_id'])
    op.create_index('ix_model_checkpoints_model', 'model_checkpoints', ['model_name'])
    op.create_index('ix_performance_metrics_name', 'performance_metrics', ['metric_name'])
    op.create_index('ix_performance_metrics_recorded', 'performance_metrics', ['recorded_at'])

def downgrade():
    """Откат миграции"""
    op.drop_table('performance_metrics')
    op.drop_table('model_checkpoints')
    op.drop_table('training_results')
    op.drop_table('training_sessions')
    op.drop_table('training_data')