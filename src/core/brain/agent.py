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
import yaml

# ============================================
# ЗАГРУЗКА КОНФИГУРАЦИИ ИЗ YAML
# ============================================

class Config:
    """Класс-обёртка для YAML конфигурации"""
    def __init__(self, data):
        for key, value in data.items():
            if isinstance(value, dict):
                setattr(self, key, Config(value))
            else:
                setattr(self, key, value)

def load_config():
    """Загрузка конфигурации из main.yaml"""
    config_path = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), '..', '..', 'configs', 'main.yaml')
    config_path = os.path.abspath(config_path)
    
    try:
        with open(config_path, 'r', encoding='utf-8') as f:
            config_data = yaml.safe_load(f)
        print(f"✅ Конфигурация загружена из: {config_path}")
        return Config(config_data)
    except FileNotFoundError:
        print(f"⚠️ Конфиг не найден: {config_path}")
        print("   Использую конфигурацию по умолчанию")
        return default_config()
    except Exception as e:
        print(f"⚠️ Ошибка загрузки конфига: {e}")
        return default_config()

def default_config():
    """Конфигурация по умолчанию"""
    return Config({
        'agent': {
            'name': 'Елена',
            'version': '1.0.0',
            'language': 'ru'
        },
        'voice': {
            'engine': 'rhvoice',
            'voice_name': 'elena',
            'rate': 150,
            'volume': 0.9,
            'stt_engine': 'whisper',
            'language': 'ru',
            'timeout': 5,
            'phrase_time_limit': 10
        },
        'interfaces': {
            'voice': {'enabled': True},
            'telegram': {'enabled': False},
            'browser': {'enabled': False},
            'obsidian': {
                'enabled': False,
                'vault_path': '/mnt/ai_data/ai-agent/Ai_Obsidian'
            }
        },
        'self_improvement': {
            'feedback_interval': 3600
        }
    })

# Загружаем конфигурацию
config = load_config()

# ============================================
# ИМПОРТЫ КОМПОНЕНТОВ — ПОЛНЫЕ ПУТИ С src.
# ============================================

