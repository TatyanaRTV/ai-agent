#!/bin/bash
# Скрипт обновления
echo "🔄 Обновление Елены..."
git pull
pip install -r requirements.txt --upgrade
echo "✅ Обновление завершено"