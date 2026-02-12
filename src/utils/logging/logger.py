"""
ПРОДВИНУТЫЙ ЛОГГЕР ДЛЯ ЕЛЕНЫ
"""

import logging
import sys
from logging.handlers import RotatingFileHandler
from pathlib import Path
import json
from datetime import datetime
from typing import Dict, Any

class ElenaLogger:
    """Кастомный логгер для ИИ-агента"""
    
    def __init__(self, name: str = "elena"):
        self.logger = logging.getLogger(name)
        self.logger.setLevel(logging.DEBUG)
        
        # Форматер
        formatter = logging.Formatter(
            '[%(asctime)s] [%(levelname)s] [%(name)s:%(filename)s:%(lineno)d] - %(message)s',
            datefmt='%Y-%m-%d %H:%M:%S'
        )
        
        # Консольный хендлер
        console_handler = logging.StreamHandler(sys.stdout)
        console_handler.setLevel(logging.INFO)
        console_handler.setFormatter(formatter)
        
        # Файловый хендлер
        log_dir = Path("logs")
        log_dir.mkdir(exist_ok=True)
        
        file_handler = RotatingFileHandler(
            log_dir / "elena.log",
            maxBytes=10*1024*1024,  # 10MB
            backupCount=5,
            encoding='utf-8'
        )
        file_handler.setLevel(logging.DEBUG)
        file_handler.setFormatter(formatter)
        
        # Очистка старых хендлеров
        if self.logger.handlers:
            self.logger.handlers.clear()
            
        # Добавление хендлеров
        self.logger.addHandler(console_handler)
        self.logger.addHandler(file_handler)
        
        # JSON логгер
        self.json_logger = self._setup_json_logger()
        
    def _setup_json_logger(self):
        """Настройка JSON логгера"""
        json_logger = logging.getLogger("elena_json")
        json_logger.setLevel(logging.INFO)
        
        json_handler = RotatingFileHandler(
            Path("logs") / "elena_json.log",
            maxBytes=5*1024*1024,
            backupCount=3,
            encoding='utf-8'
        )
        
        class JSONFormatter(logging.Formatter):
            def format(self, record):
                log_data = {
                    "timestamp": datetime.now().isoformat(),
                    "level": record.levelname,
                    "logger": record.name,
                    "message": record.getMessage(),
                    "module": record.module,
                    "function": record.funcName,
                    "line": record.lineno
                }
                
                if hasattr(record, 'extra_data'):
                    log_data.update(record.extra_data)
                    
                return json.dumps(log_data, ensure_ascii=False)
                
        json_handler.setFormatter(JSONFormatter())
        
        if not json_logger.handlers:
            json_logger.addHandler(json_handler)
            json_logger.propagate = False
            
        return json_logger
        
    def debug(self, message: str, **kwargs):
        """Логирование отладки"""
        self.logger.debug(message, extra={'extra_data': kwargs})
        
    def info(self, message: str, **kwargs):
        """Информационное логирование"""
        self.logger.info(message, extra={'extra_data': kwargs})
        
    def warning(self, message: str, **kwargs):
        """Логирование предупреждений"""
        self.logger.warning(message, extra={'extra_data': kwargs})
        
    def error(self, message: str, **kwargs):
        """Логирование ошибок"""
        self.logger.error(message, extra={'extra_data': kwargs})
        
    def critical(self, message: str, **kwargs):
        """Критическое логирование"""
        self.logger.critical(message, extra={'extra_data': kwargs})
        
    def log_interaction(self, user_input: str, agent_response: str, metadata: Dict[str, Any] = None):
        """Логирование взаимодействий"""
        log_entry = {
            "type": "interaction",
            "user_input": user_input,
            "agent_response": agent_response,
            "timestamp": datetime.now().isoformat(),
            "metadata": metadata or {}
        }
        
        self.json_logger.info("Interaction", extra={'extra_data': log_entry})
        
    def log_voice(self, audio_data: Dict[str, Any]):
        """Логирование голосовых взаимодействий"""
        log_entry = {
            "type": "voice",
            "duration": audio_data.get("duration"),
            "text": audio_data.get("text"),
            "confidence": audio_data.get("confidence"),
            "timestamp": datetime.now().isoformat()
        }
        
        self.json_logger.info("Voice interaction", extra={'extra_data': log_entry})
        
    def log_memory(self, operation: str, data: Dict[str, Any]):
        """Логирование операций с памятью"""
        log_entry = {
            "type": "memory",
            "operation": operation,
            "data_size": len(str(data)),
            "timestamp": datetime.now().isoformat()
        }
        
        self.json_logger.info(f"Memory {operation}", extra={'extra_data': log_entry})
        
    def log_performance(self, metric: str, value: float, context: str = ""):
        """Логирование производительности"""
        log_entry = {
            "type": "performance",
            "metric": metric,
            "value": value,
            "context": context,
            "timestamp": datetime.now().isoformat()
        }
        
        self.json_logger.info(f"Performance: {metric}", extra={'extra_data': log_entry})
        
    def get_log_stats(self) -> Dict[str, Any]:
        """Получение статистики логов"""
        log_file = Path("logs") / "elena.log"
        
        if not log_file.exists():
            return {"total_lines": 0, "last_modified": None}
            
        with open(log_file, 'r', encoding='utf-8') as f:
            lines = f.readlines()
            
        return {
            "total_lines": len(lines),
            "last_modified": datetime.fromtimestamp(log_file.stat().st_mtime).isoformat(),
            "file_size": log_file.stat().st_size
        }

# ============================================
# ФУНКЦИЯ ДЛЯ ОБРАТНОЙ СОВМЕСТИМОСТИ С main.py
# ============================================

def setup_logging(name: str = "elena", level: str = "INFO") -> ElenaLogger:
    """Настройка логирования"""
    return ElenaLogger(name)

__all__ = ['ElenaLogger', 'setup_logging']