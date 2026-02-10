"""
ПОМОЩНИКИ И УТИЛИТЫ
"""

import os
import sys
import json
import yaml
import hashlib
import random
import string
from datetime import datetime, timedelta
from typing import Any, Dict, List, Optional, Union
from pathlib import Path
import inspect
import textwrap

class Helpers:
    """Коллекция полезных утилит"""
    
    @staticmethod
    def get_project_root() -> Path:
        """Получение корневой директории проекта"""
        current_file = Path(inspect.getfile(inspect.currentframe()))
        project_root = current_file.parent.parent.parent
        return project_root
        
    @staticmethod
    def load_config(config_path: str) -> Dict[str, Any]:
        """Загрузка конфигурации YAML/JSON"""
        config_path = Path(config_path)
        
        if not config_path.exists():
            raise FileNotFoundError(f"Config file not found: {config_path}")
            
        if config_path.suffix in ['.yaml', '.yml']:
            with open(config_path, 'r', encoding='utf-8') as f:
                return yaml.safe_load(f)
        elif config_path.suffix == '.json':
            with open(config_path, 'r', encoding='utf-8') as f:
                return json.load(f)
        else:
            raise ValueError(f"Unsupported config format: {config_path.suffix}")
            
    @staticmethod
    def save_config(config: Dict[str, Any], config_path: str):
        """Сохранение конфигурации"""
        config_path = Path(config_path)
        
        if config_path.suffix in ['.yaml', '.yml']:
            with open(config_path, 'w', encoding='utf-8') as f:
                yaml.dump(config, f, default_flow_style=False, allow_unicode=True)
        elif config_path.suffix == '.json':
            with open(config_path, 'w', encoding='utf-8') as f:
                json.dump(config, f, indent=2, ensure_ascii=False)
        else:
            raise ValueError(f"Unsupported config format: {config_path.suffix}")
            
    @staticmethod
    def generate_id(length: int = 16) -> str:
        """Генерация уникального ID"""
        chars = string.ascii_letters + string.digits
        return ''.join(random.choice(chars) for _ in range(length))
        
    @staticmethod
    def format_size(size_bytes: int) -> str:
        """Форматирование размера файла"""
        for unit in ['B', 'KB', 'MB', 'GB', 'TB']:
            if size_bytes < 1024.0:
                return f"{size_bytes:.2f} {unit}"
            size_bytes /= 1024.0
        return f"{size_bytes:.2f} PB"
        
    @staticmethod
    def format_duration(seconds: float) -> str:
        """Форматирование продолжительности"""
        if seconds < 1:
            return f"{seconds*1000:.0f}ms"
        elif seconds < 60:
            return f"{seconds:.1f}s"
        elif seconds < 3600:
            minutes = seconds // 60
            seconds %= 60
            return f"{minutes:.0f}m {seconds:.0f}s"
        else:
            hours = seconds // 3600
            minutes = (seconds % 3600) // 60
            return f"{hours:.0f}h {minutes:.0f}m"
            
    @staticmethod
    def truncate_text(text: str, max_length: int = 100, suffix: str = "...") -> str:
        """Обрезка текста с добавлением суффикса"""
        if len(text) <= max_length:
            return text
        return text[:max_length - len(suffix)] + suffix
    
    @staticmethod
    def clean_filename(filename: str) -> str:
        """Очистка имени файла от недопустимых символов"""
        import re
        # Удаляем недопустимые символы
        cleaned = re.sub(r'[<>:"/\\|?*]', '_', filename)
        # Удаляем начальные и конечные точки/пробелы
        cleaned = cleaned.strip('. ')
        # Ограничиваем длину
        if len(cleaned) > 255:
            name, ext = os.path.splitext(cleaned)
            cleaned = name[:255 - len(ext)] + ext
        return cleaned
    
    @staticmethod
    def get_file_hash(filepath: str, algorithm: str = 'sha256') -> str:
        """Получение хеша файла"""
        hash_func = hashlib.new(algorithm)
        
        with open(filepath, 'rb') as f:
            for chunk in iter(lambda: f.read(4096), b''):
                hash_func.update(chunk)
                
        return hash_func.hexdigest()
    
    @staticmethod
    def human_readable_list(items: List[str], conjunction: str = "и") -> str:
        """Преобразование списка в читаемую строку"""
        if not items:
            return ""
        elif len(items) == 1:
            return items[0]
        elif len(items) == 2:
            return f"{items[0]} {conjunction} {items[1]}"
        else:
            return f"{', '.join(items[:-1])} {conjunction} {items[-1]}"
    
    @staticmethod
    def parse_time_string(time_str: str) -> timedelta:
        """Парсинг строки времени"""
        import re
        
        patterns = {
            'seconds': r'(\d+)\s*сек',
            'minutes': r'(\d+)\s*мин',
            'hours': r'(\d+)\s*час',
            'days': r'(\d+)\s*дн',
            'weeks': r'(\d+)\s*нед'
        }
        
        total_seconds = 0
        
        for unit, pattern in patterns.items():
            match = re.search(pattern, time_str.lower())
            if match:
                value = int(match.group(1))
                if unit == 'seconds':
                    total_seconds += value
                elif unit == 'minutes':
                    total_seconds += value * 60
                elif unit == 'hours':
                    total_seconds += value * 3600
                elif unit == 'days':
                    total_seconds += value * 86400
                elif unit == 'weeks':
                    total_seconds += value * 604800
                    
        return timedelta(seconds=total_seconds)
    
    @staticmethod
    def format_datetime(dt: datetime, format_str: str = "%Y-%m-%d %H:%M:%S") -> str:
        """Форматирование даты и времени"""
        return dt.strftime(format_str)
    
    @staticmethod
    def parse_datetime(dt_str: str) -> Optional[datetime]:
        """Парсинг строки даты и времени"""
        formats = [
            "%Y-%m-%d %H:%M:%S",
            "%Y-%m-%d %H:%M",
            "%Y-%m-%d",
            "%d.%m.%Y %H:%M:%S",
            "%d.%m.%Y %H:%M",
            "%d.%m.%Y",
            "%H:%M:%S",
            "%H:%M"
        ]
        
        for fmt in formats:
            try:
                return datetime.strptime(dt_str, fmt)
            except ValueError:
                continue
                
        return None
    
    @staticmethod
    def progress_bar(iteration: int, total: int, length: int = 50, fill: str = '█') -> str:
        """Создание прогресс-бара"""
        percent = ("{0:.1f}").format(100 * (iteration / float(total)))
        filled_length = int(length * iteration // total)
        bar = fill * filled_length + '-' * (length - filled_length)
        return f"|{bar}| {percent}%"
    
    @staticmethod
    def wrap_text(text: str, width: int = 80) -> List[str]:
        """Перенос текста по ширине"""
        return textwrap.wrap(text, width)
    
    @staticmethod
    def count_words(text: str) -> Dict[str, int]:
        """Подсчет слов в тексте"""
        words = text.lower().split()
        word_count = {}
        
        for word in words:
            # Удаляем знаки препинания
            word = word.strip('.,!?;:"\'()[]{}')
            if word:
                word_count[word] = word_count.get(word, 0) + 1
                
        return dict(sorted(word_count.items(), key=lambda x: x[1], reverse=True))
    
    @staticmethod
    def get_system_info() -> Dict[str, Any]:
        """Получение информации о системе"""
        import platform
        import psutil
        
        return {
            "system": platform.system(),
            "release": platform.release(),
            "version": platform.version(),
            "machine": platform.machine(),
            "processor": platform.processor(),
            "python_version": platform.python_version(),
            "cpu_count": psutil.cpu_count(),
            "cpu_percent": psutil.cpu_percent(),
            "memory_total": psutil.virtual_memory().total,
            "memory_available": psutil.virtual_memory().available,
            "memory_percent": psutil.virtual_memory().percent,
            "disk_usage": psutil.disk_usage('/').percent
        }
    
    @staticmethod
    def retry(func, max_attempts: int = 3, delay: float = 1.0, 
              exceptions: tuple = (Exception,)):
        """Декоратор для повторных попыток"""
        import time
        
        def wrapper(*args, **kwargs):
            last_exception = None
            
            for attempt in range(max_attempts):
                try:
                    return func(*args, **kwargs)
                except exceptions as e:
                    last_exception = e
                    if attempt < max_attempts - 1:
                        time.sleep(delay * (2 ** attempt))  # Exponential backoff
                        
            raise last_exception
            
        return wrapper
    
    @staticmethod
    def timeit(func):
        """Декоратор для измерения времени выполнения"""
        import time
        
        def wrapper(*args, **kwargs):
            start_time = time.time()
            result = func(*args, **kwargs)
            end_time = time.time()
            
            print(f"Function {func.__name__} took {end_time - start_time:.4f} seconds")
            return result
            
        return wrapper