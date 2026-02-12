#!#!/bin/bash
# Резервное копирование

BACKUP_DIR="/mnt/ai_data/ai-agent/backups/$(date +%Y%m%d_%H%M%S)"
mkdir -p "$BACKUP_DIR"

echo "💾 Создание резервной копии в $BACKUP_DIR..."

# Копируем важные данные
cp -r configs "$BACKUP_DIR/" 2>/dev/null && echo "  ✅ configs"
cp -r data/vectors "$BACKUP_DIR/" 2>/dev/null && echo "  ✅ data/vectors"
cp -r scripts "$BACKUP_DIR/" 2>/dev/null && echo "  ✅ scripts"
cp .env "$BACKUP_DIR/" 2>/dev/null && echo "  ✅ .env"
cp simple_voice.py "$BACKUP_DIR/" 2>/dev/null && echo "  ✅ simple_voice.py"
cp start_elena.py "$BACKUP_DIR/" 2>/dev/null && echo "  ✅ start_elena.py"
cp requirements.txt "$BACKUP_DIR/" 2>/dev/null && echo "  ✅ requirements.txt"

# Список пакетов
if [ -f ".venv/bin/activate" ]; then
    source .venv/bin/activate
    pip freeze > "$BACKUP_DIR/requirements_frozen.txt" 2>/dev/null
    echo "  ✅ requirements_frozen.txt"
fi

echo "✅ Резервная копия создана!"
echo "📁 $BACKUP_DIR"
echo "📊 Размер: $(du -sh "$BACKUP_DIR" | cut -f1)"

# Оставляем 5 последних бэкапов
cd /mnt/ai_data/ai-agent/backups && ls -t | tail -n +6 | xargs rm -rf 2>/dev/null && echo "🧹 Старые бэкапы удалены"