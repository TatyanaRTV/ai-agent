"""
audio_preprocessor.py - предобработка аудио для распознавания
"""
import numpy as np
import librosa
import soundfile as sf
from typing import Union, Optional
from pathlib import Path
import logging

logger = logging.getLogger(__name__)

class AudioPreprocessor:
    """Класс для предобработки аудио перед распознаванием"""
    
    def __init__(self,
                 target_sample_rate: int = 16000,
                 normalize: bool = True,
                 remove_noise: bool = True):
        """
        Инициализация предобработчика аудио.
        
        Args:
            target_sample_rate: Целевая частота дискретизации
            normalize: Нормализовать ли аудио
            remove_noise: Удалять ли шум
        """
        self.target_sample_rate = target_sample_rate
        self.normalize = normalize
        self.remove_noise = remove_noise
    
    def process_file(self, 
                    audio_path: Union[str, Path]) -> np.ndarray:
        """
        Загрузка и предобработка аудиофайла.
        
        Args:
            audio_path: Путь к аудиофайлу
            
        Returns:
            Обработанные аудиоданные
        """
        audio_path = Path(audio_path)
        
        # Загрузка аудио
        audio, sr = librosa.load(str(audio_path), sr=None, mono=True)
        
        # Предобработка
        audio = self._preprocess_audio(audio, sr)
        
        return audio
    
    def process_bytes(self, 
                     audio_bytes: bytes,
                     sample_rate: int) -> np.ndarray:
        """
        Обработка аудио из байтов.
        
        Args:
            audio_bytes: Байты аудио
            sample_rate: Частота дискретизации
            
        Returns:
            Обработанные аудиоданные
        """
        import io
        
        # Конвертация байтов в аудио
        with io.BytesIO(audio_bytes) as bio:
            audio, sr = sf.read(bio)
            
            # Если многоканальное, конвертируем в моно
            if len(audio.shape) > 1:
                audio = np.mean(audio, axis=1)
            
            # Предобработка
            audio = self._preprocess_audio(audio, sr)
            
            return audio
    
    def _preprocess_audio(self, 
                         audio: np.ndarray,
                         sample_rate: int) -> np.ndarray:
        """
        Основная предобработка аудио.
        
        Args:
            audio: Аудиоданные
            sample_rate: Исходная частота дискретизации
            
        Returns:
            Обработанные аудиоданные
        """
        # 1. Ресемплинг до целевой частоты
        if sample_rate != self.target_sample_rate:
            audio = librosa.resample(
                audio,
                orig_sr=sample_rate,
                target_sr=self.target_sample_rate
            )
        
        # 2. Удаление шума (если включено)
        if self.remove_noise:
            audio = self._remove_noise(audio)
        
        # 3. Нормализация (если включено)
        if self.normalize:
            audio = self._normalize_audio(audio)
        
        # 4. Обрезка тишины
        audio = self._trim_silence(audio)
        
        return audio
    
    def _remove_noise(self, audio: np.ndarray) -> np.ndarray:
        """Удаление шума из аудио"""
        try:
            import noisereduce as nr
            return nr.reduce_noise(y=audio, sr=self.target_sample_rate)
        except ImportError:
            logger.warning("noisereduce не установлен, пропускаем удаление шума")
            return audio
    
    def _normalize_audio(self, audio: np.ndarray) -> np.ndarray:
        """Нормализация аудио"""
        if np.max(np.abs(audio)) > 0:
            return audio / np.max(np.abs(audio))
        return audio
    
    def _trim_silence(self, audio: np.ndarray, threshold: float = 0.01) -> np.ndarray:
        """Обрезка тишины в начале и конце"""
        # Находим индексы, где аудио превышает порог
        above_threshold = np.where(np.abs(audio) > threshold)[0]
        
        if len(above_threshold) > 0:
            start = max(0, above_threshold[0] - 100)
            end = min(len(audio), above_threshold[-1] + 100)
            return audio[start:end]
        
        return audio
    
    def bytes_to_audio(self, 
                      audio_bytes: bytes,
                      sample_rate: int) -> np.ndarray:
        """Конвертация байтов в аудио данные"""
        return self.process_bytes(audio_bytes, sample_rate)