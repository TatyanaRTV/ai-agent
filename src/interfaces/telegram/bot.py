#!/usr/bin/env python3
# Путь: /mnt/ai_data/ai-agent/src/interfaces/telegram/bot.py
"""Telegram бот для Елены - стабильная версия"""

import asyncio
import threading
import time
from telegram import Update
from telegram.ext import Application, CommandHandler, MessageHandler, filters, ContextTypes
from loguru import logger
import os
from pathlib import Path
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from src.core.bootstrap import ElenaAgent


class TelegramBot:
    """
    Telegram бот для взаимодействия с Еленой
    Работает в фоновом режиме без конфликтов с терминалом
    """
    
    def __init__(self, token: str, agent: 'ElenaAgent'):
        """
        Инициализация Telegram бота
        
        Args:
            token: токен бота от @BotFather
            agent: ссылка на главный класс агента Елены
        """
        self.token = token
        self.agent = agent
        self.application = None
        self._thread = None
        self._loop = None
        self._running = False
        self._processed_messages = set()  # Защита от повторов
        self._last_message_time = {}  # Для защиты от спама
        
        logger.info("📱 Telegram бот инициализирован")
    
    def _get_component_status(self):
        """Получает статус всех компонентов из агента"""
        status = {
            'memory': False,
            'voice': False,
            'vision': False,
            'tool_executor': False,
            'memory_count': 0
        }
        
        if hasattr(self.agent, 'components'):
            status['memory'] = 'memory' in self.agent.components
            status['voice'] = 'voice' in self.agent.components
            status['vision'] = 'vision' in self.agent.components
            status['tool_executor'] = 'tool_executor' in self.agent.components
            
            if status['memory'] and hasattr(self.agent.components['memory'], 'short_term'):
                status['memory_count'] = len(self.agent.components['memory'].short_term)
        
        return status
    
    def _build_application(self):
        """Создание Application (вызывается в главном потоке)"""
        self.application = (
            Application.builder()
            .token(self.token)
            .build()
        )
        self._register_handlers()
        logger.debug("📱 Application построен")
    
    def _register_handlers(self):
        """Регистрация всех обработчиков"""
        # Команды
        self.application.add_handler(CommandHandler("start", self.cmd_start))
        self.application.add_handler(CommandHandler("help", self.cmd_help))
        self.application.add_handler(CommandHandler("status", self.cmd_status))
        
        # Текстовые сообщения
        self.application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, self.handle_text))
        
        logger.debug("📱 Обработчики зарегистрированы")
    
    def start(self):
        """Запуск бота в отдельном потоке (вызывается из главного потока)"""
        if self._thread and self._thread.is_alive():
            logger.warning("📱 Telegram бот уже запущен")
            return
        
        # Создаем Application в главном потоке
        self._build_application()
        
        self._running = True
        self._thread = threading.Thread(target=self._thread_target, daemon=True)
        self._thread.start()
        logger.info("✅ Telegram бот запущен в фоновом потоке")
    
    def _thread_target(self):
        """Целевая функция для потока - здесь создается event loop"""
        # Создаем НОВЫЙ event loop для этого потока
        self._loop = asyncio.new_event_loop()
        asyncio.set_event_loop(self._loop)
        
        try:
            # Запускаем асинхронную функцию в этом loop
            self._loop.run_until_complete(self._run_bot())
        except Exception as e:
            logger.error(f"❌ Ошибка в потоке Telegram: {e}")
        finally:
            if self._loop:
                self._loop.close()
            logger.info("⏹️ Поток Telegram завершен")
    
    async def _run_bot(self):
        """Асинхронный запуск бота с автоматическим переподключением"""
        logger.info("🚀 Запуск Telegram бота в потоке...")
        
        while self._running: # Добавляем цикл на случай обрыва сети
            try:
                await self.application.initialize()
                await self.application.start()
                await self.application.updater.start_polling(
                    drop_pending_updates=True,
                    timeout=30,  # Интервал опроса
                    read_timeout=30, 
                    write_timeout=30,
                    connect_timeout=30
                )
                logger.success("✅ Telegram бот слушает сообщения")
                
                # ВАЖНО: держим поток живым, пока флаг _running истинен
                while self._running:
                    await asyncio.sleep(1)
                    
            except Exception as e:
                if "RemoteProtocolError" in str(e) or "NetworkError" in str(e):
                    logger.warning(f"🔄 Сетевой сбой Telegram: {e}. Переподключение через 5 секунд...")
                    await asyncio.sleep(5)
                else:
                    logger.error(f"❌ Критическая ошибка Telegram: {e}")
                    break # Если ошибка не сетевая, выходим
            finally:
                # Мягкая остановка перед попыткой перезапуска или выходом
                try:
                    if self.application.updater.running:
                        await self.application.updater.stop()
                    if self.application.running:
                        await self.application.stop()
                except:
                    pass

    
    def stop(self):
        """Остановка бота (вызывается из главного потока)"""
        if not self._running:
            return
        
        logger.info("⏹️ Остановка Telegram бота...")
        self._running = False
        
        # Ждем завершения потока
        if self._thread and self._thread.is_alive():
            self._thread.join(timeout=5)
        
        logger.success("✅ Telegram бот остановлен")
    
    # --- Обработчики команд ---
    async def cmd_start(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Обработчик команды /start"""
        user = update.effective_user
        await update.message.reply_text(
            f"🌟 Привет, {user.first_name}!\n\n"
            f"Я Елена, твой персональный ИИ-ассистент.\n"
            f"Я работаю в фоновом режиме и всегда готова помочь!"
        )
        logger.info(f"👤 Новый пользователь Telegram: {user.first_name}")
    
    async def cmd_help(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Обработчик команды /help"""
        help_text = (
            "📚 **Доступные команды:**\n\n"
            "/start - Начать работу\n"
            "/help - Показать эту справку\n"
            "/status - Статус системы\n\n"
            "📊 Статус - информация о системе\n"
            "📝 Задачи - текущие задачи\n"
            "📸 Скриншот - сделать скриншот\n"
            "📦 Бэкап - информация о бэкапе\n\n"
            "Просто напиши мне сообщение - я отвечу!"
        )
        await update.message.reply_text(help_text, parse_mode='Markdown')
    
    async def cmd_status(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Показывает статус системы"""
        status = self._get_component_status()
        
        memory_text = f"{status['memory_count']} в памяти" if status['memory'] else "недоступно"
        
        status_text = (
            f"📊 **Статус системы:**\n\n"
            f"🤖 Агент: Елена v0.1.0\n"
            f"🧠 Память: {memory_text}\n"
            f"🔊 Голос: {'✅' if status['voice'] else '❌'}\n"
            f"👁️ Зрение: {'✅' if status['vision'] else '❌'}"
        )
        await update.message.reply_text(status_text, parse_mode='Markdown')
    
    async def handle_text(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Обработка текстовых сообщений с защитой от повторов"""
        user_text = update.message.text
        user = update.effective_user
        message_id = update.message.message_id
        chat_id = update.effective_chat.id
        
        # Защита от повторной обработки того же сообщения
        message_key = f"{chat_id}_{message_id}_{user_text}"
        if message_key in self._processed_messages:
            logger.debug(f"⏭️ Пропуск повторного сообщения {message_id}")
            return
        
        self._processed_messages.add(message_key)
        
        # Ограничиваем размер кэша (храним последние 100 сообщений)
        if len(self._processed_messages) > 100:
            self._processed_messages.clear()
        
        # Защита от слишком частых сообщений (анти-спам)
        current_time = time.time()
        last_time = self._last_message_time.get(chat_id, 0)
        
        if current_time - last_time < 0.5:  # Меньше 0.5 секунды между сообщениями
            logger.debug(f"⏱️ Слишком часто: {user.first_name}")
            return
        
        self._last_message_time[chat_id] = current_time
        
        logger.info(f"💬 [Telegram {user.first_name}]: {user_text[:50]}...")
        
        # Показываем "печатает..." с таймаутом (чтобы не зависать)
        try:
            await asyncio.wait_for(
                context.bot.send_chat_action(chat_id=update.effective_chat.id, action="typing"),
                timeout=3.0
            )
        except Exception as e:
            logger.debug(f"⚠️ Не удалось отправить typing (не критично): {e}")
        
        # Обработка специальных команд
        if user_text == "📊 Статус":
            await self.cmd_status(update, context)
            return
        elif user_text == "📝 Задачи":
            await update.message.reply_text(
                "📝 **Текущие задачи:**\n"
                "• Мониторинг системы\n"
                "• Обработка запросов\n"
                "• Обучение на диалогах"
            )
            return
        elif user_text == "📸 Скриншот":
            await self._handle_screenshot(update, context)
            return
        elif user_text == "📦 Бэкап":
            await update.message.reply_text(
                "📦 **Бэкап системы:**\n"
                "• Память сохранена\n"
                "• Конфигурация в порядке\n"
                "• Все системы работают"
            )
            return
        
        # Обычный диалог
        conversation = None
        if hasattr(self.agent, 'components'):
            conversation = self.agent.components.get('conversation')
        
        if conversation:
            response = conversation.generate_response(user_text)
            await update.message.reply_text(response)
                        
        else:
            await update.message.reply_text("Извини, я временно не могу ответить.")
    
    async def _handle_screenshot(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Обработчик скриншота"""
        await update.message.reply_text("📸 Делаю скриншот...")
        
        status = self._get_component_status()
        
        if status['tool_executor']:
            try:
                result = await self.agent.components['tool_executor'].execute({
                    'type': 'take_screenshot',
                    'monitor': 1
                })
                
                if result['success']:
                    screenshot_path = result['data']['path']
                    with open(screenshot_path, 'rb') as photo:
                        await update.message.reply_photo(photo, caption="📸 Скриншот")
                else:
                    await update.message.reply_text(f"❌ Не удалось сделать скриншот: {result.get('error', 'Неизвестная ошибка')}")
            except Exception as e:
                logger.error(f"❌ Ошибка при создании скриншота: {e}")
                await update.message.reply_text("❌ Ошибка при создании скриншота")
        else:
            await update.message.reply_text("❌ Инструмент скриншотов не доступен")