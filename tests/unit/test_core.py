"""
ЮНИТ-ТЕСТЫ ДЛЯ ЯДРА СИСТЕМЫ
"""

import unittest
import sys
import os
from pathlib import Path

# Добавляем путь к проекту
sys.path.append(str(Path(__file__).parent.parent.parent))

from src.core.brain.agent import ElenaAgent
from src.utils.logging.logger import ElenaLogger
from src.utils.helpers.helpers import Helpers

class TestElenaAgent(unittest.TestCase):
    """Тесты для основного агента"""
    
    def setUp(self):
        """Настройка перед каждым тестом"""
        self.agent = ElenaAgent()
        self.logger = ElenaLogger("test")
        
    def test_agent_initialization(self):
        """Тест инициализации агента"""
        self.assertIsNotNone(self.agent)
        self.assertEqual(self.agent.name, "Елена")
        self.assertEqual(self.agent.version, "1.0.0")
        
    def test_agent_start(self):
        """Тест запуска агента"""
        result = self.agent.start()
        self.assertEqual(result, "Готово")
        
    def test_agent_response(self):
        """Тест получения ответа от агента"""
        response = self.agent.process_query("привет")
        self.assertIsInstance(response, str)
        self.assertGreater(len(response), 0)
        
    def test_agent_memory(self):
        """Тест работы памяти агента"""
        test_memory = "Тестовое воспоминание"
        memory_id = self.agent.memory.store_memory(test_memory)
        
        self.assertIsNotNone(memory_id)
        self.assertIsInstance(memory_id, str)
        self.assertGreater(len(memory_id), 0)
        
    def tearDown(self):
        """Очистка после каждого теста"""
        del self.agent

class TestHelpers(unittest.TestCase):
    """Тесты для утилит-помощников"""
    
    def test_generate_id(self):
        """Тест генерации ID"""
        helpers = Helpers()
        id1 = helpers.generate_id()
        id2 = helpers.generate_id()
        
        self.assertIsInstance(id1, str)
        self.assertEqual(len(id1), 16)
        self.assertNotEqual(id1, id2)
        
    def test_format_size(self):
        """Тест форматирования размера"""
        helpers = Helpers()
        
        self.assertEqual(helpers.format_size(500), "500.00 B")
        self.assertEqual(helpers.format_size(1500), "1.46 KB")
        self.assertEqual(helpers.format_size(1500000), "1.43 MB")
        
    def test_truncate_text(self):
        """Тест обрезки текста"""
        helpers = Helpers()
        
        text = "Очень длинный текст, который нужно обрезать"
        truncated = helpers.truncate_text(text, 20)
        
        self.assertLessEqual(len(truncated), 23)  # 20 + "..."
        self.assertTrue(truncated.endswith("..."))
        
    def test_clean_filename(self):
        """Тест очистки имени файла"""
        helpers = Helpers()
        
        dirty_name = 'file<>:"/\\|?*name.txt'
        clean_name = helpers.clean_filename(dirty_name)
        
        self.assertNotIn('<', clean_name)
        self.assertNotIn('>', clean_name)
        self.assertNotIn(':', clean_name)
        self.assertNotIn('"', clean_name)
        self.assertNotIn('/', clean_name)
        self.assertNotIn('\\', clean_name)
        self.assertNotIn('|', clean_name)
        self.assertNotIn('?', clean_name)
        self.assertNotIn('*', clean_name)
        
    def test_human_readable_list(self):
        """Тест преобразования списка в строку"""
        helpers = Helpers()
        
        self.assertEqual(helpers.human_readable_list([]), "")
        self.assertEqual(helpers.human_readable_list(["яблоко"]), "яблоко")
        self.assertEqual(helpers.human_readable_list(["яблоко", "груша"]), "яблоко и груша")
        self.assertEqual(helpers.human_readable_list(["яблоко", "груша", "банан"]), "яблоко, груша и банан")

class TestLogger(unittest.TestCase):
    """Тесты для логгера"""
    
    def test_logger_creation(self):
        """Тест создания логгера"""
        logger = ElenaLogger("test_logger")
        self.assertIsNotNone(logger.logger)
        
    def test_logging_functions(self):
        """Тест функций логирования"""
        logger = ElenaLogger("test_logger")
        
        # Проверяем что функции не вызывают ошибок
        try:
            logger.debug("Тестовое отладочное сообщение")
            logger.info("Тестовое информационное сообщение")
            logger.warning("Тестовое предупреждение")
            logger.error("Тестовая ошибка")
            logger.critical("Тестовая критическая ошибка")
            success = True
        except Exception as e:
            print(f"Logging error: {e}")
            success = False
            
        self.assertTrue(success)
        
    def test_interaction_logging(self):
        """Тест логирования взаимодействий"""
        logger = ElenaLogger("test_logger")
        
        try:
            logger.log_interaction(
                user_input="привет",
                agent_response="Привет! Как дела?",
                metadata={"source": "test"}
            )
            success = True
        except:
            success = False
            
        self.assertTrue(success)
        
    def test_log_stats(self):
        """Тест получения статистики логов"""
        logger = ElenaLogger("test_logger")
        
        stats = logger.get_log_stats()
        self.assertIsInstance(stats, dict)
        self.assertIn("total_lines", stats)
        self.assertIn("last_modified", stats)

if __name__ == '__main__':
    # Создаем временную папку для логов
    os.makedirs("logs", exist_ok=True)
    
    # Запускаем тесты
    unittest.main(verbosity=2)