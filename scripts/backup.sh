#!/bin/bash
# Резервное копирование
BACKUP_DIR="backups/$(date +%Y%m%d_%H%M%S)"
mkdir -p $BACKUP_DIR
cp -r data $BACKUP_DIR/
cp -r configs $BACKUP_DIR/
echo "💾 Резервная копия создана: $BACKUP_DIR"