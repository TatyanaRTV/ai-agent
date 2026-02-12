#!/bin/bash

echo "🎀 Установка ИИ-агента Елена..."
echo "========================================"

# Проверка Python 3.11+
if command -v python3.11 &> /dev/null; then
    PYTHON_CMD="python3.11"
    echo "✅ Python 3.11 найден"
elif command -v python3.12 &> /dev/null; then
    PYTHON_CMD="python3.12"
    echo "✅ Python 3.12 найден"
elif command -v python3 &> /dev/null; then
    PYTHON_CMD="python3"
    PY_VERSION=$($PYTHON_CMD -c 'import sys; print(f"{sys.version_info.major}.{sys.version_info.minor}")')
    if $PYTHON_CMD -c "import sys; sys.exit(0 if sys.version_info >= (3, 11) else 1)"; then
        echo "✅ Python $PY_VERSION найден"
    else
        echo "❌ Требуется Python 3.11 или выше. У вас: $PY_VERSION"
        echo ""
        echo "Установка Python 3.11:"
        echo "  sudo apt update"
        echo "  sudo apt install python3.11 python3.11-venv python3.11-dev"
        echo ""
        exit 1
    fi
else
    echo "❌ Python 3 не найден"
    exit 1
fi

# Создание виртуального окружения
echo ""
echo "🔧 Создание виртуального окружения..."
if [ ! -d ".venv" ]; then
    $PYTHON_CMD -m venv .venv
    echo "✅ Виртуальное окружение создано: .venv"
else
    echo "✅ Виртуальное окружение уже существует: .venv"
fi

# Активация окружения
echo ""
echo "🔧 Активация виртуального окружения..."
source .venv/bin/activate
echo "✅ Виртуальное окружение активировано"

# Обновление pip
echo ""
echo "📦 Обновление pip..."
pip install --upgrade pip
echo "✅ pip обновлён"

# Установка зависимостей
echo ""
echo "📦 Установка зависимостей..."
if [ -f "requirements.txt" ]; then
    pip install -r requirements.txt
    echo "✅ Зависимости установлены"
else
    echo "❌ Файл requirements.txt не найден!"
    exit 1
fi

# Создание директорий
echo ""
echo "📁 Создание структуры директорий..."
mkdir -p data/{temp,cache,logs,vectors,backups}
mkdir -p models/llms
mkdir -p configs
mkdir -p logs
mkdir -p backups
mkdir -p scripts
echo "✅ Структура директорий создана"

# Копирование конфигурации
echo ""
echo "⚙️ Настройка конфигурации..."
if [ ! -f configs/main.yaml ]; then
    if [ -f config.example.yaml ]; then
        cp config.example.yaml configs/main.yaml
        echo "✅ Конфигурация создана: configs/main.yaml"
        echo "⚠️  ОБЯЗАТЕЛЬНО отредактируйте configs/main.yaml!"
        echo "   - Проверьте пути: /mnt/ai_data/ai-agent"
        echo "   - Проверьте голос: engine: rhvoice, voice_name: elena"
    else
        echo "❌ Файл config.example.yaml не найден!"
    fi
else
    echo "✅ Конфигурация уже существует: configs/main.yaml"
fi

# Настройка голоса
echo ""
echo "🔊 Настройка голосового модуля..."
if command -v RHVoice-test &> /dev/null; then
    echo "✅ RHVoice установлен (голос Елены)"
else
    echo "⚠️ RHVoice не найден"
    echo "   Для голоса Елены выполните:"
    echo "   sudo apt install rhvoice rhvoice-russian"
fi

if [ -f "simple_voice.py" ]; then
    echo "✅ Голосовой модуль найден: simple_voice.py"
else
    echo "⚠️ Голосовой модуль не найден"
    echo "   Создайте файл simple_voice.py или скопируйте из examples/"
fi

# Установка прав
echo ""
echo "🔧 Установка прав на скрипты..."
chmod +x scripts/*.sh 2>/dev/null || true
chmod +x start_elena.py 2>/dev/null || true
echo "✅ Права установлены"

# Проверка PID файла (на случай предыдущего запуска)
rm -f elena.pid 2>/dev/null || true

echo ""
echo "========================================"
echo "✅ УСТАНОВКА ЗАВЕРШЕНА!"
echo "========================================"
echo ""
echo "🎀 Елена готова к работе!"
echo ""
echo "Для запуска:"
echo "  source .venv/bin/activate"
echo "  python start_elena.py"
echo ""
echo "Или используйте скрипт запуска:"
echo "  ./scripts/run.sh"
echo ""
echo "Для теста голоса:"
echo "  ./scripts/run.sh --voice"
echo ""