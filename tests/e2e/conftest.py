"""
Конфигурация и фикстуры для End-to-End тестов
"""
import pytest
import tempfile
import asyncio
from pathlib import Path
from unittest.mock import AsyncMock, Mock


@pytest.fixture(scope="session")
def event_loop():
    """Фикстура для asyncio event loop"""
    loop = asyncio.get_event_loop_policy().new_event_loop()
    yield loop
    loop.close()


@pytest.fixture
def test_agent():
    """Фикстура: тестовый агент Елена"""
    from src.core.brain.agent import AIAgent
    return AIAgent(name="Тестовая Елена")


@pytest.fixture
def mock_voice_interface():
    """Фикстура: мок голосового интерфейса"""
    interface = Mock()
    interface.process_command = AsyncMock()
    interface.synthesize_response = AsyncMock()
    return interface


@pytest.fixture
def sample_documents_dir(tmp_path_factory):
    """Фикстура: директория с тестовыми документами"""
    base_dir = tmp_path_factory.mktemp("test_docs")
    
    # Создаем тестовые файлы
    (base_dir / "test.txt").write_text("Текстовый документ для тестирования")
    (base_dir / "readme.md").write_text("# Тестовый Markdown")
    
    return base_dir


@pytest.fixture
def test_audio_files(tmp_path_factory):
    """Фикстура: тестовые аудиофайлы"""
    audio_dir = tmp_path_factory.mktemp("test_audio")
    
    # Создаем пустые аудиофайлы (в реальных тестах нужны реальные аудио)
    (audio_dir / "test_voice.wav").write_bytes(b"fake_audio_data")
    (audio_dir / "response.wav").write_bytes(b"fake_response_data")
    
    return audio_dir


@pytest.fixture(autouse=True)
def cleanup_temp_files():
    """Автоматическая очистка временных файлов после тестов"""
    yield
    # Код очистки
    import shutil
    temp_dir = Path(tempfile.gettempdir())
    for item in temp_dir.glob("elena_test_*"):
        if item.is_file():
            item.unlink()
        elif item.is_dir():
            shutil.rmtree(item, ignore_errors=True)