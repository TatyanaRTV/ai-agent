#!/usr/bin/env python3
# Путь: /mnt/ai_data/ai-agent/src/tools/tool_executor.py
"""
Исполнитель инструментов Елены.
Выполняет различные действия: работа с файлами, документами, медиа, скриншотами.
"""

import os
import subprocess
from pathlib import Path
import json
from datetime import datetime
from loguru import logger

# Импорты инструментов
from src.tools.document.parser import DocumentParser
from src.tools.media.video_processor import VideoProcessor
from src.tools.media.audio_processor import AudioProcessor
from src.tools.media.image_processor import ImageProcessor
from src.tools.screenshot.taker import ScreenshotTaker
from src.tools.file_manager.manager import FileManager


class ToolExecutor:
    """
    Исполнитель инструментов - "руки" Елены.
    Выполняет конкретные действия по плану.
    """

    def __init__(self, config):
        """
        Инициализация исполнителя инструментов

        Args:
            config: словарь с конфигурацией
        """
        self.config = config
        self.tools = {}
        self.execution_history = []

        # Создаём необходимые директории
        self._setup_directories()

        # Инициализация всех инструментов
        self._init_tools()

        logger.info("🔧 ToolExecutor инициализирован")

    def _setup_directories(self):
        """Создание необходимых директорий"""
        paths = self.config.get("paths", {})
        data_path = Path(paths.get("data", "/mnt/ai_data/ai-agent/data"))

        # Директории для разных типов файлов
        dirs = [
            data_path / "documents",
            data_path / "videos",
            data_path / "audio",
            data_path / "images",
            data_path / "screenshots",
            data_path / "processed",
            data_path / "temp",
        ]

        for dir_path in dirs:
            dir_path.mkdir(parents=True, exist_ok=True)
            logger.debug(f"📁 Директория готова: {dir_path}")

    def _init_tools(self):
        """Инициализация всех доступных инструментов"""
        try:
            self.tools["document"] = DocumentParser(self.config)
            logger.info("   ✅ DocumentParser загружен")
        except Exception as e:
            logger.warning(f"   ⚠️ DocumentParser не загружен: {e}")

        try:
            self.tools["video"] = VideoProcessor(self.config)
            logger.info("   ✅ VideoProcessor загружен")
        except Exception as e:
            logger.warning(f"   ⚠️ VideoProcessor не загружен: {e}")

        try:
            self.tools["audio"] = AudioProcessor(self.config)
            logger.info("   ✅ AudioProcessor загружен")
        except Exception as e:
            logger.warning(f"   ⚠️ AudioProcessor не загружен: {e}")

        try:
            self.tools["image"] = ImageProcessor(self.config)
            logger.info("   ✅ ImageProcessor загружен")
        except Exception as e:
            logger.warning(f"   ⚠️ ImageProcessor не загружен: {e}")

        try:
            self.tools["screenshot"] = ScreenshotTaker(self.config)
            logger.info("   ✅ ScreenshotTaker загружен")
        except Exception as e:
            logger.warning(f"   ⚠️ ScreenshotTaker не загружен: {e}")

        try:
            self.tools["file_manager"] = FileManager(self.config)
            logger.info("   ✅ FileManager загружен")
        except Exception as e:
            logger.warning(f"   ⚠️ FileManager не загружен: {e}")

    async def execute(self, action: dict) -> dict:
        """
        Выполнение одного действия

        Args:
            action: словарь с описанием действия

        Returns:
            результат выполнения
        """
        action_type = action.get("type", "unknown")
        logger.info(f"🎯 Выполнение действия: {action_type}")

        result = {"success": False, "action": action, "timestamp": str(datetime.now()), "data": None, "error": None}

        try:
            if action_type == "read_document":
                result = await self._read_document(action)

            elif action_type == "process_video":
                result = await self._process_video(action)

            elif action_type == "process_audio":
                result = await self._process_audio(action)

            elif action_type == "process_image":
                result = await self._process_image(action)

            elif action_type == "take_screenshot":
                result = await self._take_screenshot(action)

            elif action_type == "save_file":
                result = await self._save_file(action)

            elif action_type == "delete_file":
                result = await self._delete_file(action)

            elif action_type == "list_files":
                result = await self._list_files(action)

            elif action_type == "execute_command":
                result = await self._execute_command(action)

            else:
                result["error"] = f"Неизвестный тип действия: {action_type}"
                logger.warning(f"⚠️ {result['error']}")

        except Exception as e:
            result["error"] = str(e)
            logger.error(f"❌ Ошибка выполнения {action_type}: {e}")

        # Сохраняем в историю
        self.execution_history.append(result)

        return result

    async def _read_document(self, action):
        """Чтение документа"""
        file_path = action.get("file_path")
        if not file_path:
            return {"success": False, "error": "Не указан путь к файлу"}

        if "document" not in self.tools:
            return {"success": False, "error": "DocumentParser не доступен"}

        content = self.tools["document"].parse(file_path)

        return {"success": True, "data": {"content": content, "file": file_path}}

    async def _process_video(self, action):
        """Обработка видео"""
        file_path = action.get("file_path")
        operation = action.get("operation", "info")

        if not file_path:
            return {"success": False, "error": "Не указан путь к видео"}

        if "video" not in self.tools:
            return {"success": False, "error": "VideoProcessor не доступен"}

        if operation == "info":
            info = self.tools["video"].get_info(file_path)
            return {"success": True, "data": info}

        elif operation == "extract_audio":
            output = self.tools["video"].extract_audio(file_path)
            return {"success": True, "data": {"audio_file": output}}

        return {"success": False, "error": f"Неизвестная операция: {operation}"}

    async def _process_audio(self, action):
        """Обработка аудио"""
        file_path = action.get("file_path")
        operation = action.get("operation", "info")

        if not file_path:
            return {"success": False, "error": "Не указан путь к аудио"}

        if "audio" not in self.tools:
            return {"success": False, "error": "AudioProcessor не доступен"}

        if operation == "info":
            info = self.tools["audio"].get_info(file_path)
            return {"success": True, "data": info}

        elif operation == "transcribe":
            # Используем Whisper для распознавания
            text = self.tools["audio"].transcribe(file_path)
            return {"success": True, "data": {"text": text}}

        return {"success": False, "error": f"Неизвестная операция: {operation}"}

    async def _process_image(self, action):
        """Обработка изображения"""
        file_path = action.get("file_path")
        operation = action.get("operation", "info")

        if not file_path:
            return {"success": False, "error": "Не указан путь к изображению"}

        if "image" not in self.tools:
            return {"success": False, "error": "ImageProcessor не доступен"}

        if operation == "info":
            info = self.tools["image"].get_info(file_path)
            return {"success": True, "data": info}

        elif operation == "resize":
            width = action.get("width")
            height = action.get("height")
            output = self.tools["image"].resize(file_path, width, height)
            return {"success": True, "data": {"output": output}}

        return {"success": False, "error": f"Неизвестная операция: {operation}"}

    async def _take_screenshot(self, action):
        """Создание скриншота"""
        if "screenshot" not in self.tools:
            return {"success": False, "error": "ScreenshotTaker не доступен"}

        monitor = action.get("monitor", 1)
        filename = action.get("filename")

        screenshot_path = self.tools["screenshot"].take(monitor, filename)

        return {"success": True, "data": {"path": screenshot_path, "filename": Path(screenshot_path).name}}

    async def _save_file(self, action):
        """Сохранение файла"""
        if "file_manager" not in self.tools:
            return {"success": False, "error": "FileManager не доступен"}

        content = action.get("content")
        filename = action.get("filename")
        directory = action.get("directory", "documents")

        file_path = self.tools["file_manager"].save(content, filename, directory)

        return {"success": True, "data": {"path": str(file_path), "filename": file_path.name}}

    async def _delete_file(self, action):
        """Удаление файла"""
        if "file_manager" not in self.tools:
            return {"success": False, "error": "FileManager не доступен"}

        file_path = action.get("file_path")

        success = self.tools["file_manager"].delete(file_path)

        return {"success": success, "data": {"deleted": file_path}}

    async def _list_files(self, action):
        """Список файлов в директории"""
        if "file_manager" not in self.tools:
            return {"success": False, "error": "FileManager не доступен"}

        directory = action.get("directory", "documents")
        pattern = action.get("pattern", "*")

        files = self.tools["file_manager"].list_files(directory, pattern)

        return {"success": True, "data": {"directory": directory, "files": files, "count": len(files)}}

    async def _execute_command(self, action):
        """Выполнение системной команды (с осторожностью!)"""
        command = action.get("command")
        if not command:
            return {"success": False, "error": "Не указана команда"}

        # Проверка на опасные команды
        dangerous = ["rm -rf", "sudo", "mkfs", "dd", "> /dev/sda"]
        for danger in dangerous:
            if danger in command:
                return {"success": False, "error": f"Команда содержит опасную операцию: {danger}"}

        try:
            result = subprocess.run(command, shell=True, capture_output=True, text=True, timeout=30)

            return {
                "success": result.returncode == 0,
                "data": {"stdout": result.stdout, "stderr": result.stderr, "returncode": result.returncode},
            }
        except subprocess.TimeoutExpired:
            return {"success": False, "error": "Команда превысила время ожидания"}
        except Exception as e:
            return {"success": False, "error": str(e)}

    def get_history(self, limit: int = 10) -> list:
        """Получение истории выполнения"""
        return self.execution_history[-limit:]

    def get_available_tools(self):
        """Список доступных инструментов"""
        return list(self.tools.keys())
