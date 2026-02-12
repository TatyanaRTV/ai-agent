#!/bin/bash

# Скрипт остановки Елены

# Цвета
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

echo -e "${BLUE}🛑 Остановка ИИ-агента Елена...${NC}"
echo "========================================"

# Поиск PID файла
if [ -f "elena.pid" ]; then
    PID=$(cat elena.pid)
    
    if ps -p $PID > /dev/null 2>&1; then
        echo -e "${YELLOW}🔍 Найден процесс с PID: $PID${NC}"
        
        # Корректная остановка
        echo -e "${BLUE}⏳ Отправка сигнала завершения...${NC}"
        kill -TERM $PID 2>/dev/null
        sleep 2
        
        # Проверка, остановился ли процесс
        if ps -p $PID > /dev/null 2>&1; then
            echo -e "${YELLOW}⚠️ Процесс не остановился, принудительная остановка...${NC}"
            kill -KILL $PID 2>/dev/null
            sleep 1
        fi
        
        echo -e "${GREEN}✅ Процесс остановлен${NC}"
    else
        echo -e "${YELLOW}⚠️ Процесс с PID $PID не найден${NC}"
    fi
    
    # Удаление PID файла
    rm -f elena.pid
    echo -e "${GREEN}✅ PID файл удален${NC}"
else
    echo -e "${YELLOW}🔍 PID файл не найден, поиск процессов...${NC}"
    
    # Поиск по имени процессов Елены
    PIDS=$(pgrep -f "python.*start_elena.py|python.*simple_voice.py|python.*elena" 2>/dev/null || true)
    
    if [ ! -z "$PIDS" ]; then
        echo -e "${YELLOW}🔍 Найдены процессы: $PIDS${NC}"
        echo -e "${BLUE}⏳ Остановка процессов...${NC}"
        kill $PIDS 2>/dev/null
        sleep 2
        echo -e "${GREEN}✅ Все процессы остановлены${NC}"
    else
        echo -e "${GREEN}✅ Нет запущенных процессов${NC}"
    fi
fi

# Остановка Telegram бота (если запущен)
TELEGRAM_PID=$(pgrep -f "python.*telegram.*bot.py" 2>/dev/null || true)
if [ ! -z "$TELEGRAM_PID" ]; then
    echo -e "${YELLOW}🔍 Найден Telegram бот (PID: $TELEGRAM_PID)${NC}"
    kill $TELEGRAM_PID 2>/dev/null
    echo -e "${GREEN}✅ Telegram бот остановлен${NC}"
fi

# Остановка веб-интерфейса (если запущен)
WEB_PID=$(pgrep -f "python.*server.py" 2>/dev/null || true)
if [ ! -z "$WEB_PID" ]; then
    echo -e "${YELLOW}🔍 Найден веб-интерфейс (PID: $WEB_PID)${NC}"
    kill $WEB_PID 2>/dev/null
    echo -e "${GREEN}✅ Веб-интерфейс остановлен${NC}"
fi

# Очистка временных файлов
echo ""
echo -e "${BLUE}🧹 Очистка временных файлов...${NC}"
rm -rf data/temp/* 2>/dev/null
rm -f out.wav 2>/dev/null
rm -f *.pid 2>/dev/null
rm -f /tmp/elena_* 2>/dev/null
echo -e "${GREEN}✅ Временные файлы удалены${NC}"

echo ""
echo "========================================"
echo -e "${GREEN}✅ Елена остановлена. До встречи! 🎀${NC}"
echo "========================================"