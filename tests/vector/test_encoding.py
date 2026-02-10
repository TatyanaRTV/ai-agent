"""
Тесты для модуля кодирования данных в векторы
"""
import pytest
import numpy as np
from src.tools.vector.encoding.encoder import VectorEncoder
from src.tools.vector.encoding.transformer import DataTransformer


class TestVectorEncoding:
    """Тесты кодирования в векторы"""
    
    def setup_method(self):
        """Настройка перед каждым тестом"""
        self.encoder = VectorEncoder(model_name="all-MiniLM-L6-v2")
        self.transformer = DataTransformer()
    
    def test_text_encoding(self):
        """Тест кодирования текста"""
        text = "Привет, меня зовут Елена"
        vector = self.encoder.encode_text(text)
        
        assert isinstance(vector, np.ndarray)
        assert vector.shape[0] == 384  # Размерность модели
        assert not np.all(vector == 0)
    
    def test_batch_encoding(self):
        """Тест пакетного кодирования"""
        texts = ["Привет", "Как дела?", "Что нового?"]
        vectors = self.encoder.encode_batch(texts)
        
        assert len(vectors) == 3
        assert all(isinstance(v, np.ndarray) for v in vectors)
    
    def test_normalization(self):
        """Тест нормализации векторов"""
        text = "Тест нормализации"
        vector = self.encoder.encode_text(text, normalize=True)
        
        norm = np.linalg.norm(vector)
        assert pytest.approx(norm, 0.001) == 1.0
    
    def test_different_languages(self):
        """Тест кодирования на разных языках"""
        texts = {
            "ru": "Привет, как дела?",
            "en": "Hello, how are you?",
            "es": "Hola, ¿cómo estás?"
        }
        
        for lang, text in texts.items():
            vector = self.encoder.encode_text(text)
            assert vector is not None
            assert len(vector) > 0