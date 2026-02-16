#!/usr/bin/env python3
"""
Скрипт аудита проекта Елена - проверяет все файлы на совместимость
и показывает, где мы забыли внести изменения после правок.
"""

import os
import sys
import re
from pathlib import Path
from datetime import datetime
from collections import defaultdict


class ProjectAudit:
    def __init__(self):
        self.root = Path("/mnt/ai_data/ai-agent")
        self.errors = []
        self.warnings = []
        self.untouched = []
        self.reports = defaultdict(list)

    def print_header(self, text):
        print(f"\n{'='*60}")
        print(f" {text}")
        print(f"{'='*60}")

    def check_file_exists(self, path):
        """Проверка существования файла"""
        if not path.exists():
            self.errors.append(f"❌ ОТСУТСТВУЕТ: {path}")
            return False
        return True

    def check_imports(self, file_path, required_imports):
        """Проверка наличия обязательных импортов"""
        if not self.check_file_exists(file_path):
            return

        with open(file_path, "r") as f:
            content = f.read()

        for imp in required_imports:
            if imp not in content:
                self.warnings.append(f"⚠️ В {file_path} нет импорта: {imp}")

    def check_exist_ok(self):
        """Проверка exist_ok=True во всех mkdir"""
        self.print_header("ПРОВЕРКА СОЗДАНИЯ ДИРЕКТОРИЙ")

        files = list(self.root.rglob("*.py"))
        for file in files:
            if "venv" in str(file):
                continue

            with open(file, "r") as f:
                content = f.read()
                if "mkdir" in content:
                    if "exist_ok=True" not in content:
                        self.warnings.append(f"⚠️ {file} использует mkdir БЕЗ exist_ok=True")
                        print(f"   ⚠️ {file} - добавить exist_ok=True")

    def check_unload_methods(self):
        """Проверка наличия методов выгрузки"""
        self.print_header("ПРОВЕРКА МЕТОДОВ ВЫГРУЗКИ")

        # Классы, которые должны иметь unload_model/cleanup
        classes_to_check = [
            ("conversation_tools.py", "unload_model"),
            ("vision_engine.py", "unload_model"),
            ("voice_engine.py", "cleanup"),
            ("memory_core.py", "save_state"),
        ]

        for filename, method in classes_to_check:
            file_path = self.root / "src" / "tools" / filename
            if not file_path.exists():
                file_path = self.root / "src" / "engines" / filename
            if not file_path.exists():
                file_path = self.root / "src" / "memory" / filename

            if file_path.exists():
                with open(file_path, "r") as f:
                    content = f.read()
                    if f"def {method}" not in content:
                        self.errors.append(f"❌ В {file_path} ОТСУТСТВУЕТ метод {method}()")
                        print(f"   ❌ {file_path} - НЕТ {method}()")
                    else:
                        print(f"   ✅ {file_path} - есть {method}()")

    def check_bootstrap_stop_services(self):
        """Проверка правильности _stop_services"""
        self.print_header("ПРОВЕРКА _stop_services В bootstrap.py")

        bootstrap = self.root / "src" / "core" / "bootstrap.py"
        if not bootstrap.exists():
            self.errors.append("❌ bootstrap.py не найден")
            return

        with open(bootstrap, "r") as f:
            content = f.read()

        # Проверяем наличие всех выгрузок
        checks = [
            ("telegram_bot", "telegram_bot.stop()"),
            ("cognitive_loop", "cognitive_loop'.stop()"),
            ("memory", "save_state"),
            ("vision", "unload_model"),
            ("voice", "cleanup"),
        ]

        for component, method in checks:
            if method not in content:
                self.warnings.append(f"⚠️ В _stop_services нет выгрузки {component}")
                print(f"   ⚠️ bootstrap.py - добавить выгрузку {component}")

    def check_telegram_bot(self):
        """Проверка telegram/bot.py на наличие защиты от повторов"""
        self.print_header("ПРОВЕРКА TELEGRAM БОТА")

        bot_file = self.root / "src" / "interfaces" / "telegram" / "bot.py"
        if not bot_file.exists():
            self.errors.append("❌ telegram/bot.py не найден")
            return

        with open(bot_file, "r") as f:
            content = f.read()

        checks = [
            ("_processed_messages", "защита от повторов"),
            ("asyncio.wait_for", "таймаут на typing"),
            ("while self._running", "цикл в _run_bot"),
        ]

        for code, desc in checks:
            if code not in content:
                self.warnings.append(f"⚠️ В telegram/bot.py нет {desc}")
                print(f"   ⚠️ telegram/bot.py - добавить {desc}")

    def check_conversation_tools(self):
        """Проверка conversation_tools.py на правильные параметры"""
        self.print_header("ПРОВЕРКА ДИАЛОГОВОГО МОДУЛЯ")

        conv_file = self.root / "src" / "tools" / "conversation_tools.py"
        if not conv_file.exists():
            self.errors.append("❌ conversation_tools.py не найден")
            return

        with open(conv_file, "r") as f:
            content = f.read()

        # Проверяем параметры для 7B модели
        if "repetition_penalty" in content:
            # Ищем значение repetition_penalty
            match = re.search(r'repetition_penalty["\s:]+([\d.]+)', content)
            if match:
                val = float(match.group(1))
                if val < 1.2:
                    self.warnings.append(f"⚠️ repetition_penalty={val} (должно быть 1.2-1.3 для 7B)")
                    print(f"   ⚠️ conversation_tools.py - увеличить repetition_penalty")

        if "system_prompt" in content and "Alibaba" in content:
            self.warnings.append("⚠️ В system_prompt осталось упоминание Alibaba")
            print(f"   ⚠️ conversation_tools.py - убрать Alibaba из system_prompt")

    def check_vector_memory(self):
        """Проверка vector_memory.py на правильное устройство"""
        self.print_header("ПРОВЕРКА ВЕКТОРНОЙ ПАМЯТИ")

        vec_file = self.root / "src" / "memory" / "vector_memory.py"
        if not vec_file.exists():
            self.errors.append("❌ vector_memory.py не найден")
            return

        with open(vec_file, "r") as f:
            content = f.read()

        if 'device="cpu"' not in content and "device='cpu'" not in content:
            self.warnings.append("⚠️ SentenceTransformer не принудительно на CPU")
            print(f"   ⚠️ vector_memory.py - добавить device='cpu'")

    def check_vision_engine(self):
        """Проверка vision_engine.py на правильную модель"""
        self.print_header("ПРОВЕРКА ЗРИТЕЛЬНОГО МОДУЛЯ")

        vis_file = self.root / "src" / "engines" / "vision_engine.py"
        if not vis_file.exists():
            self.errors.append("❌ vision_engine.py не найден")
            return

        with open(vis_file, "r") as f:
            content = f.read()

        if "moondream" in content.lower() and "nanollava" not in content.lower():
            self.warnings.append("⚠️ Всё ещё используется Moondream вместо nanoLLaVA")
            print(f"   ⚠️ vision_engine.py - заменить Moondream на nanoLLaVA")

    def check_config(self):
        """Проверка config.yaml на правильные параметры"""
        self.print_header("ПРОВЕРКА КОНФИГУРАЦИИ")

        config_file = self.root / "configs" / "main.yaml"
        if not config_file.exists():
            self.errors.append("❌ main.yaml не найден")
            return

        with open(config_file, "r") as f:
            content = f.read()

        checks = [
            ("7b", "модель"),
            ("cuda", "устройство"),
            ("telegram", "включён"),
            ("8080", "порт"),
        ]

        for code, desc in checks:
            if code not in content.lower():
                self.warnings.append(f"⚠️ В конфиге нет {desc}")
                print(f"   ⚠️ main.yaml - проверить {desc}")

    def check_logger(self):
        """Проверка logger.py на фильтрацию"""
        self.print_header("ПРОВЕРКА ЛОГГЕРА")

        log_file = self.root / "src" / "utils" / "logger.py"
        if not log_file.exists():
            self.errors.append("❌ logger.py не найден")
            return

        with open(log_file, "r") as f:
            content = f.read()

        if "filter" not in content or "telegram" not in content:
            self.warnings.append("⚠️ В логгере нет фильтрации Telegram-логов")
            print(f"   ⚠️ logger.py - добавить фильтрацию")

    def run_audit(self):
        """Запуск полного аудита"""
        print("\n" + "🔥" * 60)
        print("🔥 АУДИТ ПРОЕКТА ЕЛЕНА - ПОИСК НЕСОГЛАСОВАННЫХ ИЗМЕНЕНИЙ")
        print("🔥" * 60)

        self.check_exist_ok()
        self.check_unload_methods()
        self.check_bootstrap_stop_services()
        self.check_telegram_bot()
        self.check_conversation_tools()
        self.check_vector_memory()
        self.check_vision_engine()
        self.check_config()
        self.check_logger()

        # ИТОГИ
        self.print_header("РЕЗУЛЬТАТЫ АУДИТА")

        if self.errors:
            print("\n❌ КРИТИЧЕСКИЕ ОШИБКИ:")
            for err in self.errors:
                print(f"   {err}")

        if self.warnings:
            print("\n⚠️ ПРЕДУПРЕЖДЕНИЯ (нужно исправить):")
            for warn in self.warnings:
                print(f"   {warn}")

        if not self.errors and not self.warnings:
            print("\n✅ ПРОЕКТ ИДЕАЛЕН! ВСЕ ИЗМЕНЕНИЯ СОГЛАСОВАНЫ!")

        print(f"\n📊 Статистика:")
        print(f"   - Ошибок: {len(self.errors)}")
        print(f"   - Предупреждений: {len(self.warnings)}")

        # Сохраняем отчёт
        report_file = self.root / "logs" / f'audit_{datetime.now().strftime("%Y%m%d_%H%M%S")}.log'
        with open(report_file, "w") as f:
            f.write("РЕЗУЛЬТАТЫ АУДИТА ПРОЕКТА\n")
            f.write("=" * 60 + "\n")
            f.write(f"Ошибок: {len(self.errors)}\n")
            f.write(f"Предупреждений: {len(self.warnings)}\n\n")

            if self.errors:
                f.write("КРИТИЧЕСКИЕ ОШИБКИ:\n")
                for err in self.errors:
                    f.write(f"{err}\n")

            if self.warnings:
                f.write("\nПРЕДУПРЕЖДЕНИЯ:\n")
                for warn in self.warnings:
                    f.write(f"{warn}\n")

        print(f"\n📄 Отчёт сохранён в: {report_file}")


if __name__ == "__main__":
    audit = ProjectAudit()
    audit.run_audit()
