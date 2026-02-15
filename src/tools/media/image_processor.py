#!/usr/bin/env python3
# Путь: /mnt/ai_data/ai-agent/src/tools/media/image_processor.py
"""Обработка изображений"""

from PIL import Image
import cv2
import numpy as np
from pathlib import Path
from loguru import logger


class ImageProcessor:
    """Обработчик изображений"""
    
    def __init__(self, config):
        self.config = config
        logger.info("🖼️ ImageProcessor инициализирован")
    
    def get_info(self, file_path):
        """Получение информации об изображении"""
        try:
            img = Image.open(file_path)
            info = {
                'format': img.format,
                'size': img.size,
                'mode': img.mode,
                'width': img.width,
                'height': img.height,
                'path': str(file_path)
            }
            return info
        except Exception as e:
            logger.error(f"❌ Ошибка получения информации: {e}")
            return None
    
    def resize(self, file_path, width=None, height=None):
        """Изменение размера изображения"""
        try:
            img = Image.open(file_path)
            
            if width and height:
                resized = img.resize((width, height), Image.Resampling.LANCZOS)
            elif width:
                ratio = width / img.width
                height = int(img.height * ratio)
                resized = img.resize((width, height), Image.Resampling.LANCZOS)
            elif height:
                ratio = height / img.height
                width = int(img.width * ratio)
                resized = img.resize((width, height), Image.Resampling.LANCZOS)
            else:
                return file_path
            
            output_path = Path(file_path).parent / f"resized_{Path(file_path).name}"
            resized.save(output_path)
            logger.info(f"📏 Изображение изменено: {output_path}")
            return str(output_path)
            
        except Exception as e:
            logger.error(f"❌ Ошибка изменения размера: {e}")
            return None
    
    def convert_format(self, file_path, output_format='JPEG'):
        """Конвертация в другой формат"""
        try:
            img = Image.open(file_path)
            output_path = Path(file_path).with_suffix(f'.{output_format.lower()}')
            img.save(output_path, format=output_format)
            logger.info(f"🔄 Изображение сконвертировано: {output_path}")
            return str(output_path)
        except Exception as e:
            logger.error(f"❌ Ошибка конвертации: {e}")
            return None