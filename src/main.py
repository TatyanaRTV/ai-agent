"""
Главный модуль запуска ИИ-агента Елена
"""

import sys
import os
import asyncio
import logging
from datetime import datetime

# Добавляем корневую папку в путь для импортов
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from src.core.brain.agent import ElenaAgent
from src.utils.logging import setup_logging

def print_banner():
    """Печать красивого баннера"""
    banner = """
    ╔══════════════════════════════════════════════════════════╗
    ║                                                          ║
    ║     🎀  И И - А Г Е Н Т   Е Л Е Н А  🎀                 ║
    ║                                                          ║
    ║     Универсальный самообучающийся помощник              ║
    ║     с женским русским голосом                           ║
    ║                                                          ║
    ╚══════════════════════════════════════════════════════════╝
    """
    print(banner)
    print(f"Дата и время запуска: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"Текущая директория: {os.getcwd()}")
    print()

async def main():
    """Основная асинхронная функция"""
    # Настройка логирования
    logger = setup_logging()
    
    try:
        print_banner()
        logger.info("Запуск ИИ-агента Елена...")
        
        # Создание экземпляра агента
        agent = ElenaAgent()
        
        # Запуск агента
        await agent.run()
        
    except KeyboardInterrupt:
        logger.info("Получен сигнал прерывания (Ctrl+C)")
    except Exception as e:
        logger.error(f"Критическая ошибка: {e}", exc_info=True)
        return 1
    
    logger.info("Работа агента завершена")
    return 0

if __name__ == "__main__":
    # Запуск асинхронного main
    exit_code = asyncio.run(main())
    sys.exit(exit_code)