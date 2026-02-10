"""
Менеджер памяти - координация разных типов памяти
"""

import logging
from typing import Dict, Any, List, Optional
from datetime import datetime, timedelta

logger = logging.getLogger(__name__)

class MemoryManager:
    """Управление всеми типами памяти агента"""
    
    def __init__(self, config=None):
        self.config = config or {}
        self.short_term_memory = {}
        self.long_term_memory = VectorMemory()
        self.context_buffer = []
        self.memory_stats = {
            "short_term_entries": 0,
            "long_term_entries": 0,
            "context_size": 0
        }
        
    async def store(self, memory_type: str, content: Dict[str, Any], metadata: Dict[str, Any] = None) -> str:
        """Сохранение информации в память"""
        logger.info(f"💾 Сохранение в память типа: {memory_type}")
        
        if metadata is None:
            metadata = {}
            
        # Добавление метаданных
        metadata.update({
            "timestamp": datetime.now().isoformat(),
            "memory_type": memory_type,
            "access_count": 0
        })
        
        memory_id = None
        
        try:
            if memory_type == "short_term":
                memory_id = await self._store_short_term(content, metadata)
            elif memory_type == "long_term":
                memory_id = await self._store_long_term(content, metadata)
            elif memory_type == "context":
                memory_id = await self._store_context(content, metadata)
            else:
                raise ValueError(f"Неизвестный тип памяти: {memory_type}")
                
            logger.info(f"✅ Сохранено с ID: {memory_id}")
            return memory_id
            
        except Exception as e:
            logger.error(f"Ошибка сохранения в память: {e}")
            raise
            
    async def retrieve(self, memory_type: str, query: str = None, limit: int = 10) -> List[Dict[str, Any]]:
        """Извлечение информации из памяти"""
        logger.info(f"🔍 Извлечение из памяти типа: {memory_type}")
        
        try:
            if memory_type == "short_term":
                results = await self._retrieve_short_term(query, limit)
            elif memory_type == "long_term":
                results = await self._retrieve_long_term(query, limit)
            elif memory_type == "context":
                results = await self._retrieve_context(query, limit)
            else:
                raise ValueError(f"Неизвестный тип памяти: {memory_type}")
                
            logger.info(f"✅ Найдено результатов: {len(results)}")
            return results
            
        except Exception as e:
            logger.error(f"Ошибка извлечения из памяти: {e}")
            return []
            
    async def update(self, memory_id: str, content: Dict[str, Any], metadata: Dict[str, Any] = None):
        """Обновление информации в памяти"""
        logger.info(f"🔄 Обновление памяти ID: {memory_id}")
        
        # Определение типа памяти по ID или другим признакам
        # В данной упрощенной версии обновляем только в долговременной памяти
        try:
            await self.long_term_memory.update_memory(memory_id, content, metadata)
            logger.info(f"✅ Память обновлена: {memory_id}")
        except Exception as e:
            logger.error(f"Ошибка обновления памяти: {e}")
            raise
            
    async def forget(self, memory_id: str, memory_type: str = None):
        """Удаление информации из памяти"""
        logger.info(f"🗑️ Удаление памяти ID: {memory_id}")
        
        try:
            if memory_type == "short_term" or memory_id in self.short_term_memory:
                self.short_term_memory.pop(memory_id, None)
            else:
                await self.long_term_memory.delete_memory(memory_id)
                
            logger.info(f"✅ Память удалена: {memory_id}")
            
        except Exception as e:
            logger.error(f"Ошибка удаления памяти: {e}")
            raise
            
    async def consolidate(self):
        """Консолидация памяти (перемещение из кратковременной в долговременную)"""
        logger.info("🔄 Консолидация памяти")
        
        consolidated_count = 0
        
        for memory_id, memory in list(self.short_term_memory.items()):
            # Проверка на важность и возраст
            if self._should_consolidate(memory):
                try:
                    # Перенос в долговременную память
                    await self.long_term_memory.store_memory(
                        content=memory["content"],
                        metadata=memory["metadata"]
                    )
                    
                    # Удаление из кратковременной
                    self.short_term_memory.pop(memory_id)
                    consolidated_count += 1
                    
                except Exception as e:
                    logger.error(f"Ошибка консолидации памяти {memory_id}: {e}")
                    
        logger.info(f"✅ Консолидировано записей: {consolidated_count}")
        
    async def cleanup(self, older_than_days: int = 30):
        """Очистка старой памяти"""
        logger.info(f"🧹 Очистка памяти старше {older_than_days} дней")
        
        # Очистка кратковременной памяти
        cutoff_date = datetime.now() - timedelta(days=older_than_days)
        
        to_delete = []
        for memory_id, memory in self.short_term_memory.items():
            timestamp = datetime.fromisoformat(memory["metadata"].get("timestamp", "2000-01-01"))
            if timestamp < cutoff_date:
                to_delete.append(memory_id)
                
        for memory_id in to_delete:
            self.short_term_memory.pop(memory_id, None)
            
        # Очистка долговременной памяти
        await self.long_term_memory.cleanup_old_memories(older_than_days)
        
        logger.info(f"✅ Очищено записей кратковременной памяти: {len(to_delete)}")
        
    def get_stats(self) -> Dict[str, Any]:
        """Получение статистики памяти"""
        self.memory_stats["short_term_entries"] = len(self.short_term_memory)
        self.memory_stats["context_size"] = len(self.context_buffer)
        
        # Получение статистики долговременной памяти
        lt_stats = self.long_term_memory.get_memory_stats()
        self.memory_stats["long_term_entries"] = lt_stats.get("total_memories", 0)
        self.memory_stats.update(lt_stats)
        
        return self.memory_stats
        
    async def _store_short_term(self, content: Dict[str, Any], metadata: Dict[str, Any]) -> str:
        """Сохранение в кратковременную память"""
        import uuid
        
        memory_id = str(uuid.uuid4())
        
        self.short_term_memory[memory_id] = {
            "content": content,
            "metadata": metadata,
            "last_accessed": datetime.now().isoformat()
        }
        
        return memory_id
        
    async def _store_long_term(self, content: Dict[str, Any], metadata: Dict[str, Any]) -> str:
        """Сохранение в долговременную память"""
        return await self.long_term_memory.store_memory(content, metadata)
        
    async def _store_context(self, content: Dict[str, Any], metadata: Dict[str, Any]) -> str:
        """Сохранение в контекстный буфер"""
        import uuid
        
        memory_id = str(uuid.uuid4())
        
        context_entry = {
            "id": memory_id,
            "content": content,
            "metadata": metadata,
            "timestamp": datetime.now().isoformat()
        }
        
        self.context_buffer.append(context_entry)
        
        # Ограничение размера буфера
        max_context_size = self.config.get("max_context_size", 20)
        if len(self.context_buffer) > max_context_size:
            self.context_buffer = self.context_buffer[-max_context_size:]
            
        return memory_id
        
    async def _retrieve_short_term(self, query: str = None, limit: int = 10) -> List[Dict[str, Any]]:
        """Извлечение из кратковременной памяти"""
        results = []
        
        for memory_id, memory in self.short_term_memory.items():
            if self._matches_query(memory, query):
                results.append({
                    "id": memory_id,
                    "content": memory["content"],
                    "metadata": memory["metadata"],
                    "score": 1.0  # В кратковременной памяти нет релевантности
                })
                
                if len(results) >= limit:
                    break
                    
        return results
        
    async def _retrieve_long_term(self, query: str = None, limit: int = 10) -> List[Dict[str, Any]]:
        """Извлечение из долговременной памяти"""
        if query:
            return await self.long_term_memory.search_memories(query, limit)
        else:
            # Возврат последних записей
            return await self.long_term_memory.get_recent_memories(limit)
            
    async def _retrieve_context(self, query: str = None, limit: int = 10) -> List[Dict[str, Any]]:
        """Извлечение из контекстного буфера"""
        results = []
        
        for entry in reversed(self.context_buffer):  # Начиная с самых новых
            if self._matches_query(entry, query):
                results.append({
                    "id": entry["id"],
                    "content": entry["content"],
                    "metadata": entry["metadata"],
                    "score": 1.0
                })
                
                if len(results) >= limit:
                    break
                    
        return results
        
    def _should_consolidate(self, memory: Dict[str, Any]) -> bool:
        """Определение, нужно ли переносить запись в долговременную память"""
        metadata = memory["metadata"]
        
        # Проверка возраста
        timestamp = datetime.fromisoformat(metadata.get("timestamp", "2000-01-01"))
        age_hours = (datetime.now() - timestamp).total_seconds() / 3600
        
        # Проверка важности
        importance = metadata.get("importance", 0)
        access_count = metadata.get("access_count", 0)
        
        # Эвристика для консолидации
        if importance > 0.7:
            return True
        elif access_count > 5:
            return True
        elif age_hours > 24 and importance > 0.3:
            return True
            
        return False
        
    def _matches_query(self, memory: Dict[str, Any], query: str = None) -> bool:
        """Проверка соответствия памяти запросу"""
        if not query:
            return True
            
        # Поиск в содержимом
        content_str = str(memory.get("content", "")).lower()
        if query.lower() in content_str:
            return True
            
        # Поиск в метаданных
        metadata_str = str(memory.get("metadata", {})).lower()
        if query.lower() in metadata_str:
            return True
            
        return False