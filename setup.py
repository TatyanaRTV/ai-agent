#!/usr/bin/env python3
# Путь: /mnt/ai_data/ai-agent/setup.py
"""Установочный скрипт для проекта Елена - финальная версия"""

from setuptools import setup, find_packages
import os
import sys
from pathlib import Path

# Проверка версии Python
if sys.version_info < (3, 11):
    print("❌ Ошибка: требуется Python 3.11 или выше")
    sys.exit(1)

# Читаем длинное описание из README
try:
    with open("README.md", "r", encoding="utf-8") as f:
        long_description = f.read()
except FileNotFoundError:
    long_description = "Елена - персональный ИИ-агент с голосом, зрением и Telegram-интеграцией"


# Читаем зависимости из requirements.txt
def read_requirements():
    """Читает зависимости из requirements.txt"""
    requirements = []
    try:
        with open("requirements/base.txt", "r", encoding="utf-8") as f:
            for line in f:
                line = line.strip()
                if line and not line.startswith("#"):
                    requirements.append(line)
    except FileNotFoundError:
        # Если нет base.txt, пробуем requirements.txt
        try:
            with open("requirements.txt", "r", encoding="utf-8") as f:
                for line in f:
                    line = line.strip()
                    if line and not line.startswith("#"):
                        requirements.append(line)
        except FileNotFoundError:
            print("⚠️ Предупреждение: не найден файл с зависимостями")

    return requirements


# Определяем дополнительные зависимости для разных платформ
extras = {
    "dev": [
        "pytest>=8.2.2",
        "pytest-asyncio>=0.23.7",
        "black>=24.4.2",
        "flake8>=7.0.0",
        "mypy>=1.10.0",
        "pre-commit>=3.7.1",
    ],
    "gpu": [
        "torch>=2.5.1",
        "torchvision>=0.20.1",
        "torchaudio>=2.5.1",
        "xformers>=0.0.28",
    ],
    "cpu": [
        "torch>=2.5.1",
        "torchvision>=0.20.1",
        "torchaudio>=2.5.1",
    ],
    "telegram": [
        "python-telegram-bot>=20.8",
        "httpx>=0.26.0",
    ],
    "vision": [
        "pillow>=10.3.0",
        "opencv-python>=4.9.0.80",
        "mss>=9.0.1",
    ],
}

# Объединяем все extras для полной установки
extras["all"] = []
for group in extras.values():
    extras["all"].extend(group)

setup(
    name="elena-ai-agent",
    version="1.0.0",
    description="Елена - персональный ИИ-агент с голосом, зрением и Telegram-интеграцией",
    long_description=long_description,
    long_description_content_type="text/markdown",
    author="Татьяна",
    author_email="tatyana@example.com",
    url="https://github.com/tatyana/elena-ai-agent",
    project_urls={
        "Bug Tracker": "https://github.com/tatyana/elena-ai-agent/issues",
        "Documentation": "https://github.com/tatyana/elena-ai-agent/wiki",
        "Source Code": "https://github.com/tatyana/elena-ai-agent",
    },
    packages=find_packages(where="src"),
    package_dir={"": "src"},
    py_modules=["src.core.bootstrap"],
    python_requires=">=3.11",
    install_requires=read_requirements(),
    extras_require=extras,
    include_package_data=True,
    package_data={
        "": ["*.yaml", "*.yml", "*.json", "*.md"],
        "configs": ["*.yaml", "*.example"],
        "scripts": ["*.sh"],
    },
    exclude_package_data={
        "": ["__pycache__", "*.pyc", "*.pyo"],
    },
    entry_points={
        "console_scripts": [
            "elena=src.core.bootstrap:main",
            "elena-web=src.interfaces.browser.app:main",
            "elena-telegram=src.interfaces.telegram.bot:main",
        ],
    },
    classifiers=[
        "Development Status :: 4 - Beta",
        "Intended Audience :: End Users/Desktop",
        "Intended Audience :: Developers",
        "Topic :: Scientific/Engineering :: Artificial Intelligence",
        "Topic :: Multimedia :: Graphics :: Capture :: Screen Capture",
        "Topic :: Communications :: Chat",
        "License :: OSI Approved :: MIT License",
        "Programming Language :: Python :: 3.11",
        "Programming Language :: Python :: 3.12",
        "Operating System :: POSIX :: Linux",
        "Environment :: Console",
        "Environment :: Web Environment",
        "Natural Language :: Russian",
    ],
    keywords=[
        "ai",
        "assistant",
        "telegram-bot",
        "voice-assistant",
        "screen-capture",
        "ollama",
        "qwen",
        "nanollava",
        "russian",
        "linux",
        "gpu",
        "cuda",
    ],
    license="MIT",
    platforms=["Linux"],
    zip_safe=False,
    tests_require=extras["dev"],
    test_suite="tests",
    scripts=[
        "scripts/setup.sh",
        "scripts/install_rhvoice.sh",
        "scripts/check_ready.sh",
        "scripts/first_run.sh",
    ],
    data_files=[
        ("configs", ["configs/main.yaml", "configs/secrets.yaml.example", "configs/env.example"]),
        ("requirements", ["requirements/base.txt", "requirements/dev.txt", "requirements/optional.txt"]),
    ],
    # Метаданные для PyPI (опционально)
    # Для публикации: python setup.py sdist bdist_wheel
    command_options={
        "build_sphinx": {
            "project": ("setup.py", "Елена"),
            "version": ("setup.py", "1.0.0"),
            "release": ("setup.py", "1.0.0"),
        },
    },
)
