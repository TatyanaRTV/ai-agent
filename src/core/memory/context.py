"""
Управление контекстом взаимодействия
"""

import logging
from typing import Dict, Any, List, Optional
from datetime import datetime, timedelta
from collections import deque

logger = logging.getLogger(__name__)

class ContextManager:
    """Менеджер контекста диалога"""
    
    def __init__(self, max_context_length: int = 20, max_history_length: int = 100):
        self.max_context_length = max_context_length
        self.max_history_length = max_history_length
        self.current_context = deque(maxlen=max_context_length)
        self.conversation_history = deque(maxlen=max_history_length)
        self.context_variables = {}
        
    def add_interaction(self, user_input: str, agent_response: str, metadata: Dict[str, Any] = None):
        """Добавление взаимодействия в контекст"""
        if metadata is None:
            metadata = {}
            
        interaction = {
            "timestamp": datetime.now().isoformat(),
            "user_input": user_input,
            "agent_response": agent_response,
            "metadata": metadata
        }
        
        # Добавление в текущий контекст
        self.current_context.append(interaction)
        
        # Добавление в историю
        self.conversation_history.append(interaction)
        
        # Извлечение контекстных переменных
        self._extract_context_variables(interaction)
        
        logger.debug(f"Добавлено взаимодействие в контекст: {user_input[:50]}...")
        
    def get_context(self, limit: int = None) -> List[Dict[str, Any]]:
        """Получение текущего контекста"""
        if limit:
            return list(self.current_context)[-limit:]
        return list(self.current_context)
        
    def get_full_history(self, limit: int = None) -> List[Dict[str, Any]]:
        """Получение полной истории"""
        if limit:
            return list(self.conversation_history)[-limit:]
        return list(self.conversation_history)
        
    def clear_context(self):
        """Очистка текущего контекста (но не истории)"""
        self.current_context.clear()
        self.context_variables.clear()
        logger.info("Контекст очищен")
        
    def set_variable(self, key: str, value: Any):
        """Установка контекстной переменной"""
        self.context_variables[key] = {
            "value": value,
            "timestamp": datetime.now().isoformat(),
            "access_count": 0
        }
        
    def get_variable(self, key: str, default: Any = None) -> Any:
        """Получение значения контекстной переменной"""
        if key in self.context_variables:
            var = self.context_variables[key]
            var["access_count"] += 1
            return var["value"]
        return default
        
    def get_all_variables(self) -> Dict[str, Any]:
        """Получение всех контекстных переменных"""
        return {k: v["value"] for k, v in self.context_variables.items()}
        
    def summarize_context(self, max_length: int = 500) -> str:
        """Создание краткого суммаризации контекста"""
        if not self.current_context:
            return "Контекст пуст"
            
        summary_parts = []
        
        for i, interaction in enumerate(self.current_context):
            summary = f"{i+1}. Пользователь: {interaction['user_input'][:100]}..."
            summary_parts.append(summary)
            
        full_summary = "\n".join(summary_parts)
        
        # Обрезка, если слишком длинный
        if len(full_summary) > max_length:
            full_summary = full_summary[:max_length] + "..."
            
        return full_summary
        
    def find_in_history(self, query: str, limit: int = 5) -> List[Dict[str, Any]]:
        """Поиск в истории по запросу"""
        results = []
        query_lower = query.lower()
        
        for interaction in reversed(self.conversation_history):
            # Поиск в пользовательском вводе и ответе агента
            text_to_search = f"{interaction['user_input']} {interaction['agent_response']}".lower()
            
            if query_lower in text_to_search:
                results.append(interaction)
                
                if len(results) >= limit:
                    break
                    
        return results
        
    def get_context_stats(self) -> Dict[str, Any]:
        """Получение статистики контекста"""
        return {
            "current_context_size": len(self.current_context),
            "history_size": len(self.conversation_history),
            "variables_count": len(self.context_variables),
            "max_context_length": self.max_context_length,
            "max_history_length": self.max_history_length
        }
        
    def cleanup_old_variables(self, older_than_hours: int = 24):
        """Очистка старых контекстных переменных"""
        cutoff_time = datetime.now() - timedelta(hours=older_than_hours)
        deleted_count = 0
        
        keys_to_delete = []
        
        for key, var in self.context_variables.items():
            timestamp = datetime.fromisoformat(var["timestamp"])
            
            if timestamp < cutoff_time:
                keys_to_delete.append(key)
                
        for key in keys_to_delete:
            del self.context_variables[key]
            deleted_count += 1
            
        if deleted_count:
            logger.debug(f"Очищено старых контекстных переменных: {deleted_count}")
            
    def _extract_context_variables(self, interaction: Dict[str, Any]):
        """Извлечение контекстных переменных из взаимодействия"""
        user_input = interaction["user_input"].lower()
        
        # Извлечение имен
        if "меня зовут" in user_input:
            # Простая логика извлечения имени
            parts = user_input.split("меня зовут")
            if len(parts) > 1:
                name = parts[1].strip().split()[0]
                self.set_variable("user_name", name)
                
        # Извлечение предпочтений
        preference_keywords = ["нравится", "люблю", "предпочитаю", "хочу", "мне нужно"]
        for keyword in preference_keywords:
            if keyword in user_input:
                # Упрощенная логика извлечения предпочтений
                self.set_variable(f"preference_{keyword}", True)
                
        # Извлечение текущей темы
        if "о " in user_input or "про " in user_input:
            # Попытка извлечь тему обсуждения
            topic_words = []
            words = user_input.split()
            
            for i, word in enumerate(words):
                if word in ["о", "про", "насчет", "касательно"] and i + 1 < len(words):
                    topic_words.append(words[i + 1])
                    
            if topic_words:
                self.set_variable("current_topic", " ".join(topic_words))