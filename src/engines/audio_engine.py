#!/usr/bin/env python3
# Путь: /mnt/ai_data/ai-agent/src/engines/audio_engine.py
"""Аудио движок Елены - запись с микрофона и распознавание речи"""

import whisper  # type: ignore[import-untyped]
import sounddevice as sd  # type: ignore[import-untyped]
import numpy as np
import asyncio
import os
import time
from pathlib import Path
from typing import Any, Dict, Optional, cast
from loguru import logger


class AudioEngine:
    """Движок для работы с аудио: запись с микрофона и распознавание речи"""

    def __init__(self, config: Dict[str, Any]) -> None:
        """
        Инициализация аудио движка

        Args:
            config: словарь с конфигурацией
        """
        # Проверяем папку для кэша Whisper
        cache_dir = Path.home() / ".cache" / "whisper"
        if not cache_dir.exists():
            cache_dir.mkdir(parents=True, exist_ok=True)
            logger.info(f"📁 Создана папка для Whisper: {cache_dir}")
        else:
            logger.debug(f"📁 Папка Whisper уже существует: {cache_dir}")

        os.environ["WHISPER_CACHE_DIR"] = str(cache_dir)

        # Загружаем модель Whisper
        self.model: Any = whisper.load_model(config["audio"]["whisper_model"])
        self.sample_rate: int = config["audio"]["sample_rate"]
        self.duration: int = config.get("audio", {}).get("listen_duration", 10)

        logger.info(f"🎵 AudioEngine инициализирован (модель: {config['audio']['whisper_model']})")

    # Исправлено MyPy: duration теперь Optional[int] (ошибка 42)
    async def listen(self, duration: Optional[int] = None, silence_timeout: float = 2.0) -> str:
        """
        Запись с микрофона и распознавание речи.

        Args:
            duration: максимальная длительность записи (по умолчанию 15 сек)
            silence_timeout: сколько секунд тишины ждать перед остановкой

        Returns:
            распознанный текст или пустая строка
        """
        if duration is None:
            duration = 15  # Увеличили до 15 секунд по умолчанию

        logger.info(f"🎤 Слушаю... (макс. {duration} сек, тишина {silence_timeout} сек)")

        try:
            # Запись звука
            recording = sd.rec(
                int(duration * self.sample_rate), samplerate=self.sample_rate, channels=1, dtype="float32"
            )

            # Ждем окончания записи или обнаружения тишины
            start_time = time.time()
            last_sound_time = time.time()
            silence_threshold = 0.01  # порог тишины

            while time.time() - start_time < duration:
                await asyncio.sleep(0.1)

                # Проверяем, есть ли звук в последнем куске
                current_pos = int((time.time() - start_time) * self.sample_rate)
                if current_pos > 100:
                    # Используем np.max для анализа амплитуды
                    if np.max(np.abs(recording[current_pos - 100 : current_pos])) > silence_threshold:
                        last_sound_time = time.time()

                # Если тишина длится дольше silence_timeout - останавливаемся
                if time.time() - last_sound_time > silence_timeout and time.time() - start_time > 3:
                    logger.info(f"🔇 Тишина {silence_timeout} сек, останавливаю запись")
                    break

            sd.stop()

            # Обрезаем запись до последнего звука
            end_idx = int((last_sound_time - start_time) * self.sample_rate) + self.sample_rate
            if end_idx > len(recording):
                end_idx = len(recording)

            audio = recording[:end_idx].flatten().astype(np.float32)

            # Распознаем речь
            result = self.model.transcribe(audio, language="ru")
            text = cast(str, result.get("text", "")).strip()

            if text:
                logger.info(f"📝 Распознано: {text}")
                return text
            else:
                logger.info("🤔 Ничего не распознано")
                return ""

        except Exception as e:
            logger.error(f"❌ Ошибка записи/распознавания: {e}")
            return ""
