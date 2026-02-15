#!/usr/bin/env python3
# Путь: /mnt/ai_data/ai-agent/src/tools/media/audio_processor.py
"""Обработка аудио файлов"""

import whisper
from pydub import AudioSegment
from pathlib import Path
from loguru import logger
import os

os.environ["WHISPER_CACHE_DIR"] = "/tmp/whisper_cache"  # временная папка


class AudioProcessor:
    """Обработчик аудио"""

    def __init__(self, config):
        self.config = config
        self.whisper_model = None
        self._load_whisper()
        logger.info("🎵 AudioProcessor инициализирован")

    def _load_whisper(self):
        """Ленивая загрузка Whisper модели с проверкой папки"""
        try:
            # Проверяем, существует ли папка
            cache_dir = Path.home() / ".cache" / "whisper"
            if not cache_dir.exists():
                cache_dir.mkdir(parents=True, exist_ok=True)
                logger.info(f"📁 Создана папка для Whisper: {cache_dir}")
            else:
                logger.debug(f"📁 Папка Whisper уже существует: {cache_dir}")

            os.environ["WHISPER_CACHE_DIR"] = str(cache_dir)

            # Загружаем модель (только если ещё не загружена)
            if not hasattr(self, "whisper_model") or self.whisper_model is None:
                self.whisper_model = whisper.load_model("base")
                logger.info("✅ Whisper модель загружена")
            else:
                logger.debug("✅ Whisper модель уже загружена")

        except Exception as e:
            logger.warning(f"⚠️ Whisper не загружен: {e}")
            self.whisper_model = None

    def get_info(self, file_path):
        """Получение информации об аудио"""
        try:
            audio = AudioSegment.from_file(str(file_path))
            info = {
                "duration": len(audio) / 1000.0,
                "channels": audio.channels,
                "frame_rate": audio.frame_rate,
                "sample_width": audio.sample_width,
            }
            return info
        except Exception as e:
            logger.error(f"❌ Ошибка получения информации об аудио: {e}")
            return {}

    def transcribe(self, file_path):
        """Распознавание речи в аудио"""
        try:
            if not self.whisper_model:
                self._load_whisper()
                if not self.whisper_model:
                    return ""

            result = self.whisper_model.transcribe(str(file_path), language="ru")
            text = result["text"].strip()
            logger.info(f"📝 Распознано: {text[:100]}...")
            return text

        except Exception as e:
            logger.error(f"❌ Ошибка распознавания речи: {e}")
            return ""

    def convert_format(self, file_path, output_format="wav"):
        """Конвертация аудио в другой формат"""
        try:
            audio = AudioSegment.from_file(str(file_path))
            output_path = Path(file_path).with_suffix(f".{output_format}")
            audio.export(str(output_path), format=output_format)
            logger.info(f"🔄 Аудио сконвертировано: {output_path}")
            return str(output_path)
        except Exception as e:
            logger.error(f"❌ Ошибка конвертации аудио: {e}")
            return None
