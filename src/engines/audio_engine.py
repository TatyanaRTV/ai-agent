# Путь: /mnt/ai_data/ai-agent/src/engines/audio_engine.py
import whisper
import sounddevice as sd
import numpy as np
import asyncio
import os
from pathlib import Path
from loguru import logger

class AudioEngine:
    def __init__(self, config):
        # Проверяем папку для кэша Whisper
        cache_dir = Path.home() / '.cache' / 'whisper'
        if not cache_dir.exists():
            cache_dir.mkdir(parents=True, exist_ok=True)
            logger.info(f"📁 Создана папка для Whisper: {cache_dir}")
        else:
            logger.debug(f"📁 Папка Whisper уже существует: {cache_dir}")
        
        os.environ['WHISPER_CACHE_DIR'] = str(cache_dir)
        
        self.model = whisper.load_model(config["audio"]["whisper_model"])
        self.sample_rate = config["audio"]["sample_rate"]
        self.duration = config.get("audio", {}).get("listen_duration", 10)

    async def listen(self, duration: int = None):
        """Запись с микрофона и распознавание речи."""
        if duration is None:
            duration = self.duration
            
        logger.info(f"🎤 Слушаю {duration} секунд...")
        
        try:
            recording = sd.rec(int(duration * self.sample_rate),
                              samplerate=self.sample_rate,
                              channels=1, dtype='float32')
            sd.wait()
            
            audio = recording.flatten().astype(np.float32)
            result = self.model.transcribe(audio, language="ru")
            text = result["text"].strip()
            
            if text:
                logger.info(f"📝 Распознано: {text}")
            else:
                logger.info("🤔 Ничего не распознано")
                
            return text
            
        except Exception as e:
            logger.error(f"❌ Ошибка записи/распознавания: {e}")
            return ""