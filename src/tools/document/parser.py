"""
Парсер документов всех форматов
"""

import os
import logging
from typing import Dict, List, Any, Optional
from datetime import datetime
import json

logger = logging.getLogger(__name__)

class DocumentParser:
    """Парсер документов всех популярных форматов"""
    
    def __init__(self):
        self.supported_formats = {
            '.pdf': self._parse_pdf,
            '.docx': self._parse_docx,
            '.doc': self._parse_doc,
            '.xlsx': self._parse_excel,
            '.xls': self._parse_excel,
            '.pptx': self._parse_pptx,
            '.ppt': self._parse_ppt,
            '.txt': self._parse_text,
            '.md': self._parse_markdown,
            '.html': self._parse_html,
            '.htm': self._parse_html,
            '.rtf': self._parse_rtf,
            '.odt': self._parse_odt,
            '.ods': self._parse_ods,
            '.odp': self._parse_odp,
            '.csv': self._parse_csv,
            '.json': self._parse_json,
            '.xml': self._parse_xml,
            '.epub': self._parse_epub,
            '.mobi': self._parse_mobi
        }
        
    def parse_document(self, file_path: str) -> Dict[str, Any]:
        """Парсинг документа любого формата"""
        if not os.path.exists(file_path):
            raise FileNotFoundError(f"Файл не найден: {file_path}")
            
        file_ext = os.path.splitext(file_path)[1].lower()
        
        if file_ext not in self.supported_formats:
            raise ValueError(f"Неподдерживаемый формат файла: {file_ext}")
            
        logger.info(f"📄 Парсинг документа: {file_path}")
        
        try:
            # Получение метаданных файла
            metadata = self._get_file_metadata(file_path)
            
            # Парсинг содержимого
            content = self.supported_formats[file_ext](file_path)
            
            # Анализ содержимого
            analysis = self._analyze_content(content)
            
            result = {
                "file_path": file_path,
                "file_name": os.path.basename(file_path),
                "file_size": metadata["size"],
                "file_type": file_ext[1:],  # Без точки
                "created": metadata["created"],
                "modified": metadata["modified"],
                "content": content,
                "analysis": analysis,
                "parsing_time": datetime.now().isoformat(),
                "success": True
            }
            
            logger.info(f"✅ Документ успешно распарсен: {file_path}")
            return result
            
        except Exception as e:
            logger.error(f"Ошибка парсинга документа {file_path}: {e}")
            raise
            
    def _parse_pdf(self, file_path: str) -> Dict[str, Any]:
        """Парсинг PDF файлов"""
        try:
            import PyPDF2
            
            content = {
                "text": "",
                "metadata": {},
                "pages": [],
                "images": [],
                "tables": []
            }
            
            with open(file_path, 'rb') as file:
                pdf_reader = PyPDF2.PdfReader(file)
                
                # Извлечение метаданных
                if pdf_reader.metadata:
                    content["metadata"] = {
                        str(k).lower(): str(v) for k, v in pdf_reader.metadata.items()
                    }
                    
                # Извлечение текста со всех страниц
                for page_num, page in enumerate(pdf_reader.pages, 1):
                    page_text = page.extract_text()
                    content["text"] += page_text + "\n"
                    
                    page_info = {
                        "page_number": page_num,
                        "text": page_text,
                        "rotation": page.get('/Rotate', 0),
                        "media_box": str(page.mediabox)
                    }
                    content["pages"].append(page_info)
                    
                # Попытка извлечения изображений
                try:
                    content["images"] = self._extract_pdf_images(file_path)
                except:
                    content["images"] = []
                    
            return content
            
        except ImportError:
            logger.warning("PyPDF2 не установлен, используется альтернативный метод")
            return self._parse_pdf_fallback(file_path)
            
    def _parse_pdf_fallback(self, file_path: str) -> Dict[str, Any]:
        """Альтернативный метод парсинга PDF"""
        try:
            import pdf2image
            import pytesseract
            
            content = {
                "text": "",
                "pages": [],
                "images": []
            }
            
            # Конвертация PDF в изображения
            images = pdf2image.convert_from_path(file_path)
            
            for page_num, image in enumerate(images, 1):
                # OCR для извлечения текста
                page_text = pytesseract.image_to_string(image, lang='rus+eng')
                content["text"] += page_text + "\n"
                
                page_info = {
                    "page_number": page_num,
                    "text": page_text,
                    "image_size": image.size
                }
                content["pages"].append(page_info)
                
            return content
            
        except Exception as e:
            logger.error(f"Ошибка альтернативного парсинга PDF: {e}")
            return {"text": "", "pages": [], "error": str(e)}
            
    def _parse_docx(self, file_path: str) -> Dict[str, Any]:
        """Парсинг DOCX файлов"""
        try:
            from docx import Document
            
            doc = Document(file_path)
            content = {
                "text": "",
                "paragraphs": [],
                "tables": [],
                "images": [],
                "metadata": {}
            }
            
            # Извлечение текста из параграфов
            for para in doc.paragraphs:
                if para.text.strip():
                    content["text"] += para.text + "\n"
                    content["paragraphs"].append({
                        "text": para.text,
                        "style": para.style.name if para.style else None,
                        "runs": len(para.runs)
                    })
                    
            # Извлечение таблиц
            for table_num, table in enumerate(doc.tables, 1):
                table_data = []
                for row in table.rows:
                    row_data = [cell.text.strip() for cell in row.cells]
                    table_data.append(row_data)
                    
                content["tables"].append({
                    "table_number": table_num,
                    "rows": len(table_data),
                    "columns": len(table_data[0]) if table_data else 0,
                    "data": table_data
                })
                
            # Извлечение изображений
            content["images"] = self._extract_docx_images(doc)
            
            # Метаданные
            content["metadata"] = {
                "author": doc.core_properties.author,
                "created": str(doc.core_properties.created),
                "modified": str(doc.core_properties.modified),
                "title": doc.core_properties.title,
                "subject": doc.core_properties.subject
            }
            
            return content
            
        except Exception as e:
            logger.error(f"Ошибка парсинга DOCX: {e}")
            raise
            
    def _parse_doc(self, file_path: str) -> Dict[str, Any]:
        """Парсинг старых DOC файлов"""
        try:
            # Попытка использовать antiword
            import subprocess
            
            result = subprocess.run(
                ['antiword', file_path],
                capture_output=True,
                text=True,
                encoding='utf-8',
                errors='ignore'
            )
            
            if result.returncode == 0:
                return {
                    "text": result.stdout,
                    "format": "doc",
                    "parsed_with": "antiword"
                }
            else:
                # Альтернативный метод
                return self._parse_doc_fallback(file_path)
                
        except Exception as e:
            logger.error(f"Ошибка парсинга DOC: {e}")
            return self._parse_doc_fallback(file_path)
            
    def _parse_excel(self, file_path: str) -> Dict[str, Any]:
        """Парсинг Excel файлов"""
        try:
            import pandas as pd
            import openpyxl
            
            content = {
                "sheets": [],
                "metadata": {},
                "tables": []
            }
            
            # Чтение всех листов
            excel_file = pd.ExcelFile(file_path)
            
            for sheet_name in excel_file.sheet_names:
                try:
                    # Чтение листа как DataFrame
                    df = pd.read_excel(file_path, sheet_name=sheet_name)
                    
                    sheet_data = {
                        "sheet_name": sheet_name,
                        "rows": len(df),
                        "columns": len(df.columns),
                        "columns_list": list(df.columns),
                        "data_preview": df.head(10).to_dict(orient='records')
                    }
                    
                    # Преобразование DataFrame в список для удобства
                    sheet_data["data"] = df.fillna('').astype(str).values.tolist()
                    
                    content["sheets"].append(sheet_data)
                    
                    # Извлечение таблиц (если есть именованные диапазоны)
                    workbook = openpyxl.load_workbook(file_path, data_only=True)
                    if sheet_name in workbook.sheetnames:
                        ws = workbook[sheet_name]
                        for table_name, table_range in ws.tables.items():
                            content["tables"].append({
                                "name": table_name,
                                "range": table_range,
                                "sheet": sheet_name
                            })
                            
                except Exception as e:
                    logger.warning(f"Ошибка чтения листа {sheet_name}: {e}")
                    continue
                    
            # Метаданные
            workbook = openpyxl.load_workbook(file_path)
            content["metadata"] = {
                "creator": workbook.properties.creator,
                "created": str(workbook.properties.created),
                "modified": str(workbook.properties.modified),
                "last_modified_by": workbook.properties.lastModifiedBy
            }
            
            return content
            
        except Exception as e:
            logger.error(f"Ошибка парсинга Excel: {e}")
            raise
            
    def _parse_pptx(self, file_path: str) -> Dict[str, Any]:
        """Парсинг PowerPoint файлов"""
        try:
            from pptx import Presentation
            
            prs = Presentation(file_path)
            content = {
                "slides": [],
                "metadata": {},
                "notes": []
            }
            
            for slide_num, slide in enumerate(prs.slides, 1):
                slide_content = {
                    "slide_number": slide_num,
                    "title": "",
                    "text": "",
                    "shapes": [],
                    "notes": ""
                }
                
                # Извлечение текста из форм
                for shape in slide.shapes:
                    if hasattr(shape, "text"):
                        shape_text = shape.text.strip()
                        if shape_text:
                            slide_content["text"] += shape_text + "\n"
                            
                        shape_info = {
                            "type": shape.shape_type,
                            "text": shape_text,
                            "has_text_frame": shape.has_text_frame
                        }
                        slide_content["shapes"].append(shape_info)
                        
                        # Проверка на заголовок
                        if "Title" in str(shape.shape_type) and shape_text:
                            slide_content["title"] = shape_text
                            
                # Извлечение заметок
                if slide.has_notes_slide:
                    notes_slide = slide.notes_slide
                    if notes_slide.notes_text_frame:
                        slide_content["notes"] = notes_slide.notes_text_frame.text
                        content["notes"].append({
                            "slide": slide_num,
                            "notes": notes_slide.notes_text_frame.text
                        })
                        
                content["slides"].append(slide_content)
                
            # Метаданные
            content["metadata"] = {
                "author": prs.core_properties.author,
                "created": str(prs.core_properties.created),
                "modified": str(prs.core_properties.modified),
                "title": prs.core_properties.title,
                "subject": prs.core_properties.subject
            }
            
            return content
            
        except Exception as e:
            logger.error(f"Ошибка парсинга PowerPoint: {e}")
            raise
            
    def _parse_text(self, file_path: str) -> Dict[str, Any]:
        """Парсинг текстовых файлов"""
        try:
            with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
                text = f.read()
                
            return {
                "text": text,
                "encoding": "utf-8",
                "line_count": len(text.split('\n')),
                "word_count": len(text.split())
            }
            
        except UnicodeDecodeError:
            # Попытка других кодировок
            encodings = ['cp1251', 'iso-8859-1', 'cp866', 'koi8-r']
            
            for encoding in encodings:
                try:
                    with open(file_path, 'r', encoding=encoding) as f:
                        text = f.read()
                        
                    return {
                        "text": text,
                        "encoding": encoding,
                        "line_count": len(text.split('\n')),
                        "word_count": len(text.split())
                    }
                except:
                    continue
                    
            raise ValueError("Не удалось определить кодировку файла")
            
    def _parse_markdown(self, file_path: str) -> Dict[str, Any]:
        """Парсинг Markdown файлов"""
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()
                
            import markdown
            from bs4 import BeautifulSoup
            
            # Конвертация в HTML для анализа структуры
            html_content = markdown.markdown(content)
            soup = BeautifulSoup(html_content, 'html.parser')
            
            # Извлечение структуры
            structure = {
                "headings": [],
                "links": [],
                "images": [],
                "code_blocks": [],
                "lists": []
            }
            
            # Заголовки
            for i in range(1, 7):
                for heading in soup.find_all(f'h{i}'):
                    structure["headings"].append({
                        "level": i,
                        "text": heading.get_text().strip()
                    })
                    
            # Ссылки
            for link in soup.find_all('a'):
                if link.get('href'):
                    structure["links"].append({
                        "text": link.get_text().strip(),
                        "url": link.get('href')
                    })
                    
            # Изображения
            for img in soup.find_all('img'):
                structure["images"].append({
                    "alt": img.get('alt', ''),
                    "src": img.get('src')
                })
                
            return {
                "raw_markdown": content,
                "html": html_content,
                "structure": structure,
                "text": soup.get_text()
            }
            
        except Exception as e:
            logger.error(f"Ошибка парсинга Markdown: {e}")
            return self._parse_text(file_path)  # Fallback
            
    def _parse_html(self, file_path: str) -> Dict[str, Any]:
        """Парсинг HTML файлов"""
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                html_content = f.read()
                
            from bs4 import BeautifulSoup
            
            soup = BeautifulSoup(html_content, 'html.parser')
            
            # Удаление скриптов и стилей
            for script in soup(["script", "style"]):
                script.decompose()
                
            structure = {
                "title": soup.title.string if soup.title else "",
                "headings": [],
                "paragraphs": [],
                "links": [],
                "images": [],
                "tables": [],
                "metadata": {}
            }
            
            # Заголовки
            for i in range(1, 7):
                for heading in soup.find_all(f'h{i}'):
                    structure["headings"].append({
                        "level": i,
                        "text": heading.get_text().strip()
                    })
                    
            # Параграфы
            for para in soup.find_all('p'):
                text = para.get_text().strip()
                if text:
                    structure["paragraphs"].append({
                        "text": text,
                        "class": para.get('class', [])
                    })
                    
            # Ссылки
            for link in soup.find_all('a'):
                href = link.get('href')
                if href:
                    structure["links"].append({
                        "text": link.get_text().strip(),
                        "url": href,
                        "title": link.get('title', '')
                    })
                    
            # Изображения
            for img in soup.find_all('img'):
                structure["images"].append({
                    "src": img.get('src'),
                    "alt": img.get('alt', ''),
                    "title": img.get('title', '')
                })
                
            # Таблицы
            for table_num, table in enumerate(soup.find_all('table'), 1):
                table_data = []
                headers = []
                
                # Заголовки таблицы
                for th in table.find_all('th'):
                    headers.append(th.get_text().strip())
                    
                # Данные таблицы
                for row in table.find_all('tr'):
                    row_data = [td.get_text().strip() for td in row.find_all('td')]
                    if row_data:
                        table_data.append(row_data)
                        
                if table_data:
                    structure["tables"].append({
                        "table_number": table_num,
                        "headers": headers,
                        "data": table_data,
                        "rows": len(table_data),
                        "columns": len(table_data[0]) if table_data else 0
                    })
                    
            # Метаданные
            meta_tags = soup.find_all('meta')
            for meta in meta_tags:
                name = meta.get('name') or meta.get('property')
                content = meta.get('content')
                if name and content:
                    structure["metadata"][name] = content
                    
            return {
                "raw_html": html_content,
                "structure": structure,
                "text": soup.get_text(),
                "title": structure["title"]
            }
            
        except Exception as e:
            logger.error(f"Ошибка парсинга HTML: {e}")
            return self._parse_text(file_path)  # Fallback
            
    def _get_file_metadata(self, file_path: str) -> Dict[str, Any]:
        """Получение метаданных файла"""
        import os
        import stat
        
        stat_info = os.stat(file_path)
        
        return {
            "size": stat_info.st_size,
            "created": datetime.fromtimestamp(stat_info.st_ctime).isoformat(),
            "modified": datetime.fromtimestamp(stat_info.st_mtime).isoformat(),
            "accessed": datetime.fromtimestamp(stat_info.st_atime).isoformat(),
            "permissions": stat.filemode(stat_info.st_mode)
        }
        
    def _analyze_content(self, content: Dict[str, Any]) -> Dict[str, Any]:
        """Анализ содержимого документа"""
        analysis = {
            "language": "unknown",
            "sentiment": "neutral",
            "complexity": "medium",
            "topics": [],
            "entities": [],
            "summary": "",
            "keywords": []
        }
        
        # Извлечение текста для анализа
        text_to_analyze = ""
        if isinstance(content, dict):
            if "text" in content:
                text_to_analyze = content["text"]
            elif "raw_markdown" in content:
                text_to_analyze = content["raw_markdown"]
            elif "raw_html" in content:
                text_to_analyze = content["raw_html"]
        elif isinstance(content, str):
            text_to_analyze = content
            
        if text_to_analyze:
            # Простой анализ
            analysis["word_count"] = len(text_to_analyze.split())
            analysis["character_count"] = len(text_to_analyze)
            analysis["sentence_count"] = text_to_analyze.count('.') + text_to_analyze.count('!') + text_to_analyze.count('?')
            
            # Определение языка (простая эвристика для русского)
            russian_chars = sum(1 for char in text_to_analyze if 'а' <= char.lower() <= 'я')
            total_chars = len([char for char in text_to_analyze if char.isalpha()])
            
            if total_chars > 0:
                russian_ratio = russian_chars / total_chars
                analysis["language"] = "russian" if russian_ratio > 0.5 else "english"
                
            # Извлечение ключевых слов (простая версия)
            words = text_to_analyze.lower().split()
            from collections import Counter
            word_freq = Counter(words)
            
            # Исключение стоп-слов
            stop_words = {"и", "в", "на", "с", "по", "для", "не", "что", "это", "как", "а", "но", "или", "у", "о", "от", "до"}
            keywords = [(word, count) for word, count in word_freq.items() 
                       if word not in stop_words and len(word) > 2]
            keywords.sort(key=lambda x: x[1], reverse=True)
            
            analysis["keywords"] = [word for word, count in keywords[:10]]
            
            # Простая оценка сложности
            avg_word_length = sum(len(word) for word in words) / len(words) if words else 0
            if avg_word_length > 7:
                analysis["complexity"] = "high"
            elif avg_word_length > 5:
                analysis["complexity"] = "medium"
            else:
                analysis["complexity"] = "low"
                
            # Простая суммаризация (первые 200 символов)
            analysis["summary"] = text_to_analyze[:200] + "..." if len(text_to_analyze) > 200 else text_to_analyze
            
        return analysis
        
    def _extract_pdf_images(self, file_path: str) -> List[Dict[str, Any]]:
        """Извлечение изображений из PDF"""
        images = []
        
        try:
            import fitz  # PyMuPDF
            
            doc = fitz.open(file_path)
            
            for page_num in range(len(doc)):
                page = doc.load_page(page_num)
                image_list = page.get_images(full=True)
                
                for img_index, img in enumerate(image_list):
                    xref = img[0]
                    base_image = doc.extract_image(xref)
                    
                    if base_image:
                        image_info = {
                            "page": page_num + 1,
                            "index": img_index,
                            "width": base_image.get("width", 0),
                            "height": base_image.get("height", 0),
                            "format": base_image.get("ext", ""),
                            "size": len(base_image.get("image", b""))
                        }
                        images.append(image_info)
                        
            doc.close()
            
        except ImportError:
            logger.warning("PyMuPDF не установлен, извлечение изображений из PDF недоступно")
            
        return images
        
    def _extract_docx_images(self, doc) -> List[Dict[str, Any]]:
        """Извлечение изображений из DOCX"""
        images = []
        
        try:
            import os
            import tempfile
            
            # Временная директория для извлечения
            temp_dir = tempfile.mkdtemp()
            
            # DOCX - это zip архив
            import zipfile
            import shutil
            
            # Создание копии файла
            temp_docx = os.path.join(temp_dir, "temp.docx")
            shutil.copy2(doc._package.package_name, temp_docx)
            
            # Извлечение изображений
            with zipfile.ZipFile(temp_docx, 'r') as zip_ref:
                image_files = [f for f in zip_ref.namelist() 
                             if f.startswith('word/media/') and f.endswith(('.png', '.jpg', '.jpeg', '.gif', '.bmp'))]
                
                for img_file in image_files:
                    image_info = {
                        "filename": os.path.basename(img_file),
                        "path_in_archive": img_file,
                        "size": zip_ref.getinfo(img_file).file_size
                    }
                    images.append(image_info)
                    
            # Очистка
            shutil.rmtree(temp_dir)
            
        except Exception as e:
            logger.error(f"Ошибка извлечения изображений из DOCX: {e}")
            
        return images
        
    # Методы для остальных форматов (упрощенные)
    
    def _parse_csv(self, file_path: str) -> Dict[str, Any]:
        """Парсинг CSV файлов"""
        import pandas as pd
        
        try:
            df = pd.read_csv(file_path, encoding='utf-8')
        except:
            # Попытка других кодировок
            encodings = ['cp1251', 'iso-8859-1', 'cp866']
            for encoding in encodings:
                try:
                    df = pd.read_csv(file_path, encoding=encoding)
                    break
                except:
                    continue
            else:
                raise ValueError("Не удалось прочитать CSV файл")
                
        return {
            "data": df.to_dict(orient='records'),
            "columns": list(df.columns),
            "rows": len(df),
            "dtypes": {col: str(dtype) for col, dtype in df.dtypes.items()}
        }
        
    def _parse_json(self, file_path: str) -> Dict[str, Any]:
        """Парсинг JSON файлов"""
        with open(file_path, 'r', encoding='utf-8') as f:
            data = json.load(f)
            
        return {
            "data": data,
            "type": type(data).__name__,
            "size": len(str(data))
        }
        
    def _parse_xml(self, file_path: str) -> Dict[str, Any]:
        """Парсинг XML файлов"""
        import xml.etree.ElementTree as ET
        
        tree = ET.parse(file_path)
        root = tree.getroot()
        
        def element_to_dict(element):
            result = {}
            result["tag"] = element.tag
            result["attrib"] = element.attrib
            result["text"] = element.text.strip() if element.text else ""
            
            children = []
            for child in element:
                children.append(element_to_dict(child))
                
            if children:
                result["children"] = children
                
            return result
            
        return {
            "root": element_to_dict(root),
            "structure": self._get_xml_structure(root)
        }
        
    def _get_xml_structure(self, element, depth=0):
        """Получение структуры XML"""
        structure = {
            "tag": element.tag,
            "depth": depth,
            "attributes": list(element.attrib.keys()),
            "children": []
        }
        
        for child in element:
            structure["children"].append(self._get_xml_structure(child, depth + 1))
            
        return structure
        
    # Заглушки для остальных форматов
        
    def _parse_ppt(self, file_path: str):
        """Парсинг старых PPT файлов"""
        return {"text": "", "error": "PPT parsing not implemented"}
        
    def _parse_rtf(self, file_path: str):
        """Парсинг RTF файлов"""
        return self._parse_text(file_path)  # Просто как текст
        
    def _parse_odt(self, file_path: str):
        """Парсинг ODT файлов"""
        return self._parse_text(file_path)
        
    def _parse_ods(self, file_path: str):
        """Парсинг ODS файлов"""
        return self._parse_excel(file_path)
        
    def _parse_odp(self, file_path: str):
        """Парсинг ODP файлов"""
        return self._parse_pptx(file_path)
        
    def _parse_epub(self, file_path: str):
        """Парсинг EPUB файлов"""
        return {"text": "", "error": "EPUB parsing not implemented"}
        
    def _parse_mobi(self, file_path: str):
        """Парсинг MOBI файлов"""
        return {"text": "", "error": "MOBI parsing not implemented"}
        
    def batch_parse(self, directory_path: str, recursive: bool = True) -> Dict[str, Any]:
        """Пакетный парсинг всех документов в директории"""
        import os
        
        results = {
            "directory": directory_path,
            "total_files": 0,
            "successful": 0,
            "failed": 0,
            "files": [],
            "start_time": datetime.now().isoformat(),
            "end_time": None
        }
        
        # Поиск файлов
        file_paths = []
        
        if recursive:
            for root, dirs, files in os.walk(directory_path):
                for file in files:
                    file_ext = os.path.splitext(file)[1].lower()
                    if file_ext in self.supported_formats:
                        file_paths.append(os.path.join(root, file))
        else:
            for file in os.listdir(directory_path):
                file_path = os.path.join(directory_path, file)
                if os.path.isfile(file_path):
                    file_ext = os.path.splitext(file)[1].lower()
                    if file_ext in self.supported_formats:
                        file_paths.append(file_path)
                        
        results["total_files"] = len(file_paths)
        
        # Парсинг каждого файла
        for file_path in file_paths:
            try:
                file_result = self.parse_document(file_path)
                results["files"].append(file_result)
                results["successful"] += 1
                
            except Exception as e:
                results["files"].append({
                    "file_path": file_path,
                    "error": str(e),
                    "success": False
                })
                results["failed"] += 1
                
        results["end_time"] = datetime.now().isoformat()
        
        return results