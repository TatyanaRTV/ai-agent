#!/bin/bash

# Проверка прав доступа
if [ "$(id -u)" != "0" ]; then
    echo "Необходимо запустить скрипт с правами суперпользователя!"
    echo "Используйте: sudo bash system_check.sh"
    exit 1
fi

# Генерация уникального имени лог-файла
LOGFILE="system_check_$(date +%Y%m%d_%H%M%S).log"
counter=1

# Создание уникального имени, если файл существует
while [ -f "$LOGFILE" ]; do
    LOGFILE="system_check_$(date +%Y%m%d_%H%M%S)_$counter.log"
    ((counter++))
done

# Установка прав доступа к лог-файлу
chmod 600 "$LOGFILE"

# Функция установки пакетов
install_packages() {
    echo "### УСТАНОВКА ПАКЕТОВ ###" >> $LOGFILE
    for pkg in "$@"; do
        echo "Проверка пакета $pkg..." >> $LOGFILE
        if ! dpkg -s "$pkg" > /dev/null 2>&1; then
            echo "Устанавливаем $pkg..." >> $LOGFILE
            if ! apt-get update && apt-get install -y "$pkg"; then
                echo "Ошибка при установке $pkg" >> $LOGFILE
                exit 1
            fi
        fi
    done
}

# Обновление системы
echo "### ОБНОВЛЕНИЕ СИСТЕМЫ ###" >> $LOGFILE
apt-get update >> $LOGFILE 2>&1
apt-get upgrade -y >> $LOGFILE 2>&1

# Список необходимых пакетов
apt_packages=(
    sysstat        # Мониторинг производительности системы
    lshw           # Информация об оборудовании
    dmidecode      # Информация о BIOS/системной плате
    lm-sensors     # Мониторинг температуры и датчиков
    nethogs        # Мониторинг сетевого трафика
    smartmontools  # Мониторинг состояния жестких дисков
)

# Установка пакетов
install_packages "${apt_packages[@]}"

# Проверка блокировки dpkg
check_dpkg_lock() {
    if [ -f /var/lib/dpkg/lock ]; then
        echo "Обнаружена блокировка dpkg, удаление..." >> $LOGFILE
        rm /var/lib/dpkg/lock
        rm /var/lib/apt/lists/lock
        rm /var/cache/apt/archives/lock
        sleep 2
    fi
}

