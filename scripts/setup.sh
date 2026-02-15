#!/bin/bash
set -e

echo "🔧 Установка системных зависимостей..."
sudo apt update
sudo apt install -y python3.11 python3.11-venv python3-pip rhvoice rhvoice-voice-elena ffmpeg aplay

echo "📁 Создание виртуального окружения..."
python3.11 -m venv venv
source venv/bin/activate

echo "📦 Установка Python-пакетов..."
pip install --upgrade pip
pip install -r requirements.txt

echo "🤖 Загрузка моделей (может занять время)..."
python -c "
from transformers import AutoModelForCausalLM, AutoTokenizer
AutoTokenizer.from_pretrained('Qwen/Qwen2.5-14B-Instruct')
AutoModelForCausalLM.from_pretrained('Qwen/Qwen2.5-14B-Instruct', device_map='auto')
"
echo "✅ Готово. Запустите: python -m src.core.bootstrap"