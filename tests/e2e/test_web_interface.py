"""
E2E тесты веб-интерфейса Елены
"""
import pytest
from fastapi.testclient import TestClient
from src.interfaces.browser.app import create_app


class TestWebInterfaceE2E:
    """E2E тесты веб-интерфейса"""
    
    @pytest.fixture
    def client(self):
        """Фикстура: тестовый клиент FastAPI"""
        app = create_app()
        return TestClient(app)
    
    def test_home_page(self, client):
        """Тест главной страницы"""
        response = client.get("/")
        
        assert response.status_code == 200
        assert "Елена" in response.text
        assert "ИИ-помощник" in response.text
    
    def test_chat_endpoint(self, client):
        """Тест API чата"""
        test_message = {"message": "Привет, как дела?"}
        
        response = client.post(
            "/api/chat",
            json=test_message
        )
        
        assert response.status_code == 200
        data = response.json()
        assert "response" in data
        assert isinstance(data["response"], str)
    
    def test_document_upload(self, client, tmp_path):
        """Тест загрузки документов через веб-интерфейс"""
        # Создаем тестовый файл
        test_file = tmp_path / "test_document.txt"
        test_file.write_text("Это тестовый документ для загрузки")
        
        # Загружаем файл
        files = {"file": ("test_document.txt", open(test_file, "rb"), "text/plain")}
        
        response = client.post(
            "/api/upload",
            files=files
        )
        
        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        assert "test_document.txt" in data["filename"]
    
    def test_voice_interaction(self, client):
        """Тест голосового взаимодействия через веб"""
        # Тест синтеза речи
        tts_request = {"text": "Привет из веб-интерфейса"}
        
        response = client.post(
            "/api/tts",
            json=tts_request
        )
        
        assert response.status_code == 200
        assert response.headers["content-type"] == "audio/wav"
        assert len(response.content) > 0