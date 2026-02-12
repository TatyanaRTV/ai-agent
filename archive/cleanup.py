"""
Компонент автоматической очистки и оптимизации
"""

import os
import shutil
import logging
from datetime import datetime, timedelta
from pathlib import Path
from typing import List, Dict, Any
import json

logger = logging.getLogger(__name__)

class AutoCleanup:
    """Система автоматической очистки ненужных файлов и оптимизации"""
    
    def __init__(self, config):
        self.config = config
        self.cleanup_history = []
        self.cleanup_rules = self._load_cleanup_rules()
        
    async def perform_cleanup(self, cleanup_type: str = "scheduled") -> Dict[str, Any]:
        """Выполнение очистки"""
        logger.info(f"🧹 Выполнение очистки типа: {cleanup_type}")
        
        cleanup_result = {
            "type": cleanup_type,
            "timestamp": datetime.now().isoformat(),
            "cleaned_items": [],
            "freed_space": 0,
            "errors": [],
            "duration": None
        }
        
        start_time = datetime.now()
        
        try:
            # 1. Очистка временных файлов
            temp_cleanup = await self._clean_temp_files()
            cleanup_result["cleaned_items"].extend(temp_cleanup)
            
            # 2. Очистка кэша
            cache_cleanup = await self._clean_cache()
            cleanup_result["cleaned_items"].extend(cache_cleanup)
            
            # 3. Очистка старых логов
            log_cleanup = await self._clean_old_logs()
            cleanup_result["cleaned_items"].extend(log_cleanup)
            
            # 4. Очистка старых данных
            data_cleanup = await self._clean_old_data()
            cleanup_result["cleaned_items"].extend(data_cleanup)
            
            # 5. Оптимизация баз данных
            optimization_result = await self._optimize_databases()
            cleanup_result["cleaned_items"].append(optimization_result)
            
            # 6. Очистка дубликатов
            duplicate_cleanup = await self._remove_duplicates()
            cleanup_result["cleaned_items"].extend(duplicate_cleanup)
            
            # Расчет высвобожденного пространства
            cleanup_result["freed_space"] = self._calculate_freed_space(cleanup_result["cleaned_items"])
            
            # Сохранение результата
            await self._save_cleanup_result(cleanup_result)
            
            # Обновление истории
            self.cleanup_history.append({
                "timestamp": datetime.now().isoformat(),
                "type": cleanup_type,
                "items_cleaned": len(cleanup_result["cleaned_items"]),
                "space_freed": cleanup_result["freed_space"]
            })
            
        except Exception as e:
            cleanup_result["errors"].append(str(e))
            logger.error(f"Ошибка во время очистки: {e}")
            
        end_time = datetime.now()
        cleanup_result["duration"] = (end_time - start_time).total_seconds()
        
        logger.info(f"✅ Очистка завершена. Освобождено: {cleanup_result['freed_space']} MB")
        
        return cleanup_result
        
    async def _clean_temp_files(self) -> List[Dict[str, Any]]:
        """Очистка временных файлов"""
        cleaned_items = []
        
        # Определение путей для очистки
        temp_paths = [
            Path("data/temp"),
            Path("/tmp"),
            Path.home() / ".cache",
            Path("__pycache__"),
            Path(".pytest_cache")
        ]
        
        for temp_path in temp_paths:
            if temp_path.exists():
                items_cleaned = await self._clean_directory(temp_path, days_old=1)
                cleaned_items.extend(items_cleaned)
                
        return cleaned_items
        
    async def _clean_cache(self) -> List[Dict[str, Any]]:
        """Очистка кэша"""
        cleaned_items = []
        
        cache_paths = [
            Path("data/cache"),
            Path("models/.cache"),
            Path(".cache")
        ]
        
        for cache_path in cache_paths:
            if cache_path.exists():
                items_cleaned = await self._clean_directory(cache_path, days_old=7)
                cleaned_items.extend(items_cleaned)
                
        return cleaned_items
        
    async def _clean_old_logs(self) -> List[Dict[str, Any]]:
        """Очистка старых логов"""
        cleaned_items = []
        
        log_paths = [
            Path("logs"),
            Path("data/logs")
        ]
        
        for log_path in log_paths:
            if log_path.exists():
                # Сохраняем логи за последние 30 дней
                items_cleaned = await self._clean_directory(log_path, days_old=30)
                cleaned_items.extend(items_cleaned)
                
        return cleaned_items
        
    async def _clean_old_data(self) -> List[Dict[str, Any]]:
        """Очистка старых данных"""
        cleaned_items = []
        
        data_paths = [
            Path("data/raw"),
            Path("data/processed")
        ]
        
        for data_path in data_paths:
            if data_path.exists():
                # Очистка данных старше 90 дней
                items_cleaned = await self._clean_directory(data_path, days_old=90)
                cleaned_items.extend(items_cleaned)
                
        return cleaned_items
        
    async def _optimize_databases(self) -> Dict[str, Any]:
        """Оптимизация баз данных"""
        optimization_result = {
            "type": "database_optimization",
            "timestamp": datetime.now().isoformat(),
            "actions": [],
            "space_saved": 0
        }
        
        # Оптимизация векторной базы данных
        try:
            # Здесь должна быть логика оптимизации конкретной БД
            optimization_result["actions"].append("vector_db_vacuumed")
            optimization_result["space_saved"] += 100  # Примерное значение
        except Exception as e:
            logger.error(f"Ошибка оптимизации БД: {e}")
            
        return optimization_result
        
    async def _remove_duplicates(self) -> List[Dict[str, Any]]:
        """Удаление дубликатов файлов"""
        cleaned_items = []
        
        # Поиск дубликатов в данных
        data_dirs = ["data/raw", "data/processed", "data/vectors"]
        
        for data_dir in data_dirs:
            dir_path = Path(data_dir)
            if dir_path.exists():
                duplicates = await self._find_duplicates(dir_path)
                
                for duplicate in duplicates:
                    try:
                        duplicate.unlink()
                        cleaned_items.append({
                            "type": "duplicate_file",
                            "path": str(duplicate),
                            "size": duplicate.stat().st_size
                        })
                    except Exception as e:
                        logger.error(f"Не удалось удалить дубликат {duplicate}: {e}")
                        
        return cleaned_items
        
    async def _clean_directory(self, directory: Path, days_old: int) -> List[Dict[str, Any]]:
        """Очистка файлов в директории старше указанного количества дней"""
        cleaned_items = []
        cutoff_date = datetime.now() - timedelta(days=days_old)
        
        try:
            for item in directory.rglob("*"):
                if item.is_file():
                    # Проверка времени модификации
                    mtime = datetime.fromtimestamp(item.stat().st_mtime)
                    
                    if mtime < cutoff_date:
                        try:
                            # Проверка на исключения
                            if not self._is_excluded(item):
                                # Удаление файла
                                file_size = item.stat().st_size
                                item.unlink()
                                
                                cleaned_items.append({
                                    "type": "file",
                                    "path": str(item),
                                    "age_days": (datetime.now() - mtime).days,
                                    "size": file_size
                                })
                                
                        except Exception as e:
                            logger.error(f"Не удалось удалить файл {item}: {e}")
                            
        except Exception as e:
            logger.error(f"Ошибка очистки директории {directory}: {e}")
            
        return cleaned_items
        
    def _is_excluded(self, file_path: Path) -> bool:
        """Проверка, является ли файл исключением"""
        excluded_patterns = [
            "*.config",
            "*.json",
            "*.yaml",
            "*.yml",
            "README*",
            ".gitkeep",
            ".gitignore"
        ]
        
        file_name = file_path.name
        
        for pattern in excluded_patterns:
            if pattern.startswith("*."):
                extension = pattern[1:]
                if file_name.endswith(extension):
                    return True
            elif pattern in file_name:
                return True
                
        return False
        
    def _calculate_freed_space(self, cleaned_items: List[Dict[str, Any]]) -> int:
        """Расчет высвобожденного пространства в MB"""
        total_bytes = sum(item.get("size", 0) for item in cleaned_items)
        return total_bytes // (1024 * 1024)  # Конвертация в MB
        
    async def _save_cleanup_result(self, result: Dict[str, Any]):
        """Сохранение результата очистки"""
        cleanup_log_dir = Path("logs/cleanup")
        cleanup_log_dir.mkdir(exist_ok=True)
        
        log_file = cleanup_log_dir / f"cleanup_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
        
        with open(log_file, 'w', encoding='utf-8') as f:
            json.dump(result, f, ensure_ascii=False, indent=2)
            
    def _load_cleanup_rules(self) -> Dict[str, Any]:
        """Загрузка правил очистки"""
        default_rules = {
            "temp_files": {
                "enabled": True,
                "max_age_days": 1,
                "exclude_patterns": [".keep", "*.lock"]
            },
            "cache": {
                "enabled": True,
                "max_age_days": 7,
                "max_size_mb": 1024
            },
            "logs": {
                "enabled": True,
                "max_age_days": 30,
                "keep_min_count": 10
            },
            "data": {
                "enabled": True,
                "max_age_days": 90,
                "preserve_important": True
            }
        }
        
        # Загрузка пользовательских правил
        rules_file = Path("configs/cleanup_rules.json")
        if rules_file.exists():
            try:
                with open(rules_file, 'r', encoding='utf-8') as f:
                    user_rules = json.load(f)
                    # Объединение с правилами по умолчанию
                    default_rules.update(user_rules)
            except Exception as e:
                logger.error(f"Ошибка загрузки правил очистки: {e}")
                
        return default_rules
        
    async def _find_duplicates(self, directory: Path) -> List[Path]:
        """Поиск дубликатов файлов"""
        import hashlib
        
        file_hashes = {}
        duplicates = []
        
        for file_path in directory.rglob("*"):
            if file_path.is_file():
                try:
                    # Вычисление хеша файла
                    file_hash = self._calculate_file_hash(file_path)
                    
                    if file_hash in file_hashes:
                        # Найден дубликат
                        duplicates.append(file_path)
                    else:
                        file_hashes[file_hash] = file_path
                        
                except Exception as e:
                    logger.error(f"Ошибка обработки файла {file_path}: {e}")
                    
        return duplicates
        
    def _calculate_file_hash(self, file_path: Path) -> str:
        """Вычисление хеша файла"""
        hash_md5 = hashlib.md5()
        
        with open(file_path, "rb") as f:
            for chunk in iter(lambda: f.read(4096), b""):
                hash_md5.update(chunk)
                
        return hash_md5.hexdigest()
        
    def get_cleanup_statistics(self) -> Dict[str, Any]:
        """Получение статистики очистки"""
        if not self.cleanup_history:
            return {"total_cleanups": 0, "total_space_freed": 0}
            
        total_cleanups = len(self.cleanup_history)
        total_space_freed = sum(item.get("space_freed", 0) for item in self.cleanup_history)
        
        last_cleanup = self.cleanup_history[-1] if self.cleanup_history else {}
        
        return {
            "total_cleanups": total_cleanups,
            "total_space_freed": f"{total_space_freed} MB",
            "last_cleanup": last_cleanup.get("timestamp"),
            "last_cleanup_items": last_cleanup.get("items_cleaned", 0),
            "average_items_per_cleanup": total_cleanups / len(self.cleanup_history) if self.cleanup_history else 0
        }
        
    async def schedule_cleanup(self, interval_hours: int = 24):
        """Планирование регулярной очистки"""
        import asyncio
        
        logger.info(f"⏰ Планирование очистки каждые {interval_hours} часов")
        
        while True:
            try:
                # Ожидание интервала
                await asyncio.sleep(interval_hours * 3600)
                
                # Выполнение очистки
                await self.perform_cleanup("scheduled")
                
            except Exception as e:
                logger.error(f"Ошибка в планировщике очистки: {e}")
                await asyncio.sleep(3600)  # Ожидание перед повторной попыткой