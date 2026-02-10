"""
Тесты для модуля индексации векторов
"""
import pytest
import tempfile
import shutil
from pathlib import Path
from src.tools.vector.indexing.indexer import VectorIndexer
from src.core.memory.vector_db.vector_storage import VectorStorage


class TestVectorIndexing:
    """Тесты индексации векторов"""
    
    def setup_method(self):
        """Настройка перед каждым тестом"""
        self.temp_dir = tempfile.mkdtemp()
        self.index_path = Path(self.temp_dir) / "test_index"
        self.indexer = VectorIndexer(index_path=str(self.index_path))
        self.storage = VectorStorage(collection_name="test_collection")
        
        # Тестовые данные
        self.test_vectors = [
            {"id": "1", "vector": [0.1, 0.2, 0.3], "text": "Первый документ"},
            {"id": "2", "vector": [0.4, 0.5, 0.6], "text": "Второй документ"},
            {"id": "3", "vector": [0.7, 0.8, 0.9], "text": "Третий документ"}
        ]
    
    def teardown_method(self):
        """Очистка после каждого теста"""
        if Path(self.temp_dir).exists():
            shutil.rmtree(self.temp_dir)
    
    def test_create_index(self):
        """Тест создания индекса"""
        self.indexer.create_index(self.test_vectors)
        assert self.indexer.index_exists()
    
    def test_add_to_index(self):
        """Тест добавления векторов в индекс"""
        self.indexer.create_index([])
        
        new_vector = {"id": "4", "vector": [1.0, 1.0, 1.0], "text": "Новый документ"}
        self.indexer.add_to_index([new_vector])
        
        count = self.indexer.get_index_size()
        assert count == 1
    
    def test_similarity_search(self):
        """Тест поиска по сходству"""
        self.indexer.create_index(self.test_vectors)
        
        query_vector = [0.15, 0.25, 0.35]
        results = self.indexer.search_similar(query_vector, k=2)
        
        assert len(results) == 2
        assert results[0]["id"] == "1"  # Самый близкий
        assert "similarity" in results[0]
    
    def test_save_load_index(self):
        """Тест сохранения и загрузки индекса"""
        self.indexer.create_index(self.test_vectors)
        self.indexer.save_index()
        
        # Создаем новый индексер и загружаем
        new_indexer = VectorIndexer(index_path=str(self.index_path))
        new_indexer.load_index()
        
        assert new_indexer.get_index_size() == 3