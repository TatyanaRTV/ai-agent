"""
End-to-End тесты голосового интерфейса Елены
"""
import pytest
import tempfile
import os
from pathlib import Path
from src.interfaces.voice.tts.synthesizer import TTSSynthesizer
from src.interfaces.voice.stt.recognizer import SpeechRecognizer


class TestVoiceAssistantE2E:
    """E2E тесты голосового ассистента Елены"""
    
    @pytest.fixture(autouse=True)
    def setup_teardown(self):
        """Настройка и очистка перед/после тестов"""
        self.test_dir = tempfile.mkdtemp()
        self.audio_file = Path(self.test_dir) / "test_output.wav"
        yield
        # Очистка
        import shutil
        if Path(self.test_dir).exists():
            shutil.rmtree(self.test_dir)
    
    @pytest.mark.slow
    @pytest.mark.integration
    def test_voice_conversation_cycle(self):
        """Тест полного цикла голосового диалога"""
        # Инициализация компонентов
        tts = TTSSynthesizer(voice="female", language="ru")
        stt = SpeechRecognizer(language="ru")
        
        # 1. Синтез речи (TTS)
        test_text = "Привет! Я Елена, ваш голосовой помощник"
        audio_path = tts.synthesize(
            text=test_text,
            output_path=str(self.audio_file),
            speed=1.0,
            pitch=0.8
        )
        
        assert Path(audio_path).exists()
        assert Path(audio_path).stat().st_size > 0
        
        # 2. Распознавание речи (STT)
        # Создаем тестовый аудиофайл с речью
        test_audio_content = "привет елена как дела"
        # Здесь будет код для создания тестового аудио
        
        # 3. Проверка распознавания
        recognized_text = stt.recognize(str(self.audio_file))
        assert isinstance(recognized_text, str)
        assert len(recognized_text) > 0
    
    @pytest.mark.integration
    def test_voice_commands_execution(self):
        """Тест выполнения голосовых команд"""
        from src.core.brain.agent import AIAgent
        from src.interfaces.voice.voice_interface import VoiceInterface
        
        agent = AIAgent(name="Елена")
        voice_interface = VoiceInterface(agent=agent)
        
        test_commands = [
            "сделай скриншот",
            "какая сейчас погода",
            "расскажи о себе",
            "прочитай последний документ"
        ]
        
        for command in test_commands:
            # Эмулируем голосовую команду
            response = voice_interface.process_command(command)
            
            assert response is not None
            assert isinstance(response, dict)
            assert "success" in response or "text" in response
    
    def test_russian_voice_quality(self):
        """Тест качества русского голоса Елены"""
        tts = TTSSynthesizer(voice="female", language="ru")
        
        # Тестовые фразы на русском
        test_phrases = [
            "Привет, меня зовут Елена",
            "Я ваш персональный помощник",
            "Чем могу помочь сегодня?",
            "Погода сегодня прекрасная"
        ]
        
        for phrase in test_phrases:
            audio_path = tts.synthesize(
                text=phrase,
                output_path=str(self.audio_file)
            )
            
            # Проверяем, что файл создан
            assert Path(audio_path).exists()
            
            # Можно добавить проверку длительности аудио
            # (должно быть пропорционально длине текста)