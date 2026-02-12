"""
Vosk engine for speech recognition (ВРЕМЕННО ОТКЛЮЧЕН)
"""

import logging

logger = logging.getLogger(__name__)

# Класс-заглушка, чтобы избежать ошибок импорта
class VoskEngine:
    """Vosk engine (отключён)"""
    
    def __init__(self, *args, **kwargs):
        logger.warning("⚠️ VoskEngine отключён, используйте Whisper")
        raise ImportError("VoskEngine отключён в конфигурации")