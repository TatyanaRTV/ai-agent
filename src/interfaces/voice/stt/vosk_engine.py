"""
vosk_engine.py - движок распознавания Vosk (оффлайн)
"""
import json
import logging
from typing import Dict, Any, Optional
import numpy as np

logger = logging.getLogger(__name__)

class VoskEngine:
    """Движок распознавания на основе Vosk (оффлайн, быстрый)"""
    
    def __init__(self, 
                 model_path: str,
                 language: str = "ru"):
        """
        Инициализация Vosk движка.
        
        Args:
            model_path: Путь к модели Vosk
            language: Язык модели
        """
        self.model_path = model_path
        self.language = language
        self.model = None
        self.recognizer = None
        
        self._load_model()
    
    def _load_model(self):
        """Загрузка модели Vosk"""
        try:
            from vosk import Model, KaldiRecognizer
            import wave
            
            self.model = Model(self.model_path)
            self.recognizer = KaldiRecognizer(self.model, 16000)
            
            logger.info(f"Vosk модель загружена: {self.model_path}")
            
        except ImportError:
            logger.error("Библиотека vosk не установлена")
            raise
        except Exception as e:
            logger.error(f"Ошибка загрузки модели Vosk: {e}")
            raise
    
    def recognize(self, 
                  audio_data: np.ndarray,
                  sample_rate: int = 16000) -> Dict[str, Any]:
        """
        Распознавание речи с помощью Vosk.
        
        Args:
            audio_data: Аудиоданные
            sample_rate: Частота дискретизации
            
        Returns:
            Результат распознавания
        """
        try:
            # Конвертация в формат, понятный Vosk
            import wave
            import io
            
            # Создаем временный WAV файл в памяти
            bio = io.BytesIO()
            with wave.open(bio, 'wb') as wf:
                wf.setnchannels(1)
                wf.setsampwidth(2)
                wf.setframerate(sample_rate)
                wf.writeframes((audio_data * 32767).astype(np.int16).tobytes())
            
            bio.seek(0)
            
            # Распознавание
            result_text = ""
            confidence = 0.0
            
            with wave.open(bio, 'rb') as wf:
                while True:
                    data = wf.readframes(4000)
                    if len(data) == 0:
                        break
                    
                    if self.recognizer.AcceptWaveform(data):
                        result = json.loads(self.recognizer.Result())
                        if 'text' in result:
                            result_text += " " + result['text']
                        if 'confidence' in result:
                            confidence = max(confidence, result['confidence'])
            
            # Финальный результат
            final_result = json.loads(self.recognizer.FinalResult())
            if 'text' in final_result:
                result_text += " " + final_result['text']
            
            return {
                "text": result_text.strip(),
                "confidence": confidence if confidence > 0 else 0.85,
                "engine": "vosk",
                "language": self.language
            }
            
        except Exception as e:
            logger.error(f"Ошибка распознавания Vosk: {e}")
            return {
                "text": "",
                "confidence": 0.0,
                "error": str(e),
                "engine": "vosk"
            }
    
    def set_language(self, language: str):
        """Изменение языка (требует перезагрузки модели)"""
        self.language = language
        # В Vosk нужно загрузить новую модель для другого языка
        # Реализация зависит от структуры моделей
    
    def get_supported_languages(self) -> list:
        """Получение поддерживаемых языков"""
        return ["ru", "en", "ru-en", "en-ru"]
    
    def supports_streaming(self) -> bool:
        """Поддерживает ли потоковое распознавание"""
        return True
    
    def is_offline(self) -> bool:
        """Работает ли оффлайн"""
        return True
    
    def get_description(self) -> str:
        """Описание движка"""
        return "Vosk - оффлайн движок распознавания речи, быстрый, поддерживает русский язык"