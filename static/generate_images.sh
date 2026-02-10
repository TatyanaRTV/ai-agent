#!/bin/bash
# generate_images.sh - генерация базовых изображений для Елены

echo "🖼️  Создание графических ресурсов для ИИ-агента Елена"

# Создаем структуру папок
mkdir -p /mnt/ai_data/ai-agent/static/images/{icons,emojis,screenshots,diagrams,voice_visualization,badges,backgrounds,icons/theme/{light,dark}}

# 1. Создаем заглушки для основных изображений (в реальном проекте тут будут реальные изображения)
echo "Создание заглушек изображений..."

# Создаем простые SVG/PNG заглушки
create_placeholder() {
    local file=$1
    local text=$2
    convert -size 256x256 xc:#6a11cb -fill white -pointsize 30 -gravity center -draw "text 0,0 '$text'" "$file"
}

# Основные изображения
create_placeholder "/mnt/ai_data/ai-agent/static/images/logo.png" "ЕЛЕНА"
create_placeholder "/mnt/ai_data/ai-agent/static/images/avatar.png" "👩‍💻"
create_placeholder "/mnt/ai_data/ai-agent/static/images/avatar_small.png" "Е"
create_placeholder "/mnt/ai_data/ai-agent/static/images/background.jpg" "ФОН"

# Создаем простую анимацию загрузки (используем ImageMagick)
echo "Создание анимации загрузки..."
convert -delay 50 -loop 0 \
  \( -size 100x100 xc:none -fill '#ff6b9d' -draw 'circle 50,50 50,10' \) \
  \( -size 100x100 xc:none -fill '#6a11cb' -draw 'circle 50,50 50,30' \) \
  \( -size 100x100 xc:none -fill '#2575fc' -draw 'circle 50,50 50,50' \) \
  /mnt/ai_data/ai-agent/static/images/loading.gif

echo "✅ Графические ресурсы созданы!"