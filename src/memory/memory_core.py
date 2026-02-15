#!/usr/bin/env python3
# Путь: /mnt/ai_data/ai-agent/src/memory/memory_core.py
"""Основной модуль памяти Елены"""

from pathlib import Path
import pickle
from loguru import logger
from src.memory.vector_memory import VectorMemory

class MemoryCore:
    """Центральный менеджер памяти, объединяющий все типы памяти"""
    
    def __init__(self, config):
        self.config = config
        self.state_file = Path(config['paths']['data']) / 'memory_state.pkl'
        
        # Инициализация векторной памяти
        self.vector = VectorMemory(config)
        
        # Кратковременная память (кэш)
        self.short_term = {}
        
        # Загрузка сохранённого состояния
        self.load_state()
        
        logger.info("🧠 MemoryCore инициализирован")
    
    def store(self, perception, plan, result):
        """
        Сохранение опыта в память
        
        Args:
            perception: воспринятая информация
            plan: выполненный план
            result: результат выполнения
        """
        # Сохраняем в векторную память для долгосрочного хранения
        experience = f"Perception: {perception}\nPlan: {plan}\nResult: {result}"
        self.vector.add(experience, {"type": "experience"})
        
        # Сохраняем в кратковременную память
        import time
        self.short_term[time.time()] = {
            'perception': perception,
            'plan': plan,
            'result': result
        }
        
        # Ограничиваем размер кратковременной памяти
        if len(self.short_term) > 100:
            oldest = min(self.short_term.keys())
            del self.short_term[oldest]
    
    def recall(self, query, n_results=5):
        """Поиск в памяти по запросу"""
        return self.vector.search(query, n_results)
    
    def save_state(self):
        """Сохранение состояния памяти в файл"""
        try:
            state = {
                'short_term': self.short_term,
                # Векторная память сохраняется автоматически ChromaDB
            }
            with open(self.state_file, 'wb') as f:
                pickle.dump(state, f)
            logger.debug("💾 Состояние памяти сохранено")
        except Exception as e:
            logger.error(f"❌ Ошибка сохранения памяти: {e}")
    
    def load_state(self):
        """Загрузка состояния памяти из файла"""
        try:
            if self.state_file.exists():
                with open(self.state_file, 'rb') as f:
                    state = pickle.load(f)
                self.short_term = state.get('short_term', {})
                logger.info(f"📂 Загружено {len(self.short_term)} элементов из кратковременной памяти")
        except Exception as e:
            logger.error(f"❌ Ошибка загрузки памяти: {e}")
            self.short_term = {}