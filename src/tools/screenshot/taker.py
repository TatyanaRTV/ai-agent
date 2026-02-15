#!/usr/bin/env python3
# Путь: /mnt/ai_data/ai-agent/src/tools/screenshot/taker.py
"""Создание скриншотов экрана"""

import mss
import mss.tools
from datetime import datetime
from pathlib import Path
from loguru import logger


class ScreenshotTaker:
    """Класс для создания скриншотов"""
    
    def __init__(self, config):
        self.config = config
        self.sct = mss.mss()
        self.screenshot_dir = Path(config['paths']['data']) / 'screenshots'
        self.screenshot_dir.mkdir(parents=True, exist_ok=True)
        logger.info("📸 ScreenshotTaker инициализирован")
    
    def take(self, monitor=1, filename=None):
        """
        Создание скриншота
        
        Args:
            monitor: номер монитора (1, 2, ...)
            filename: имя файла (если не указано, генерируется автоматически)
            
        Returns:
            путь к сохранённому скриншоту или None при ошибке
        """
        try:
            if filename is None:
                timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                filename = f"screenshot_{timestamp}.png"
            
            output_path = self.screenshot_dir / filename
            
            # Захват экрана
            screenshot = self.sct.grab(self.sct.monitors[monitor])
            mss.tools.to_png(screenshot.rgb, screenshot.size, output=str(output_path))
            
            logger.info(f"📸 Скриншот сохранён: {output_path}")
            return str(output_path)
            
        except Exception as e:
            logger.error(f"❌ Ошибка создания скриншота: {e}")
            return None
    
    def take_all_monitors(self):
        """Создание скриншотов всех мониторов"""
        paths = []
        try:
            for i, monitor in enumerate(self.sct.monitors[1:], 1):
                path = self.take(monitor=i, filename=f"monitor_{i}.png")
                if path:
                    paths.append(path)
            return paths
        except Exception as e:
            logger.error(f"❌ Ошибка создания скриншотов всех мониторов: {e}")
            return []