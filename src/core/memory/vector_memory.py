"""
Векторная память на основе ChromaDB
"""

import chromadb
from chromadb.config import Settings
import logging
from typing import List, Dict, Any, Optional
from datetime import datetime, timedelta
import json
import hashlib
import os
import shutil

logger = logging.getLogger(__name__)

class VectorMemory:
    """Управление векторной памятью"""
    
    def __init__(self, persist_directory: str = "./data/vectors"):
        self.persist_directory = persist_directory
        
        # Инициализация ChromaDB - НОВАЯ ВЕРСИЯ
        try:
            # Используем PersistentClient вместо устаревшего Client
            self.client = chromadb.PersistentClient(
                path=persist_directory
            )
            
            # Коллекция для общих воспоминаний
            self.memories_collection = self.client.get_or_create_collection(
                name="memories",
                metadata={"description": "Долговременная память агента", "hnsw:space": "cosine"}
            )
            
            # Коллекция для знаний
            self.knowledge_collection = self.client.get_or_create_collection(
                name="knowledge",
                metadata={"description": "База знаний агента", "hnsw:space": "cosine"}
            )
            
            # Коллекция для опыта
            self.experience_collection = self.client.get_or_create_collection(
                name="experience",
                metadata={"description": "Опыт взаимодействий", "hnsw:space": "cosine"}
            )
            
            logger.info("🧠 Векторная память инициализирована (PersistentClient)")
            
        except Exception as e:
            logger.error(f"❌ Ошибка инициализации ChromaDB: {e}")
            raise
        
    def store_memory(self, content: str, metadata: Dict[str, Any] = None, 
                    embedding: Optional[List[float]] = None) -> str:
        """Сохранение воспоминания"""
        memory_id = hashlib.md5(f"{content}{datetime.now().isoformat()}".encode()).hexdigest()
        
        if metadata is None:
            metadata = {}
            
        metadata.update({
            "timestamp": datetime.now().isoformat(),
            "type": "memory",
            "source": "agent"
        })
        
        try:
            self.memories_collection.add(
                documents=[content],
                metadatas=[metadata],
                ids=[memory_id],
                embeddings=[embedding] if embedding else None
            )
            
            logger.debug(f"Сохранено воспоминание: {memory_id}")
            return memory_id
            
        except Exception as e:
            logger.error(f"Ошибка сохранения воспоминания: {e}")
            raise
            
    def store_knowledge(self, content: str, category: str, 
                       metadata: Dict[str, Any] = None) -> str:
        """Сохранение знания"""
        knowledge_id = hashlib.md5(f"{content}{category}".encode()).hexdigest()
        
        if metadata is None:
            metadata = {}
            
        metadata.update({
            "category": category,
            "timestamp": datetime.now().isoformat(),
            "verified": True,
            "confidence": 0.9
        })
        
        try:
            self.knowledge_collection.add(
                documents=[content],
                metadatas=[metadata],
                ids=[knowledge_id]
            )
            
            logger.debug(f"Сохранено знание: {knowledge_id}")
            return knowledge_id
            
        except Exception as e:
            logger.error(f"Ошибка сохранения знания: {e}")
            raise
            
    def store_experience(self, interaction_data: Dict[str, Any]) -> str:
        """Сохранение опыта взаимодействия"""
        experience_id = hashlib.md5(
            f"{json.dumps(interaction_data)}{datetime.now().isoformat()}".encode()
        ).hexdigest()
        
        metadata = {
            "timestamp": datetime.now().isoformat(),
            "type": "experience",
            "success_rate": interaction_data.get("success_rate", 0.5),
            "learning_outcome": interaction_data.get("learning_outcome", "")
        }
        
        # Сериализация данных взаимодействия
        content = json.dumps(interaction_data, ensure_ascii=False)
        
        try:
            self.experience_collection.add(
                documents=[content],
                metadatas=[metadata],
                ids=[experience_id]
            )
            
            logger.debug(f"Сохранен опыт: {experience_id}")
            return experience_id
            
        except Exception as e:
            logger.error(f"Ошибка сохранения опыта: {e}")
            raise
            
    def search_memories(self, query: str, limit: int = 10, 
                       threshold: float = 0.3) -> List[Dict[str, Any]]:
        """Поиск воспоминаний"""
        try:
            results = self.memories_collection.query(
                query_texts=[query],
                n_results=limit
            )
            
            memories = []
            if results['documents'] and results['documents'][0]:
                for i, doc in enumerate(results['documents'][0]):
                    memories.append({
                        "content": doc,
                        "metadata": results['metadatas'][0][i] if results['metadatas'] else {},
                        "distance": results['distances'][0][i] if results['distances'] else 0,
                        "id": results['ids'][0][i]
                    })
                    
            return memories
            
        except Exception as e:
            logger.error(f"Ошибка поиска воспоминаний: {e}")
            return []
            
    def search_knowledge(self, query: str, category: Optional[str] = None, 
                        limit: int = 5) -> List[Dict[str, Any]]:
        """Поиск знаний"""
        try:
            where_filter = None
            if category:
                where_filter = {"category": category}
                
            results = self.knowledge_collection.query(
                query_texts=[query],
                n_results=limit,
                where=where_filter
            )
            
            knowledge_items = []
            if results['documents'] and results['documents'][0]:
                for i, doc in enumerate(results['documents'][0]):
                    knowledge_items.append({
                        "content": doc,
                        "metadata": results['metadatas'][0][i] if results['metadatas'] else {},
                        "distance": results['distances'][0][i] if results['distances'] else 0,
                        "id": results['ids'][0][i]
                    })
                
            return knowledge_items
            
        except Exception as e:
            logger.error(f"Ошибка поиска знаний: {e}")
            return []
            
    def get_similar_experiences(self, current_experience: Dict[str, Any], 
                               limit: int = 3) -> List[Dict[str, Any]]:
        """Поиск похожего опыта"""
        try:
            # Создание текстового запроса из опыта
            query_text = json.dumps(current_experience, ensure_ascii=False)
            
            results = self.experience_collection.query(
                query_texts=[query_text],
                n_results=limit
            )
            
            experiences = []
            if results['documents'] and results['documents'][0]:
                for i, doc in enumerate(results['documents'][0]):
                    try:
                        experience_data = json.loads(doc)
                        experiences.append({
                            "data": experience_data,
                            "metadata": results['metadatas'][0][i] if results['metadatas'] else {},
                            "similarity": 1 - (results['distances'][0][i] if results['distances'] else 0),
                            "id": results['ids'][0][i]
                        })
                    except json.JSONDecodeError:
                        continue
                    
            return experiences
            
        except Exception as e:
            logger.error(f"Ошибка поиска похожего опыта: {e}")
            return []
            
    def update_memory(self, memory_id: str, new_content: str, 
                     new_metadata: Dict[str, Any] = None):
        """Обновление воспоминания"""
        try:
            current = self.memories_collection.get(ids=[memory_id])
            if not current['documents']:
                raise ValueError(f"Воспоминание {memory_id} не найдено")
                
            metadata = current['metadatas'][0] if current['metadatas'] else {}
            if new_metadata:
                metadata.update(new_metadata)
                
            metadata['updated_at'] = datetime.now().isoformat()
            metadata['update_count'] = metadata.get('update_count', 0) + 1
            
            # Удаление старой записи
            self.memories_collection.delete(ids=[memory_id])
            
            # Добавление обновленной записи
            self.memories_collection.add(
                documents=[new_content],
                metadatas=[metadata],
                ids=[memory_id]
            )
            
            logger.debug(f"Обновлено воспоминание: {memory_id}")
            
        except Exception as e:
            logger.error(f"Ошибка обновления воспоминания: {e}")
            raise
            
    def delete_memory(self, memory_id: str):
        """Удаление воспоминания"""
        try:
            self.memories_collection.delete(ids=[memory_id])
            logger.debug(f"Удалено воспоминание: {memory_id}")
            
        except Exception as e:
            logger.error(f"Ошибка удаления воспоминания: {e}")
            raise
            
    def get_memory_stats(self) -> Dict[str, Any]:
        """Получение статистики памяти"""
        try:
            memory_count = self.memories_collection.count()
            knowledge_count = self.knowledge_collection.count()
            experience_count = self.experience_collection.count()
            
            # Получение примеров категорий знаний
            categories = set()
            try:
                knowledge_samples = self.knowledge_collection.get(limit=5)
                for meta in knowledge_samples['metadatas']:
                    if meta and 'category' in meta:
                        categories.add(meta['category'])
            except:
                pass
                    
            return {
                "total_memories": memory_count,
                "total_knowledge": knowledge_count,
                "total_experience": experience_count,
                "knowledge_categories": list(categories),
                "memory_size": self._estimate_memory_size(),
                "last_backup": self._get_last_backup_time()
            }
            
        except Exception as e:
            logger.error(f"Ошибка получения статистики памяти: {e}")
            return {}
            
    def _estimate_memory_size(self) -> str:
        """Оценка размера памяти"""
        total_size = 0
        if os.path.exists(self.persist_directory):
            for dirpath, dirnames, filenames in os.walk(self.persist_directory):
                for f in filenames:
                    fp = os.path.join(dirpath, f)
                    total_size += os.path.getsize(fp)
                    
        # Конвертация в читаемый формат
        for unit in ['B', 'KB', 'MB', 'GB']:
            if total_size < 1024:
                return f"{total_size:.2f} {unit}"
            total_size /= 1024
            
        return f"{total_size:.2f} TB"
        
    def _get_last_backup_time(self) -> str:
        """Получение времени последнего бэкапа"""
        backup_file = f"{self.persist_directory}/backup_timestamp.txt"
        
        try:
            if os.path.exists(backup_file):
                with open(backup_file, 'r') as f:
                    return f.read().strip()
        except:
            pass
            
        return "никогда"
        
    def create_backup(self, backup_path: str = None):
        """Создание резервной копии памяти"""
        if backup_path is None:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            backup_path = f"./data/backups/memory_backup_{timestamp}"
            
        try:
            # Создание директории для бэкапа
            os.makedirs(os.path.dirname(backup_path), exist_ok=True)
            
            # Копирование директории
            shutil.copytree(self.persist_directory, backup_path)
            
            # Сохранение метаданных бэкапа
            backup_meta = {
                "timestamp": datetime.now().isoformat(),
                "source": self.persist_directory,
                "destination": backup_path,
                "stats": self.get_memory_stats()
            }
            
            meta_file = f"{backup_path}/backup_metadata.json"
            with open(meta_file, 'w', encoding='utf-8') as f:
                json.dump(backup_meta, f, ensure_ascii=False, indent=2)
                
            # Обновление времени последнего бэкапа
            os.makedirs(self.persist_directory, exist_ok=True)
            timestamp_file = f"{self.persist_directory}/backup_timestamp.txt"
            with open(timestamp_file, 'w') as f:
                f.write(datetime.now().isoformat())
                
            logger.info(f"✅ Резервная копия создана: {backup_path}")
            return backup_path
            
        except Exception as e:
            logger.error(f"Ошибка создания резервной копии: {e}")
            raise
            
    def restore_from_backup(self, backup_path: str):
        """Восстановление памяти из резервной копии"""
        try:
            # Проверка существования бэкапа
            if not os.path.exists(backup_path):
                raise ValueError(f"Путь бэкапа не существует: {backup_path}")
                
            # Создание резервной копии текущих данных
            temp_backup = f"{self.persist_directory}_temp_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
            if os.path.exists(self.persist_directory):
                shutil.move(self.persist_directory, temp_backup)
                
            # Копирование бэкапа
            shutil.copytree(backup_path, self.persist_directory)
            
            logger.info(f"✅ Память восстановлена из бэкапа: {backup_path}")
            
            # Удаление временной копии после успешного восстановления
            import time
            time.sleep(1)
            if os.path.exists(temp_backup):
                shutil.rmtree(temp_backup)
                
        except Exception as e:
            logger.error(f"Ошибка восстановления из бэкапа: {e}")
            
            # Попытка восстановить оригинальные данные
            if 'temp_backup' in locals() and os.path.exists(temp_backup):
                if os.path.exists(self.persist_directory):
                    shutil.rmtree(self.persist_directory)
                shutil.move(temp_backup, self.persist_directory)
                
            raise
            
    def cleanup_old_memories(self, days_old: int = 90):
        """Очистка старых воспоминаний"""
        try:
            cutoff_date = (datetime.now() - timedelta(days=days_old)).isoformat()
            
            # Получение старых воспоминаний
            old_memories = self.memories_collection.get(
                where={"timestamp": {"$lt": cutoff_date}}
            )
            
            if old_memories['ids']:
                # Удаление старых воспоминаний
                self.memories_collection.delete(ids=old_memories['ids'])
                logger.info(f"Удалено {len(old_memories['ids'])} старых воспоминаний")
                
            return len(old_memories['ids'])
            
        except Exception as e:
            logger.error(f"Ошибка очистки старых воспоминаний: {e}")
            return 0
            
    def export_memories(self, export_path: str, format: str = "json"):
        """Экспорт воспоминаний"""
        try:
            # Получение всех воспоминаний
            all_memories = self.memories_collection.get(
                include=["documents", "metadatas", "ids"]
            )
            
            export_data = {
                "export_timestamp": datetime.now().isoformat(),
                "total_memories": len(all_memories['ids']),
                "memories": []
            }
            
            for i, memory_id in enumerate(all_memories['ids']):
                export_data["memories"].append({
                    "id": memory_id,
                    "content": all_memories['documents'][i],
                    "metadata": all_memories['metadatas'][i] if all_memories['metadatas'] else {}
                })
                
            # Сохранение в указанном формате
            os.makedirs(os.path.dirname(export_path), exist_ok=True)
            
            if format.lower() == "json":
                with open(f"{export_path}.json", 'w', encoding='utf-8') as f:
                    json.dump(export_data, f, ensure_ascii=False, indent=2)
            elif format.lower() == "csv":
                import csv
                with open(f"{export_path}.csv", 'w', newline='', encoding='utf-8') as f:
                    writer = csv.writer(f)
                    writer.writerow(['ID', 'Content', 'Timestamp', 'Type'])
                    for memory in export_data["memories"]:
                        writer.writerow([
                            memory['id'],
                            memory['content'][:100] + "..." if len(memory['content']) > 100 else memory['content'],
                            memory['metadata'].get('timestamp', ''),
                            memory['metadata'].get('type', '')
                        ])
            else:
                raise ValueError(f"Неподдерживаемый формат: {format}")
                
            logger.info(f"Экспортировано {len(export_data['memories'])} воспоминаний в {export_path}.{format}")
            
        except Exception as e:
            logger.error(f"Ошибка экспорта воспоминаний: {e}")
            raise