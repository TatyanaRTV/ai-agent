#!#!/bin/bash
# Очистка временных файлов

echo "🧹 Очистка временных файлов..."

# Удаляем файлы старше 1 дня в temp
find ./data/temp -type f -mtime +1 -delete 2>/dev/null && echo "  ✅ data/temp очищен"

# Удаляем файлы старше 7 дней в cache
find ./data/cache -type f -mtime +7 -delete 2>/dev/null && echo "  ✅ data/cache очищен"

# Удаляем логи больше 10MB
find ./logs -name "*.log" -type f -size +10M -delete 2>/dev/null && echo "  ✅ logs очищены (файлы >10MB)"

# Удаляем временные WAV файлы
find . -name "out.wav" -type f -delete 2>/dev/null && echo "  ✅ временные WAV файлы удалены"

echo "✅ Очистка завершена"