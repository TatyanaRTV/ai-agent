"""
ИНТЕГРАЦИОННЫЕ ТЕСТЫ
"""

import unittest
import sys
import os
from pathlib import Path

# Добавляем путь к проекту
sys.path.append(str(Path(__file__).parent.parent.parent))

from src.core.brain.agent import ElenaAgent
from src.interfaces.voice.tts.synthesizer import SpeechSynthesizer
from src.tools.document.parser import DocumentParser

class TestIntegration(unittest.TestCase):
    """Интеграционные тесты"""
    
    def setUp(self):
        """Настройка перед тестами"""
        self.agent = ElenaAgent()
        self.tts = SpeechSynthesizer()
        self.parser = DocumentParser()
        
        # Создаем тестовые файлы
        self.test_text_file = "test_integration.txt"
        with open(self.test_text_file, "w", encoding="utf-8") as f:
            f.write("Тестовый файл для интеграционного тестирования.\n")
            f.write("Елена должна уметь читать такие файлы.\n")
            
    def test_agent_voice_integration(self):
        """Тест интеграции агента с голосом"""
        # Проверяем что агент может работать с TTS
        try:
            response = self.agent.process_query("тест")
            self.assertIsInstance(response, str)
            
            # Проверяем что TTS может озвучить ответ
            success = self.tts.speak(response, wait=False)
            self.assertTrue(success)
        except Exception as e:
            self.fail(f"Agent-voice integration failed: {e}")
            
    def test_agent_document_integration(self):
        """Тест интеграции агента с парсером документов"""
        try:
            # Читаем тестовый файл
            content = self.parser.read_file(self.test_text_file)
            self.assertIsInstance(content, dict)
            self.assertIn("text", content)
            
            # Агент обрабатывает содержимое
            response = self.agent.process_query(f"Проанализируй текст: {content['text'][:50]}")
            self.assertIsInstance(response, str)
            self.assertGreater(len(response), 0)
        except Exception as e:
            self.fail(f"Agent-document integration failed: {e}")
            
    def test_voice_document_integration(self):
        """Тест интеграции голоса с документами"""
        try:
            # Читаем документ
            content = self.parser.read_file(self.test_text_file)
            
            # Озвучиваем часть содержимого
            text_to_speak = content.get("text", "")[:100] + "..." if len(content.get("text", "")) > 100 else content.get("text", "")
            success = self.tts.speak(f"Содержимое документа: {text_to_speak}", wait=False)
            self.assertTrue(success)
        except Exception as e:
            self.fail(f"Voice-document integration failed: {e}")
            
    def test_full_pipeline(self):
        """Тест полного пайплайна обработки"""
        test_query = "прочитай тестовый файл и озвучь первую строку"
        
        try:
            # 1. Агент понимает запрос
            response = self.agent.process_query(test_query)
            
            # 2. Парсер читает файл
            content = self.parser.read_file(self.test_text_file)
            
            # 3. Извлекаем первую строку
            first_line = content.get("text", "").split('\n')[0]
            
            # 4. TTS озвучивает
            tts_response = self.tts.speak(f"Первая строка файла: {first_line}", wait=False)
            
            self.assertTrue(tts_response)
            self.assertIsInstance(response, str)
            self.assertIsInstance(content, dict)
            
        except Exception as e:
            self.fail(f"Full pipeline test failed: {e}")
            
    def test_error_handling_integration(self):
        """Тест обработки ошибок во всей системе"""
        # Тестируем обработку несуществующего файла
        try:
            content = self.parser.read_file("non_existent_file.txt")
            self.fail("Should have raised an exception")
        except Exception as e:
            # Ожидаем ошибку
            self.assertIsInstance(e, (FileNotFoundError, ValueError))
            
        # Тестируем обработку некорректного запроса
        try:
            response = self.agent.process_query("")
            # Пустой запрос может вернуть дефолтный ответ
            self.assertIsInstance(response, str)
        except Exception as e:
            # Не должно быть исключений
            self.fail(f"Empty query should not raise exception: {e}")
            
    def tearDown(self):
        """Очистка после тестов"""
        # Удаляем тестовые файлы
        if os.path.exists(self.test_text_file):
            os.remove(self.test_text_file)
            
        del self.agent
        del self.tts
        del self.parser

if __name__ == '__main__':
    unittest.main(verbosity=2)