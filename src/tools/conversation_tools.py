"""
Инструменты для обработки разговоров
"""

import logging
from typing import Dict, Any, Optional

logger = logging.getLogger(__name__)

class ConversationManager:
    """Управление диалогом с пользователем"""
    
    def __init__(self):
        self.history = []
        logger.info("💬 Менеджер диалога инициализирован")
        
    async def process_query(self, query: str) -> str:
        """Обработка запроса пользователя"""
        # Простая заглушка для тестирования
        response = f"Я получила ваш запрос: '{query}'"
        
        # Сохраняем в историю
        self.history.append({
            "user": query,
            "agent": response,
            "timestamp": __import__('datetime').datetime.now().isoformat()
        })
        
        return response
        
    def get_history(self, limit: int = 10) -> list:
        """Получение истории диалога"""
        return self.history[-limit:]