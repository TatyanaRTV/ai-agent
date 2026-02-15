#!/usr/bin/env python3
# Путь: /mnt/ai_data/ai-agent/src/learning/cleanup.py
"""Автоматическая очистка временных файлов и устаревших данных"""

from pathlib import Path
import time
import shutil
import gc
from loguru import logger

class CleanupManager:
    """Менеджер автоматической очистки"""
    
    def __init__(self, config):
        self.config = config
        self.temp_dir = Path(config['paths']['data']) / 'temp'
        self.cache_dir = Path(config['paths']['data']) / 'cache'
        self.logs_dir = Path(config['paths']['logs'])
        
        # Настройки очистки
        self.temp_max_age = config.get('cleanup', {}).get('temp_max_age', 86400)  # 24 часа
        self.cache_max_age = config.get('cleanup', {}).get('cache_max_age', 604800)  # 7 дней
        self.log_max_age = config.get('cleanup', {}).get('log_max_age', 2592000)  # 30 дней
        
        # Создаём директории, если их нет
        self.temp_dir.mkdir(parents=True, exist_ok=True)
        self.cache_dir.mkdir(parents=True, exist_ok=True)
        self.logs_dir.mkdir(parents=True, exist_ok=True)
        
        logger.info("🧹 CleanupManager инициализирован")
    
    def cleanup_now(self):
        """Немедленная очистка всех временных файлов"""
        try:
            logger.info("🧹 Запуск очистки...")
            
            cleaned = 0
            freed_space = 0
            
            # Очистка временной директории
            cleaned_temp, freed_temp = self._clean_directory(
                self.temp_dir, 
                self.temp_max_age,
                "временных файлов"
            )
            cleaned += cleaned_temp
            freed_space += freed_temp
            
            # Очистка кэша
            cleaned_cache, freed_cache = self._clean_directory(
                self.cache_dir,
                self.cache_max_age,
                "кэша"
            )
            cleaned += cleaned_cache
            freed_space += freed_cache
            
            # Очистка старых логов
            cleaned_logs, freed_logs = self._clean_logs()
            cleaned += cleaned_logs
            freed_space += freed_logs
            
            # Запускаем сборщик мусора Python
            gc.collect()
            
            if cleaned > 0:
                logger.success(
                    f"✅ Очищено {cleaned} файлов, "
                    f"освобождено {freed_space / (1024*1024):.1f} MB"
                )
            else:
                logger.info("✨ Ничего не требуется очищать")
                
        except Exception as e:
            logger.error(f"❌ Ошибка при очистке: {e}")
    
    def _clean_directory(self, directory: Path, max_age: int, name: str):
        """
        Очистка директории от старых файлов
        
        Returns:
            (количество удалённых файлов, освобождённое место в байтах)
        """
        if not directory.exists():
            return 0, 0
        
        now = time.time()
        cleaned = 0
        freed = 0
        
        try:
            for item in directory.glob("*"):
                if item.is_file():
                    # Проверяем возраст файла
                    age = now - item.stat().st_mtime
                    if age > max_age:
                        size = item.stat().st_size
                        item.unlink()
                        cleaned += 1
                        freed += size
                        logger.debug(f"   Удалён {name}: {item.name} (возраст: {age/3600:.1f} ч)")
            
            # Удаляем пустые поддиректории
            for item in directory.glob("*"):
                if item.is_dir() and not any(item.iterdir()):
                    item.rmdir()
                    logger.debug(f"   Удалена пустая папка: {item.name}")
                    
        except Exception as e:
            logger.error(f"❌ Ошибка при очистке {directory}: {e}")
        
        return cleaned, freed
    
    def _clean_logs(self):
        """Специальная очистка лог-файлов с ротацией"""
        if not self.logs_dir.exists():
            return 0, 0
        
        cleaned = 0
        freed = 0
        now = time.time()
        
        try:
            for log_file in self.logs_dir.glob("*.log*"):
                if log_file.is_file():
                    # Удаляем логи старше log_max_age
                    age = now - log_file.stat().st_mtime
                    if age > self.log_max_age:
                        size = log_file.stat().st_size
                        log_file.unlink()
                        cleaned += 1
                        freed += size
                        logger.debug(f"   Удалён старый лог: {log_file.name}")
        except Exception as e:
            logger.error(f"❌ Ошибка при очистке логов: {e}")
        
        return cleaned, freed
    
    def schedule_cleanup(self, hours=24):
        """
        Запланировать периодическую очистку
        
        Args:
            hours: интервал в часах
        """
        import threading
        
        def cleanup_loop():
            while True:
                time.sleep(hours * 3600)
                self.cleanup_now()
        
        thread = threading.Thread(target=cleanup_loop, daemon=True)
        thread.start()
        logger.info(f"⏰ Запланирована очистка каждые {hours} часов")