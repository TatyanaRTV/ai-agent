# Путь: /mnt/ai_data/ai-agent/src/utils/config_loader.py
import os
import yaml
from dotenv import load_dotenv
from pathlib import Path

load_dotenv()

def load_config(config_path: str = "configs/main.yaml") -> dict:
    """Загружает конфиг и подставляет переменные окружения."""
    with open(config_path, "r", encoding="utf-8") as f:
        config = yaml.safe_load(f)
    # Рекурсивная подстановка ${VAR}
    config = _substitute_env(config)
    return config

def _substitute_env(obj):
    if isinstance(obj, dict):
        return {k: _substitute_env(v) for k, v in obj.items()}
    elif isinstance(obj, list):
        return [_substitute_env(v) for v in obj]
    elif isinstance(obj, str) and obj.startswith("${") and obj.endswith("}"):
        env_var = obj[2:-1]
        return os.getenv(env_var, obj)
    else:
        return obj