"""
Основной класс ИИ-агента Елена
"""

import asyncio
import logging
from datetime import datetime
from typing import Dict, Any, Optional
from dataclasses import dataclass
import sys
import os

sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(__file__))))

from configs.main import config
from memory.memory_manager import MemoryManager
from interfaces.voice.tts.synthesizer import SpeechSynthesizer
from interfaces.voice.stt.recognizer import SpeechRecognizer
from engines.vision_engine import VisionEngine
from tools.conversation_tools import ConversationManager

logger = logging.getLogger(__name__)

@dataclass
class AgentState:
    """Состояние агента"""
    is_active: bool = True
    is_listening: bool = False
    is_speaking: bool = False
    current_task: Optional[str] = None
    last_interaction: Optional[datetime] = None
    emotion: str = "нейтральное"

class ElenaAgent:
    """Основной класс ИИ-агента Елена"""
    
    def __init__(self):
        logger.info("🎀 Инициализация Елены...")
        
        # Основные компоненты
        self.state = AgentState()
        self.config = config
        
        # Инициализация компонентов
        self.memory = MemoryManager()
        self.speech_synth = SpeechSynthesizer()
        self.speech_recognizer = SpeechRecognizer()
        self.vision_engine = VisionEngine()
        self.conversation = ConversationManager()
        
        # Инициализация интерфейсов
        self._init_interfaces()
        
        logger.info("✨ Елена готова к работе!")
        
    def _init_interfaces(self):
        """Инициализация интерфейсов"""
        from interfaces.telegram.bot import TelegramBot
        from interfaces.browser.views import BrowserInterface
        from interfaces.obsidian.connector import ObsidianConnector
        
        if self.config.interfaces.telegram.enabled:
            self.telegram_bot = TelegramBot()
            
        if self.config.interfaces.browser.enabled:
            self.browser_interface = BrowserInterface()
            
        if self.config.interfaces.obsidian.enabled:
            self.obsidian = ObsidianConnector(self.config.interfaces.obsidian.vault_path)
            
    async def run(self):
        """Основной цикл работы агента"""
        logger.info("🔄 Запуск основного цикла Елены")
        
        while self.state.is_active:
            try:
                # Проверка голосовых команд
                if self.config.interfaces.voice.enabled:
                    await self._check_voice_commands()
                    
                # Проверка Telegram сообщений
                if self.config.interfaces.telegram.enabled:
                    await self._check_telegram_messages()
                    
                # Самообучение и очистка
                await self._self_improvement_cycle()
                
                await asyncio.sleep(0.1)
                
            except Exception as e:
                logger.error(f"Ошибка в основном цикле: {e}")
                
    async def _check_voice_commands(self):
        """Проверка голосовых команд"""
        if not self.state.is_speaking:
            text = self.speech_recognizer.listen()
            if text and self._is_wake_word(text):
                await self._process_command(text)
                
    async def _check_telegram_messages(self):
        """Проверка сообщений Telegram"""
        # Реализация в Telegram боте
        pass
        
    def _is_wake_word(self, text: str) -> bool:
        """Проверка ключевых слов"""
        wake_words = ["елена", "лена", "помоги", "слушай", "внимание"]
        return any(word in text.lower() for word in wake_words)
        
    async def _process_command(self, command: str):
        """Обработка команд"""
        logger.info(f"🎤 Команда: {command}")
        
        # Анализ команды
        response = await self.conversation.process_query(command)
        
        # Голосовой ответ
        if self.config.interfaces.voice.enabled:
            self.speak(response)
            
        # Сохранение в память
        self.memory.store_interaction(command, response)
        
    def speak(self, text: str):
        """Произнести текст"""
        self.state.is_speaking = True
        try:
            self.speech_synth.speak(text)
        finally:
            self.state.is_speaking = False
            
    async def _self_improvement_cycle(self):
        """Цикл самообучения и очистки"""
        # Проверяем время последнего обучения
        last_learning = self.memory.get_last_learning_time()
        current_time = datetime.now()
        
        if (current_time - last_learning).seconds > self.config.self_improvement.feedback_interval:
            await self._learn_from_interactions()
            
        # Очистка старых файлов
        if (current_time - last_learning).days >= 1:
            await self._cleanup_old_files()
            
    async def _learn_from_interactions(self):
        """Обучение на основе взаимодействий"""
        logger.info("🧠 Самообучение на основе опыта...")
        # Реализация обучения
        pass
        
    async def _cleanup_old_files(self):
        """Очистка старых файлов"""
        logger.info("🧹 Очистка устаревших файлов...")
        # Реализация очистки
        pass
        
    def stop(self):
        """Остановка агента"""
        logger.info("🛑 Остановка Елены...")
        self.state.is_active = False
        
if __name__ == "__main__":
    # Создаем и запускаем агента
    agent = ElenaAgent()
    asyncio.run(agent.run())