from src.core.memory.memory_manager import MemoryManager
from src.interfaces.voice.tts.synthesizer import SpeechSynthesizer
from src.interfaces.voice.stt.recognizer import SpeechRecognizer
from src.tools.conversation_tools import ConversationManager
from src.core.brain.cognitive_loop import CognitiveLoop
from src.core.brain.execution import ExecutionEngine
from src.core.brain.planning import PlanningModule
from src.core.brain.reasoning import ReasoningEngine

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
        
        # Инициализация компонентов с защитой от ошибок
        self.memory = None
        self.speech_synth = None
        self.speech_recognizer = None
        self.vision_engine = None  # Оставляем None, VisionEngine отключён
        self.conversation = None
        self.cognitive_loop = None
        self.execution_engine = None
        self.planning = None
        self.reasoning = None
        
        try:
            self.memory = MemoryManager()
            logger.info("✅ MemoryManager загружен")
        except Exception as e:
            logger.error(f"❌ Ошибка MemoryManager: {e}")
            
        try:
            self.speech_synth = SpeechSynthesizer()
            logger.info("✅ SpeechSynthesizer загружен")
        except Exception as e:
            logger.error(f"❌ Ошибка SpeechSynthesizer: {e}")
            
        try:
            self.speech_recognizer = SpeechRecognizer()
            logger.info("✅ SpeechRecognizer загружен")
        except Exception as e:
            logger.error(f"❌ Ошибка SpeechRecognizer: {e}")
            
        # VisionEngine временно отключён
        self.vision_engine = None
        logger.info("⚠️ VisionEngine временно отключён")
            
        try:
            self.conversation = ConversationManager()
            logger.info("✅ ConversationManager загружен")
        except Exception as e:
            logger.error(f"❌ Ошибка ConversationManager: {e}")
            
        try:
            self.cognitive_loop = CognitiveLoop(self.memory, None)
            logger.info("✅ CognitiveLoop загружен")
        except Exception as e:
            logger.error(f"❌ Ошибка CognitiveLoop: {e}")
            
        try:
            self.execution_engine = ExecutionEngine()
            logger.info("✅ ExecutionEngine загружен")
        except Exception as e:
            logger.error(f"❌ Ошибка ExecutionEngine: {e}")
            
        try:
            self.planning = PlanningModule(self.memory, self.execution_engine)
            logger.info("✅ PlanningModule загружен")
        except Exception as e:
            logger.error(f"❌ Ошибка PlanningModule: {e}")
            
        try:
            self.reasoning = ReasoningEngine(self.memory)
            logger.info("✅ ReasoningEngine загружен")
        except Exception as e:
            logger.error(f"❌ Ошибка ReasoningEngine: {e}")
        
        # Инициализация интерфейсов
        self._init_interfaces()
        
        logger.info("✨ Елена готова к работе!")
        
    def _init_interfaces(self):
        """Инициализация интерфейсов"""
        try:
            # Telegram
            if hasattr(self.config, 'interfaces') and hasattr(self.config.interfaces, 'telegram'):
                if getattr(self.config.interfaces.telegram, 'enabled', False):
                    from src.interfaces.telegram.bot import TelegramBot
                    self.telegram_bot = TelegramBot()
                    logger.info("✅ TelegramBot загружен")
            
            # Browser
            if hasattr(self.config, 'interfaces') and hasattr(self.config.interfaces, 'browser'):
                if getattr(self.config.interfaces.browser, 'enabled', False):
                    from src.interfaces.browser.views import BrowserInterface
                    self.browser_interface = BrowserInterface()
                    logger.info("✅ BrowserInterface загружен")
            
            # Obsidian
            if hasattr(self.config, 'interfaces') and hasattr(self.config.interfaces, 'obsidian'):
                if getattr(self.config.interfaces.obsidian, 'enabled', False):
                    from src.interfaces.obsidian.connector import ObsidianConnector
                    vault_path = getattr(self.config.interfaces.obsidian, 'vault_path', '/mnt/ai_data/ai-agent/Ai_Obsidian')
                    self.obsidian = ObsidianConnector(vault_path)
                    logger.info("✅ ObsidianConnector загружен")
                    
        except Exception as e:
            logger.error(f"⚠️ Ошибка инициализации интерфейсов: {e}")
            
    async def run(self):
        """Основной цикл работы агента"""
        logger.info("🔄 Запуск основного цикла Елены")
        print("\n🎀 Елена запущена в полной версии!")
        print("   Ожидание команд...\n")
        
        while self.state.is_active:
            try:
                # Проверка голосовых команд
                if self._is_voice_enabled() and self.speech_recognizer:
                    await self._check_voice_commands()
                
                # Telegram сообщения
                if hasattr(self, 'telegram_bot'):
                    await self._check_telegram_messages()
                
                # Самообучение
                if self._is_self_improvement_enabled() and self.memory:
                    await self._self_improvement_cycle()
                
                await asyncio.sleep(0.1)
                
            except KeyboardInterrupt:
                self.stop()
                break
            except Exception as e:
                logger.error(f"Ошибка в основном цикле: {e}")
                
    def _is_voice_enabled(self) -> bool:
        """Проверка включен ли голосовой интерфейс"""
        try:
            return hasattr(self.config, 'interfaces') and \
                   hasattr(self.config.interfaces, 'voice') and \
                   getattr(self.config.interfaces.voice, 'enabled', False)
        except:
            return False
            
    def _is_self_improvement_enabled(self) -> bool:
        """Проверка включено ли самообучение"""
        try:
            return hasattr(self.config, 'self_improvement') and \
                   getattr(self.config.self_improvement, 'enabled', True)
        except:
            return True
                
    async def _check_voice_commands(self):
        """Проверка голосовых команд"""
        if not self.state.is_speaking and self.speech_recognizer:
            try:
                text = self.speech_recognizer.listen()
                if text and self._is_wake_word(text):
                    await self._process_command(text)
            except Exception as e:
                logger.error(f"Ошибка голосовой команды: {e}")
                
    async def _check_telegram_messages(self):
        """Проверка сообщений Telegram"""
        if hasattr(self, 'telegram_bot'):
            try:
                await self.telegram_bot.process_updates()
            except Exception as e:
                logger.error(f"Ошибка Telegram: {e}")
        
    def _is_wake_word(self, text: str) -> bool:
        """Проверка ключевых слов"""
        wake_words = ["елена", "лена", "помоги", "слушай", "внимание"]
        return any(word in text.lower() for word in wake_words)
        
    async def _process_command(self, command: str):
        """Обработка команд"""
        logger.info(f"🎤 Команда: {command}")
        
        # Анализ команды
        response = "Я вас слушаю. Чем могу помочь?"
        if self.conversation:
            try:
                response = await self.conversation.process_query(command)
            except Exception as e:
                logger.error(f"Ошибка обработки команды: {e}")
        
        # Голосовой ответ
        if self._is_voice_enabled() and self.speech_synth:
            self.speak(response)
        else:
            print(f"🎀 Елена: {response}")
        
        # Сохранение в память
        if self.memory:
            try:
                self.memory.store_interaction(command, response)
            except Exception as e:
                logger.error(f"Ошибка сохранения в память: {e}")
        
    def speak(self, text: str):
        """Произнести текст"""
        self.state.is_speaking = True
        try:
            if self.speech_synth:
                self.speech_synth.speak(text)
            else:
                # Fallback на простой голос
                try:
                    from simple_voice import SimpleVoice
                    voice = SimpleVoice()
                    voice.speak(text)
                except:
                    print(f"💬 Елена: {text}")
        finally:
            self.state.is_speaking = False
            
    async def _self_improvement_cycle(self):
        """Цикл самообучения и очистки"""
        if not self.memory:
            return
            
        try:
            last_learning = self.memory.get_last_learning_time()
            current_time = datetime.now()
            
            if hasattr(self.config, 'self_improvement'):
                interval = getattr(self.config.self_improvement, 'feedback_interval', 3600)
                if (current_time - last_learning).seconds > interval:
                    await self._learn_from_interactions()
            
            # Очистка старых файлов
            if (current_time - last_learning).days >= 1:
                await self._cleanup_old_files()
                
        except Exception as e:
            logger.error(f"Ошибка в цикле самообучения: {e}")
            
    async def _learn_from_interactions(self):
        """Обучение на основе взаимодействий"""
        logger.info("🧠 Самообучение...")
        pass
        
    async def _cleanup_old_files(self):
        """Очистка старых файлов"""
        logger.info("🧹 Очистка...")
        pass
        
    def stop(self):
        """Остановка агента"""
        logger.info("🛑 Остановка Елены...")
        self.state.is_active = False
        print("\n👋 Елена завершила работу. До встречи!")
        
if __name__ == "__main__":
    # Создаем и запускаем агента
    agent = ElenaAgent()
    try:
        asyncio.run(agent.run())
    except KeyboardInterrupt:
        agent.stop()
    except Exception as e:
        print(f"❌ Критическая ошибка: {e}")
        agent.stop()