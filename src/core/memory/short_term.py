"""
Кратковременная память агента
"""

import logging
from typing import Dict, Any, List, Optional
from datetime import datetime, timedelta
from collections import OrderedDict

logger = logging.getLogger(__name__)

class ShortTermMemory:
    """Кратковременная память с ограниченной емкостью"""
    
    def __init__(self, capacity: int = 100, ttl_seconds: int = 3600):
        self.capacity = capacity
        self.ttl_seconds = ttl_seconds
        self.memory = OrderedDict()
        self.access_counter = 0
        
    def store(self, key: str, value: Any, metadata: Dict[str, Any] = None) -> str:
        """Сохранение значения в кратковременную память"""
        if metadata is None:
            metadata = {}
            
        entry = {
            "value": value,
            "metadata": metadata,
            "timestamp": datetime.now().isoformat(),
            "access_count": 0,
            "last_accessed": datetime.now().isoformat(),
            "importance": metadata.get("importance", 0.5)
        }
        
        # Если достигнута емкость, удаляем самые старые/менее важные записи
        if len(self.memory) >= self.capacity:
            self._evict_oldest()
            
        self.memory[key] = entry
        logger.debug(f"Сохранено в кратковременную память: {key}")
        
        return key
        
    def retrieve(self, key: str) -> Optional[Dict[str, Any]]:
        """Извлечение значения из кратковременной памяти"""
        if key not in self.memory:
            return None
            
        entry = self.memory[key]
        
        # Проверка срока годности
        if self._is_expired(entry):
            self.memory.pop(key)
            return None
            
        # Обновление статистики доступа
        entry["access_count"] += 1
        entry["last_accessed"] = datetime.now().isoformat()
        
        # Перемещение в конец (как недавно использованное)
        self.memory.move_to_end(key)
        
        return {
            "value": entry["value"],
            "metadata": entry["metadata"],
            "access_count": entry["access_count"],
            "age_seconds": self._get_age_seconds(entry)
        }
        
    def search(self, query: str = None, limit: int = 10) -> List[Dict[str, Any]]:
        """Поиск в кратковременной памяти"""
        results = []
        
        for key, entry in reversed(self.memory.items()):  # Сначала новые
            if self._is_expired(entry):
                continue
                
            if query:
                # Простой поиск по тексту
                entry_text = str(entry["value"]).lower() + str(entry["metadata"]).lower()
                if query.lower() not in entry_text:
                    continue
                    
            results.append({
                "key": key,
                "value": entry["value"],
                "metadata": entry["metadata"],
                "age_seconds": self._get_age_seconds(entry),
                "access_count": entry["access_count"]
            })
            
            if len(results) >= limit:
                break
                
        return results
        
    def update(self, key: str, value: Any = None, metadata: Dict[str, Any] = None):
        """Обновление записи в кратковременной памяти"""
        if key not in self.memory:
            raise KeyError(f"Запись не найдена: {key}")
            
        entry = self.memory[key]
        
        if value is not None:
            entry["value"] = value
            
        if metadata is not None:
            entry["metadata"].update(metadata)
            
        entry["timestamp"] = datetime.now().isoformat()
        self.memory.move_to_end(key)
        
    def delete(self, key: str) -> bool:
        """Удаление записи из кратковременной памяти"""
        if key in self.memory:
            del self.memory[key]
            return True
        return False
        
    def cleanup(self):
        """Очистка просроченных записей"""
        expired_keys = []
        
        for key, entry in self.memory.items():
            if self._is_expired(entry):
                expired_keys.append(key)
                
        for key in expired_keys:
            del self.memory[key]
            
        if expired_keys:
            logger.debug(f"Очищено просроченных записей: {len(expired_keys)}")
            
    def get_stats(self) -> Dict[str, Any]:
        """Получение статистики кратковременной памяти"""
        total_size = len(self.memory)
        
        # Расчет средней важности и количества обращений
        total_importance = 0
        total_accesses = 0
        
        for entry in self.memory.values():
            total_importance += entry["importance"]
            total_accesses += entry["access_count"]
            
        avg_importance = total_importance / total_size if total_size > 0 else 0
        avg_accesses = total_accesses / total_size if total_size > 0 else 0
        
        # Подсчет просроченных записей
        expired_count = sum(1 for entry in self.memory.values() if self._is_expired(entry))
        
        return {
            "total_entries": total_size,
            "capacity": self.capacity,
            "usage_percent": (total_size / self.capacity) * 100 if self.capacity > 0 else 0,
            "avg_importance": avg_importance,
            "avg_access_count": avg_accesses,
            "expired_entries": expired_count,
            "ttl_seconds": self.ttl_seconds
        }
        
    def _is_expired(self, entry: Dict[str, Any]) -> bool:
        """Проверка, истек ли срок записи"""
        timestamp = datetime.fromisoformat(entry["timestamp"])
        age_seconds = (datetime.now() - timestamp).total_seconds()
        
        return age_seconds > self.ttl_seconds
        
    def _get_age_seconds(self, entry: Dict[str, Any]) -> float:
        """Получение возраста записи в секундах"""
        timestamp = datetime.fromisoformat(entry["timestamp"])
        return (datetime.now() - timestamp).total_seconds()
        
    def _evict_oldest(self):
        """Удаление самых старых/менее важных записей"""
        if not self.memory:
            return
            
        # Находим запись с наименьшей важностью и наибольшим возрастом
        worst_key = None
        worst_score = float('inf')
        
        for key, entry in self.memory.items():
            # Оценка записи: чем меньше важность и больше возраст, тем хуже
            age_seconds = self._get_age_seconds(entry)
            score = (1 - entry["importance"]) * age_seconds
            
            if score < worst_score:
                worst_score = score
                worst_key = key
                
        if worst_key:
            del self.memory[worst_key]
            logger.debug(f"Удалена запись из кратковременной памяти: {worst_key}")