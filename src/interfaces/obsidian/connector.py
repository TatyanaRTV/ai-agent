"""
Интеграция с Obsidian для работы с заметками и знаниями
"""

import os
import logging
from pathlib import Path
from typing import Dict, List, Optional, Any
import json
import yaml
import frontmatter

logger = logging.getLogger(__name__)

class ObsidianConnector:
    """Соединитель с Obsidian vault"""
    
    def __init__(self, vault_path: str):
        self.vault_path = Path(vault_path)
        self.notes_cache = {}
        self.tags_cache = {}
        self.backlinks_cache = {}
        
        logger.info(f"📒 Инициализация подключения к Obsidian: {vault_path}")
        
        # Проверка существования vault
        if not self.vault_path.exists():
            logger.error(f"Vault не найден: {vault_path}")
            raise FileNotFoundError(f"Obsidian vault не найден: {vault_path}")
        
        # Проверка наличия папки .obsidian
        if not (self.vault_path / ".obsidian").exists():
            logger.warning("Папка .obsidian не найдена. Vault может быть не инициализирован.")
    
    def scan_vault(self, force: bool = False) -> Dict[str, Any]:
        """Сканирование vault для построения индекса"""
        if not force and self.notes_cache:
            logger.info("Использую кэшированный индекс vault")
            return self._get_vault_stats()
        
        logger.info("Сканирование Obsidian vault...")
        
        notes = []
        tags = set()
        backlinks = {}
        
        # Рекурсивный обход всех .md файлов
        for md_file in self.vault_path.rglob("*.md"):
            if md_file.is_file():
                note_info = self._parse_note(md_file)
                if note_info:
                    notes.append(note_info)
                    tags.update(note_info.get('tags', []))
                    
                    # Сбор backlinks
                    for link in note_info.get('links', []):
                        if link not in backlinks:
                            backlinks[link] = []
                        backlinks[link].append(note_info['path'])
        
        # Кэширование
        self.notes_cache = {note['path']: note for note in notes}
        self.tags_cache = list(tags)
        self.backlinks_cache = backlinks
        
        logger.info(f"Сканирование завершено. Найдено {len(notes)} заметок, {len(tags)} тегов")
        
        return self._get_vault_stats()
    
    def _parse_note(self, file_path: Path) -> Optional[Dict[str, Any]]:
        """Парсинг отдельной заметки"""
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()
            
            # Парсинг frontmatter
            post = frontmatter.loads(content)
            
            # Извлечение метаданных
            metadata = dict(post.metadata)
            
            # Извлечение контента
            content_text = post.content
            
            # Поиск ссылок [[...]]
            import re
            links = re.findall(r'\[\[([^\]]+)\]\]', content_text)
            
            # Поиск тегов #tag
            tags_in_text = re.findall(r'#([a-zA-Zа-яА-Я0-9_-]+)', content_text)
            
            # Объединение тегов из frontmatter и текста
            all_tags = set(metadata.get('tags', []))
            all_tags.update(tags_in_text)
            
            # Извлечение заголовка
            title = metadata.get('title', file_path.stem)
            
            # Поиск заголовка в тексте (# Заголовок)
            title_match = re.search(r'^#\s+(.+)$', content_text, re.MULTILINE)
            if title_match and not metadata.get('title'):
                title = title_match.group(1).strip()
            
            return {
                'path': str(file_path.relative_to(self.vault_path)),
                'full_path': str(file_path),
                'title': title,
                'content': content_text,
                'metadata': metadata,
                'tags': list(all_tags),
                'links': links,
                'word_count': len(content_text.split()),
                'character_count': len(content_text),
                'created': metadata.get('created', file_path.stat().st_ctime),
                'modified': metadata.get('modified', file_path.stat().st_mtime),
            }
            
        except Exception as e:
            logger.error(f"Ошибка парсинга заметки {file_path}: {e}")
            return None
    
    def _get_vault_stats(self) -> Dict[str, Any]:
        """Получение статистики vault"""
        total_notes = len(self.notes_cache)
        total_tags = len(self.tags_cache)
        total_links = sum(len(note.get('links', [])) for note in self.notes_cache.values())
        
        # Самые популярные теги
        tag_counts = {}
        for note in self.notes_cache.values():
            for tag in note.get('tags', []):
                tag_counts[tag] = tag_counts.get(tag, 0) + 1
        
        popular_tags = sorted(tag_counts.items(), key=lambda x: x[1], reverse=True)[:10]
        
        return {
            'total_notes': total_notes,
            'total_tags': total_tags,
            'total_links': total_links,
            'popular_tags': popular_tags,
            'vault_size': self._get_vault_size(),
            'last_scanned': getattr(self, '_last_scanned', None)
        }
    
    def _get_vault_size(self) -> str:
        """Получение размера vault"""
        total_size = 0
        for file in self.vault_path.rglob("*"):
            if file.is_file():
                total_size += file.stat().st_size
        
        # Форматирование размера
        for unit in ['B', 'KB', 'MB', 'GB']:
            if total_size < 1024:
                return f"{total_size:.2f} {unit}"
            total_size /= 1024
        
        return f"{total_size:.2f} TB"
    
    def search_notes(self, query: str, limit: int = 20) -> List[Dict[str, Any]]:
        """Поиск заметок по запросу"""
        results = []
        
        for note in self.notes_cache.values():
            # Поиск в заголовке
            if query.lower() in note['title'].lower():
                results.append(note)
                continue
            
            # Поиск в контенте
            if query.lower() in note['content'].lower():
                results.append(note)
                continue
            
            # Поиск в тегах
            for tag in note.get('tags', []):
                if query.lower() in tag.lower():
                    results.append(note)
                    break
        
        # Сортировка по релевантности (простейшая)
        results.sort(key=lambda x: (
            query.lower() in x['title'].lower(),
            x['content'].lower().count(query.lower()),
            len(x['content'])
        ), reverse=True)
        
        return results[:limit]
    
    def get_note(self, note_path: str) -> Optional[Dict[str, Any]]:
        """Получение конкретной заметки"""
        # Попробовать найти в кэше
        if note_path in self.notes_cache:
            return self.notes_cache[note_path]
        
        # Если нет в кэше, загрузить файл
        full_path = self.vault_path / note_path
        if full_path.exists():
            return self._parse_note(full_path)
        
        return None
    
    def create_note(self, title: str, content: str, tags: List[str] = None, 
                   metadata: Dict[str, Any] = None) -> Optional[str]:
        """Создание новой заметки"""
        try:
            # Генерация имени файла
            import re
            from datetime import datetime
            
            # Очистка названия для имени файла
            filename = re.sub(r'[^\w\s-]', '', title)
            filename = re.sub(r'[-\s]+', '-', filename)
            filename = filename.strip('-')
            
            # Добавление временной метки для уникальности
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"{filename}_{timestamp}.md"
            
            # Путь для сохранения
            save_path = self.vault_path / filename
            
            # Подготовка frontmatter
            frontmatter_data = {
                'title': title,
                'created': datetime.now().isoformat(),
                'tags': tags or [],
            }
            
            if metadata:
                frontmatter_data.update(metadata)
            
            # Запись файла
            with open(save_path, 'w', encoding='utf-8') as f:
                # Запись frontmatter
                f.write('---\n')
                yaml.dump(frontmatter_data, f, allow_unicode=True)
                f.write('---\n\n')
                
                # Запись контента
                f.write(content)
            
            logger.info(f"Создана новая заметка: {filename}")
            
            # Обновление кэша
            self.notes_cache[str(save_path.relative_to(self.vault_path))] = {
                'path': str(save_path.relative_to(self.vault_path)),
                'title': title,
                'content': content,
                'tags': tags or [],
                'created': datetime.now().isoformat(),
                'modified': datetime.now().isoformat(),
            }
            
            return str(save_path.relative_to(self.vault_path))
            
        except Exception as e:
            logger.error(f"Ошибка создания заметки: {e}")
            return None
    
    def update_note(self, note_path: str, content: str = None, 
                   new_tags: List[str] = None, metadata_updates: Dict[str, Any] = None) -> bool:
        """Обновление существующей заметки"""
        try:
            full_path = self.vault_path / note_path
            
            if not full_path.exists():
                logger.error(f"Заметка не найдена: {note_path}")
                return False
            
            # Загрузка существующей заметки
            with open(full_path, 'r', encoding='utf-8') as f:
                post = frontmatter.load(f)
            
            # Обновление контента
            if content is not None:
                post.content = content
            
            # Обновление тегов
            if new_tags is not None:
                post['tags'] = new_tags
            
            # Обновление метаданных
            if metadata_updates:
                for key, value in metadata_updates.items():
                    post[key] = value
            
            # Обновление времени модификации
            from datetime import datetime
            post['modified'] = datetime.now().isoformat()
            
            # Сохранение
            with open(full_path, 'w', encoding='utf-8') as f:
                f.write(frontmatter.dumps(post))
            
            logger.info(f"Заметка обновлена: {note_path}")
            
            # Обновление кэша
            if note_path in self.notes_cache:
                self.notes_cache[note_path]['content'] = content or self.notes_cache[note_path]['content']
                self.notes_cache[note_path]['tags'] = new_tags or self.notes_cache[note_path]['tags']
                self.notes_cache[note_path]['modified'] = post['modified']
            
            return True
            
        except Exception as e:
            logger.error(f"Ошибка обновления заметки: {e}")
            return False
    
    def get_backlinks(self, note_path: str) -> List[str]:
        """Получение backlinks для заметки"""
        return self.backlinks_cache.get(note_path, [])
    
    def get_graph_data(self) -> Dict[str, Any]:
        """Получение данных для графа связей"""
        nodes = []
        edges = []
        
        for note_path, note in self.notes_cache.items():
            # Узел для заметки
            nodes.append({
                'id': note_path,
                'label': note['title'],
                'size': min(20 + note['word_count'] / 100, 50),
                'color': self._get_tag_color(note.get('tags', [])),
                'tags': note.get('tags', [])
            })
            
            # Рёбра для ссылок
            for link in note.get('links', []):
                edges.append({
                    'source': note_path,
                    'target': link,
                    'value': 1
                })
        
        return {
            'nodes': nodes,
            'edges': edges,
            'directed': False,
            'multigraph': False
        }
    
    def _get_tag_color(self, tags: List[str]) -> str:
        """Получение цвета для тега"""
        if not tags:
            return '#6b5bff'  # Синий по умолчанию
        
        # Простая хэш-функция для генерации цвета
        import hashlib
        
        tag_str = ','.join(sorted(tags))
        hash_hex = hashlib.md5(tag_str.encode()).hexdigest()[:6]
        
        # Яркие, но приятные цвета
        colors = [
            '#ff6b9d', '#6b5bff', '#4dabf7', '#51cf66', '#ffd43b',
            '#ff922b', '#cc5de8', '#339af0', '#20c997', '#fab005'
        ]
        
        # Использовать хэш для выбора цвета
        color_index = int(hash_hex, 16) % len(colors)
        return colors[color_index]
    
    def export_to_vector_db(self, vector_memory) -> int:
        """Экспорт заметок в векторную базу данных"""
        logger.info("Экспорт заметок Obsidian в векторную БД...")
        
        exported_count = 0
        
        for note_path, note in self.notes_cache.items():
            try:
                # Подготовка текста для эмбеддинга
                text = f"{note['title']}\n\n{note['content']}"
                
                # Метаданные для вектора
                metadata = {
                    'source': 'obsidian',
                    'path': note_path,
                    'title': note['title'],
                    'tags': note['tags'],
                    'word_count': note['word_count'],
                    'created': note['created'],
                    'modified': note['modified']
                }
                
                # Сохранение в векторную БД
                vector_memory.store_memory(
                    content=text,
                    metadata=metadata
                )
                
                exported_count += 1
                
                if exported_count % 10 == 0:
                    logger.info(f"Экспортировано {exported_count} заметок...")
                    
            except Exception as e:
                logger.error(f"Ошибка экспорта заметки {note_path}: {e}")
        
        logger.info(f"Экспорт завершен. Всего экспортировано: {exported_count}")
        return exported_count