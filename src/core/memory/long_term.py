"""
Долговременная память агента
"""

import logging
import json
import pickle
from typing import Dict, Any, List, Optional
from datetime import datetime, timedelta
import os

logger = logging.getLogger(__name__)

class LongTermMemory:
    """Долговременная память с сохранением на диск"""
    
    def __init__(self, storage_path: str = "./data/memory"):
        self.storage_path = storage_path
        self.memory_index = {}
        self.memory_data = {}
        
        # Создание директории, если не существует
        os.makedirs(storage_path, exist_ok=True)
        
        # Загрузка существующей памяти
        self._load_memory()
        
    def store(self, category: str, key: str, value: Any, metadata: Dict[str, Any] = None) -> str:
        """Сохранение значения в долговременную память"""
        if metadata is None:
            metadata = {}
            
        entry_id = f"{category}_{key}"
        
        entry = {
            "id": entry_id,
            "category": category,
            "key": key,
            "value": value,
            "metadata": metadata,
            "created_at": datetime.now().isoformat(),
            "updated_at": datetime.now().isoformat(),
            "access_count": 0,
            "importance": metadata.get("importance", 0.5)
        }
        
        # Сохранение в памяти
        self.memory_data[entry_id] = entry
        self._update_index(entry_id, entry)
        
        # Автосохранение на диск
        self._save_entry(entry)
        
        logger.info(f"Сохранено в долговременную память: {entry_id}")
        return entry_id
        
    def retrieve(self, entry_id: str) -> Optional[Dict[str, Any]]:
        """Извлечение значения из долговременной памяти"""
        if entry_id not in self.memory_data:
            # Попытка загрузки с диска
            entry = self._load_entry(entry_id)
            if not entry:
                return None
            self.memory_data[entry_id] = entry
            
        entry = self.memory_data[entry_id]
        
        # Обновление статистики доступа
        entry["access_count"] += 1
        entry["updated_at"] = datetime.now().isoformat()
        
        # Обновление на диске
        self._save_entry(entry)
        
        return {
            "id": entry["id"],
            "value": entry["value"],
            "metadata": entry["metadata"],
            "access_count": entry["access_count"],
            "created_at": entry["created_at"],
            "updated_at": entry["updated_at"]
        }
        
    def search(self, query: str = None, category: str = None, limit: int = 10) -> List[Dict[str, Any]]:
        """Поиск в долговременной памяти"""
        results = []
        
        for entry_id, entry in self.memory_data.items():
            # Фильтрация по категории
            if category and entry["category"] != category:
                continue
                
            # Фильтрация по запросу
            if query:
                entry_text = str(entry["value"]).lower() + str(entry["metadata"]).lower()
                if query.lower() not in entry_text:
                    continue
                    
            results.append({
                "id": entry_id,
                "category": entry["category"],
                "value": entry["value"],
                "metadata": entry["metadata"],
                "access_count": entry["access_count"],
                "created_at": entry["created_at"]
            })
            
            if len(results) >= limit:
                break
                
        # Сортировка по дате создания (сначала новые)
        results.sort(key=lambda x: x["created_at"], reverse=True)
        
        return results[:limit]
        
    def update(self, entry_id: str, value: Any = None, metadata: Dict[str, Any] = None):
        """Обновление записи в долговременной памяти"""
        if entry_id not in self.memory_data:
            raise KeyError(f"Запись не найдена: {entry_id}")
            
        entry = self.memory_data[entry_id]
        
        if value is not None:
            entry["value"] = value
            
        if metadata is not None:
            entry["metadata"].update(metadata)
            
        entry["updated_at"] = datetime.now().isoformat()
        
        # Сохранение на диск
        self._save_entry(entry)
        
    def delete(self, entry_id: str) -> bool:
        """Удаление записи из долговременной памяти"""
        if entry_id in self.memory_data:
            del self.memory_data[entry_id]
            
            # Удаление с диска
            self._delete_entry(entry_id)
            
            # Удаление из индекса
            self._remove_from_index(entry_id)
            
            return True
            
        return False
        
    def get_categories(self) -> List[str]:
        """Получение списка категорий"""
        categories = set()
        
        for entry in self.memory_data.values():
            categories.add(entry["category"])
            
        return sorted(list(categories))
        
    def get_stats(self) -> Dict[str, Any]:
        """Получение статистики долговременной памяти"""
        total_entries = len(self.memory_data)
        
        # Подсчет по категориям
        category_counts = {}
        total_accesses = 0
        total_importance = 0
        
        for entry in self.memory_data.values():
            category = entry["category"]
            category_counts[category] = category_counts.get(category, 0) + 1
            total_accesses += entry["access_count"]
            total_importance += entry["importance"]
            
        avg_accesses = total_accesses / total_entries if total_entries > 0 else 0
        avg_importance = total_importance / total_entries if total_entries > 0 else 0
        
        # Размер на диске
        disk_size = self._get_disk_size()
        
        return {
            "total_entries": total_entries,
            "categories": len(category_counts),
            "category_counts": category_counts,
            "avg_access_count": avg_accesses,
            "avg_importance": avg_importance,
            "disk_size_mb": disk_size,
            "storage_path": self.storage_path
        }
        
    def cleanup(self, older_than_days: int = 90, min_importance: float = 0.1):
        """Очистка старых и неважных записей"""
        cutoff_date = datetime.now() - timedelta(days=older_than_days)
        deleted_count = 0
        
        entries_to_delete = []
        
        for entry_id, entry in self.memory_data.items():
            created_at = datetime.fromisoformat(entry["created_at"])
            
            # Критерии удаления
            too_old = created_at < cutoff_date
            too_unimportant = entry["importance"] < min_importance
            never_accessed = entry["access_count"] == 0
            
            if too_old or (too_unimportant and never_accessed):
                entries_to_delete.append(entry_id)
                
        for entry_id in entries_to_delete:
            self.delete(entry_id)
            deleted_count += 1
            
        logger.info(f"Очищено записей из долговременной памяти: {deleted_count}")
        
    def backup(self, backup_path: str = None):
        """Создание резервной копии памяти"""
        if backup_path is None:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            backup_path = f"{self.storage_path}/backup_{timestamp}"
            
        os.makedirs(backup_path, exist_ok=True)
        
        # Копирование всех файлов памяти
        import shutil
        for filename in os.listdir(self.storage_path):
            if filename.endswith(".json") or filename.endswith(".pkl"):
                src = os.path.join(self.storage_path, filename)
                dst = os.path.join(backup_path, filename)
                shutil.copy2(src, dst)
                
        # Сохранение метаданных бэкапа
        backup_info = {
            "timestamp": datetime.now().isoformat(),
            "total_entries": len(self.memory_data),
            "storage_path": self.storage_path
        }
        
        with open(os.path.join(backup_path, "backup_info.json"), "w", encoding="utf-8") as f:
            json.dump(backup_info, f, ensure_ascii=False, indent=2)
            
        logger.info(f"Создана резервная копия долговременной памяти: {backup_path}")
        
    def _update_index(self, entry_id: str, entry: Dict[str, Any]):
        """Обновление поискового индекса"""
        # Простой индекс по категориям
        category = entry["category"]
        
        if category not in self.memory_index:
            self.memory_index[category] = []
            
        if entry_id not in self.memory_index[category]:
            self.memory_index[category].append(entry_id)
            
    def _remove_from_index(self, entry_id: str):
        """Удаление из поискового индекса"""
        for category, entries in self.memory_index.items():
            if entry_id in entries:
                entries.remove(entry_id)
                
        # Удаление пустых категорий
        empty_categories = [cat for cat, entries in self.memory_index.items() if not entries]
        for category in empty_categories:
            del self.memory_index[category]
            
    def _save_entry(self, entry: Dict[str, Any]):
        """Сохранение записи на диск"""
        entry_id = entry["id"]
        filepath = os.path.join(self.storage_path, f"{entry_id}.json")
        
        try:
            with open(filepath, "w", encoding="utf-8") as f:
                json.dump(entry, f, ensure_ascii=False, indent=2)
        except Exception as e:
            logger.error(f"Ошибка сохранения записи {entry_id}: {e}")
            
    def _load_entry(self, entry_id: str) -> Optional[Dict[str, Any]]:
        """Загрузка записи с диска"""
        filepath = os.path.join(self.storage_path, f"{entry_id}.json")
        
        if not os.path.exists(filepath):
            return None
            
        try:
            with open(filepath, "r", encoding="utf-8") as f:
                return json.load(f)
        except Exception as e:
            logger.error(f"Ошибка загрузки записи {entry_id}: {e}")
            return None
            
    def _delete_entry(self, entry_id: str):
        """Удаление файла записи с диска"""
        filepath = os.path.join(self.storage_path, f"{entry_id}.json")
        
        if os.path.exists(filepath):
            try:
                os.remove(filepath)
            except Exception as e:
                logger.error(f"Ошибка удаления файла записи {entry_id}: {e}")
                
    def _load_memory(self):
        """Загрузка памяти с диска"""
        logger.info(f"Загрузка долговременной памяти из {self.storage_path}")
        
        loaded_count = 0
        
        for filename in os.listdir(self.storage_path):
            if filename.endswith(".json"):
                entry_id = filename[:-5]  # Удаляем .json
                
                try:
                    entry = self._load_entry(entry_id)
                    if entry:
                        self.memory_data[entry_id] = entry
                        self._update_index(entry_id, entry)
                        loaded_count += 1
                except Exception as e:
                    logger.error(f"Ошибка загрузки {filename}: {e}")
                    
        logger.info(f"Загружено записей: {loaded_count}")
        
    def _get_disk_size(self) -> float:
        """Получение размера памяти на диске в мегабайтах"""
        total_size = 0
        
        for filename in os.listdir(self.storage_path):
            filepath = os.path.join(self.storage_path, filename)
            if os.path.isfile(filepath):
                total_size += os.path.getsize(filepath)
                
        return total_size / (1024 * 1024)  # Конвертация в MB