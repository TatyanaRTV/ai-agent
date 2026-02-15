#!/usr/bin/env python3
# Путь: /mnt/ai_data/ai-agent/src/interfaces/obsidian/connector.py
"""
Интеграция с Obsidian.md
Позволяет Елене читать и создавать заметки в Obsidian хранилище
"""

import os
import re
import json
from pathlib import Path
from datetime import datetime
from typing import Any, Dict, List, Optional, Union

# Библиотека для работы с YAML в Markdown
import frontmatter  # type: ignore
from loguru import logger


class ObsidianConnector:
    """
    Коннектор к Obsidian хранилищу
    Позволяет работать с заметками, тегами, ссылками
    """
    
    # Аннотации для Mypy (устраняют ошибки var-annotated)
    vault_path: Path
    stats: Dict[str, Any]
    notes_cache: Dict[str, Dict[str, Any]]
    tags_cache: Dict[str, List[str]]

    def __init__(self, vault_path: Union[str, Path]):
        """
        Инициализация коннектора к Obsidian
        
        Args:
            vault_path: путь к корневой папке хранилища Obsidian
        """
        self.vault_path = Path(vault_path)
        self.vault_path.mkdir(parents=True, exist_ok=True)
        
        # Статистика
        self.stats = {
            'total_notes': 0,
            'total_tags': 0,
            'total_links': 0
        }
        
        # Кэш для быстрого поиска
        self.notes_cache = {}
        self.tags_cache = {}
        
        # Сканируем хранилище при инициализации
        self._scan_vault()
        
        logger.info(f"📔 Obsidian коннектор инициализирован: {self.vault_path}")
        logger.info(f"   📊 Найдено заметок: {self.stats['total_notes']}")

    def _scan_vault(self) -> None:
        """Сканирование хранилища и сбор статистики"""
        self.notes_cache.clear()
        self.tags_cache.clear()
        
        # Ищем все .md файлы
        md_files = list(self.vault_path.rglob("*.md"))
        self.stats['total_notes'] = len(md_files)
        
        for md_file in md_files:
            try:
                # Читаем содержимое заметки
                with open(md_file, 'r', encoding='utf-8') as f:
                    content = f.read()
                
                # Парсим frontmatter если есть
                metadata: Dict[str, Any] = {}
                if content.startswith('---'):
                    try:
                        post = frontmatter.loads(content)
                        metadata = dict(post.metadata)
                    except Exception:
                        metadata = {}
                
                # Извлекаем теги из содержимого #tag
                tags = re.findall(r'#(\w+)', content)
                metadata['tags'] = tags
                
                # Извлекаем вики-ссылки [[ссылка]]
                links = re.findall(r'\[\[(.*?)\]\]', content)
                metadata['links'] = links
                
                # Сохраняем в кэш
                rel_path = str(md_file.relative_to(self.vault_path))
                self.notes_cache[rel_path] = {
                    'path': md_file,
                    'title': md_file.stem,
                    'metadata': metadata,
                    'modified': datetime.fromtimestamp(md_file.stat().st_mtime),
                    'tags': tags,
                    'links': links
                }
                
                # Обновляем кэш тегов
                for tag in tags:
                    if tag not in self.tags_cache:
                        self.tags_cache[tag] = []
                    self.tags_cache[tag].append(rel_path)
                
            except Exception as e:
                logger.error(f"❌ Ошибка чтения {md_file}: {e}")
        
        self.stats['total_tags'] = len(self.tags_cache)
        logger.debug(f"📊 Найдено тегов: {self.stats['total_tags']}")


    def create_note(self, title: str, content: str, tags: Optional[List[str]] = None, folder: Optional[str] = None) -> str:
        """
        Создание новой заметки
        """
        # Очищаем заголовок от недопустимых символов
        clean_title = re.sub(r'[<>:"/\\|?*]', '', title)
        clean_title = clean_title.replace(' ', '_')
        
        # Определяем путь
        if folder:
            note_path = self.vault_path / folder / f"{clean_title}.md"
            note_path.parent.mkdir(parents=True, exist_ok=True)
        else:
            note_path = self.vault_path / f"{clean_title}.md"
        
        # Проверяем, существует ли уже
        if note_path.exists():
            base = note_path.stem
            counter = 1
            while note_path.exists():
                note_path = note_path.with_name(f"{base}_{counter}.md")
                counter += 1
        
        # Формируем frontmatter если есть теги
        if tags:
            yaml_tags = '\n'.join([f'  - {tag}' for tag in tags])
            frontmatter_text = f"---\ntags:\n{yaml_tags}\ncreated: {datetime.now().strftime('%Y-%m-%d %H:%M')}\n---\n"
            full_content = frontmatter_text + "\n" + content
        else:
            full_content = content
        
        # Сохраняем
        with open(note_path, 'w', encoding='utf-8') as f:
            f.write(full_content)
        
        logger.info(f"📝 Создана заметка: {note_path.relative_to(self.vault_path)}")
        
        # Обновляем кэш
        self._scan_vault()
        
        return str(note_path)
    
    def read_note(self, note_name: str, folder: Optional[str] = None) -> Optional[str]:
        """
        Чтение заметки
        """
        # Определяем путь
        if folder:
            note_path: Optional[Path] = self.vault_path / folder / f"{note_name}.md"
        else:
            # Ищем по имени во всем хранилище
            note_path = None
            for md_file in self.vault_path.rglob("*.md"):
                if md_file.stem == note_name or md_file.name == note_name:
                    note_path = md_file
                    break
        
        if not note_path or not note_path.exists():
            logger.warning(f"⚠️ Заметка не найдена: {note_name}")
            return None
        
        try:
            with open(note_path, 'r', encoding='utf-8') as f:
                content = f.read()
            
            logger.debug(f"📖 Прочитана заметка: {note_path.relative_to(self.vault_path)}")
            return content
        except Exception as e:
            logger.error(f"❌ Ошибка чтения {note_path}: {e}")
            return None



    def update_note(self, note_name: str, content: str, folder: Optional[str] = None) -> bool:
        """
        Обновление существующей заметки
        """
        # Находим заметку
        note_path: Optional[Path] = None
        if folder:
            note_path = self.vault_path / folder / f"{note_name}.md"
        else:
            for md_file in self.vault_path.rglob("*.md"):
                if md_file.stem == note_name:
                    note_path = md_file
                    break
        
        if not note_path or not note_path.exists():
            logger.warning(f"⚠️ Заметка не найдена для обновления: {note_name}")
            return False
        
        try:
            # Сохраняем frontmatter если есть
            with open(note_path, 'r', encoding='utf-8') as f:
                old_content = f.read()
            
            if old_content.startswith('---'):
                # Извлекаем старый frontmatter
                parts = old_content.split('---', 2)
                if len(parts) >= 3:
                    frontmatter_text = '---' + parts[1] + '---'
                    new_content = frontmatter_text + "\n" + content
                else:
                    new_content = content
            else:
                new_content = content
            
            with open(note_path, 'w', encoding='utf-8') as f:
                f.write(new_content)
            
            logger.info(f"📝 Обновлена заметка: {note_path.relative_to(self.vault_path)}")
            
            # Обновляем кэш
            self._scan_vault()
            return True
            
        except Exception as e:
            logger.error(f"❌ Ошибка обновления {note_path}: {e}")
            return False

    def delete_note(self, note_name: str, folder: Optional[str] = None) -> bool:
        """
        Удаление заметки
        """
        # Находим заметку
        note_path: Optional[Path] = None
        if folder:
            note_path = self.vault_path / folder / f"{note_name}.md"
        else:
            for md_file in self.vault_path.rglob("*.md"):
                if md_file.stem == note_name:
                    note_path = md_file
                    break
        
        if not note_path or not note_path.exists():
            logger.warning(f"⚠️ Заметка не найдена для удаления: {note_name}")
            return False
        
        try:
            note_path.unlink()
            logger.info(f"🗑️ Удалена заметка: {note_path.relative_to(self.vault_path)}")
            
            # Обновляем кэш
            self._scan_vault()
            return True
        except Exception as e:
            logger.error(f"❌ Ошибка удаления {note_path}: {e}")
            return False

    def search_notes(self, query: str, search_type: str = 'all') -> List[Dict[str, Any]]:
        """
        Поиск заметок
        """
        results: List[Dict[str, Any]] = []
        query_lower = query.lower()
        
        for rel_path, note_info in self.notes_cache.items():
            score = 0
            matches: List[str] = []
            
            # Поиск в заголовке
            if search_type in ['title', 'all'] and query_lower in note_info['title'].lower():
                score += 10
                matches.append('title')
            
            # Поиск в тегах
            if search_type in ['tags', 'all']:
                for tag in note_info['tags']:
                    if query_lower in tag.lower():
                        score += 5
                        matches.append(f'tag:{tag}')
            
            # Поиск в содержимом
            if search_type in ['content', 'all']:
                try:
                    with open(note_info['path'], 'r', encoding='utf-8') as f:
                        content = f.read().lower()
                    if query_lower in content:
                        score += 1
                        matches.append('content')
                except Exception:
                    pass
            
            if score > 0:
                results.append({
                    'path': rel_path,
                    'title': note_info['title'],
                    'score': score,
                    'matches': matches,
                    'modified': note_info['modified']
                })
        
        # Сортируем по релевантности
        results.sort(key=lambda x: x['score'], reverse=True)
        
        logger.debug(f"🔍 Поиск '{query}': найдено {len(results)} результатов")
        return results
    
    def get_notes_by_tag(self, tag: str) -> List[Dict[str, Any]]:
        """
        Получение всех заметок с определённым тегом
        """
        tag = tag.lstrip('#')
        notes = self.tags_cache.get(tag, [])
        
        result = []
        for rel_path in notes:
            if rel_path in self.notes_cache:
                result.append(self.notes_cache[rel_path])
        
        logger.debug(f"🏷️ Тег #{tag}: {len(result)} заметок")
        return result

    def get_all_tags(self) -> Dict[str, int]:
        """Получение всех тегов с количеством использований"""
        tags_with_count = {}
        for tag, notes in self.tags_cache.items():
            tags_with_count[tag] = len(notes)
        
        return dict(sorted(tags_with_count.items(), key=lambda x: x[1], reverse=True))

    def create_link(self, from_note: str, to_note: str, alias: Optional[str] = None) -> bool:
        """
        Создание вики-ссылки между заметками
        """
        from_path: Optional[Path] = None
        to_name: Optional[str] = None
        
        for rel_path, info in self.notes_cache.items():
            if info['title'] == from_note:
                from_path = info['path']
            if info['title'] == to_note:
                to_name = info['title']
        
        if not from_path or not to_name:
            logger.warning(f"⚠️ Не удалось создать ссылку: заметки не найдены")
            return False
        
        try:
            with open(from_path, 'r', encoding='utf-8') as f:
                content = f.read()
            
            # Создаем ссылку
            link = f"[[{to_name}|{alias}]]" if alias else f"[[{to_name}]]"
            
            # Добавляем в конец
            new_content = content + f"\n\n{link}"
            
            with open(from_path, 'w', encoding='utf-8') as f:
                f.write(new_content)
            
            logger.info(f"🔗 Создана ссылка из {from_note} на {to_name}")
            self._scan_vault()
            return True
            
        except Exception as e:
            logger.error(f"❌ Ошибка создания ссылки: {e}")
            return False

    def get_backlinks(self, note_name: str) -> List[Dict[str, str]]:
        """
        Получение обратных ссылок
        """
        backlinks = []
        for rel_path, info in self.notes_cache.items():
            if note_name in info.get('links', []):
                backlinks.append({'path': rel_path, 'title': info['title']})
        return backlinks
    
    def get_stats(self) -> Dict[str, Any]:
        """Получение статистики"""
        self._scan_vault()
        return {
            'total_notes': self.stats['total_notes'],
            'total_tags': self.stats['total_tags'],
            'vault_path': str(self.vault_path),
            'tags': self.get_all_tags()
        }
    
    def export_to_json(self, output_path: Optional[str] = None) -> Dict[str, Any]:
        """
        Экспорт всего хранилища в JSON
        """
        export_data: Dict[str, Any] = {
            'vault': str(self.vault_path),
            'exported': datetime.now().isoformat(),
            'stats': self.stats,
            'notes': {}
        }
        
        for rel_path, info in self.notes_cache.items():
            try:
                with open(info['path'], 'r', encoding='utf-8') as f:
                    content = f.read()
                
                export_data['notes'][rel_path] = {
                    'title': info['title'],
                    'content': content,
                    'tags': info['tags'],
                    'links': info['links'],
                    'modified': info['modified'].isoformat()
                }
            except Exception as e:
                logger.error(f"❌ Ошибка экспорта {rel_path}: {e}")
        
        if output_path:
            with open(output_path, 'w', encoding='utf-8') as f:
                json.dump(export_data, f, ensure_ascii=False, indent=2)
            logger.info(f"💾 Экспорт сохранён в {output_path}")
        
        return export_data

if __name__ == "__main__":
    # Тестовый запуск
    import argparse
    parser = argparse.ArgumentParser()
    parser.add_argument('--vault', type=str, default="data/test_vault")
    args = parser.parse_args()
    
    connector = ObsidianConnector(args.vault)
    print(connector.get_stats())
