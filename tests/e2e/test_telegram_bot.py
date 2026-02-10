"""
E2E тесты Telegram-бота Елены
"""
import pytest
import asyncio
from unittest.mock import AsyncMock, Mock, patch
from src.interfaces.telegram.bot import ElenaTelegramBot
from src.interfaces.telegram.handlers import MessageHandlers


class TestTelegramBotE2E:
    """E2E тесты Telegram-интерфейса"""
    
    @pytest.fixture
    def mock_bot(self):
        """Фикстура: мок Telegram-бота"""
        bot = Mock(spec=ElenaTelegramBot)
        bot.process_message = AsyncMock()
        bot.send_message = AsyncMock()
        return bot
    
    @pytest.mark.asyncio
    async def test_message_processing_flow(self, mock_bot):
        """Тест полного потока обработки сообщения"""
        handlers = MessageHandlers(bot=mock_bot)
        
        # Тестовое сообщение
        test_message = {
            "message_id": 123,
            "from": {"id": 456, "first_name": "Тест"},
            "chat": {"id": 789},
            "text": "Привет, Елена!"
        }
        
        # Обработка сообщения
        response = await handlers.handle_text_message(test_message)
        
        # Проверки
        assert response is not None
        mock_bot.process_message.assert_called_once()
        mock_bot.send_message.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_document_processing_via_telegram(self):
        """Тест обработки документов через Telegram"""
        from src.interfaces.telegram.handlers import DocumentHandlers
        
        handlers = DocumentHandlers()
        
        # Мок документа
        mock_document = {
            "file_id": "test_file_id",
            "file_name": "test_document.pdf",
            "mime_type": "application/pdf"
        }
        
        # Тест обработки PDF
        with patch('src.tools.document.parser.PDFParser.extract_text') as mock_extract:
            mock_extract.return_value = "Текст из PDF документа"
            
            result = await handlers.handle_document(
                document=mock_document,
                chat_id=123
            )
            
            assert result["success"] is True
            assert "Текст из PDF документа" in result["content"]
    
    @pytest.mark.asyncio
    async def test_voice_message_processing(self):
        """Тест обработки голосовых сообщений в Telegram"""
        from src.interfaces.telegram.handlers import VoiceHandlers
        
        handlers = VoiceHandlers()
        
        # Мок голосового сообщения
        mock_voice = {
            "file_id": "test_voice_id",
            "duration": 5,
            "mime_type": "audio/ogg"
        }
        
        with patch('src.interfaces.voice.stt.recognizer.SpeechRecognizer.recognize') as mock_recognize:
            mock_recognize.return_value = "тестовое голосовое сообщение"
            
            result = await handlers.handle_voice_message(
                voice=mock_voice,
                chat_id=456
            )
            
            assert result["success"] is True
            assert "распознано" in result
            assert "тестовое голосовое сообщение" in result["text"]