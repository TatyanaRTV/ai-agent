"""
Тесты для вычисления сходства между векторами
"""
import pytest
import numpy as np
from src.tools.vector.search.matcher import VectorMatcher


class TestSimilarity:
    """Тесты вычисления сходства"""
    
    def setup_method(self):
        self.matcher = VectorMatcher()
    
    def test_dot_product(self):
        """Тест скалярного произведения"""
        a = np.array([1, 2, 3])
        b = np.array([4, 5, 6])
        
        result = self.matcher.dot_product(a, b)
        expected = 1*4 + 2*5 + 3*6
        assert result == expected
    
    def test_vector_norm(self):
        """Тест вычисления нормы вектора"""
        v = np.array([3, 4])
        norm = self.matcher.vector_norm(v)
        assert norm == 5.0
    
    def test_similarity_matrix(self):
        """Тест вычисления матрицы сходства"""
        vectors = np.array([
            [1, 0, 0],
            [0, 1, 0],
            [0, 0, 1]
        ])
        
        matrix = self.matcher.similarity_matrix(vectors)
        
        assert matrix.shape == (3, 3)
        assert np.all(np.diag(matrix) == 1.0)  # Диагональ = 1
        assert matrix[0, 1] == 0.0  # Ортогональные векторы
    
    def test_cluster_similarity(self):
        """Тест сходства кластеров"""
        cluster1 = np.array([[1, 0], [0.9, 0.1]])
        cluster2 = np.array([[0, 1], [0.1, 0.9]])
        
        similarity = self.matcher.cluster_similarity(cluster1, cluster2)
        assert similarity < 0.5  # Кластеры разные