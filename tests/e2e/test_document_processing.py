"""
E2E тесты обработки различных типов документов
"""
import pytest
import tempfile
from pathlib import Path
from src.tools.document.parser import DocumentParser


class TestDocumentProcessingE2E:
    """E2E тесты обработки документов"""
    
    @pytest.fixture
    def sample_documents(self, tmp_path):
        """Фикстура: тестовые документы разных форматов"""
        docs = {}
        
        # 1. Текстовый файл
        txt_file = tmp_path / "test.txt"
        txt_file.write_text("Это простой текстовый документ.\nВторая строка.")
        docs["txt"] = str(txt_file)
        
        # 2. PDF файл
        pdf_file = tmp_path / "test.pdf"
        # Здесь создаем простой PDF (в реальном тесте нужно использовать библиотеку)
        pdf_file.write_text("PDF content mock")  # Заглушка
        docs["pdf"] = str(pdf_file)
        
        # 3. Word документ
        docx_file = tmp_path / "test.docx"
        docx_file.write_text("DOCX content mock")  # Заглушка
        docs["docx"] = str(docx_file)
        
        return docs
    
    @pytest.mark.parametrize("file_type", ["txt", "pdf", "docx"])
    def test_document_parsing(self, sample_documents, file_type):
        """Тест парсинга документов разных форматов"""
        parser = DocumentParser()
        
        file_path = sample_documents[file_type]
        result = parser.parse_document(file_path)
        
        assert result is not None
        assert "content" in result
        assert "metadata" in result
        assert result["metadata"]["file_type"] == file_type
    
    def test_document_to_vector_conversion(self):
        """Тест конвертации документа в вектор"""
        from src.tools.document.parser import DocumentParser
        from src.tools.vector.encoding.encoder import VectorEncoder
        
        parser = DocumentParser()
        encoder = VectorEncoder()
        
        test_text = """
        Искусственный интеллект - это область компьютерных наук,
        занимающаяся созданием интеллектуальных машин.
        Елена - это ИИ-помощник с женским голосом.
        """
        
        # Парсинг
        parsed = parser.parse_text(test_text)
        
        # Конвертация в вектор
        vector = encoder.encode_text(parsed["content"])
        
        assert vector is not None
        assert len(vector) == 384  # Размерность модели
    
    def test_document_summarization(self):
        """Тест суммаризации документа"""
        from src.tools.document.processor import DocumentProcessor
        
        processor = DocumentProcessor()
        
        long_text = " ".join(["Строка номер {}".format(i) for i in range(100)])
        
        summary = processor.summarize(
            text=long_text,
            max_length=50
        )
        
        assert len(summary) < len(long_text)
        assert "Строка" in summary  # Должен сохранить ключевые слова