#!/usr/bin/env python3
# Путь: /mnt/ai_data/ai-agent/src/engines/voice_engine.py
"""
ПРОСТОЙ ГОЛОСОВОЙ МОДУЛЬ ДЛЯ ЕЛЕНЫ
Говорит голосом Елены через RHVoice с женским нежным голосом
"""

import os
import subprocess
import tempfile
from pathlib import Path
import threading
import queue
import time
from typing import Any, Dict, List, Optional, Union, cast
from loguru import logger


class VoiceEngine:
    """
    Голосовой движок Елены с использованием RHVoice
    Автоматически определяет доступные голоса и настройки
    """

    def __init__(self, config: Optional[Dict[str, Any]] = None) -> None:
        """
        Инициализация голосового движка

        Args:
            config: словарь с настройками (опционально)
        """
        logger.info("🎤 Инициализация голосового движка Елены...")

        # Настройки по умолчанию
        self.config = config or {}
        self.voice_profile = self.config.get("voice", {}).get("profile", "elena")
        self.speed = self.config.get("voice", {}).get("speed", 85)  # скорость речи
        self.pitch = self.config.get("voice", {}).get("pitch", 50)  # высота тона
        self.volume = self.config.get("voice", {}).get("volume", 100)  # громкость

        # Временная директория для аудиофайлов
        self.temp_dir = Path("/mnt/ai_data/ai-agent/data/temp/voice")
        self.temp_dir.mkdir(parents=True, exist_ok=True)

        # Проверка доступности RHVoice
        self.rhvoice_command: str = "RHVoice-test"
        self.rhvoice_available = self._check_rhvoice()

        # Очередь для асинхронного воспроизведения (Исправлено для MyPy: тип очереди)
        self.speech_queue: queue.Queue[Optional[str]] = queue.Queue()
        self.is_speaking = False
        self.speaker_thread: Optional[threading.Thread] = None

        # Запуск потока для асинхронной речи
        self._start_speaker_thread()

        if self.rhvoice_available:
            self._list_available_voices()
            logger.success("✅ Голосовой движок Елены готов")
        else:
            logger.warning("⚠️ RHVoice не найден, голосовой вывод отключён")

    def _check_rhvoice(self) -> bool:
        """Проверка наличия RHVoice в системе"""
        try:
            # Проверяем разные возможные имена исполняемых файлов
            rhvoice_commands = ["RHVoice-test", "rhvoice-client", "RHVoice-client"]

            for cmd in rhvoice_commands:
                result = subprocess.run(["which", cmd], capture_output=True, text=True)
                if result.returncode == 0:
                    self.rhvoice_command = cmd
                    logger.info(f"✅ Найден RHVoice: {cmd}")
                    return True

            # Проверка через пакетный менеджер
            result = subprocess.run(["dpkg", "-l", "rhvoice"], capture_output=True, text=True)
            if "ii  rhvoice" in result.stdout:
                logger.info("✅ RHVoice установлен через пакетный менеджер")
                self.rhvoice_command = "RHVoice-test"
                return True

            return False

        except Exception as e:
            logger.error(f"❌ Ошибка проверки RHVoice: {e}")
            return False

    def _list_available_voices(self) -> None:
        """Получение списка доступных голосов"""
        try:
            result = subprocess.run([self.rhvoice_command, "--voices"], capture_output=True, text=True)
            if result.returncode == 0:
                voices = result.stdout
                logger.info(f"📋 Доступные голоса:\n{voices}")

                # Проверяем наличие голоса Елены
                if "elena" in voices.lower() or "елена" in voices.lower():
                    logger.success("🎯 Голос 'Елена' найден!")
                else:
                    logger.warning("⚠️ Голос 'Елена' не найден, будет использован голос по умолчанию")
                    # Пытаемся найти женский голос
                    if "anna" in voices.lower():
                        self.voice_profile = "anna"
                    elif "irina" in voices.lower():
                        self.voice_profile = "irina"
                    elif "natalia" in voices.lower():
                        self.voice_profile = "natalia"
        except Exception as e:
            logger.error(f"❌ Ошибка получения списка голосов: {e}")

    def _start_speaker_thread(self) -> None:
        """Запуск потока для асинхронного воспроизведения"""

        def speaker_worker() -> None:
            while True:
                try:
                    text = self.speech_queue.get()
                    if text is None:  # сигнал остановки
                        self.speech_queue.task_done()
                        break

                    self.is_speaking = True
                    self._speak_sync(text)
                    self.is_speaking = False
                    self.speech_queue.task_done()

                except Exception as e:
                    logger.error(f"❌ Ошибка в потоке речи: {e}")
                    self.is_speaking = False

        self.speaker_thread = threading.Thread(target=speaker_worker, daemon=True)
        self.speaker_thread.start()
        logger.debug("🔊 Поток речи запущен")

    def _speak_sync(self, text: str) -> None:
        """
        Синхронное воспроизведение речи (внутренний метод)
        """
        if not self.rhvoice_available:
            logger.info(f"💬 (без голоса): {text}")
            return

        output_file: str = ""
        # Создаём временный файл с уникальным именем
        with tempfile.NamedTemporaryFile(suffix=".wav", dir=self.temp_dir, delete=False) as tmp_file:
            output_file = tmp_file.name

        try:
            # Команда для синтеза речи
            if self.rhvoice_command == "RHVoice-test":
                cmd = [self.rhvoice_command, "-p", self.voice_profile, "-r", str(self.speed), "-o", output_file]
                # Передаём текст через STDIN (как в твоем оригинале)
                process = subprocess.Popen(
                    cmd, stdin=subprocess.PIPE, stdout=subprocess.DEVNULL, stderr=subprocess.PIPE, text=True
                )
                process.communicate(input=text)

            else:  # rhvoice-client
                cmd = [
                    self.rhvoice_command,
                    "-p",
                    self.voice_profile,
                    "-r",
                    str(self.speed),
                    "-o",
                    output_file,
                    "-i",
                    text,
                ]
                subprocess.run(cmd, check=True, capture_output=True)

            # Проверяем, создан ли файл
            if os.path.exists(output_file) and os.path.getsize(output_file) > 0:
                # Воспроизводим через aplay или paplay (твой оригинальный цикл)
                for player in ["aplay", "paplay", "play"]:
                    if subprocess.run(["which", player], capture_output=True).returncode == 0:
                        subprocess.run([player, "-q", output_file])
                        break
                else:
                    logger.warning("⚠️ Не найден аудиоплеер")

            logger.debug(f"🔊 Сказано: {text[:50]}...")

        except Exception as e:
            logger.error(f"❌ Ошибка синтеза речи: {e}")
            logger.info(f"💬 Текст: {text}")

        finally:
            # Очистка временного файла
            try:
                if output_file and os.path.exists(output_file):
                    os.unlink(output_file)
            except Exception:
                pass

    def speak(self, text: str) -> bool:
        """
        Асинхронное воспроизведение речи

        Args:
            text: текст для произнесения

        Returns:
            bool: True если текст добавлен в очередь
        """
        if not text:
            return False

        # Очищаем текст от лишних символов
        text = text.strip()
        if not text:
            return False

        # Добавляем в очередь
        self.speech_queue.put(text)
        logger.debug(f"📝 Добавлено в очередь речи: {text[:50]}...")
        return True

    def speak_wait(self, text: str) -> None:
        """
        Синхронное воспроизведение речи (ждёт окончания)

        Args:
            text: текст для произнесения
        """
        if not self.rhvoice_available:
            logger.info(f"💬 (без голоса): {text}")
            return

        # Ждём, если сейчас что-то говорится
        while self.is_speaking:
            time.sleep(0.1)

        self._speak_sync(text)

    def wait_until_done(self) -> None:
        """Ожидание окончания всей речи в очереди"""
        self.speech_queue.join()
        while self.is_speaking:
            time.sleep(0.1)

    def stop_speaking(self) -> None:
        """Остановка текущей речи"""
        # Очищаем очередь
        while not self.speech_queue.empty():
            try:
                self.speech_queue.get_nowait()
                self.speech_queue.task_done()
            except Exception:
                pass

        # Останавливаем текущее воспроизведение
        try:
            subprocess.run(["pkill", "-f", "aplay"], capture_output=True)
            subprocess.run(["pkill", "-f", "paplay"], capture_output=True)
        except Exception:
            pass

        self.is_speaking = False
        logger.debug("⏹️ Речь остановлена")

    def test_voice(self) -> None:
        """Тестирование голоса"""
        logger.info("🎤 ТЕСТ ГОЛОСА ЕЛЕНЫ")
        logger.info("=" * 40)

        test_phrases = [
            "Привет! Я Елена, твой голосовой помощник.",
            "Я говорю нежным женским голосом.",
            "Рада тебя слышать и помогать тебе.",
            "Как у тебя дела сегодня?",
        ]

        for phrase in test_phrases:
            self.speak_wait(phrase)
            time.sleep(0.5)

        logger.success("✅ Тест голоса завершён")

    def set_voice_params(
        self, speed: Optional[int] = None, pitch: Optional[int] = None, volume: Optional[int] = None
    ) -> None:
        """Изменение параметров голоса"""
        if speed is not None:
            self.speed = max(30, min(200, speed))
        if pitch is not None:
            self.pitch = max(0, min(100, pitch))
        if volume is not None:
            self.volume = max(0, min(200, volume))

        logger.info(f"⚙️ Параметры голоса: скорость={self.speed}, тон={self.pitch}, громкость={self.volume}")

    def get_available_voices(self) -> str:
        """Получение списка доступных голосов"""
        try:
            result = subprocess.run([self.rhvoice_command, "--voices"], capture_output=True, text=True)
            if result.returncode == 0:
                return result.stdout
        except Exception:
            pass
        return "Список голосов недоступен"

    def cleanup(self) -> None:
        """Очистка ресурсов перед завершением"""
        logger.info("🧹 Очистка голосового движка...")
        self.stop_speaking()
        # Сигнал остановки потока
        self.speech_queue.put(None)
        if self.speaker_thread and self.speaker_thread.is_alive():
            self.speaker_thread.join(timeout=1)
        logger.success("✅ Голосовой движок остановлен")


