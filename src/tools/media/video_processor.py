#!/usr/bin/env python3
# Путь: /mnt/ai_data/ai-agent/src/tools/media/video_processor.py
"""Обработка видео файлов"""

import cv2
from moviepy.editor import VideoFileClip
from pathlib import Path
from loguru import logger


class VideoProcessor:
    """Обработчик видео"""

    def __init__(self, config):
        self.config = config
        logger.info("🎬 VideoProcessor инициализирован")

    def get_info(self, file_path):
        """Получение информации о видео"""
        try:
            cap = cv2.VideoCapture(str(file_path))
            if not cap.isOpened():
                logger.error(f"❌ Не удалось открыть видео: {file_path}")
                return {}

            info = {
                "frames": int(cap.get(cv2.CAP_PROP_FRAME_COUNT)),
                "fps": cap.get(cv2.CAP_PROP_FPS),
                "width": int(cap.get(cv2.CAP_PROP_FRAME_WIDTH)),
                "height": int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT)),
                "duration": float(cap.get(cv2.CAP_PROP_FRAME_COUNT) / cap.get(cv2.CAP_PROP_FPS)),
            }
            cap.release()
            return info

        except Exception as e:
            logger.error(f"❌ Ошибка получения информации о видео: {e}")
            return {}

    def extract_audio(self, file_path, output_path=None):
        """Извлечение аудио из видео"""
        try:
            video = VideoFileClip(str(file_path))
            if output_path is None:
                output_path = Path(file_path).with_suffix(".mp3")

            video.audio.write_audiofile(str(output_path), logger=None)
            video.close()
            logger.info(f"🎵 Аудио извлечено: {output_path}")
            return str(output_path)

        except Exception as e:
            logger.error(f"❌ Ошибка извлечения аудио: {e}")
            return None
