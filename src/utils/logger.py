#!/usr/bin/env python3
# Путь: /mnt/ai_data/ai-agent/src/utils/logger.py
"""Настройка логирования для Елены - финальная версия"""

import sys
from pathlib import Path
from loguru import logger

# Убираем стандартный вывод в stderr по умолчанию
logger.remove()


def setup_logger(config: dict) -> logger:
    """
    Настройка логгера с ротацией файлов и фильтрацией
    
    Args:
        config: словарь с конфигурацией
        
    Returns:
        настроенный логгер
    """
    log_config = config.get('logging', {})
    log_level = log_config.get('level', 'INFO')
    log_file = Path(log_config.get('file', 'logs/app.log'))
    
    # Создаём директорию для логов
    log_file.parent.mkdir(parents=True, exist_ok=True)
    
    # Добавляем вывод в консоль (только важное, без спама от Telegram)
    logger.add(
        sys.stderr,
        format="<green>{time:YYYY-MM-DD HH:mm:ss}</green> | <level>{level: <8}</level> | <cyan>{name}</cyan>:<cyan>{function}</cyan>:<cyan>{line}</cyan> - <level>{message}</level>",
        level=log_level,
        colorize=True,
        filter=lambda record: "telegram" not in record["name"].lower() or record["level"].no >= 30  # Фильтруем INFO от Telegram
    )
    
    # Добавляем вывод в файл (полный, без фильтрации)
    logger.add(
        str(log_file),
        format="{time:YYYY-MM-DD HH:mm:ss} | {level: <8} | {name}:{function}:{line} - {message}",
        level=log_level,
        rotation=log_config.get('rotation', '10 MB'),
        retention=log_config.get('retention', '30 days'),
        compression='zip',
        encoding='utf-8',
        backtrace=True,
        diagnose=True
    )
    
    # Добавляем отдельный файл для ошибок
    error_file = log_file.parent / 'error.log'
    logger.add(
        str(error_file),
        format="{time:YYYY-MM-DD HH:mm:ss} | {level: <8} | {name}:{function}:{line} - {message}",
        level='ERROR',
        rotation='10 MB',
        retention='30 days',
        compression='zip',
        encoding='utf-8',
        backtrace=True,
        diagnose=True
    )
    
    # Добавляем отдельный файл для отладки Telegram (если нужно)
    telegram_file = log_file.parent / 'telegram.log'
    logger.add(
        str(telegram_file),
        format="{time:YYYY-MM-DD HH:mm:ss} | {level: <8} | {name}:{function}:{line} - {message}",
        level='DEBUG',
        rotation='5 MB',
        retention='7 days',
        compression='zip',
        encoding='utf-8',
        filter=lambda record: "telegram" in record["name"].lower()
    )
    
    logger.success("✅ Логирование настроено")
    return logger