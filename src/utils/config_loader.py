import os
import yaml
from dotenv import load_dotenv
from pathlib import Path
from typing import Any, Dict, List, Union

# Загружаем .env один раз при импорте модуля
load_dotenv()

# Тип для рекурсивных данных YAML (словарь, список, строка, число или None)
YamlValue = Union[Dict[str, Any], List[Any], str, int, float, None]


def load_config(config_path: str = "configs/main.yaml") -> Dict[str, Any]:
    """
    Загружает YAML-конфиг и рекурсивно подставляет переменные окружения.
    Поддерживает синтаксис ${VAR_NAME} и ${VAR_NAME:default_value}.
    """
    path = Path(config_path)
    if not path.exists():
        raise FileNotFoundError(f"Конфигурационный файл не найден: {config_path}")

    with open(path, "r", encoding="utf-8") as f:
        # Используем or {}, чтобы config всегда был словарем, а не None
        config: Any = yaml.safe_load(f) or {}

    if not isinstance(config, dict):
        raise ValueError(f"Ошибка в {config_path}: Корневой элемент должен быть словарем.")

    # Выполняем подстановку и возвращаем результат
    result: Dict[str, Any] = _substitute_env(config)
    return result


def _substitute_env(obj: Any) -> Any:
    """Рекурсивно ищет строки вида ${VAR} и заменяет их на значения из окружения."""
    if isinstance(obj, dict):
        return {k: _substitute_env(v) for k, v in obj.items()}

    elif isinstance(obj, list):
        return [_substitute_env(v) for v in obj]

    elif isinstance(obj, str) and obj.startswith("${") and obj.endswith("}"):
        # Извлекаем содержимое между ${ и }
        content = obj[2:-1].strip()

        # Проверяем наличие значения по умолчанию (синтаксис ${VAR:default})
        if ":" in content:
            env_var, default_value = content.split(":", 1)
            return os.getenv(env_var, default_value)

        # Если двоеточия нет, возвращаем значение или саму строку ${VAR}, если переменной нет
        return os.getenv(content, obj)

    return obj
