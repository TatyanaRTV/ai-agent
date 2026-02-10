"""
whisper_engine.py - движок распознавания Whisper (OpenAI)
"""
import logging
from typing import Dict, Any, Optional
import numpy as np

logger = logging.getLogger(__name__)

class WhisperEngine:
    """Движок распознавания на основе Whisper"""
    
    def __init__(self,
                 model_size: str = "base",
                 language: str = "ru",
                 use_gpu: bool = False):
        """
        Инициализация Whisper движка.
        
        Args:
            model_size: Размер модели ('tiny', 'base', 'small', 'medium', 'large')
            language: Язык распознавания
            use_gpu: Использовать GPU
        """
        self.model_size = model_size
        self.language = language
        self.use_gpu = use_gpu
        self.model = None
        
        self._load_model()
    
    def _load_model(self):
        """Загрузка модели Whisper"""
        try:
            import whisper
            
            device = "cuda" if self.use_gpu else "cpu"
            self.model = whisper.load_model(self.model_size, device=device)
            
            logger.info(f"Whisper модель загружена: {self.model_size}, устройство: {device}")
            
        except ImportError:
            logger.error("Библиотека whisper не установлена")
            raise
        except Exception as e:
            logger.error(f"Ошибка загрузки модели Whisper: {e}")
            raise
    
    def recognize(self, 
                  audio_data: np.ndarray,
                  sample_rate: int = 16000,
                  **kwargs) -> Dict[str, Any]:
        """
        Распознавание речи с помощью Whisper.
        
        Args:
            audio_data: Аудиоданные
            sample_rate: Частота дискретизации
            **kwargs: Дополнительные параметры
            
        Returns:
            Результат распознавания
        """
        try:
            import whisper
            
            # Подготовка аудио для Whisper
            audio = audio_data.astype(np.float32)
            
            # Распознавание
            result = self.model.transcribe(
                audio,
                language=self.language,
                fp16=self.use_gpu,  # Использовать половинную точность на GPU
                **kwargs
            )
            
            return {
                "text": result.get("text", "").strip(),
                "segments": result.get("segments", []),
                "language": result.get("language", self.language),
                "confidence": self._calculate_confidence(result),
                "engine": "whisper",
                "model_size": self.model_size
            }
            
        except Exception as e:
            logger.error(f"Ошибка распознавания Whisper: {e}")
            return {
                "text": "",
                "confidence": 0.0,
                "error": str(e),
                "engine": "whisper"
            }
    
    def _calculate_confidence(self, result: Dict[str, Any]) -> float:
        """Расчет уверенности распознавания"""
        if "segments" in result and result["segments"]:
            confidences = [seg.get("confidence", 0.0) for seg in result["segments"]]
            return sum(confidences) / len(confidences) if confidences else 0.0
        return 0.9  # По умолчанию
    
    def set_language(self, language: str):
        """Изменение языка распознавания"""
        self.language = language
    
    def get_supported_languages(self) -> list:
        """Получение поддерживаемых языков"""
        return ["ru", "en", "es", "fr", "de", "it", "ja", "zh", "ko", "ar"]
    
    def supports_streaming(self) -> bool:
        """Поддерживает ли потоковое распознавание"""
        return False  # Whisper не поддерживает потоковое распознавание из коробки
    
    def is_offline(self) -> bool:
        """Работает ли оффлайн"""
        return True
    
    def get_description(self) -> str:
        """Описание движка"""
        return "Whisper - мощный движок распознавания от OpenAI, поддерживает множество языков"