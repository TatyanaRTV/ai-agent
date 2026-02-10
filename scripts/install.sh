#!/bin/bash

# ============================================
# СКРИПТ УСТАНОВКИ ИИ-АГЕНТА ЕЛЕНА
# ============================================

set -e  # Выход при ошибке

# Цвета для вывода
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

print_header() {
    echo -e "${BLUE}"
    echo "╔══════════════════════════════════════════════════════════╗"
    echo "║                 УСТАНОВКА ИИ-АГЕНТА ЕЛЕНА               ║"
    echo "╚══════════════════════════════════════════════════════════╝"
    echo -e "${NC}"
    echo
}

print_step() {
    echo -e "${GREEN}▶${NC} $1"
}

print_success() {
    echo -e "${GREEN}✓${NC} $1"
}

print_warning() {
    echo -e "${YELLOW}⚠${NC} $1"
}

print_error() {
    echo -e "${RED}✗${NC} $1"
}

check_requirements() {
    print_step "Проверка требований системы..."
    
    # Проверка Python
    if command -v python3 &> /dev/null; then
        PYTHON_VERSION=$(python3 -c 'import sys; print(f"{sys.version_info.major}.{sys.version_info.minor}")')
        print_success "Python $PYTHON_VERSION установлен"
    else
        print_error "Python 3 не установлен"
        echo "Установите Python 3.10+:"
        echo "  sudo apt update && sudo apt install python3 python3-pip"
        exit 1
    fi
    
    # Проверка версии Python
    if python3 -c "import sys; sys.exit(0 if sys.version_info >= (3, 10) else 1)"; then
        print_success "Версия Python >= 3.10"
    else
        print_error "Требуется Python 3.10 или выше"
        exit 1
    fi
    
    # Проверка pip
    if command -v pip3 &> /dev/null; then
        print_success "pip3 установлен"
    else
        print_warning "pip3 не найден, устанавливаю..."
        sudo apt install -y python3-pip
    fi
    
    # Проверка свободного места
    FREE_SPACE=$(df -h . | awk 'NR==2 {print $4}')
    print_success "Свободно места: $FREE_SPACE"
    
    # Проверка оперативной памяти
    TOTAL_MEM=$(free -h | awk '/^Mem:/ {print $2}')
    print_success "Оперативная память: $TOTAL_MEM"
}

create_directories() {
    print_step "Создание структуры папок..."
    
    # Основные папки
    mkdir -p data/{raw,processed,cache,temp,vectors,indexes,logs,backups}
    mkdir -p models/{llms,embeddings,voice,vision}
    mkdir -p configs
    mkdir -p logs
    mkdir -p docs
    mkdir -p tests
    mkdir -p src/{core,interfaces,tools,memory,utils}
    
    # Подпапки
    mkdir -p src/interfaces/{telegram,browser,voice,obsidian}
    mkdir -p src/tools/{document,media,vector,screenshot}
    mkdir -p src/utils/{logging,security,helpers}
    
    print_success "Структура папок создана"
}

create_virtualenv() {
    print_step "Создание виртуального окружения..."
    
    # Проверка наличия venv
    if python3 -m venv --help &> /dev/null; then
        python3 -m venv venv
        print_success "Виртуальное окружение создано"
    else
        print_warning "Модуль venv не найден, устанавливаю..."
        sudo apt install -y python3-venv
        python3 -m venv venv
    fi
    
    # Активация venv
    source venv/bin/activate
    print_success "Виртуальное окружение активировано"
}

install_dependencies() {
    print_step "Установка зависимостей..."
    
    # Обновление pip
    pip install --upgrade pip setuptools wheel
    
    # Установка базовых зависимостей
    if [ -f "requirements_simple.txt" ]; then
        print_step "Установка простых зависимостей..."
        pip install -r requirements_simple.txt
    fi
    
    # Установка полных зависимостей (опционально)
    if [ "$1" = "--full" ] && [ -f "requirements.txt" ]; then
        print_step "Установка полных зависимостей..."
        pip install -r requirements.txt
    fi
    
    print_success "Зависимости установлены"
}

