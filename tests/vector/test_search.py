"""
Тесты для модуля поиска по векторам
"""
import pytest
import numpy as np
from src.tools.vector.search.query import VectorQuery
from src.tools.vector.search.matcher import VectorMatcher


class TestVectorSearch:
    """Тесты поиска по векторам"""
    
    def setup_method(self):
        """Настройка перед каждым тестом"""
        self.query = VectorQuery()
        self.matcher = VectorMatcher()
        
        # Тестовые векторы и метаданные
        self.vectors = np.array([
            [0.1, 0.2, 0.3],
            [0.4, 0.5, 0.6],
            [0.7, 0.8, 0.9]
        ])
        
        self.metadata = [
            {"id": "1", "text": "Котики милые", "category": "животные"},
            {"id": "2", "text": "Собаки верные", "category": "животные"},
            {"id": "3", "text": "Программирование интересно", "category": "технологии"}
        ]
    
    def test_cosine_similarity(self):
        """Тест косинусного сходства"""
        vec1 = np.array([1, 0, 0])
        vec2 = np.array([0, 1, 0])
        
        similarity = self.matcher.cosine_similarity(vec1, vec2)
        assert similarity == 0.0
        
        vec3 = np.array([1, 0, 0])
        similarity = self.matcher.cosine_similarity(vec1, vec3)
        assert similarity == 1.0
    
    def test_euclidean_distance(self):
        """Тест евклидова расстояния"""
        vec1 = np.array([0, 0])
        vec2 = np.array([3, 4])
        
        distance = self.matcher.euclidean_distance(vec1, vec2)
        assert distance == 5.0
    
    def test_knn_search(self):
        """Тест поиска k ближайших соседей"""
        query_vector = np.array([0.15, 0.25, 0.35])
        
        results = self.matcher.knn_search(
            query_vector, 
            self.vectors, 
            self.metadata, 
            k=2
        )
        
        assert len(results) == 2
        assert results[0]["id"] == "1"
        assert results[1]["id"] == "2"
    
    def test_threshold_search(self):
        """Тест поиска с порогом сходства"""
        query_vector = np.array([0.1, 0.2, 0.3])
        
        results = self.matcher.threshold_search(
            query_vector,
            self.vectors,
            self.metadata,
            threshold=0.9
        )
        
        assert len(results) >= 1
        assert results[0]["similarity"] >= 0.9