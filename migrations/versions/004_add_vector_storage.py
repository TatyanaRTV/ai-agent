"""
004_add_vector_storage.py - добавление векторного хранилища
"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

revision = '004_add_vector_storage'
down_revision = '003_add_memory_tables'
branch_labels = None
depends_on = None

def upgrade():
    """Применение миграции"""
    
    # Таблица эмбеддингов (векторные представления)
    op.create_table('embeddings',
        sa.Column('id', sa.String(length=36), nullable=False),
        sa.Column('source_type', sa.String(length=50), nullable=False),
        sa.Column('source_id', sa.String(length=100), nullable=False),
        sa.Column('model_name', sa.String(length=100), nullable=False),
        sa.Column('embedding_vector', postgresql.ARRAY(sa.Float()), nullable=False),
        sa.Column('dimensions', sa.Integer(), nullable=False),
        sa.Column('normalized', sa.Boolean(), nullable=True, server_default='true'),
        sa.Column('metadata', sa.JSON(), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=True, server_default=sa.text('CURRENT_TIMESTAMP')),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('source_type', 'source_id', 'model_name', name='uq_embedding_source')
    )
    
    # Таблица векторных коллекций (для организации)
    op.create_table('vector_collections',
        sa.Column('id', sa.String(length=36), nullable=False),
        sa.Column('name', sa.String(length=255), nullable=False),
        sa.Column('description', sa.Text(), nullable=True),
        sa.Column('model_name', sa.String(length=100), nullable=True),
        sa.Column('dimensions', sa.Integer(), nullable=True),
        sa.Column('distance_metric', sa.String(length=50), nullable=True, server_default='cosine'),
        sa.Column('metadata', sa.JSON(), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=True, server_default=sa.text('CURRENT_TIMESTAMP')),
        sa.Column('updated_at', sa.DateTime(), nullable=True, server_default=sa.text('CURRENT_TIMESTAMP')),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('name')
    )
    
    # Таблица элементов коллекций
    op.create_table('collection_items',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('collection_id', sa.String(length=36), nullable=False),
        sa.Column('embedding_id', sa.String(length=36), nullable=False),
        sa.Column('item_metadata', sa.JSON(), nullable=True),
        sa.Column('added_at', sa.DateTime(), nullable=True, server_default=sa.text('CURRENT_TIMESTAMP')),
        sa.ForeignKeyConstraint(['collection_id'], ['vector_collections.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['embedding_id'], ['embeddings.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('collection_id', 'embedding_id', name='uq_collection_item')
    )
    
    # Таблица результатов поиска (кеш)
    op.create_table('vector_search_results',
        sa.Column('id', sa.String(length=36), nullable=False),
        sa.Column('query_hash', sa.String(length=64), nullable=False),
        sa.Column('collection_id', sa.String(length=36), nullable=True),
        sa.Column('query_vector', postgresql.ARRAY(sa.Float()), nullable=True),
        sa.Column('results', sa.JSON(), nullable=False),
        sa.Column('top_k', sa.Integer(), nullable=True),
        sa.Column('threshold', sa.Float(), nullable=True),
        sa.Column('search_time_ms', sa.Integer(), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=True, server_default=sa.text('CURRENT_TIMESTAMP')),
        sa.Column('expires_at', sa.DateTime(), nullable=True),
        sa.ForeignKeyConstraint(['collection_id'], ['vector_collections.id'], ondelete='SET NULL'),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('query_hash')
    )
    
    # Вставляем базовые коллекции
    op.execute("""
        INSERT INTO vector_collections (id, name, description, model_name, dimensions, distance_metric) VALUES
        ('general_knowledge', 'Общие знания', 'Общая база знаний Елены', 'all-MiniLM-L6-v2', 384, 'cosine'),
        ('user_profiles', 'Профили пользователей', 'Векторные представления пользователей', 'all-MiniLM-L6-v2', 384, 'cosine'),
        ('conversation_context', 'Контекст диалогов', 'Контекстные эмбеддинги диалогов', 'all-MiniLM-L6-v2', 384, 'cosine'),
        ('document_store', 'Хранилище документов', 'Эмбеддинги документов', 'all-MiniLM-L6-v2', 384, 'cosine')
    """)
    
    # Индексы
    op.create_index('ix_embeddings_source_type', 'embeddings', ['source_type'])
    op.create_index('ix_embeddings_source_id', 'embeddings', ['source_id'])
    op.create_index('ix_embeddings_model_name', 'embeddings', ['model_name'])
    op.create_index('ix_collection_items_collection', 'collection_items', ['collection_id'])
    op.create_index('ix_vector_search_results_query_hash', 'vector_search_results', ['query_hash'])
    op.create_index('ix_vector_search_results_expires', 'vector_search_results', ['expires_at'])
    
    # Создаем специальные индексы для векторного поиска (PostgreSQL с pgvector)
    op.execute('''
        CREATE INDEX idx_embeddings_vector ON embeddings 
        USING ivfflat (embedding_vector vector_cosine_ops) 
        WITH (lists = 100)
    ''')

def downgrade():
    """Откат миграции"""
    op.drop_table('vector_search_results')
    op.drop_table('collection_items')
    op.drop_table('vector_collections')
    op.drop_table('embeddings')