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
    if command -v python3.11 &> /dev/null; then
        PYTHON_CMD="python3.11"
        PYTHON_VERSION=$($PYTHON_CMD -c 'import sys; print(f"{sys.version_info.major}.{sys.version_info.minor}")')
        print_success "Python $PYTHON_VERSION установлен"
    elif command -v python3.12 &> /dev/null; then
        PYTHON_CMD="python3.12"
        PYTHON_VERSION=$($PYTHON_CMD -c 'import sys; print(f"{sys.version_info.major}.{sys.version_info.minor}")')
        print_success "Python $PYTHON_VERSION установлен"
    elif command -v python3.13 &> /dev/null; then
        PYTHON_CMD="python3.13"
        PYTHON_VERSION=$($PYTHON_CMD -c 'import sys; print(f"{sys.version_info.major}.{sys.version_info.minor}")')
        print_success "Python $PYTHON_VERSION установлен"
    elif command -v python3 &> /dev/null; then
        PYTHON_CMD="python3"
        PYTHON_VERSION=$($PYTHON_CMD -c 'import sys; print(f"{sys.version_info.major}.{sys.version_info.minor}")')
        
        # Проверка версии
        if python3 -c "import sys; sys.exit(0 if sys.version_info >= (3, 11) else 1)"; then
            print_success "Python $PYTHON_VERSION установлен"
        else
            print_error "Требуется Python 3.11 или выше. У вас: $PYTHON_VERSION"
            echo ""
            echo "Для Ubuntu 22.04:"
            echo "  sudo add-apt-repository ppa:deadsnakes/ppa"
            echo "  sudo apt update"
            echo "  sudo apt install python3.11 python3.11-venv python3.11-dev"
            echo ""
            echo "Для Linux Mint:"
            echo "  sudo apt install python3.11 python3.11-venv python3.11-dev"
            echo ""
            exit 1
        fi
    else
        print_error "Python 3 не установлен"
        exit 1
    fi
    
    # Сохраняем команду Python для дальнейшего использования
    export PYTHON_CMD
}

create_directories() {
    print_step "Создание структуры папок..."
    
    # Основные папки
    mkdir -p data/{temp,cache,logs,vectors,backups}
    mkdir -p models/llms
    mkdir -p configs
    mkdir -p logs
    mkdir -p backups
    
    print_success "Структура папок создана"
}

create_virtualenv() {
    print_step "Создание виртуального окружения..."
    
    # Используем .venv (с точкой) с правильной версией Python
    if [ ! -d ".venv" ]; then
        $PYTHON_CMD -m venv .venv
        print_success "Виртуальное окружение создано: .venv (Python $PYTHON_VERSION)"
    else
        print_warning "Виртуальное окружение уже существует"
    fi
    
    # Активация
    source .venv/bin/activate
    print_success "Виртуальное окружение активировано"
}

install_dependencies() {
    print_step "Установка зависимостей..."
    
    # Обновление pip
    pip install --upgrade pip setuptools wheel
    
    # Установка зависимостей
    if [ -f "requirements.txt" ]; then
        pip install -r requirements.txt
        print_success "Зависимости установлены"
    else
        print_error "Файл requirements.txt не найден!"
        exit 1
    fi
}

setup_configs() {
    print_step "Настройка конфигурации..."
    
    # Копирование примера конфигурации
    if [ ! -f "configs/main.yaml" ]; then
        if [ -f "config.example.yaml" ]; then
            cp config.example.yaml configs/main.yaml
            print_success "Конфигурация создана: configs/main.yaml"
            print_warning "Отредактируйте configs/main.yaml перед запуском!"
        else
            print_error "Файл config.example.yaml не найден!"
        fi
    else
        print_warning "Конфигурация уже существует"
    fi
    
    # Создание файла секретов
    if [ ! -f "configs/secrets.yaml" ]; then
        cat > configs/secrets.yaml << 'EOF'
# Секретные данные (НЕ ДОБАВЛЯТЬ В GIT!)
telegram:
  bot_token: ""
  admin_ids: []
EOF
        chmod 600 configs/secrets.yaml
        print_success "Файл секретов создан: configs/secrets.yaml"
    fi
}

setup_voice() {
    print_step "Настройка голосового модуля..."
    
    # Проверка RHVoice
    if command -v RHVoice-test &> /dev/null; then
        print_success "RHVoice установлен (голос Елены)"
    else
        print_warning "RHVoice не найден"
        echo "   Для голоса Елены установите:"
        echo "   sudo apt install rhvoice rhvoice-russian"
    fi
    
    # Проверка голосового модуля
    if [ -f "simple_voice.py" ]; then
        print_success "Голосовой модуль найден: simple_voice.py"
    else
        print_warning "Голосовой модуль не найден"
    fi
}

post_install() {
    print_step "Завершение установки..."
    
    # Права на скрипты
    chmod +x scripts/*.sh 2>/dev/null || true
    chmod +x start_elena.py 2>/dev/null || true
    print_success "Права на скрипты установлены"
    
    print_success "Установка завершена!"
}

# Основная функция
main() {
    print_header
    
    check_requirements
    create_directories
    create_virtualenv
    install_dependencies
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
    echo "Для запуска:"
    echo "  source .venv/bin/activate"
    echo "  python start_elena.py"
    echo
}

# Запуск
main "$@"