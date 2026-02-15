#!/usr/bin/env python3
# Путь: /mnt/ai_data/ai-agent/src/memory/vector_memory.py
"""Векторная память Елены на базе ChromaDB - финальная версия"""

import chromadb
from chromadb.config import Settings
from sentence_transformers import SentenceTransformer
from loguru import logger
from pathlib import Path
import hashlib
import time
import gc
import torch


class VectorMemory:
    """Векторная память для долговременного хранения"""

    def __init__(self, config):
        """
        Инициализация векторной памяти

        Args:
            config: словарь с конфигурацией
        """
        self.persist_dir = Path(config["memory"]["persist_directory"])
        self.persist_dir.mkdir(parents=True, exist_ok=True)

        self.collection_name = config["memory"]["collection_name"]

        # Инициализация ChromaDB
        self.client = chromadb.PersistentClient(
            path=str(self.persist_dir), settings=Settings(anonymized_telemetry=False)
        )

        # Создаём или получаем коллекцию
        self.collection = self.client.get_or_create_collection(name=self.collection_name)

        # Модель для создания эмбеддингов (принудительно на CPU)
        logger.info("📥 Загрузка SentenceTransformer (all-MiniLM-L6-v2) на CPU...")
        self.encoder = SentenceTransformer("all-MiniLM-L6-v2", device="cpu")  # Всегда на CPU, чтобы не занимать GPU
        logger.success("✅ SentenceTransformer загружен на CPU")

        logger.info(f"🧠 VectorMemory инициализирована: {self.persist_dir}")
        logger.info(f"   📊 Всего записей: {self.count()}")

    def add(self, text: str, metadata: dict = None):
        """
        Добавление текста в векторную память

        Args:
            text: текст для сохранения
            metadata: метаданные (опционально)

        Returns:
            ID добавленной записи или None при ошибке
        """
        try:
            embedding = self.encoder.encode(text).tolist()

            # Генерируем уникальный ID
            unique_id = hashlib.md5(f"{text}{time.time()}".encode()).hexdigest()[:10]
            doc_id = f"doc_{unique_id}"

            # Подготавливаем метаданные
            if metadata is None:
                metadata = {}
            metadata["timestamp"] = time.time()

            self.collection.add(documents=[text], embeddings=[embedding], metadatas=[metadata], ids=[doc_id])

            logger.debug(f"📝 Добавлено в векторную память: {text[:50]}... (ID: {doc_id})")
            return doc_id

        except Exception as e:
            logger.error(f"❌ Ошибка добавления в векторную память: {e}")
            return None

    def search(self, query: str, n_results: int = 5):
        """
        Поиск в векторной памяти

        Args:
            query: поисковый запрос
            n_results: количество результатов

        Returns:
            список найденных документов
        """
        try:
            query_emb = self.encoder.encode(query).tolist()

            results = self.collection.query(query_embeddings=[query_emb], n_results=n_results)

            documents = results["documents"][0] if results["documents"] else []
            distances = results["distances"][0] if results["distances"] else []
            metadatas = results["metadatas"][0] if results["metadatas"] else []
            ids = results["ids"][0] if results["ids"] else []

            # Формируем результаты с метаданными
            formatted_results = []
            for i, doc in enumerate(documents):
                formatted_results.append(
                    {
                        "text": doc,
                        "distance": distances[i] if i < len(distances) else None,
                        "metadata": metadatas[i] if i < len(metadatas) else {},
                        "id": ids[i] if i < len(ids) else None,
                    }
                )

            logger.debug(f"🔍 Поиск '{query}': найдено {len(formatted_results)} результатов")
            return formatted_results

        except Exception as e:
            logger.error(f"❌ Ошибка поиска в векторной памяти: {e}")
            return []

    def search_text(self, query: str, n_results: int = 5):
        """
        Поиск в векторной памяти (только текст, для обратной совместимости)

        Args:
            query: поисковый запрос
            n_results: количество результатов

        Returns:
            список найденных текстов
        """
        results = self.search(query, n_results)
        return [r["text"] for r in results]

    def get_all(self, limit: int = 100):
        """
        Получение всех записей из памяти

        Args:
            limit: максимальное количество записей

        Returns:
            список записей
        """
        try:
            results = self.collection.get(limit=limit)

            items = []
            if results and "documents" in results and results["documents"]:
                for i, doc in enumerate(results["documents"]):
                    items.append(
                        {
                            "text": doc,
                            "metadata": results["metadatas"][i] if results["metadatas"] else {},
                            "id": results["ids"][i] if results["ids"] else None,
                        }
                    )

            return items

        except Exception as e:
            logger.error(f"❌ Ошибка получения всех записей: {e}")
            return []

    def count(self):
        """Количество записей в памяти"""
        try:
            return self.collection.count()
        except Exception as e:
            logger.error(f"❌ Ошибка получения количества: {e}")
            return 0

    def delete(self, ids=None, where=None):
        """
        Удаление записей из памяти

        Args:
            ids: список ID для удаления
            where: условие для удаления (например, {"type": "old"})

        Returns:
            bool: успешно или нет
        """
        try:
            if ids:
                self.collection.delete(ids=ids)
                logger.info(f"🗑️ Удалено {len(ids)} записей из векторной памяти")
                return True
            elif where:
                # Получаем ID по условию
                results = self.collection.get(where=where)
                if results and "ids" in results and results["ids"]:
                    self.collection.delete(ids=results["ids"])
                    logger.info(f"🗑️ Удалено {len(results['ids'])} записей по условию {where}")
                    return True
            else:
                logger.warning("⚠️ Не указаны ID или условие для удаления")
                return False

        except Exception as e:
            logger.error(f"❌ Ошибка удаления из векторной памяти: {e}")
            return False

    def clear(self):
        """Очистка всей памяти"""
        try:
            # Получаем все ID
            results = self.collection.get()
            if results and "ids" in results and results["ids"]:
                self.collection.delete(ids=results["ids"])
                logger.info(f"🗑️ Очищена вся векторная память (удалено {len(results['ids'])} записей)")
            return True
        except Exception as e:
            logger.error(f"❌ Ошибка очистки векторной памяти: {e}")
            return False

    def get_stats(self):
        """Получение статистики памяти"""
        return {"total_records": self.count(), "collection": self.collection_name, "persist_dir": str(self.persist_dir)}

    def cleanup(self):
        """Очистка ресурсов"""
        try:
            # Очищаем кэш модели
            if hasattr(self, "encoder"):
                # Перемещаем на CPU и удаляем
                self.encoder = None

            # Запускаем сборщик мусора
            gc.collect()

            logger.info("🧹 VectorMemory: ресурсы очищены")

        except Exception as e:
            logger.error(f"❌ Ошибка очистки ресурсов: {e}")