setup_configs() {
    print_step "Настройка конфигурации..."
    
    # Копирование примеров конфигурации
    if [ ! -f "configs/main.yaml" ]; then
        if [ -f "config.example.yaml" ]; then
            cp config.example.yaml configs/main.yaml
            print_success "Конфигурация создана: configs/main.yaml"
        else
            # Создание базовой конфигурации
            cat > configs/main.yaml << 'EOF'
# Основная конфигурация Елены
agent:
  name: "Елена"
  version: "1.0.0"
  language: "ru"
  voice_gender: "female"
  learning_rate: 0.01

paths:
  home: "/mnt/ai_data/II_AGENT"
  obsidian: "/mnt/ai_data/My_Obsidian"
  data: "./data"
  logs: "./logs"
  models: "./models"

features:
  voice: true
  vision: true
  memory: true
  telegram: false
  browser: false
  obsidian: true

voice:
  engine: "pyttsx3"
  voice_name: "Елена"
  rate: 150
  volume: 0.9

memory:
  vector_db: "chromadb"
  persist_directory: "./data/vectors"
  collection_name: "elena_memory"

logging:
  level: "INFO"
  file: "./logs/app.log"
  max_size: "10MB"
  backup_count: 5
EOF
            print_success "Базовая конфигурация создана"
        fi
    fi
    
    # Создание файла секретов
    if [ ! -f "configs/secrets.yaml" ]; then
        cat > configs/secrets.yaml << 'EOF'
# Секретные данные (не добавляйте в Git!)
telegram:
  bot_token: "YOUR_TELEGRAM_BOT_TOKEN"
  admin_ids: []
  
api_keys:
  openai: ""
  google: ""
  yandex: ""
  
database:
  password: ""
  
encryption:
  secret_key: ""
EOF
        chmod 600 configs/secrets.yaml
        print_success "Файл секретов создан: configs/secrets.yaml"
    fi
    
    # Создание .env файла
    if [ ! -f ".env" ]; then
        cat > .env << 'EOF'
# Переменные окружения
PYTHONPATH=./src
ELENA_HOME=$(pwd)
ELENA_DATA=./data
ELENA_LOGS=./logs

# Настройки Python
PYTHONUNBUFFERED=1
PYTHONDONTWRITEBYTECODE=1

# Настройки памяти
ELENA_MEMORY_LIMIT=2GB
ELENA_CACHE_SIZE=1GB
EOF
        print_success "Файл .env создан"
    fi
}

install_system_deps() {
    print_step "Установка системных зависимостей..."
    
    # Для Linux Mint/Ubuntu/Debian
    if command -v apt &> /dev/null; then
        print_step "Обновление пакетов..."
        sudo apt update
        
        print_step "Установка системных пакетов..."
        sudo apt install -y \
            python3-dev \
            build-essential \
            ffmpeg \
            libsm6 \
            libxext6 \
            libxrender-dev \
            libgl1-mesa-glx \
            portaudio19-dev \
            espeak-ng \
            tesseract-ocr \
            tesseract-ocr-rus \
            sox \
            libsox-fmt-all \
            git \
            curl \
            wget
        
        print_success "Системные зависимости установлены"
    else
        print_warning "Не удалось определить пакетный менеджер, пропускаю..."
    fi
}

setup_voice() {
    print_step "Настройка голосового интерфейса..."
    
    # Проверка RHVoice
    if ! command -v RHVoice-client &> /dev/null; then
        print_warning "RHVoice не установлен"
        echo "Для русского голоса установите RHVoice:"
        echo "  git clone https://github.com/Olga-Yakovleva/RHVoice.git"
        echo "  cd RHVoice && sudo ./install.sh"
    else
        print_success "RHVoice установлен"
    fi
    
    # Проверка espeak-ng
    if command -v espeak-ng &> /dev/null; then
        print_success "espeak-ng установлен"
    else
        print_warning "espeak-ng не установлен"
    fi
}

post_install() {
    print_step "Завершение установки..."
    
    # Создание файла с версией
    echo "1.0.0" > VERSION
    
    # Настройка прав
    chmod +x scripts/*.sh
    chmod +x src/main.py 2>/dev/null || true
    
    # Создание символических ссылок
    ln -sf "$(pwd)/scripts/run.sh" /usr/local/bin/elena 2>/dev/null || true
    
    # Инициализация Git (если нужно)
    if [ ! -d ".git" ]; then
        git init
        print_success "Репозиторий Git инициализирован"
    fi
    
    print_success "Установка завершена!"
}

show_usage() {
    print_step "Использование установки:"
    echo "  ./scripts/install.sh [опции]"
    echo
    echo "Опции:"
    echo "  --full      Установить полную версию с ML-зависимостями"
    echo "  --minimal   Установить минимальную версию"
    echo "  --help      Показать эту справку"
    echo
}

# Основная функция
main() {
    print_header
    
    # Парсинг аргументов
    MODE="simple"
    for arg in "$@"; do
        case $arg in
            --full)
                MODE="full"
                ;;
            --minimal)
                MODE="minimal"
                ;;
            --help)
                show_usage
                exit 0
                ;;
        esac
    done
    
    echo -e "${YELLOW}Режим установки: ${MODE}${NC}"
    echo
    
    # Выполнение шагов установки
    check_requirements
    create_directories
    create_virtualenv
    install_dependencies "$@"
    install_system_deps
    setup_configs
    setup_voice
    post_install
    
    echo
    echo -e "${GREEN}══════════════════════════════════════════════════════════${NC}"
    echo -e "${GREEN}           УСТАНОВКА УСПЕШНО ЗАВЕРШЕНА!                  ${NC}"
    echo -e "${GREEN}══════════════════════════════════════════════════════════${NC}"
    echo
    echo -e "${BLUE}🎀 Елена готова к работе!${NC}"
    echo
    echo "Для запуска выполните:"
    echo "  source venv/bin/activate"
    echo "  ./scripts/run.sh"
    echo
    echo "Или используйте команду:"
    echo "  elena"
    echo
    echo -e "${YELLOW}Не забудьте настроить configs/main.yaml под свои нужды!${NC}"
    echo
}

# Запуск скрипта
main "$@"