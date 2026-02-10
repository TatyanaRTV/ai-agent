"""
recognizer.py - основной модуль распознавания речи для Елены
"""
import logging
import numpy as np
from typing import Optional, Dict, Any, Union
from pathlib import Path

logger = logging.getLogger(__name__)

class SpeechRecognizer:
    """
    Основной класс для распознавания речи.
    Поддерживает несколько движков: Vosk (оффлайн), Whisper, Google.
    """
    
    def __init__(self, 
                 language: str = "ru",
                 engine: str = "vosk",
                 model_path: Optional[str] = None,
                 use_gpu: bool = False):
        """
        Инициализация распознавателя речи.
        
        Args:
            language: Язык распознавания ('ru', 'en', 'ru-en')
            engine: Движок распознавания ('vosk', 'whisper', 'google')
            model_path: Путь к модели (для Vosk/Whisper)
            use_gpu: Использовать GPU для ускорения
        """
        self.language = language
        self.engine_name = engine
        self.use_gpu = use_gpu
        
        # Инициализация выбранного движка
        self.engine = self._init_engine(engine, model_path)
        
        logger.info(f"Инициализирован распознаватель речи: {engine}, язык: {language}")
    
    def _init_engine(self, engine: str, model_path: Optional[str]) -> Any:
        """Инициализация выбранного движка распознавания"""
        if engine == "vosk":
            from .vosk_engine import VoskEngine
            return VoskEngine(
                model_path=model_path or "/mnt/ai_data/models/vosk/ru",
                language=self.language
            )
        elif engine == "whisper":
            from .whisper_engine import WhisperEngine
            return WhisperEngine(
                model_size="base",
                language=self.language,
                use_gpu=self.use_gpu
            )
        elif engine == "google":
            from .google_engine import GoogleEngine
            return GoogleEngine(language=self.language)
        else:
            raise ValueError(f"Неизвестный движок распознавания: {engine}")
    
    def recognize_file(self, 
                      audio_path: Union[str, Path],
                      **kwargs) -> Dict[str, Any]:
        """
        Распознавание речи из аудиофайла.
        
        Args:
            audio_path: Путь к аудиофайлу
            **kwargs: Дополнительные параметры
            
        Returns:
            Словарь с результатом распознавания
        """
        audio_path = Path(audio_path)
        if not audio_path.exists():
            raise FileNotFoundError(f"Аудиофайл не найден: {audio_path}")
        
        logger.info(f"Распознавание речи из файла: {audio_path}")
        
        try:
            # Предобработка аудио
            from .audio_preprocessor import AudioPreprocessor
            preprocessor = AudioPreprocessor()
            processed_audio = preprocessor.process_file(audio_path)
            
            # Распознавание
            result = self.engine.recognize(processed_audio, **kwargs)
            
            # Постобработка результата
            result = self._postprocess_result(result)
            
            logger.info(f"Распознавание завершено: {result.get('text', '')[:50]}...")
            return result
            
        except Exception as e:
            logger.error(f"Ошибка распознавания: {e}", exc_info=True)
            return {
                "text": "",
                "confidence": 0.0,
                "error": str(e),
                "success": False
            }
    
    def recognize_bytes(self, 
                       audio_bytes: bytes,
                       sample_rate: int = 16000,
                       **kwargs) -> Dict[str, Any]:
        """
        Распознавание речи из байтов аудио.
        
        Args:
            audio_bytes: Байты аудиоданных
            sample_rate: Частота дискретизации
            **kwargs: Дополнительные параметры
            
        Returns:
            Словарь с результатом распознавания
        """
        logger.info(f"Распознавание речи из байтов (размер: {len(audio_bytes)})")
        
        try:
            from .audio_preprocessor import AudioPreprocessor
            preprocessor = AudioPreprocessor()
            
            # Конвертация байтов в аудио данные
            audio_data = preprocessor.bytes_to_audio(audio_bytes, sample_rate)
            
            # Распознавание
            result = self.engine.recognize(audio_data, **kwargs)
            result = self._postprocess_result(result)
            
            return result
            
        except Exception as e:
            logger.error(f"Ошибка распознавания: {e}")
            return {
                "text": "",
                "confidence": 0.0,
                "error": str(e),
                "success": False
            }
    
    def stream_recognize(self, 
                        stream_generator,
                        **kwargs) -> Dict[str, Any]:
        """
        Потоковое распознавание речи.
        
        Args:
            stream_generator: Генератор аудио фрагментов
            **kwargs: Дополнительные параметры
            
        Returns:
            Словарь с результатом распознавания
        """
        from .stream_recognizer import StreamRecognizer
        stream_processor = StreamRecognizer(self.engine)
        return stream_processor.recognize_stream(stream_generator, **kwargs)
    
    def _postprocess_result(self, result: Dict[str, Any]) -> Dict[str, Any]:
        """Постобработка результата распознавания"""
        # Очистка текста
        if "text" in result:
            text = result["text"].strip()
            
            # Удаление лишних пробелов
            text = ' '.join(text.split())
            
            # Капитализация первого слова
            if text:
                text = text[0].upper() + text[1:]
            
            result["text"] = text
            
            # Добавление уверенности, если нет
            if "confidence" not in result:
                result["confidence"] = 0.9 if text else 0.0
            
            # Добавление флага успеха
            result["success"] = bool(text and len(text) > 0)
        
        return result
    
    def set_language(self, language: str):
        """Изменение языка распознавания"""
        self.language = language
        self.engine.set_language(language)
        logger.info(f"Язык распознавания изменен на: {language}")
    
    def get_supported_languages(self) -> list:
        """Получение списка поддерживаемых языков"""
        return self.engine.get_supported_languages()
    
    def get_engine_info(self) -> Dict[str, Any]:
        """Получение информации о движке"""
        return {
            "name": self.engine_name,
            "language": self.language,
            "supports_streaming": self.engine.supports_streaming(),
            "is_offline": self.engine.is_offline(),
            "description": self.engine.get_description()
        }