#!/usr/bin/env python3
# Путь: /mnt/ai_data/ai-agent/src/interfaces/obsidian/connector.py
"""
Интеграция с Obsidian.md
Позволяет Елене читать и создавать заметки в Obsidian хранилище
"""

from pathlib import Path
import re
from datetime import datetime
import frontmatter
from loguru import logger


class ObsidianConnector:
    """
    Коннектор к Obsidian хранилищу
    Позволяет работать с заметками, тегами, ссылками
    """

    def __init__(self, vault_path: str):
        """
        Инициализация коннектора к Obsidian

        Args:
            vault_path: путь к корневой папке хранилища Obsidian
        """
        self.vault_path = Path(vault_path)
        self.vault_path.mkdir(parents=True, exist_ok=True)

        # Статистика
        self.stats = {"total_notes": 0, "total_tags": 0, "total_links": 0}

        # Кэш для быстрого поиска
        self.notes_cache = {}
        self.tags_cache = {}

        # Сканируем хранилище при инициализации
        self._scan_vault()

        logger.info(f"📔 Obsidian коннектор инициализирован: {self.vault_path}")
        logger.info(f"   📊 Найдено заметок: {self.stats['total_notes']}")

    def _scan_vault(self):
        """Сканирование хранилища и сбор статистики"""
        self.notes_cache.clear()
        self.tags_cache.clear()

        # Ищем все .md файлы
        md_files = list(self.vault_path.rglob("*.md"))
        self.stats["total_notes"] = len(md_files)

        for md_file in md_files:
            try:
                # Читаем метаданные заметки
                with open(md_file, "r", encoding="utf-8") as f:
                    content = f.read()

                # Парсим frontmatter если есть
                if content.startswith("---"):
                    post = frontmatter.loads(content)
                    metadata = post.metadata
                else:
                    metadata = {}

                # Извлекаем теги из содержимого
                tags = re.findall(r"#(\w+)", content)
                metadata["tags"] = tags

                # Извлекаем вики-ссылки [[ссылка]]
                links = re.findall(r"\[\[(.*?)\]\]", content)
                metadata["links"] = links

                # Сохраняем в кэш
                rel_path = md_file.relative_to(self.vault_path)
                self.notes_cache[str(rel_path)] = {
                    "path": md_file,
                    "title": md_file.stem,
                    "metadata": metadata,
                    "modified": datetime.fromtimestamp(md_file.stat().st_mtime),
                    "tags": tags,
                    "links": links,
                }

                # Обновляем кэш тегов
                for tag in tags:
                    if tag not in self.tags_cache:
                        self.tags_cache[tag] = []
                    self.tags_cache[tag].append(str(rel_path))

            except Exception as e:
                logger.error(f"❌ Ошибка чтения {md_file}: {e}")

        self.stats["total_tags"] = len(self.tags_cache)
        logger.debug(f"📊 Найдено тегов: {self.stats['total_tags']}")

    def create_note(self, title: str, content: str, tags=None, folder=None):
        """
        Создание новой заметки

        Args:
            title: заголовок заметки (будет именем файла)
            content: содержимое заметки в Markdown
            tags: список тегов
            folder: подпапка в хранилище (опционально)

        Returns:
            путь к созданной заметке
        """
        # Очищаем заголовок от недопустимых символов
        clean_title = re.sub(r'[<>:"/\\|?*]', "", title)
        clean_title = clean_title.replace(" ", "_")

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
                note_path = note_path.with_stem(f"{base}_{counter}")
                counter += 1

        # Формируем frontmatter если есть теги
        if tags:
            yaml_tags = "\n".join([f"  - {tag}" for tag in tags])
            frontmatter_text = f"""---
tags:
{yaml_tags}
created: {datetime.now().strftime('%Y-%m-%d %H:%M')}
---
"""
            full_content = frontmatter_text + "\n" + content
        else:
            full_content = content

        # Сохраняем
        with open(note_path, "w", encoding="utf-8") as f:
            f.write(full_content)

        logger.info(f"📝 Создана заметка: {note_path.relative_to(self.vault_path)}")

        # Обновляем кэш
        self._scan_vault()

        return str(note_path)

    def read_note(self, note_name: str, folder=None):
        """
        Чтение заметки

        Args:
            note_name: имя заметки (без .md) или путь
            folder: папка (если note_name не содержит путь)

        Returns:
            содержимое заметки или None
        """
        # Определяем путь
        if folder:
            note_path = self.vault_path / folder / f"{note_name}.md"
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
            with open(note_path, "r", encoding="utf-8") as f:
                content = f.read()

            logger.debug(f"📖 Прочитана заметка: {note_path.relative_to(self.vault_path)}")
            return content
        except Exception as e:
            logger.error(f"❌ Ошибка чтения {note_path}: {e}")
            return None

    def update_note(self, note_name: str, content: str, folder=None):
        """
        Обновление существующей заметки

        Args:
            note_name: имя заметки
            content: новое содержимое
            folder: папка

        Returns:
            bool: успешно или нет
        """
        # Находим заметку
        if folder:
            note_path = self.vault_path / folder / f"{note_name}.md"
        else:
            note_path = None
            for md_file in self.vault_path.rglob("*.md"):
                if md_file.stem == note_name:
                    note_path = md_file
                    break

        if not note_path or not note_path.exists():
            logger.warning(f"⚠️ Заметка не найдена для обновления: {note_name}")
            return False

        try:
            # Сохраняем frontmatter если есть
            with open(note_path, "r", encoding="utf-8") as f:
                old_content = f.read()

            if old_content.startswith("---"):
                # Извлекаем старый frontmatter
                parts = old_content.split("---", 2)
                if len(parts) >= 3:
                    frontmatter_text = "---" + parts[1] + "---"
                    new_content = frontmatter_text + "\n" + content
                else:
                    new_content = content
            else:
                new_content = content

            with open(note_path, "w", encoding="utf-8") as f:
                f.write(new_content)

            logger.info(f"📝 Обновлена заметка: {note_path.relative_to(self.vault_path)}")

            # Обновляем кэш
            self._scan_vault()

            return True

        except Exception as e:
            logger.error(f"❌ Ошибка обновления {note_path}: {e}")
            return False

    def delete_note(self, note_name: str, folder=None):
        """
        Удаление заметки

        Args:
            note_name: имя заметки
            folder: папка

        Returns:
            bool: успешно или нет
        """
        # Находим заметку
        if folder:
            note_path = self.vault_path / folder / f"{note_name}.md"
        else:
            note_path = None
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

    def search_notes(self, query: str, search_type="all"):
        """
        Поиск заметок

        Args:
            query: поисковый запрос
            search_type: 'title', 'content', 'tags', 'all'

        Returns:
            список найденных заметок с релевантностью
        """
        results = []
        query_lower = query.lower()

        for rel_path, note_info in self.notes_cache.items():
            score = 0
            matches = []

            # Поиск в заголовке
            if search_type in ["title", "all"] and query_lower in note_info["title"].lower():
                score += 10
                matches.append("title")

            # Поиск в тегах
            if search_type in ["tags", "all"]:
                for tag in note_info["tags"]:
                    if query_lower in tag.lower():
                        score += 5
                        matches.append(f"tag:{tag}")

            # Поиск в содержимом (если нужно)
            if search_type in ["content", "all"]:
                try:
                    with open(note_info["path"], "r", encoding="utf-8") as f:
                        content = f.read().lower()
                    if query_lower in content:
                        score += 1
                        matches.append("content")
                except:
                    pass

            if score > 0:
                results.append(
                    {
                        "path": rel_path,
                        "title": note_info["title"],
                        "score": score,
                        "matches": matches,
                        "modified": note_info["modified"],
                    }
                )

        # Сортируем по релевантности
        results.sort(key=lambda x: x["score"], reverse=True)

        logger.debug(f"🔍 Поиск '{query}': найдено {len(results)} результатов")
        return results

    def get_notes_by_tag(self, tag: str):
        """
        Получение всех заметок с определённым тегом

        Args:
            tag: тег (без #)

        Returns:
            список заметок с этим тегом
        """
        tag = tag.lstrip("#")
        notes = self.tags_cache.get(tag, [])

        result = []
        for rel_path in notes:
            if rel_path in self.notes_cache:
                result.append(self.notes_cache[rel_path])

        logger.debug(f"🏷️ Тег #{tag}: {len(result)} заметок")
        return result

    def get_all_tags(self):
        """Получение всех тегов с количеством использований"""
        tags_with_count = {}
        for tag, notes in self.tags_cache.items():
            tags_with_count[tag] = len(notes)

        return dict(sorted(tags_with_count.items(), key=lambda x: x[1], reverse=True))

    def create_link(self, from_note: str, to_note: str, alias=None):
        """
        Создание вики-ссылки между заметками

        Args:
            from_note: заметка, в которую добавить ссылку
            to_note: заметка, на которую ссылаться
            alias: отображаемый текст (опционально)

        Returns:
            bool: успешно или нет
        """
        # Находим заметки
        from_path = None
        to_name = None

        for rel_path, info in self.notes_cache.items():
            if info["title"] == from_note:
                from_path = info["path"]
            if info["title"] == to_note:
                to_name = info["title"]

        if not from_path or not to_name:
            logger.warning(f"⚠️ Не удалось создать ссылку: заметки не найдены")
            return False

        try:
            with open(from_path, "r", encoding="utf-8") as f:
                content = f.read()

            # Создаем ссылку
            if alias:
                link = f"[[{to_name}|{alias}]]"
            else:
                link = f"[[{to_name}]]"

            # Добавляем в конец
            new_content = content + f"\n\n{link}"

            with open(from_path, "w", encoding="utf-8") as f:
                f.write(new_content)

            logger.info(f"🔗 Создана ссылка из {from_note} на {to_name}")

            # Обновляем кэш
            self._scan_vault()

            return True

        except Exception as e:
            logger.error(f"❌ Ошибка создания ссылки: {e}")
            return False

    def get_backlinks(self, note_name: str):
        """
        Получение всех ссылающихся на заметку

        Args:
            note_name: имя заметки

        Returns:
            список заметок, которые ссылаются на данную
        """
        backlinks = []

        for rel_path, info in self.notes_cache.items():
            if note_name in info.get("links", []):
                backlinks.append({"path": rel_path, "title": info["title"]})

        return backlinks

    def get_stats(self):
        """Получение статистики по хранилищу"""
        self._scan_vault()  # Обновляем

        return {
            "total_notes": self.stats["total_notes"],
            "total_tags": self.stats["total_tags"],
            "vault_path": str(self.vault_path),
            "tags": self.get_all_tags(),
        }

    def export_to_json(self, output_path=None):
        """
        Экспорт всего хранилища в JSON

        Args:
            output_path: путь для сохранения (опционально)

        Returns:
            dict с данными всех заметок
        """
        export_data = {
            "vault": str(self.vault_path),
            "exported": datetime.now().isoformat(),
            "stats": self.stats,
            "notes": {},
        }

        for rel_path, info in self.notes_cache.items():
            try:
                with open(info["path"], "r", encoding="utf-8") as f:
                    content = f.read()

                export_data["notes"][rel_path] = {
                    "title": info["title"],
                    "content": content,
                    "tags": info["tags"],
                    "links": info["links"],
                    "modified": info["modified"].isoformat(),
                }
            except Exception as e:
                logger.error(f"❌ Ошибка экспорта {rel_path}: {e}")

        if output_path:
            import json

            with open(output_path, "w", encoding="utf-8") as f:
                json.dump(export_data, f, ensure_ascii=False, indent=2)
            logger.info(f"💾 Экспорт сохранён в {output_path}")

        return export_data
