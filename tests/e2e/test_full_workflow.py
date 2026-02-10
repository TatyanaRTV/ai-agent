"""
E2E тесты полного рабочего процесса Елены
"""
import pytest
import asyncio
from unittest.mock import Mock, patch


class TestFullWorkflowE2E:
    """Тесты полного сквозного рабочего процесса"""
    
    @pytest.mark.integration
    @pytest.mark.slow
    def test_complete_user_scenario(self):
        """
        Тест полного сценария использования:
        1. Пользователь отправляет голосовое сообщение
        2. Елена распознает речь
        3. Обрабатывает запрос
        4. Ищет в памяти
        5. Формирует ответ
        6. Озвучивает ответ
        7. Сохраняет в историю
        """
        from src.core.brain.agent import AIAgent
        from src.interfaces.voice.voice_interface import VoiceInterface
        from src.core.memory.memory_manager import MemoryManager
        
        # Инициализация компонентов
        agent = AIAgent(name="Елена")
        voice_interface = VoiceInterface(agent=agent)
        memory = MemoryManager()
        
        # Тестовый сценарий
        test_scenarios = [
            {
                "input": "привет представься пожалуйста",
                "expected_keywords": ["Елена", "помощник", "привет"]
            },
            {
                "input": "сделай скриншот рабочего стола",
                "expected_keywords": ["скриншот", "создан", "сохранен"]
            },
            {
                "input": "что ты умеешь делать",
                "expected_keywords": ["умею", "могу", "помочь"]
            }
        ]
        
        for scenario in test_scenarios:
            # Эмулируем обработку
            with patch('src.interfaces.voice.stt.recognizer.SpeechRecognizer.recognize') as mock_stt:
                mock_stt.return_value = scenario["input"]
                
                with patch('src.interfaces.voice.tts.synthesizer.TTSSynthesizer.synthesize') as mock_tts:
                    mock_tts.return_value = "/tmp/test_audio.wav"
                    
                    # Выполняем полный цикл
                    result = voice_interface.process_voice_input(
                        audio_path="/tmp/test_input.wav"
                    )
                    
                    # Проверяем результат
                    assert result is not None
                    assert "response" in result
                    
                    # Проверяем ключевые слова в ответе
                    response_text = result["response"].lower()
                    for keyword in scenario["expected_keywords"]:
                        assert keyword in response_text
    
    def test_self_learning_cycle(self):
        """Тест цикла самообучения"""
        from src.core.learning.self_improvement import SelfImprovementSystem
        
        learning_system = SelfImprovementSystem()
        
        # Собираем метрики
        metrics = {
            "accuracy": 0.85,
            "response_time": 2.3,
            "user_satisfaction": 4.2
        }
        
        # Анализируем метрики
        analysis = learning_system.analyze_performance(metrics)
        
        assert analysis is not None
        assert "improvements" in analysis
        assert "recommendations" in analysis
        
        # Применяем улучшения
        result = learning_system.apply_improvements(analysis["improvements"])
        
        assert result["success"] is True
        assert "applied_changes" in result