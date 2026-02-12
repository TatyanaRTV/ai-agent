#!/bin/bash

# ============================================
# СКРИПТ ЗАПУСКА ИИ-АГЕНТА ЕЛЕНА
# ============================================

set -e

# Цвета
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
PINK='\033[0;35m'
CYAN='\033[0;36m'
NC='\033[0m'

# Пути
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(dirname "$SCRIPT_DIR")"
VENV_PATH="$PROJECT_ROOT/.venv"
LOG_DIR="$PROJECT_ROOT/logs"
CONFIG_DIR="$PROJECT_ROOT/configs"
DATA_DIR="$PROJECT_ROOT/data"

# Проверка логов
mkdir -p "$LOG_DIR"

# Функции логирования
log_info() {
    echo -e "${BLUE}[INFO]${NC} $(date '+%Y-%m-%d %H:%M:%S') - $1" | tee -a "$LOG_DIR/run.log"
}

log_success() {
    echo -e "${GREEN}[SUCCESS]${NC} $(date '+%Y-%m-%d %H:%M:%S') - $1" | tee -a "$LOG_DIR/run.log"
}

log_warning() {
    echo -e "${YELLOW}[WARNING]${NC} $(date '+%Y-%m-%d %H:%M:%S') - $1" | tee -a "$LOG_DIR/run.log"
}

log_error() {
    echo -e "${RED}[ERROR]${NC} $(date '+%Y-%m-%d %H:%M:%S') - $1" | tee -a "$LOG_DIR/run.log"
}

show_banner() {
    clear
    echo -e "${PINK}"
    cat << "EOF"
╔══════════════════════════════════════════════════════════╗
║                                                          ║
║     🎀  И И - А Г Е Н Т   Е Л Е Н А  🎀                 ║
║                                                          ║
║     Универсальный самообучающийся помощник              ║
║     с женским русским голосом                           ║
║                                                          ║
╚══════════════════════════════════════════════════════════╝
EOF
    echo -e "${NC}"
    echo -e "${CYAN}Версия: 1.0.0${NC}"
    echo -e "${CYAN}Дата: $(date '+%d.%m.%Y %H:%M:%S')${NC}"
    echo -e "${CYAN}Путь: $PROJECT_ROOT${NC}"
    echo
}

check_environment() {
    log_info "Проверка окружения..."
    
    # Проверка виртуального окружения
    if [ ! -d "$VENV_PATH" ]; then
        log_error "Виртуальное окружение не найдено!"
        echo "Выполните установку: ./scripts/install.sh"
        exit 1
    fi
    
    # Проверка активации venv
    if [ -z "$VIRTUAL_ENV" ]; then
        log_warning "Виртуальное окружение не активировано, активирую..."
        source "$VENV_PATH/bin/activate"
    fi
    
    # Проверка Python
    if ! python3 --version &> /dev/null; then
        log_error "Python не найден!"
        exit 1
    fi
    
    # Проверка версии Python (3.11+)
    if ! python3 -c "import sys; sys.exit(0 if sys.version_info >= (3, 11) else 1)"; then
        log_error "Требуется Python 3.11 или выше!"
        exit 1
    fi
    
    # Проверка голосового модуля
    if [ -f "$PROJECT_ROOT/simple_voice.py" ]; then
        log_success "Голосовой модуль найден"
    else
        log_warning "Голосовой модуль не найден"
    fi
    
    log_success "Окружение проверено"
}

check_configs() {
    log_info "Проверка конфигурации..."
    
    # Основная конфигурация
    if [ ! -f "$CONFIG_DIR/main.yaml" ]; then
        log_error "Основной конфиг не найден!"
        echo "Скопируйте config.example.yaml -> configs/main.yaml"
        exit 1
    fi
    
    # Папки данных
    mkdir -p "$DATA_DIR"/{temp,cache,logs,vectors,backups}
    
    log_success "Конфигурация проверена"
}

start_services() {
    log_info "Запуск сервисов..."
    
    # Очистка старых логов
    find "$LOG_DIR" -name "*.log" -type f -size +10M -delete 2>/dev/null || true
    
    # Создание PID файла
    echo $$ > "$PROJECT_ROOT/elena.pid"
    
    # Запуск мониторинга ресурсов
    start_resource_monitor &
    RESOURCE_MONITOR_PID=$!
    
    log_success "Сервисы запущены"
}

start_resource_monitor() {
    while true; do
        CPU=$(top -bn1 | grep "Cpu(s)" | awk '{print $2}' | cut -d'%' -f1)
        MEM=$(free | grep Mem | awk '{printf "%.1f", $3/$2 * 100}')
        DISK=$(df -h / | awk 'NR==2 {print $5}' | tr -d '%')
        
        echo "CPU: ${CPU}% | RAM: ${MEM}% | DISK: ${DISK}%" > "$DATA_DIR/monitor.txt"
        sleep 5
    done 2>/dev/null || true
}

