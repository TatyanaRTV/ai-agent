"""
Конфигурация и фикстуры для тестов векторных операций
"""
import pytest
import numpy as np
import tempfile
from pathlib import Path


@pytest.fixture
def sample_vectors():
    """Фикстура: тестовые векторы"""
    return np.random.randn(10, 384)  # 10 векторов по 384 измерения


@pytest.fixture
def sample_metadata():
    """Фикстура: тестовые метаданные"""
    return [
        {"id": f"doc_{i}", "text": f"Документ номер {i}", "timestamp": i}
        for i in range(10)
    ]


@pytest.fixture
def temp_vector_dir():
    """Фикстура: временная директория для векторных данных"""
    temp_dir = tempfile.mkdtemp()
    yield Path(temp_dir)
    # Автоматическая очистка после теста
    import shutil
    if Path(temp_dir).exists():
        shutil.rmtree(temp_dir)


@pytest.fixture
def encoder():
    """Фикстура: энкодер векторов"""
    from src.tools.vector.encoding.encoder import VectorEncoder
    return VectorEncoder(model_name="all-MiniLM-L6-v2")


@pytest.fixture
def indexer(temp_vector_dir):
    """Фикстура: индексатор векторов"""
    from src.tools.vector.indexing.indexer import VectorIndexer
    return VectorIndexer(index_path=str(temp_vector_dir / "test_index"))