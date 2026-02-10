"""
Telegram бот для взаимодействия с агентом
"""

import logging
from telegram import Update, Bot, InlineKeyboardMarkup, InlineKeyboardButton
from telegram.ext import Application, CommandHandler, MessageHandler, filters, CallbackQueryHandler, ContextTypes
from typing import Dict, Any, Optional
import asyncio

logger = logging.getLogger(__name__)

class TelegramBot:
    """Telegram бот для взаимодействия с пользователем"""
    
    def __init__(self, token: str, agent_instance):
        self.token = token
        self.agent = agent_instance
        self.application = None
        self.user_sessions = {}  # Сессии пользователей
        
    async def start(self):
        """Запуск бота"""
        logger.info("🤖 Запуск Telegram бота...")
        
        # Создание приложения
        self.application = Application.builder().token(self.token).build()
        
        # Регистрация обработчиков
        self._register_handlers()
        
        # Запуск бота
        await self.application.initialize()
        await self.application.start()
        await self.application.updater.start_polling()
        
        logger.info("✅ Telegram бот запущен и готов к работе")
        
    def _register_handlers(self):
        """Регистрация обработчиков команд"""
        
        # Команды
        self.application.add_handler(CommandHandler("start", self._handle_start))
        self.application.add_handler(CommandHandler("help", self._handle_help))
        self.application.add_handler(CommandHandler("status", self._handle_status))
        self.application.add_handler(CommandHandler("memory", self._handle_memory))
        self.application.add_handler(CommandHandler("cleanup", self._handle_cleanup))
        self.application.add_handler(CommandHandler("voice", self._handle_voice))
        self.application.add_handler(CommandHandler("screen", self._handle_screen))
        
        # Обработка документов
        self.application.add_handler(MessageHandler(
            filters.Document.ALL, self._handle_document
        ))
        
        # Обработка изображений
        self.application.add_handler(MessageHandler(
            filters.PHOTO, self._handle_photo
        ))
        
        # Обработка голосовых сообщений
        self.application.add_handler(MessageHandler(
            filters.VOICE, self._handle_voice_message
        ))
        
        # Обработка текстовых сообщений
        self.application.add_handler(MessageHandler(
            filters.TEXT & ~filters.COMMAND, self._handle_text
        ))
        
        # Обработка callback-запросов
        self.application.add_handler(CallbackQueryHandler(self._handle_callback))
        
        # Обработка ошибок
        self.application.add_error_handler(self._handle_error)
        
    async def _handle_start(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Обработка команды /start"""
        user = update.effective_user
        
        welcome_message = (
            f"Привет, {user.first_name}! 👋\n\n"
            "Я — Елена, ваш персональный ИИ-ассистент.\n\n"
            "Я могу:\n"
            "• Отвечать на ваши вопросы\n"
            "• Обрабатывать документы и изображения\n"
            "• Анализировать скриншоты\n"
            "• Запоминать важную информацию\n"
            "• Самостоятельно развиваться\n\n"
            "Используйте /help для списка команд."
        )
        
        await update.message.reply_text(welcome_message)
        
        # Создание сессии пользователя
        self.user_sessions[user.id] = {
            "user_id": user.id,
            "username": user.username,
            "first_name": user.first_name,
            "last_name": user.last_name,
            "start_time": update.message.date.isoformat(),
            "message_count": 0
        }
        
    async def _handle_help(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Обработка команды /help"""
        help_text = (
            "📚 **Доступные команды:**\n\n"
            "• /start - Начать работу с ботом\n"
            "• /help - Показать это сообщение\n"
            "• /status - Статус системы\n"
            "• /memory - Информация о памяти\n"
            "• /cleanup - Очистка временных файлов\n"
            "• /voice - Голосовое сообщение\n"
            "• /screen - Анализ экрана\n\n"
            "**Возможности:**\n"
            "• Отправляйте текстовые сообщения для общения\n"
            "• Отправляйте документы для анализа\n"
            "• Отправляйте изображения для описания\n"
            "• Отправляйте голосовые сообщения\n\n"
            "Я постоянно учусь и развиваюсь! 🧠"
        )
        
        await update.message.reply_text(help_text, parse_mode='Markdown')
        
    async def _handle_status(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Обработка команды /status"""
        import psutil
        import platform
        
        # Сбор информации о системе
        cpu_percent = psutil.cpu_percent(interval=1)
        memory = psutil.virtual_memory()
        disk = psutil.disk_usage('/')
        
        status_message = (
            "📊 **Статус системы:**\n\n"
            f"• **ОС:** {platform.system()} {platform.release()}\n"
            f"• **CPU:** {cpu_percent}%\n"
            f"• **Память:** {memory.percent}% ({memory.used // (1024**2)} MB / {memory.total // (1024**2)} MB)\n"
            f"• **Диск:** {disk.percent}%\n"
            f"• **Пользователей:** {len(self.user_sessions)}\n"
            f"• **Сообщений сегодня:** {self._get_today_message_count()}\n\n"
            "Всё работает отлично! ✅"
        )
        
        await update.message.reply_text(status_message, parse_mode='Markdown')
        
    async def _handle_memory(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Обработка команды /memory"""
        try:
            memory_stats = await self.agent.memory.get_memory_stats()
            
            memory_message = (
                "🧠 **Информация о памяти:**\n\n"
                f"• **Воспоминаний:** {memory_stats.get('total_memories', 0)}\n"
                f"• **Знаний:** {memory_stats.get('total_knowledge', 0)}\n"
                f"• **Опыта:** {memory_stats.get('total_experience', 0)}\n"
                f"• **Размер памяти:** {memory_stats.get('memory_size', '0 MB')}\n"
                f"• **Категории знаний:** {', '.join(memory_stats.get('knowledge_categories', []))}\n"
                f"• **Последний бэкап:** {memory_stats.get('last_backup', 'никогда')}\n"
            )
            
            # Добавление кнопки для бэкапа
            keyboard = [
                [InlineKeyboardButton("Создать бэкап", callback_data="backup_memory")]
            ]
            reply_markup = InlineKeyboardMarkup(keyboard)
            
            await update.message.reply_text(
                memory_message, 
                parse_mode='Markdown',
                reply_markup=reply_markup
            )
            
        except Exception as e:
            await update.message.reply_text(f"Ошибка получения информации о памяти: {e}")
            
    async def _handle_cleanup(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Обработка команды /cleanup"""
        try:
            # Показать клавиатуру с опциями
            keyboard = [
                [
                    InlineKeyboardButton("Временные файлы", callback_data="cleanup_temp"),
                    InlineKeyboardButton("Кэш", callback_data="cleanup_cache")
                ],
                [
                    InlineKeyboardButton("Логи", callback_data="cleanup_logs"),
                    InlineKeyboardButton("Все", callback_data="cleanup_all")
                ]
            ]
            reply_markup = InlineKeyboardMarkup(keyboard)
            
            await update.message.reply_text(
                "🧹 **Выберите тип очистки:**",
                reply_markup=reply_markup
            )
            
        except Exception as e:
            await update.message.reply_text(f"Ошибка: {e}")
            
    async def _handle_voice(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Обработка команды /voice"""
        await update.message.reply_text(
            "🎤 Отправьте голосовое сообщение, и я его расшифрую и отвечу!\n\n"
            "Или просто напишите сообщение, и я отвечу голосом."
        )
        
    async def _handle_screen(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Обработка команды /screen"""
        try:
            # Анализ текущего экрана
            screen_analysis = await self.agent.vision_engine.analyze_screen(
                "Что ты видишь на экране?"
            )
            
            if screen_analysis and "analysis" in screen_analysis:
                await update.message.reply_text(
                    f"👁️ **Анализ экрана:**\n\n{screen_analysis['analysis']}"
                )
            else:
                await update.message.reply_text("Не удалось проанализировать экран.")
                
        except Exception as e:
            await update.message.reply_text(f"Ошибка анализа экрана: {e}")
            
    async def _handle_text(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Обработка текстовых сообщений"""
        user_id = update.effective_user.id
        text = update.message.text
        
        # Обновление счетчика сообщений
        if user_id in self.user_sessions:
            self.user_sessions[user_id]["message_count"] += 1
            
        # Отправка статуса "печатает"
        await update.message.chat.send_action(action="typing")
        
        try:
            # Обработка запроса агентом
            response = await self.agent.process_query(text)
            
            # Отправка ответа
            await update.message.reply_text(response)
            
            # Сохранение взаимодействия в память
            await self.agent.memory.store_interaction(
                user_input=text,
                agent_response=response,
                context={"source": "telegram", "user_id": user_id}
            )
            
        except Exception as e:
            logger.error(f"Ошибка обработки сообщения: {e}")
            await update.message.reply_text(
                "Извините, произошла ошибка при обработке вашего запроса. "
                "Пожалуйста, попробуйте еще раз."
            )
            
    async def _handle_document(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Обработка документов"""
        document = update.message.document
        
        # Отправка статуса "загружает документ"
        await update.message.chat.send_action(action="upload_document")
        
        try:
            # Скачивание документа
            file = await document.get_file()
            file_path = f"data/temp/{document.file_name}"
            await file.download_to_drive(file_path)
            
            # Парсинг документа
            document_content = await self.agent.document_parser.parse_document(file_path)
            
            # Анализ содержимого
            summary = document_content.get("analysis", {}).get("summary", "Не удалось создать краткое содержание.")
            
            # Формирование ответа
            response = (
                f"📄 **Документ:** {document.file_name}\n"
                f"📏 **Размер:** {document.file_size // 1024} KB\n"
                f"📝 **Тип:** {document_content.get('file_type', 'unknown')}\n\n"
                f"**Краткое содержание:**\n{summary}\n\n"
                f"**Ключевые слова:** {', '.join(document_content.get('analysis', {}).get('keywords', []))}"
            )
            
            await update.message.reply_text(response, parse_mode='Markdown')
            
            # Сохранение в память
            await self.agent.memory.store_document_analysis(
                file_name=document.file_name,
                content=document_content,
                summary=summary
            )
            
        except Exception as e:
            logger.error(f"Ошибка обработки документа: {e}")
            await update.message.reply_text(
                f"Не удалось обработать документ: {e}"
            )
            
    async def _handle_photo(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Обработка фотографий"""
        photo = update.message.photo[-1]  # Самое большое изображение
        
        # Отправка статуса "загружает фото"
        await update.message.chat.send_action(action="upload_photo")
        
        try:
            # Скачивание фото
            file = await photo.get_file()
            file_path = f"data/temp/photo_{photo.file_unique_id}.jpg"
            await file.download_to_drive(file_path)
            
            # Анализ изображения
            image_analysis = await self.agent.vision_engine.analyze_image(
                file_path,
                "Опиши подробно, что ты видишь на этом изображении?"
            )
            
            if image_analysis and "description" in image_analysis:
                response = f"🖼️ **Описание изображения:**\n\n{image_analysis['description']}"
                await update.message.reply_text(response, parse_mode='Markdown')
            else:
                await update.message.reply_text("Не удалось проанализировать изображение.")
                
        except Exception as e:
            logger.error(f"Ошибка обработки фото: {e}")
            await update.message.reply_text(
                f"Не удалось обработать изображение: {e}"
            )
            
    async def _handle_voice_message(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Обработка голосовых сообщений"""
        voice = update.message.voice
        
        # Отправка статуса "распознает голос"
        await update.message.chat.send_action(action="record_voice")
        
        try:
            # Скачивание голосового сообщения
            file = await voice.get_file()
            file_path = f"data/temp/voice_{voice.file_unique_id}.ogg"
            await file.download_to_drive(file_path)
            
            # Распознавание речи
            text = await self.agent.speech_recognizer.transcribe(file_path)
            
            if text:
                response = f"🎤 **Распознанный текст:**\n\n{text}"
                await update.message.reply_text(response, parse_mode='Markdown')
                
                # Обработка распознанного текста
                await self._handle_text(update, context)
            else:
                await update.message.reply_text("Не удалось распознать речь.")
                
        except Exception as e:
            logger.error(f"Ошибка обработки голосового сообщения: {e}")
            await update.message.reply_text(
                f"Не удалось обработать голосовое сообщение: {e}"
            )
            
    async def _handle_callback(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Обработка callback-запросов"""
        query = update.callback_query
        await query.answer()
        
        callback_data = query.data
        
        if callback_data == "backup_memory":
            await self._handle_backup_memory(query)
        elif callback_data.startswith("cleanup_"):
            await self._handle_cleanup_callback(query, callback_data)
            
    async def _handle_backup_memory(self, query):
        """Обработка создания бэкапа памяти"""
        try:
            await query.edit_message_text("🔄 Создание резервной копии памяти...")
            
            backup_path = await self.agent.memory.create_backup()
            
            await query.edit_message_text(
                f"✅ **Резервная копия создана!**\n\n"
                f"Путь: `{backup_path}`\n\n"
                f"Резервная копия содержит все воспоминания и знания.",
                parse_mode='Markdown'
            )
            
        except Exception as e:
            await query.edit_message_text(f"❌ Ошибка создания бэкапа: {e}")
            
    async def _handle_cleanup_callback(self, query, callback_data):
        """Обработка callback для очистки"""
        cleanup_type = callback_data.replace("cleanup_", "")
        
        cleanup_types = {
            "temp": "временных файлов",
            "cache": "кэша",
            "logs": "логов",
            "all": "всего"
        }
        
        try:
            await query.edit_message_text(f"🧹 Очистка {cleanup_types.get(cleanup_type, '')}...")
            
            # Выполнение очистки
            if cleanup_type == "all":
                result = await self.agent.cleanup.perform_cleanup("manual")
            else:
                result = await self.agent.cleanup.perform_selective_cleanup(cleanup_type)
                
            await query.edit_message_text(
                f"✅ **Очистка завершена!**\n\n"
                f"• Очищено элементов: {len(result.get('cleaned_items', []))}\n"
                f"• Освобождено места: {result.get('freed_space', 0)} MB\n"
                f"• Время выполнения: {result.get('duration', 0):.2f} секунд",
                parse_mode='Markdown'
            )
            
        except Exception as e:
            await query.edit_message_text(f"❌ Ошибка очистки: {e}")
            
    async def _handle_error(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Обработка ошибок"""
        logger.error(f"Ошибка в боте: {context.error}")
        
        if update and update.effective_message:
            await update.effective_message.reply_text(
                "Извините, произошла внутренняя ошибка. "
                "Пожалуйста, попробуйте еще раз позже."
            )
            
    def _get_today_message_count(self) -> int:
        """Получение количества сообщений за сегодня"""
        from datetime import datetime
        
        today = datetime.now().date()
        count = 0
        
        for session in self.user_sessions.values():
            # Здесь должна быть логика подсчета сообщений за сегодня
            # Упрощенная версия
            count += session.get("message_count", 0)
            
        return count
        
    async def stop(self):
        """Остановка бота"""
        if self.application:
            await self.application.stop()
            await self.application.shutdown()
            logger.info("🛑 Telegram бот остановлен")