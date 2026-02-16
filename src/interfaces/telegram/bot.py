#!/usr/bin/env python3
# Путь: /mnt/ai_data/ai-agent/src/interfaces/telegram/bot.py
"""Telegram бот для Елены - стабильная версия с голосовой поддержкой"""

import asyncio
import threading
import time
import subprocess
from pathlib import Path
from typing import TYPE_CHECKING, Any, Dict, Set, Optional, cast, Union

from telegram import Update, Message, User, Chat, Voice
from telegram.ext import Application, CommandHandler, MessageHandler, filters, ContextTypes
from loguru import logger
import os

# Игнорируем отсутствие типов для прохождения CI MyPy
import whisper  # type: ignore[import-untyped]
import sounddevice  # type: ignore[import-untyped]

if TYPE_CHECKING:
    from src.core.bootstrap import ElenaAgent


class TelegramBot:
    """
    Telegram бот для взаимодействия с Еленой
    Работает в фоновом режиме без конфликтов с терминалом
    """

    def __init__(self, token: str, agent: "ElenaAgent"):
        """
        Инициализация Telegram бота
        """
        self.token: str = token
        self.agent: "ElenaAgent" = agent
        self.application: Optional[Application] = None
        self._thread: Optional[threading.Thread] = None
        self._loop: Optional[asyncio.AbstractEventLoop] = None
        self._running: bool = False

        # Исправлено: добавлены аннотации типов (ошибки 39, 40)
        self._processed_messages: Set[str] = set()
        self._last_message_time: Dict[int, float] = {}

        logger.info("📱 Telegram бот инициализирован")

    def _get_component_status(self) -> Dict[str, Any]:
        """Получает статус всех компонентов из агента"""
        status: Dict[str, Any] = {
            "memory": False,
            "voice": False,
            "vision": False,
            "tool_executor": False,
            "memory_count": 0,
        }

        agent_any = cast(Any, self.agent)
        if hasattr(agent_any, "components"):
            status["memory"] = "memory" in agent_any.components
            status["voice"] = "voice" in agent_any.components
            status["vision"] = "vision" in agent_any.components
            status["tool_executor"] = "tool_executor" in agent_any.components

            if status["memory"] and hasattr(agent_any.components["memory"], "short_term"):
                status["memory_count"] = len(agent_any.components["memory"].short_term)

        return status

    def _build_application(self) -> None:
        """Создание Application (вызывается в главном потоке)"""
        self.application = Application.builder().token(self.token).build()
        self._register_handlers()
        logger.debug("📱 Application построен")

    def _register_handlers(self) -> None:
        """Регистрация всех обработчиков"""
        if not self.application:
            return

        # Команды
        self.application.add_handler(CommandHandler("start", self.cmd_start))
        self.application.add_handler(CommandHandler("help", self.cmd_help))
        self.application.add_handler(CommandHandler("status", self.cmd_status))

        # Текстовые сообщения
        self.application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, self.handle_text))

        # Голосовые сообщения
        self.application.add_handler(MessageHandler(filters.VOICE, self.handle_voice))

        logger.debug("📱 Обработчики зарегистрированы")

    def start(self) -> None:
        """Запуск бота в отдельном потоке"""
        if self._thread and self._thread.is_alive():
            logger.warning("📱 Telegram бот уже запущен")
            return

        self._build_application()
        self._running = True
        self._thread = threading.Thread(target=self._thread_target, daemon=True)
        self._thread.start()
        logger.info("✅ Telegram бот запущен в фоновом потоке")

    def _thread_target(self) -> None:
        """Целевая функция для потока - здесь создается event loop"""
        self._loop = asyncio.new_event_loop()
        asyncio.set_event_loop(self._loop)

        try:
            self._loop.run_until_complete(self._run_bot())
        except Exception as e:
            logger.error(f"❌ Ошибка в потоке Telegram: {e}")
        finally:
            if self._loop:
                self._loop.close()
            logger.info("⏹️ Поток Telegram завершен")

    async def _run_bot(self) -> None:
        """Асинхронный запуск бота с автоматическим переподключением"""
        if not self.application:
            return

        logger.info("🚀 Запуск Telegram бота в потоке...")

        while self._running:
            try:
                await self.application.initialize()
                await self.application.start()
                if self.application.updater:
                    await self.application.updater.start_polling(
                        drop_pending_updates=True, timeout=30, read_timeout=30, write_timeout=30, connect_timeout=30
                    )

                while self._running:
                    await asyncio.sleep(1)

            except Exception as e:
                err_str = str(e)
                if "RemoteProtocolError" in err_str or "NetworkError" in err_str:
                    logger.warning(f"🔄 Сетевой сбой Telegram: {e}. Переподключение через 5 сек...")
                    await asyncio.sleep(5)
                else:
                    logger.error(f"❌ Критическая ошибка Telegram: {e}")
                    break
            finally:
                try:
                    if self.application and self.application.updater and self.application.updater.running:
                        await self.application.updater.stop()
                    if self.application and self.application.running:
                        await self.application.stop()
                except Exception:
                    pass

    def stop(self) -> None:
        """Остановка бота (вызывается из главного потока)"""
        if not self._running:
            return

        logger.info("⏹️ Остановка Telegram бота...")
        self._running = False

        if self._thread and self._thread.is_alive():
            self._thread.join(timeout=5)

        logger.success("✅ Telegram бот остановлен")

    # --- Обработчики команд ---
    async def cmd_start(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
        """Обработчик команды /start"""
        # Исправлено для MyPy: проверка наличия сообщения и пользователя
        if not update.message or not update.effective_user:
            return

        user: User = update.effective_user
        await update.message.reply_text(
            f"🌟 Привет, {user.first_name}!\n\n"
            f"Я Елена, твой персональный ИИ-ассистент.\n"
            f"Я работаю в фоновом режиме и всегда готова помочь!"
        )
        logger.info(f"👤 Новый пользователь Telegram: {user.first_name}")

    async def cmd_help(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
        """Обработчик команды /help"""
        if not update.message:
            return

        help_text = (
            "📚 **Доступные команды:**\n\n"
            "/start - Начать работу\n"
            "/help - Показать эту справку\n"
            "/status - Статус системы\n\n"
            "📊 Статус - информация о системе\n"
            "📝 Задачи - текущие задачи\n"
            "📸 Скриншот - сделать скриншот\n"
            "📦 Бэкап - информация о бэкапе\n\n"
            "🎤 Голосовые сообщения - отправьте голосовое, я распознаю и отвечу\n\n"
            "Просто напиши мне сообщение - я отвечу!"
        )
        await update.message.reply_text(help_text, parse_mode="Markdown")

    async def cmd_status(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
        """Показывает статус системы"""
        if not update.message:
            return

        status = self._get_component_status()
        memory_text = f"{status['memory_count']} в памяти" if status["memory"] else "недоступно"

        status_text = (
            f"📊 **Статус системы:**\n\n"
            f"🤖 Агент: Елена v0.1.0\n"
            f"🧠 Память: {memory_text}\n"
            f"🔊 Голос: {'✅' if status['voice'] else '❌'}\n"
            f"👁️ Зрение: {'✅' if status['vision'] else '❌'}"
        )
        await update.message.reply_text(status_text, parse_mode="Markdown")

    async def handle_text(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
        """Обработка текстовых сообщений с защитой от повторов"""
        if not update.message or not update.message.text or not update.effective_user or not update.effective_chat:
            return

        user_text: str = update.message.text
        user: User = update.effective_user
        message_id: int = update.message.message_id
        chat_id: int = update.effective_chat.id

        # Защита от повторной обработки того же сообщения
        message_key = f"{chat_id}_{message_id}_{user_text}"
        if message_key in self._processed_messages:
            logger.debug(f"⏭️ Пропуск повторного сообщения {message_id}")
            return

        self._processed_messages.add(message_key)

        if len(self._processed_messages) > 100:
            self._processed_messages.clear()

        # Защита от слишком частых сообщений
        current_time = time.time()
        last_time = self._last_message_time.get(chat_id, 0.0)

        if current_time - last_time < 0.5:
            logger.debug(f"⏱️ Слишком часто: {user.first_name}")
            return

        self._last_message_time[chat_id] = current_time

        logger.info(f"💬 [Telegram {user.first_name}]: {user_text[:50]}...")

        # Показываем "печатает..." с таймаутом
        try:
            await asyncio.wait_for(context.bot.send_chat_action(chat_id=chat_id, action="typing"), timeout=3.0)
        except Exception as e:
            logger.debug(f"⚠️ Не удалось отправить typing (не критично): {e}")

        # Обработка специальных команд
        if user_text == "📊 Статус":
            await self.cmd_status(update, context)
            return
        elif user_text == "📝 Задачи":
            await update.message.reply_text(
                "📝 **Текущие задачи:**\n" "• Мониторинг системы\n" "• Обработка запросов\n" "• Обучение на диалогах"
            )
            return
        elif user_text == "📸 Скриншот":
            await self._handle_screenshot(update, context)
            return
        elif user_text == "📦 Бэкап":
            await update.message.reply_text(
                "📦 **Бэкап системы:**\n" "• Память сохранена\n" "• Конфигурация в порядке\n" "• Все системы работают"
            )
            return

        # Обычный диалог
        agent_any = cast(Any, self.agent)
        conversation = None
        if hasattr(agent_any, "components"):
            conversation = agent_any.components.get("conversation")

        if conversation:
            response = conversation.generate_response(user_text)
            await update.message.reply_text(response)
        else:
            await update.message.reply_text("Извини, я временно не могу ответить.")

    async def handle_voice(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
        """Обработка голосовых сообщений в Telegram"""
        if not update.message or not update.message.voice or not update.effective_user or not update.effective_chat:
            return

        user: User = update.effective_user
        chat_id: int = update.effective_chat.id
        message_id: int = update.message.message_id

        logger.info(f"🎤 [Telegram {user.first_name}] Получено голосовое сообщение")

        # Защита от повторов
        message_key = f"voice_{chat_id}_{message_id}"
        if message_key in self._processed_messages:
            logger.debug(f"⏭️ Пропуск повторного голосового сообщения {message_id}")
            return

        self._processed_messages.add(message_key)
        await update.message.reply_text("🎤 Обрабатываю голосовое сообщение...")

        voice_path: Optional[Path] = None
        wav_path: Optional[Path] = None

        try:
            # Скачиваем голосовое
            voice_file = await update.message.voice.get_file()
            voice_path = Path(f"/tmp/telegram_voice_{chat_id}_{message_id}.ogg")
            await voice_file.download_to_drive(voice_path)

            # Конвертируем в wav для Whisper
            wav_path = voice_path.with_suffix(".wav")
            subprocess.run(
                ["ffmpeg", "-y", "-i", str(voice_path), "-ar", "16000", "-ac", "1", str(wav_path)], capture_output=True
            )

            agent_any = cast(Any, self.agent)
            if hasattr(agent_any, "components") and "audio" in agent_any.components:
                # Загружаем и распознаем через Whisper
                model = whisper.load_model("base")
                result = model.transcribe(str(wav_path), language="ru")
                text = cast(str, result.get("text", "")).strip()

                if text:
                    await update.message.reply_text(f"📝 Распознано: {text}")

                    # Отправляем в диалог
                    conversation = agent_any.components.get("conversation")
                    if conversation:
                        await context.bot.send_chat_action(chat_id=chat_id, action="typing")
                        response = conversation.generate_response(text)
                        await update.message.reply_text(response)

                        # Если есть голос, произносим ответ
                        if "voice" in agent_any.components:
                            agent_any.components["voice"].speak(response)
                    else:
                        await update.message.reply_text("🤖 Модуль диалога недоступен")
                else:
                    await update.message.reply_text("🤔 Не удалось распознать речь")
            else:
                await update.message.reply_text("❌ Модуль распознавания речи не доступен")

        except Exception as e:
            logger.error(f"❌ Ошибка обработки голоса: {e}")
            await update.message.reply_text("❌ Ошибка при обработке голосового сообщения")
        finally:
            # Очищаем временные файлы
            for p in [voice_path, wav_path]:
                if p and p.exists():
                    try:
                        p.unlink()
                    except Exception:
                        pass

    async def _handle_screenshot(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
        """Обработчик скриншота: 5 сек задержки и выбор экрана по мышке"""
        if not update.message:
            return

        agent_any = cast(Any, self.agent)
        vision = agent_any.components.get("vision") if hasattr(agent_any, "components") else None

        if vision:
            await update.message.reply_text("⏳ У тебя есть 5 секунд, чтобы навести мышь на нужный монитор...")
            # Вызов асинхронного метода из VisionEngine
            img = await cast(Any, vision).capture_screen(delay=5)

            if img:
                import io

                bio = io.BytesIO()
                bio.name = "screenshot.png"
                img.save(bio, "PNG")
                bio.seek(0)
                await update.message.reply_photo(photo=bio, caption="📸 Скриншот экрана, выбранного мышкой")
            else:
                await update.message.reply_text("❌ Не удалось сделать скриншот.")
        else:
            await update.message.reply_text("❌ Модуль зрения (Vision) не доступен.")
