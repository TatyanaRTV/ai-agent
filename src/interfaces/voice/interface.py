"""
Голосовой интерфейс для Елены
"""

import logging
from typing import Optional

logger = logging.getLogger(__name__)

class VoiceInterface:
    """Голосовой интерфейс"""
    
    def __init__(self):
        self.tts_engine = None
        self.stt_engine = None
        logger.info("🎤 Голосовой интерфейс инициализирован")
        
    async def speak(self, text: str):
        """Произнести текст"""
        logger.info(f"🔊 Елена: {text}")
        print(f"🔊 Елена: {text}")
        
    async def listen(self) -> Optional[str]:
        """Прослушать команду"""
        logger.info("🎧 Ожидание команды...")
        return None