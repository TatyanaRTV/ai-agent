#!/usr/bin/env python3
# Путь: /mnt/ai_data/ai-agent/src/tools/file_manager/manager.py
"""Управление файлами и директориями"""

import os
import shutil
from pathlib import Path
from datetime import datetime
from loguru import logger


class FileManager:
    """Менеджер файлов"""

    def __init__(self, config):
        self.config = config
        self.data_dir = Path(config["paths"]["data"])
        logger.info("📁 FileManager инициализирован")

    def save(self, content, filename, directory="documents"):
        """
        Сохранение содержимого в файл

        Args:
            content: содержимое для сохранения
            filename: имя файла
            directory: поддиректория в data/

        Returns:
            путь к сохранённому файлу или None при ошибке
        """
        try:
            save_dir = self.data_dir / directory
            save_dir.mkdir(parents=True, exist_ok=True)

            file_path = save_dir / filename

            # Если файл существует, добавляем timestamp
            if file_path.exists():
                stem = file_path.stem
                suffix = file_path.suffix
                timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                file_path = save_dir / f"{stem}_{timestamp}{suffix}"

            with open(file_path, "w", encoding="utf-8") as f:
                f.write(content)

            logger.info(f"💾 Файл сохранён: {file_path}")
            return str(file_path)

        except Exception as e:
            logger.error(f"❌ Ошибка сохранения файла: {e}")
            return None

    def delete(self, file_path):
        """Удаление файла"""
        try:
            path = Path(file_path)
            if path.exists() and path.is_file():
                path.unlink()
                logger.info(f"🗑️ Файл удалён: {file_path}")
                return True
            return False
        except Exception as e:
            logger.error(f"❌ Ошибка удаления файла: {e}")
            return False

    def list_files(self, directory="documents", pattern="*"):
        """Список файлов в директории"""
        try:
            search_dir = self.data_dir / directory
            if not search_dir.exists():
                return []

            files = []
            for file_path in search_dir.glob(pattern):
                if file_path.is_file():
                    stat = file_path.stat()
                    files.append(
                        {
                            "name": file_path.name,
                            "path": str(file_path),
                            "size": stat.st_size,
                            "modified": datetime.fromtimestamp(stat.st_mtime).isoformat(),
                        }
                    )

            return files

        except Exception as e:
            logger.error(f"❌ Ошибка получения списка файлов: {e}")
            return []

    def copy(self, source, destination):
        """Копирование файла"""
        try:
            shutil.copy2(source, destination)
            logger.info(f"📋 Файл скопирован: {source} -> {destination}")
            return destination
        except Exception as e:
            logger.error(f"❌ Ошибка копирования файла: {e}")
            return None

    def move(self, source, destination):
        """Перемещение файла"""
        try:
            shutil.move(source, destination)
            logger.info(f"📦 Файл перемещён: {source} -> {destination}")
            return destination
        except Exception as e:
            logger.error(f"❌ Ошибка перемещения файла: {e}")
            return None

    def file_exists(self, file_path):
        """Проверка существования файла"""
        return Path(file_path).exists()

    def get_file_size(self, file_path):
        """Получение размера файла в байтах"""
        try:
            return Path(file_path).stat().st_size
        except Exception as e:
            logger.error(f"❌ Ошибка получения размера файла: {e}")
            return 0
