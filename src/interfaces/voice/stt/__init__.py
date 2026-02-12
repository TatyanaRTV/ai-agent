"""
Модуль распознавания речи (Speech-to-Text) для ИИ-агента Елена
"""

from .recognizer import SpeechRecognizer
# from .vosk_engine import VoskEngine  # ❌ Временное отключение Vosk
from .whisper_engine import WhisperEngine

__all__ = [
    'SpeechRecognizer',
    # 'VoskEngine',      # ❌ Отключено до установки модели
    'WhisperEngine',
]

__version__ = '1.0.0'
__author__ = 'Елена ИИ-Агент'
__description__ = 'Модуль распознавания речи с поддержкой русского языка (Whisper)'