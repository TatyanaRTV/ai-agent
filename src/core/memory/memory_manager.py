"""
Менеджер памяти - координация разных типов памяти
"""

import logging
import uuid
from typing import Dict, Any, List, Optional
from datetime import datetime, timedelta

from src.core.memory.vector_memory import VectorMemory

logger = logging.getLogger(__name__)

class MemoryManager:
    """Управление всеми типами памяти агента"""
    
    def __init__(self, config=None):
        self.config = config or {}
        self.short_term_memory = {}
        self.long_term_memory = VectorMemory()
        self.context_buffer = []
        self.last_learning_time = datetime.now()
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
            logger.error(f"❌ Ошибка сохранения в память: {e}")
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
            logger.error(f"❌ Ошибка извлечения из памяти: {e}")
            return []
            
    async def update(self, memory_id: str, content: Dict[str, Any], metadata: Dict[str, Any] = None):
        """Обновление информации в памяти"""
        logger.info(f"🔄 Обновление памяти ID: {memory_id}")
        
        try:
            await self.long_term_memory.update_memory(memory_id, content, metadata)
            logger.info(f"✅ Память обновлена: {memory_id}")
        except Exception as e:
            logger.error(f"❌ Ошибка обновления памяти: {e}")
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
            logger.error(f"❌ Ошибка удаления памяти: {e}")
            raise
            
    async def consolidate(self):
        """Консолидация памяти (перемещение из кратковременной в долговременную)"""
        logger.info("🔄 Консолидация памяти")
        
        consolidated_count = 0
        
        for memory_id, memory in list(self.short_term_memory.items()):
            if self._should_consolidate(memory):
                try:
                    content = memory.get("content", {})
                    metadata = memory.get("metadata", {})
                    
                    if isinstance(content, dict):
                        content_str = str(content)
                    else:
                        content_str = str(content)
                        
                    await self.long_term_memory.store_memory(
                        content=content_str,
                        metadata=metadata
                    )
                    
                    self.short_term_memory.pop(memory_id)
                    consolidated_count += 1
                    
                except Exception as e:
                    logger.error(f"❌ Ошибка консолидации памяти {memory_id}: {e}")
                    
        logger.info(f"✅ Консолидировано записей: {consolidated_count}")
        
    async def cleanup(self, older_than_days: int = 30):
        """Очистка старой памяти"""
        logger.info(f"🧹 Очистка памяти старше {older_than_days} дней")
        
        cutoff_date = datetime.now() - timedelta(days=older_than_days)
        
        to_delete = []
        for memory_id, memory in self.short_term_memory.items():
            try:
                timestamp_str = memory.get("metadata", {}).get("timestamp", "2000-01-01")
                timestamp = datetime.fromisoformat(timestamp_str)
                if timestamp < cutoff_date:
                    to_delete.append(memory_id)
            except:
                continue
                
        for memory_id in to_delete:
            self.short_term_memory.pop(memory_id, None)
            
        await self.long_term_memory.cleanup_old_memories(older_than_days)
        
        logger.info(f"✅ Очищено записей кратковременной памяти: {len(to_delete)}")
        
    def store_interaction(self, user_input: str, agent_response: str, metadata: Dict[str, Any] = None) -> str:
        """Сохранение взаимодействия в память (синхронная обёртка)"""
        import asyncio
        
        content = {
            "user": user_input,
            "agent": agent_response,
            "type": "interaction"
        }
        
        try:
            loop = asyncio.get_event_loop()
        except RuntimeError:
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            
        return loop.run_until_complete(
            self.store("short_term", content, metadata)
        )
        
    def get_recent_interactions(self, limit: int = 5) -> List[Dict[str, Any]]:
        """Получение последних взаимодействий"""
        results = []
        for memory_id, memory in list(self.short_term_memory.items())[-limit:]:
            content = memory.get("content", {})
            if isinstance(content, dict) and content.get("type") == "interaction":
                results.append({
                    "id": memory_id,
                    "user": content.get("user", ""),
                    "agent": content.get("agent", ""),
                    "timestamp": memory.get("metadata", {}).get("timestamp"),
                    "metadata": memory.get("metadata", {})
                })
        return results
        
    def get_conversation_context(self, limit: int = 10) -> str:
        """Получение контекста разговора"""
        interactions = self.get_recent_interactions(limit)
        context_lines = []
        for i in interactions:
            context_lines.append(f"User: {i.get('user', '')}")
            context_lines.append(f"Agent: {i.get('agent', '')}")
        return "\n".join(context_lines)
        
    def get_last_learning_time(self) -> datetime:
        """Получение времени последнего обучения"""
        return self.last_learning_time
        
    def update_learning_time(self):
        """Обновление времени обучения"""
        self.last_learning_time = datetime.now()
        
    async def find_similar_interactions(self, context: Dict[str, Any], limit: int = 5) -> List[Dict[str, Any]]:
        """Поиск похожих взаимодействий"""
        query = context.get('text', '')
        if not query:
            return []
            
        try:
            results = await self.long_term_memory.search_memories(query, limit)
            
            interactions = []
            for r in results:
                interactions.append({
                    "text": r.get("content", ""),
                    "timestamp": r.get("metadata", {}).get("timestamp", ""),
                    "similarity": 1 - r.get("distance", 0)
                })
            return interactions
            
        except Exception as e:
            logger.error(f"❌ Ошибка поиска похожих взаимодействий: {e}")
            return []
            
    def store_reflection(self, reflection: Dict[str, Any]):
        """Сохранение саморефлексии"""
        import asyncio
        import json
        
        try:
            content_str = json.dumps(reflection, ensure_ascii=False)
            metadata = {
                "type": "reflection",
                "timestamp": datetime.now().isoformat(),
                "effectiveness": reflection.get("effectiveness", 0)
            }
            
            try:
                loop = asyncio.get_event_loop()
            except RuntimeError:
                loop = asyncio.new_event_loop()
                asyncio.set_event_loop(loop)
                
            loop.run_until_complete(
                self.long_term_memory.store_memory(content_str, metadata)
            )
            
        except Exception as e:
            logger.error(f"❌ Ошибка сохранения рефлексии: {e}")
            
    async def search_memories(self, query: str, limit: int = 10, threshold: float = 0.3) -> List[Dict[str, Any]]:
        """Поиск воспоминаний (асинхронный)"""
        try:
            return await self.long_term_memory.search_memories(query, limit, threshold)
        except Exception as e:
            logger.error(f"❌ Ошибка поиска воспоминаний: {e}")
            return []
            
    def get_stats(self) -> Dict[str, Any]:
        """Получение статистики памяти"""
        self.memory_stats["short_term_entries"] = len(self.short_term_memory)
        self.memory_stats["context_size"] = len(self.context_buffer)
        
        try:
            lt_stats = self.long_term_memory.get_memory_stats()
            self.memory_stats["long_term_entries"] = lt_stats.get("total_memories", 0)
            self.memory_stats.update(lt_stats)
        except Exception as e:
            logger.error(f"❌ Ошибка получения статистики долговременной памяти: {e}")
            
        self.memory_stats["last_learning"] = self.last_learning_time.isoformat()
        
        return self.memory_stats
        
    async def _store_short_term(self, content: Dict[str, Any], metadata: Dict[str, Any]) -> str:
        """Сохранение в кратковременную память"""
        memory_id = str(uuid.uuid4())
        
        self.short_term_memory[memory_id] = {
            "content": content,
            "metadata": metadata,
            "last_accessed": datetime.now().isoformat()
        }
        
        if len(self.short_term_memory) > 1000:
            oldest_keys = list(self.short_term_memory.keys())[:500]
            for key in oldest_keys:
                self.short_term_memory.pop(key, None)
        
        return memory_id
        
    async def _store_long_term(self, content: Dict[str, Any], metadata: Dict[str, Any]) -> str:
        """Сохранение в долговременную память"""
        content_str = str(content) if not isinstance(content, str) else content
        return await self.long_term_memory.store_memory(content_str, metadata)
        
    async def _store_context(self, content: Dict[str, Any], metadata: Dict[str, Any]) -> str:
        """Сохранение в контекстный буфер"""
        memory_id = str(uuid.uuid4())
        
        context_entry = {
            "id": memory_id,
            "content": content,
            "metadata": metadata,
            "timestamp": datetime.now().isoformat()
        }
        
        self.context_buffer.append(context_entry)
        
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
                    "score": 1.0
                })
                
                if len(results) >= limit:
                    break
                    
        return results
        
    async def _retrieve_long_term(self, query: str = None, limit: int = 10) -> List[Dict[str, Any]]:
        """Извлечение из долговременной памяти"""
        if query:
            return await self.long_term_memory.search_memories(query, limit)
        else:
            return []
            
    async def _retrieve_context(self, query: str = None, limit: int = 10) -> List[Dict[str, Any]]:
        """Извлечение из контекстного буфера"""
        results = []
        
        for entry in reversed(self.context_buffer):
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
        metadata = memory.get("metadata", {})
        
        try:
            timestamp = datetime.fromisoformat(metadata.get("timestamp", "2000-01-01"))
            age_hours = (datetime.now() - timestamp).total_seconds() / 3600
        except:
            age_hours = 0
            
        importance = metadata.get("importance", 0)
        access_count = metadata.get("access_count", 0)
        
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
            
        query_lower = query.lower()
        content_str = str(memory.get("content", "")).lower()
        if query_lower in content_str:
            return True
            
        metadata_str = str(memory.get("metadata", {})).lower()
        if query_lower in metadata_str:
            return True
            
        return False