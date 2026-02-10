#!/bin/bash
# Очистка временных файлов
echo "🧹 Очистка временных файлов..."
find data/temp -type f -mtime +1 -delete
find data/cache -type f -mtime +7 -delete
find logs -name "*.log" -type f -size +10M -delete
echo "✅ Очистка завершена"