# Простой класс для быстрого тестирования
class SimpleVoice:
    """Упрощённая версия для тестирования"""

    def __init__(self) -> None:
        print("🎤 Инициализация простого голосового модуля...")
        # Исправлено MyPy: передан конфиг (ошибка 360)
        self.engine = VoiceEngine(config={})

    def speak(self, text: str) -> None:
        self.engine.speak_wait(text)

    def test_voice(self) -> None:
        self.engine.test_voice()


# Если файл запущен напрямую
if __name__ == "__main__":
    import sys

    print("\n" + "=" * 50)
    print("ТЕСТ ГОЛОСОВОГО МОДУЛЯ ЕЛЕНЫ")
    print("=" * 50)

    # Исправлено MyPy: передан конфиг (ошибка 360)
    voice = VoiceEngine(config={})

    if voice.rhvoice_available:
        print("\n📋 Доступные голоса:")
        print(voice.get_available_voices())

        print("\n🔊 Запуск теста голоса:")
        voice.test_voice()

        print("\n📝 Тест асинхронной речи:")
        voice.speak("Я могу говорить асинхронно.")
        voice.speak("Это значит, что я не блокирую программу.")
        voice.speak("Сейчас все эти фразы будут произнесены по очереди.")

        print("⏳ Ожидание окончания речи...")
        voice.wait_until_done()

        print("\n⚙️ Тест изменения параметров:")
        voice.set_voice_params(speed=60)
        voice.speak_wait("Я говорю немного медленнее.")

        voice.set_voice_params(speed=120, pitch=70)
        voice.speak_wait("А теперь быстрее и выше.")

        voice.set_voice_params(speed=85, pitch=50)

    else:
        print("\n❌ RHVoice не найден. Установите: sudo apt install rhvoice")
        voice.speak_wait("Я работаю в текстовом режиме без голоса.")

    voice.cleanup()
    print("\n" + "=" * 50)
    print("✅ Тест завершён")
    print("=" * 50)