stop_services() {
    log_info "Остановка сервисов..."
    
    # Остановка мониторинга
    if [ ! -z "$RESOURCE_MONITOR_PID" ]; then
        kill $RESOURCE_MONITOR_PID 2>/dev/null || true
    fi
    
    # Удаление PID файла
    rm -f "$PROJECT_ROOT/elena.pid"
    
    log_success "Сервисы остановлены"
}

start_agent() {
    log_info "Запуск ИИ-агента Елена..."
    
    # Экспорт переменных
    export PYTHONPATH="$PROJECT_ROOT/src:$PYTHONPATH"
    export ELENA_HOME="$PROJECT_ROOT"
    export ELENA_CONFIG="$CONFIG_DIR/main.yaml"
    
    # Запуск в зависимости от режима
    cd "$PROJECT_ROOT"
    
    case $MODE in
        "simple")
            log_info "Запуск простой версии..."
            if [ -f "start_elena.py" ]; then
                python3 start_elena.py "${EXTRA_ARGS[@]}"
            else
                log_error "Файл start_elena.py не найден!"
                exit 1
            fi
            ;;
        "voice")
            log_info "Запуск голосового режима..."
            if [ -f "simple_voice.py" ]; then
                python3 -c "from simple_voice import SimpleVoice; SimpleVoice().test_voice()"
            else
                log_error "Голосовой модуль не найден!"
                exit 1
            fi
            ;;
        "telegram")
            log_info "Запуск Telegram бота..."
            if [ -f "src/interfaces/telegram/bot.py" ]; then
                python3 src/interfaces/telegram/bot.py "${EXTRA_ARGS[@]}"
            else
                log_error "Telegram бот не найден!"
                exit 1
            fi
            ;;
        "web")
            log_info "Запуск веб-интерфейса..."
            if [ -f "src/interfaces/browser/server.py" ]; then
                python3 src/interfaces/browser/server.py "${EXTRA_ARGS[@]}"
            else
                log_error "Веб-интерфейс не найден!"
                exit 1
            fi
            ;;
        "full")
            log_info "Полный запуск агента..."
            if [ -f "start_elena.py" ]; then
                python3 start_elena.py "${EXTRA_ARGS[@]}"
            else
                log_error "Файл start_elena.py не найден!"
                exit 1
            fi
            ;;
    esac
}

cleanup() {
    log_info "Очистка перед выходом..."
    stop_services
    
    # Очистка временных файлов
    find "$DATA_DIR/temp" -type f -name "*.tmp" -delete 2>/dev/null || true
    find "$DATA_DIR/cache" -type f -mtime +1 -delete 2>/dev/null || true
    rm -f out.wav 2>/dev/null || true
    
    log_success "Очистка завершена"
}

show_help() {
    echo -e "${CYAN}Использование: ./scripts/run.sh [опции]${NC}"
    echo
    echo "Опции:"
    echo "  --simple          Запустить простую версию"
    echo "  --voice           Только голосовой режим (тест)"
    echo "  --telegram        Запустить Telegram бота"
    echo "  --web             Запустить веб-интерфейс"
    echo "  --debug           Режим отладки"
    echo "  --help            Показать эту справку"
    echo
    echo "Примеры:"
    echo "  ./scripts/run.sh                # Полный запуск"
    echo "  ./scripts/run.sh --voice        # Тест голоса"
    echo "  ./scripts/run.sh --debug        # С отладкой"
    echo
}

parse_arguments() {
    MODE="full"
    EXTRA_ARGS=()
    
    while [[ $# -gt 0 ]]; do
        case $1 in
            --simple)
                MODE="simple"
                shift
                ;;
            --voice)
                MODE="voice"
                shift
                ;;
            --telegram)
                MODE="telegram"
                shift
                ;;
            --web)
                MODE="web"
                shift
                ;;
            --debug)
                EXTRA_ARGS+=("--debug")
                shift
                ;;
            --help)
                show_help
                exit 0
                ;;
            *)
                EXTRA_ARGS+=("$1")
                shift
                ;;
        esac
    done
}

# Основная функция
main() {
    # Обработка сигналов
    trap cleanup EXIT INT TERM
    
    # Парсинг аргументов
    parse_arguments "$@"
    
    # Показ баннера
    show_banner
    
    # Проверки
    check_environment
    check_configs
    
    # Запуск сервисов
    start_services
    
    log_success "Режим работы: $MODE"
    
    # Запуск агента
    start_agent
    
    log_success "Работа завершена"
}

# Запуск основной функции
main "$@"