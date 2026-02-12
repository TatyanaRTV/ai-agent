#!/bin/bash

echo "========================================"
echo "   УСТАНОВКА ИИ-АГЕНТА ЕЛЕНА"
echo "========================================"
echo

echo "📦 Проверяю Python..."
python3 --version
if [ $? -ne 0 ]; then
    echo "❌ Python не установлен!"
    echo "Установите Python: sudo apt install python3 python3-pip"
    exit 1
fi

echo
echo "📁 Создаю папки проекта..."
mkdir -p data/{logs,temp,vectors,cache}
mkdir -p models
mkdir -p configs
mkdir -p logs

echo
echo "🔧 Устанавливаю зависимости..."
pip3 install pyttsx3 colorama pyyaml

echo
echo "📝 Создаю файлы настроек..."
cat > configs/simple_config.yaml << EOF
# Настройки Елены
agent:
  name: "Елена"
  version: "1.0"
  language: "ru"
  voice_gender: "female"
EOF

echo
echo "🎯 Даю права на запуск..."
chmod +x start_elena.py

echo
echo "✅ Установка завершена!"
echo
echo "🚀 Для запуска выполните:"
echo "    python3 start_elena.py"
echo