# Основная часть скрипта
main() {
    # Заголовки и основная информация
    echo "### СИСТЕМНАЯ ПРОВЕРКА ###" >> $LOGFILE
    echo "Дата и время запуска: $(date)" >> $LOGFILE
    
    # Информация о системе
    echo "### SYSTEM INFORMATION ###" >> $LOGFILE
    {
        uname -a
        uptime
        hostname
        whoami
        date
    } >> $LOGFILE

    # Информация о CPU
    echo "### CPU INFORMATION ###" >> $LOGFILE
    lscpu >> $LOGFILE

    # Информация о памяти
    echo "### MEMORY INFORMATION ###" >> $LOGFILE
    {
        free -h
        vmstat
        cat /proc/meminfo
    } >> $LOGFILE

    # Информация о GPU
    echo "### GPU INFORMATION ###" >> $LOGFILE
    {
        lspci | grep -i vga
        if command -v nvidia-smi &> /dev/null; then
            nvidia-smi
        else
            echo "NVIDIA driver not found"
        fi
    } >> $LOGFILE

    # Информация о хранении данных
    echo "### STORAGE INFORMATION ###" >> $LOGFILE
    {
        df -h
        lsblk
        smartctl -a /dev/sda 2>/dev/null || echo "smartctl not found or device not supported"
    } >> $LOGFILE

    # Сетевая информация
    echo "### NETWORK INFORMATION ###" >> $LOGFILE
    {
        ip addr
        netstat -antp
        arp -a
        if command -v nethogs &> /dev/null; then
            nethogs -s 1 1
        else
            echo "nethogs not installed"
        fi
    } >> $LOGFILE

    # Мониторинг ресурсов
    echo "### RESOURCE MONITORING ###" >> $LOGFILE
    {
        top -bn1
        mpstat
        iostat
    } >> $LOGFILE

    # Информация о процессах
    echo "### PROCESS INFORMATION ###" >> $LOGFILE
    {
        echo "### ps -ef output ###"
        ps -ef 2>/dev/null
        
        echo "### pstree output ###"
        pstree 2>/dev/null
        
        echo "### lsof output ###"
        lsof 2>&1 | tee /dev/tty | grep -v "WARNING"
    } >> $LOGFILE

    # Информация об оборудовании
    echo "### HARDWARE DETAILS ###" >> $LOGFILE
    {
        lshw -short
        dmidecode
        sensors
    } >> $LOGFILE

    # Информация о безопасности
    echo "### SECURITY INFORMATION ###" >> $LOGFILE
    {
        echo "### Последние входы в систему (last) ###"
        last 2>/dev/null
        
        echo "### Открытые сетевые соединения (lsof -i) ###"
        lsof -i 2>&1 | grep -v "WARNING"
        
        echo "### Активные подключения (netstat) ###"
        netstat -tan 2>/dev/null
        
        echo "### Статус файервола ###"
        ufw status 2>/dev/null
        
        echo "### Открытые порты ###"
        ss -tuln 2>/dev/null
    } >> $LOGFILE

    # Проверка ошибок и зависимостей
    echo "### CHECKING DEPENDENCIES ###" >> $LOGFILE
    {
        dpkg -l | grep rc
        apt-get check
    } >> $LOGFILE

    # Информация о виртуализации
    echo "### VIRTUALIZATION CHECK ###" >> $LOGFILE
    egrep '(vmx|svm)' /proc/cpuinfo >> $LOGFILE

    # Информация о модулях ядра
    echo "### KERNEL MODULES ###" >> $LOGFILE
    lsmod >> $LOGFILE

    # Информация о правах доступа
    echo "### FILE PERMISSIONS ###" >> $LOGFILE
    {
        ls -la /etc/ | head -n 20
        ls -la /var/log/ | head -n 20
    } >> $LOGFILE

    # Информация о репозиториях
    echo "### REPOSITORY INFORMATION ###" >> $LOGFILE
    {
        cat /etc/apt/sources.list
        ls /etc/apt/sources.list.d/
    } >> $LOGFILE

    # Проверка целостности лог-файла
    echo "### FILE INTEGRITY CHECK ###" >> $LOGFILE
    {
        md5sum $LOGFILE
        sha256sum $LOGFILE
    } >> $LOGFILE

    # Проверка прав на запись
    if [[ -w $LOGFILE ]]; then
        echo "### LOGFILE WRITE PERMISSIONS OK ###" >> $LOGFILE
    else
        echo "### WARNING: LOGFILE WRITE PERMISSIONS DENIED ###" >> $LOGFILE
    fi

    # Финальная проверка ошибок
    echo "### FINAL CHECK ###" >> $LOGFILE
    {
        dpkg --get-selections | grep deinstall
        apt-get check
    } >> $LOGFILE

    # Очистка временных файлов
    echo "### CLEANUP ###" >> $LOGFILE
    find /tmp -type f -mmin +60 -exec rm -f {} \; 2>/dev/null
}

# Запуск основной функции
main

# Установка прав доступа к логу
set_log_permissions() {
    chmod 600 "$LOGFILE"
    echo "Права доступа к логу установлены: 600"
}

set_log_permissions

# Финальное сообщение
echo "Системная проверка завершена. Результаты сохранены в $LOGFILE"

# Проверка статуса выполнения
EXIT_CODE=$?
if [[ $EXIT_CODE -eq 0 ]]; then
    echo "Скрипт выполнен успешно"
    exit 0
else
    echo "Ошибка при выполнении скрипта: код $EXIT_CODE"
    exit $EXIT_CODE
fi
