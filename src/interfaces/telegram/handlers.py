"""
Обработчики команд и сообщений Telegram бота
"""

import logging
from typing import Dict, Any
from telegram import Update, InlineKeyboardMarkup, InlineKeyboardButton
from telegram.ext import ContextTypes

logger = logging.getLogger(__name__)

class TelegramHandlers:
    """Обработчики для Telegram бота"""
    
    def __init__(self, agent):
        self.agent = agent
        
    async def handle_start(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Обработчик команды /start"""
        user = update.effective_user
        
        welcome_text = f"""
        Привет, {user.first_name}! 👋

        Я — *Елена*, твой персональный ИИ-помощник.

        ✨ *Что я умею:*
        • Отвечать на вопросы
        • Читать и анализировать документы
        • Работать с изображениями
        • Распознавать и синтезировать речь
        • Запоминать важную информацию

        📝 *Основные команды:*
        /help - Справка по командам
        /status - Статус системы
        /memory - Информация о памяти
        /voice - Голосовое сообщение
        /screen - Анализ экрана

        Просто отправь мне сообщение, и я отвечу! 🎀
        """
        
        await update.message.reply_text(welcome_text, parse_mode='Markdown')
        
        # Регистрация пользователя
        await self.agent.memory.store_interaction(
            user_input="/start",
            agent_response=welcome_text,
            metadata={"source": "telegram", "user_id": user.id}
        )
        
    async def handle_help(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Обработчик команды /help"""
        help_text = """
        📚 *Справка по командам:*

        🎯 *Основные команды:*
        /start - Начать работу с ботом
        /help - Эта справка
        /status - Статус системы

        📄 *Работа с документами:*
        Просто отправь файл (PDF, DOCX, TXT)
        Я прочитаю его и сделаю анализ

        🖼️ *Работа с изображениями:*
        Отправь фото, и я опишу что на нем

        🎤 *Голосовые сообщения:*
        Отправь голосовое сообщение
        Используй /voice для инструкций

        ⚙️ *Управление:*
        /memory - Информация о памяти
        /cleanup - Очистка временных файлов
        /settings - Настройки бота

        💬 *Просто отправь текст, и я отвечу!*
        """
        
        await update.message.reply_text(help_text, parse_mode='Markdown')
        
    async def handle_status(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Обработчик команды /status"""
        import psutil
        
        # Получение информации о системе
        cpu_percent = psutil.cpu_percent()
        memory = psutil.virtual_memory()
        disk = psutil.disk_usage('/')
        
        # Получение статуса агента
        agent_status = "🟢 Активен" if self.agent.state.is_active else "🔴 Неактивен"
        
        status_text = f"""
        📊 *Статус системы:*

        🤖 *Агент:*
        • Имя: {self.agent.config.get('agent', {}).get('name', 'Елена')}
        • Статус: {agent_status}
        • Версия: 1.0.0

        💻 *Система:*
        • CPU: {cpu_percent}%
        • Память: {memory.percent}% ({memory.used // (1024**2)}MB/{memory.total // (1024**2)}MB)
        • Диск: {disk.percent}% ({disk.used // (1024**3)}GB/{disk.total // (1024**3)}GB)

        🧠 *Память агента:*
        • Взаимодействий: {len(self.agent.memory.memory_data)}
        • Контекст: {len(self.agent.context_manager.current_context)}

        🎀 *Все системы работают нормально!*
        """
        
        await update.message.reply_text(status_text, parse_mode='Markdown')
        
    async def handle_text(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Обработчик текстовых сообщений"""
        user = update.effective_user
        text = update.message.text
        
        logger.info(f"Текст от {user.username}: {text}")
        
        # Показать статус "печатает"
        await update.message.chat.send_action(action="typing")
        
        try:
            # Обработка запроса агентом
            response = await self.agent.process_query(text)
            
            # Отправка ответа
            await update.message.reply_text(response, parse_mode='Markdown')
            
            # Сохранение в память
            await self.agent.memory.store_interaction(
                user_input=text,
                agent_response=response,
                metadata={
                    "source": "telegram",
                    "user_id": user.id,
                    "username": user.username
                }
            )
            
        except Exception as e:
            logger.error(f"Ошибка обработки сообщения: {e}")
            await update.message.reply_text(
                "Извини, произошла ошибка при обработке твоего запроса. "
                "Попробуй еще раз или обратись к разработчику."
            )
            
    async def handle_document(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Обработчик документов"""
        document = update.message.document
        
        logger.info(f"Документ от пользователя: {document.file_name}")
        
        await update.message.chat.send_action(action="upload_document")
        
        try:
            # Скачивание документа
            file = await document.get_file()
            file_path = f"data/temp/{document.file_name}"
            await file.download_to_drive(file_path)
            
            # Анализ документа
            await update.message.reply_text(f"📄 Анализирую документ: {document.file_name}...")
            
            # Здесь должен быть анализ документа через DocumentParser
            # В упрощенной версии просто подтверждаем получение
            response = f"""
            ✅ *Документ получен!*

            📋 *Информация:*
            • Имя: {document.file_name}
            • Размер: {document.file_size // 1024} KB
            • MIME тип: {document.mime_type}

            В полной версии я проанализирую содержимое документа и сделаю выжимку.
            """
            
            await update.message.reply_text(response, parse_mode='Markdown')
            
        except Exception as e:
            logger.error(f"Ошибка обработки документа: {e}")
            await update.message.reply_text(f"❌ Ошибка обработки документа: {e}")
            
    async def handle_photo(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Обработчик фотографий"""
        photo = update.message.photo[-1]  # Самое большое изображение
        
        await update.message.chat.send_action(action="upload_photo")
        
        try:
            # Скачивание фото
            file = await photo.get_file()
            file_path = f"data/temp/photo_{photo.file_unique_id}.jpg"
            await file.download_to_drive(file_path)
            
            # Анализ изображения
            await update.message.reply_text("🖼️ Анализирую изображение...")
            
            # Здесь должен быть анализ изображения через VisionEngine
            response = """
            ✅ *Изображение получено!*

            В полной версии я:
            • Распознаю объекты на изображении
            • Прочитаю текст (если есть)
            • Опишу что вижу
            • Проанализирую цвета и композицию

            Пока что я могу только сохранить изображение для дальнейшего анализа.
            """
            
            await update.message.reply_text(response, parse_mode='Markdown')
            
        except Exception as e:
            logger.error(f"Ошибка обработки фото: {e}")
            await update.message.reply_text(f"❌ Ошибка обработки изображения: {e}")
            
    async def handle_voice(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Обработчик голосовых сообщений"""
        voice = update.message.voice
        
        await update.message.chat.send_action(action="record_voice")
        
        try:
            # Скачивание голосового сообщения
            file = await voice.get_file()
            file_path = f"data/temp/voice_{voice.file_unique_id}.ogg"
            await file.download_to_drive(file_path)
            
            # Распознавание речи
            await update.message.reply_text("🎤 Распознаю речь...")
            
            # Здесь должно быть распознавание речи через SpeechRecognizer
            response = """
            ✅ *Голосовое сообщение получено!*

            В полной версии я:
            • Распознаю речь и преобразую в текст
            • Проанализирую эмоции по голосу
            • Отвечу текстом или голосом

            Для работы голосового интерфейса нужно установить дополнительные библиотеки.
            """
            
            await update.message.reply_text(response, parse_mode='Markdown')
            
        except Exception as e:
            logger.error(f"Ошибка обработки голосового сообщения: {e}")
            await update.message.reply_text(f"❌ Ошибка обработки голосового сообщения: {e}")