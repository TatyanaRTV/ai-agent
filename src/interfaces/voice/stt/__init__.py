"""
Модуль распознавания речи (Speech-to-Text) для ИИ-агента Елена
"""

from .recognizer import SpeechRecognizer
from .vosk_engine import VoskEngine
from .whisper_engine import WhisperEngine
from .google_engine import GoogleEngine
from .engine_manager import EngineManager
from .audio_preprocessor import AudioPreprocessor
from .language_detector import LanguageDetector
from .vad import VoiceActivityDetector
from .stream_recognizer import StreamRecognizer

__all__ = [
    'SpeechRecognizer',
    'VoskEngine',
    'WhisperEngine',
    'GoogleEngine',
    'EngineManager',
    'AudioPreprocessor',
    'LanguageDetector',
    'VoiceActivityDetector',
    'StreamRecognizer'
]

__version__ = '1.0.0'
__author__ = 'Елена ИИ-Агент'
__description__ = 'Модуль распознавания речи с поддержкой русского языка'