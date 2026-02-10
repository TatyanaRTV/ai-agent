"""
Схемы данных для векторного API
"""

from pydantic import BaseModel, Field
from typing import List, Dict, Any, Optional
from datetime import datetime

class MemoryBase(BaseModel):
    """Базовая схема памяти"""
    content: str = Field(..., description="Содержимое памяти")
    metadata: Optional[Dict[str, Any]] = Field(default=None, description="Метаданные")

class MemoryCreate(MemoryBase):
    """Схема для создания памяти"""
    collection: str = Field("memories", description="Коллекция для сохранения")

class MemoryResponse(MemoryBase):
    """Схема ответа с памятью"""
    id: str = Field(..., description="ID памяти")
    similarity: Optional[float] = Field(None, description="Схожесть (для поиска)")
    created_at: datetime = Field(..., description="Время создания")
    updated_at: Optional[datetime] = Field(None, description="Время обновления")

class SearchQuery(BaseModel):
    """Схема поискового запроса"""
    query: str = Field(..., description="Поисковый запрос")
    limit: int = Field(10, description="Количество результатов")
    threshold: float = Field(0.3, description="Порог схожести")
    collection: Optional[str] = Field(None, description="Коллекция для поиска")

class SearchResponse(BaseModel):
    """Схема ответа на поиск"""
    query: str = Field(..., description="Исходный запрос")
    results: List[MemoryResponse] = Field(..., description="Результаты поиска")
    count: int = Field(..., description="Количество найденных результатов")

class StatsResponse(BaseModel):
    """Схема статистики"""
    total_memories: int = Field(..., description="Всего воспоминаний")
    total_knowledge: int = Field(..., description="Всего знаний")
    total_experience: int = Field(..., description="Всего опыта")
    memory_size: str = Field(..., description="Размер памяти")
    collections: List[str] = Field(..., description="Доступные коллекции")

class BackupResponse(BaseModel):
    """Схема ответа бэкапа"""
    backup_path: str = Field(..., description="Путь к бэкапу")
    created_at: datetime = Field(..., description="Время создания бэкапа")
    size: Optional[str] = Field(None, description="Размер бэкапа")

class ErrorResponse(BaseModel):
    """Схема ошибки"""
    error: str = Field(..., description="Сообщение об ошибке")
    details: Optional[Dict[str, Any]] = Field(None, description="Детали ошибки")
    timestamp: datetime = Field(default_factory=datetime.now, description="Время ошибки")