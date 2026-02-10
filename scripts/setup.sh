#!/bin/bash

echo "🎀 Установка ИИ-агента Елена..."

# Проверка Python
if ! command -v python3 &> /dev/null; then
    echo "❌ Python3 не установлен"
    exit 1
fi

# Создание виртуального окружения
echo "🔧 Создание виртуального окружения..."
python3 -m venv .venv

# Активация окружения
source .venv/bin/activate

# Установка зависимостей
echo "📦 Установка зависимостей..."
pip install --upgrade pip
pip install -r requirements.txt

# Создание директорий
echo "📁 Создание структуры директорий..."
mkdir -p data/{raw,cache,logs,temp,processed,vectors,indexes}
mkdir -p models/{llms,embeddings}
mkdir -p logs

# Копирование конфигурации
if [ ! -f configs/main.yaml ]; then
    echo "⚙️ Копирование конфигурации..."
    cp config.example.yaml configs/main.yaml
    echo "⚠️ Отредактируйте configs/main.yaml перед запуском"
fi

# Установка прав
chmod +x scripts/*.sh

echo "✅ Установка завершена!"
echo ""
echo "Для запуска:"
echo "1. Отредактируйте configs/main.yaml"
echo "2. Запустите: ./scripts/run.sh"