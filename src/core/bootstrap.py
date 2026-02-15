#!/usr/bin/env python3
# Путь: /mnt/ai_data/ai-agent/src/core/bootstrap.py
"""Загрузка и запуск агента Елены - финальная стабильная версия"""

import sys
import os
from pathlib import Path
import asyncio
import threading
from datetime import datetime

project_root = str(Path(__file__).parent.parent.parent)
if project_root not in sys.path:
    sys.path.insert(0, project_root)

from loguru import logger
from src.utils.config_loader import load_config
from src.utils.logger import setup_logger
from src.core.cognitive_loop import CognitiveLoop
from src.memory.memory_core import MemoryCore
from src.engines.vision_engine import VisionEngine
from src.engines.audio_engine import AudioEngine
from src.engines.voice_engine import VoiceEngine
from src.tools.conversation_tools import ConversationTools
from src.tools.tool_executor import ToolExecutor
from src.planning.planner_stage2 import Planner
from src.learning.self_improvement import SelfImprovement
from src.learning.cleanup import CleanupManager
from src.interfaces.telegram.bot import TelegramBot
from src.interfaces.browser.app import BrowserApp
from src.interfaces.obsidian.connector import ObsidianConnector
from src.security.auth import Authenticator


class ElenaAgent:
    """Главный класс агента Елены - финальная версия"""
    
    def __init__(self, test_mode: bool = False):
        self.test_mode = test_mode
        self.running = False
        self.components: dict[str, object] = {}  # ← ДОБАВИТЬ ЭТО
        self.browser_thread = None
        self.telegram_bot = None
        
        self._load_configuration()
        self._setup_logging()
        self._init_components()
        self._check_readiness()
    
    def _load_configuration(self):
        """Загрузка конфигурации"""
        print("📁 Загрузка конфигурации...")
        self.config = load_config()
        self.config['paths']['root'] = project_root
        self.config['paths']['data'] = str(Path(project_root) / 'data')
        self.config['paths']['models'] = str(Path(project_root) / 'models')
        self.config['paths']['logs'] = str(Path(project_root) / 'logs')
        print("✅ Конфигурация загружена")
    
    def _setup_logging(self):
        """Настройка логирования"""
        self.logger = setup_logger(self.config)
    
    def _init_components(self):
        """Инициализация всех компонентов"""
        print("\n🔧 Инициализация компонентов Елены...")
        
        try:
            # Основные компоненты
            self.components['memory'] = MemoryCore(self.config)
            print("   ✅ Память инициализирована")
            
            self.components['planner'] = Planner(self.config)
            print("   ✅ Планировщик инициализирован")
            
            self.components['tool_executor'] = ToolExecutor(self.config)
            print("   ✅ Исполнитель инструментов инициализирован")
            
            # Опциональные компоненты
            if not self.test_mode:
                # Голос
                try:
                    self.components['voice'] = VoiceEngine(self.config)
                    print("   ✅ Голосовой движок инициализирован")
                except Exception as e:
                    print(f"   ⚠️ Голосовой движок не загружен: {e}")
                
                # Аудио
                try:
                    self.components['audio'] = AudioEngine(self.config)
                    print("   ✅ Аудио движок инициализирован")
                except Exception as e:
                    print(f"   ⚠️ Аудио движок не загружен: {e}")
                
                # Зрение (nanoLLaVA)
                try:
                    self.components['vision'] = VisionEngine(self.config)
                    print("   ✅ Зрительный движок инициализирован")
                except Exception as e:
                    print(f"   ⚠️ Зрительный движок не загружен: {e}")
                
                # Самообучение
                try:
                    self.components['self_improvement'] = SelfImprovement(self.components['memory'])
                    print("   ✅ Модуль самообучения инициализирован")
                except Exception as e:
                    print(f"   ⚠️ Модуль самообучения не загружен: {e}")
                
                # Очистка
                try:
                    self.components['cleanup'] = CleanupManager(self.config)
                    print("   ✅ Менеджер очистки инициализирован")
                except Exception as e:
                    print(f"   ⚠️ Менеджер очистки не загружен: {e}")
                
                # Безопасность
                try:
                    self.components['auth'] = Authenticator(self.config)
                    print("   ✅ Модуль безопасности инициализирован")
                except Exception as e:
                    print(f"   ⚠️ Модуль безопасности не загружен: {e}")
            
            # Инструменты диалога (Ollama)
            self.components['conversation'] = ConversationTools(
                self.config,
                memory=self.components.get('memory'),
                voice=self.components.get('voice')
            )
            print("   ✅ Инструменты диалога инициализированы")
            
            # Когнитивный цикл
            self.components['cognitive_loop'] = CognitiveLoop(self)
            print("   ✅ Когнитивный цикл инициализирован")
            
            print("\n✅ Все компоненты инициализированы успешно")
            
        except Exception as e:
            print(f"\n❌ Критическая ошибка при инициализации: {e}")
            raise
    
    def _check_readiness(self):
        """Проверка готовности системы"""
        print("\n🔍 Проверка готовности...")
        checks_passed = True
        
        required_dirs = [
            self.config['paths']['data'],
            self.config['paths']['logs'],
            self.config['paths']['models'],
            os.path.join(self.config['paths']['data'], 'vectors'),
            os.path.join(self.config['paths']['data'], 'temp'),
            os.path.join(self.config['paths']['data'], 'cache'),
        ]
        
        for dir_path in required_dirs:
            if not os.path.exists(dir_path):
                try:
                    os.makedirs(dir_path, exist_ok=True)
                    print(f"   📁 Создана директория: {dir_path}")
                except Exception as e:
                    print(f"   ❌ Не удалось создать {dir_path}: {e}")
                    checks_passed = False
        
        if checks_passed:
            print("✅ Система готова")
        else:
            print("⚠️ Есть проблемы")
    
    def _show_welcome(self):
        """Показывает приветственное сообщение"""
        print("\n" + "="*60)
        print(" " * 15 + "🚀 ЕЛЕНА - ПЕРСОНАЛЬНЫЙ ИИ-АГЕНТ")
        print("="*60)
        print(f" Версия: 0.1.0")
        print(f" Режим: {'ТЕСТОВЫЙ' if self.test_mode else 'РАБОЧИЙ'}")
        print(f" Корень: {project_root}")
        print(f" Время: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        print("-"*60)
        print(" ЗАГРУЖЕННЫЕ КОМПОНЕНТЫ:")
        for name, comp in self.components.items():
            if name != 'cognitive_loop':
                print(f"   • {name}: {type(comp).__name__}")
        print("="*60)
    
    def _start_telegram(self):
        """Запуск Telegram бота в фоновом режиме"""
        if self.telegram_bot is not None:
            return
        
        telegram_token = os.getenv('TELEGRAM_TOKEN')
        if not telegram_token or telegram_token == '${TELEGRAM_TOKEN}':
            print("⚠️ Telegram токен не настроен. Пропускаем...")
            return
        
        try:
            self.telegram_bot = TelegramBot(telegram_token, self)
            self.telegram_bot.start()
            print("✅ Telegram бот запущен в фоне")
        except Exception as e:
            print(f"❌ Ошибка при запуске Telegram: {e}")
    
    def _open_browser(self):
        """Открывает веб-интерфейс в браузере"""
        if not self.browser_thread or not self.browser_thread.is_alive():
            def run_browser():
                try:
                    app = BrowserApp(self.config, self)
                    app.run()
                except Exception as e:
                    print(f"❌ Ошибка веб-интерфейса: {e}")
            
            self.browser_thread = threading.Thread(target=run_browser, daemon=True)
            self.browser_thread.start()
            import time
            time.sleep(2)
        
        import webbrowser
        url = f"http://localhost:{self.config['browser']['port']}"
        try:
            webbrowser.open_new(url)
            print(f"\n🌐 Браузер открыт: {url}")
        except Exception as e:
            print(f"⚠️ Не удалось открыть браузер: {e}")
    
    async def terminal_loop(self):
        """Основной цикл общения в терминале"""
        conversation = self.components.get('conversation')
        if not conversation:
            print("❌ Инструменты диалога не доступны")
            return
        
        print("\n" + "-"*60)
        print("💬 РЕЖИМ ОБЩЕНИЯ В ТЕРМИНАЛЕ")
        print("-"*60)
        print("(Введите 'браузер' для открытия веб-интерфейса)")
        print("(Введите 'выход' для завершения работы)")
        print("-"*60)
        
        while self.running:
            try:
                user_input = input("\n👤 Вы: ").strip()
                
                if user_input.lower() in ['выход', 'exit', 'quit', 'q']:
                    print("\n👋 Завершение работы...")
                    self.running = False
                    break
                    
                elif user_input.lower() in ['браузер', 'browser', 'web']:
                    self._open_browser()
                    continue
                    
                elif not user_input:
                    continue
                
                print("🤖 Елена думает...", end="", flush=True)
                response = conversation.generate_response(user_input)
                print("\r", end="")
                print(f"\n💬 Елена: {response}")
                
                                    
            except KeyboardInterrupt:
                print("\n\n👋 Получен сигнал прерывания")
                self.running = False
                break
            except Exception as e:
                print(f"\n❌ Ошибка: {e}")
    
    def _stop_services(self):
        """Остановка всех сервисов и выгрузка моделей"""
        print("\n🛑 Остановка сервисов...")
        
        # Останавливаем Telegram
        if hasattr(self, 'telegram_bot') and self.telegram_bot:
            try:
                self.telegram_bot.stop()
                print("   ✅ Telegram бот остановлен")
            except Exception as e:
                print(f"   ⚠️ Ошибка при остановке Telegram: {e}")
        
        # Останавливаем когнитивный цикл
        if 'cognitive_loop' in self.components:
            self.components['cognitive_loop'].stop()
            print("   ✅ Когнитивный цикл остановлен")
        
        # Сохраняем память
        if 'memory' in self.components:
            self.components['memory'].save_state()
            print("   ✅ Состояние памяти сохранено")
        
        # Ollama сам управляет памятью - не выгружаем Qwen
        # if 'conversation' in self.components and hasattr(self.components['conversation'], 'unload_model'):
        #     self.components['conversation'].unload_model()
        #     print("   ✅ Qwen выгружен из GPU")
        
        # Выгружаем nanoLLaVA из памяти
        if 'vision' in self.components and hasattr(self.components['vision'], 'unload_model'):
            self.components['vision'].unload_model()
            print("   ✅ nanoLLaVA выгружен из GPU")
        
        # Прощаемся голосом
        if 'voice' in self.components:
            self.components['voice'].speak("До свидания!")
            self.components['voice'].cleanup()
            print("   ✅ Голосовой движок остановлен")
        
        print("✅ Все сервисы остановлены")
    
    async def run(self):
        """Основной метод запуска"""
        self.running = True
        self._show_welcome()
        
        # Приветствуем голосом
        if 'voice' in self.components:
            self.components['voice'].speak("Привет! Я Елена. Я готова к работе. Можем общаться здесь или ввести браузер для открытия веб-интерфейса.")
        
        self._start_telegram()
        cognitive_task = asyncio.create_task(self.components['cognitive_loop'].run())
        
        try:
            await self.terminal_loop()
        finally:
            self.running = False
            if cognitive_task:
                cognitive_task.cancel()
            self._stop_services()


async def main_async():
    """Асинхронная главная функция"""
    import argparse
    parser = argparse.ArgumentParser()
    parser.add_argument('--test', action='store_true')
    args = parser.parse_args()
    
    try:
        agent = ElenaAgent(test_mode=args.test)
        await agent.run()
    except KeyboardInterrupt:
        print("\n👋 Программа остановлена пользователем")
    except Exception as e:
        print(f"\n❌ Фатальная ошибка: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)


def main():
    """Синхронная обёртка"""
    asyncio.run(main_async())


if __name__ == "__main__":
    main()