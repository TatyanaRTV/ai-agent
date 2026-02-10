"""
ОБРАБОТКА ВИДЕО ФАЙЛОВ
"""

import cv2
import numpy as np
from pathlib import Path
import tempfile
import json
from datetime import datetime
from typing import Dict, List, Any, Optional
import subprocess
import os

class VideoProcessor:
    """Процессор видео файлов"""
    
    def __init__(self):
        self.supported_formats = ['.mp4', '.avi', '.mov', '.mkv', '.flv', '.wmv']
        
    def process_video(self, video_path: str) -> Dict[str, Any]:
        """Обработка видео файла"""
        if not Path(video_path).exists():
            raise FileNotFoundError(f"Video file not found: {video_path}")
            
        video_path = Path(video_path)
        
        if video_path.suffix.lower() not in self.supported_formats:
            raise ValueError(f"Unsupported video format: {video_path.suffix}")
            
        print(f"🎬 Обработка видео: {video_path.name}")
        
        try:
            # Открываем видео
            cap = cv2.VideoCapture(str(video_path))
            
            if not cap.isOpened():
                raise ValueError("Cannot open video file")
                
            # Получаем метаданные
            metadata = self._get_video_metadata(cap, video_path)
            
            # Извлекаем ключевые кадры
            key_frames = self._extract_key_frames(cap)
            
            # Извлекаем аудио
            audio_info = self._extract_audio_info(video_path)
            
            # Анализируем содержание
            analysis = self._analyze_content(cap, key_frames)
            
            # Закрываем видео
            cap.release()
            
            result = {
                "file_info": metadata,
                "analysis": analysis,
                "key_frames_count": len(key_frames),
                "audio_info": audio_info,
                "processing_time": datetime.now().isoformat(),
                "success": True
            }
            
            return result
            
        except Exception as e:
            raise Exception(f"Error processing video: {e}")
            
    def _get_video_metadata(self, cap, video_path: Path) -> Dict[str, Any]:
        """Получение метаданных видео"""
        metadata = {
            "filename": video_path.name,
            "path": str(video_path),
            "size": video_path.stat().st_size,
            "format": video_path.suffix.lower()[1:],
            
            # Основные параметры
            "fps": cap.get(cv2.CAP_PROP_FPS),
            "frame_count": int(cap.get(cv2.CAP_PROP_FRAME_COUNT)),
            "width": int(cap.get(cv2.CAP_PROP_FRAME_WIDTH)),
            "height": int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT)),
            "duration": int(cap.get(cv2.CAP_PROP_FRAME_COUNT)) / cap.get(cv2.CAP_PROP_FPS) if cap.get(cv2.CAP_PROP_FPS) > 0 else 0,
            
            # Дополнительные параметры
            "codec": self._get_video_codec(cap),
            "bitrate": self._estimate_bitrate(video_path),
        }
        
        return metadata
        
    def _extract_key_frames(self, cap, max_frames: int = 10) -> List[Dict[str, Any]]:
        """Извлечение ключевых кадров"""
        key_frames = []
        total_frames = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
        
        if total_frames == 0:
            return key_frames
            
        # Выбираем равномерно распределенные кадры
        step = max(1, total_frames // max_frames)
        
        for i in range(0, total_frames, step):
            cap.set(cv2.CAP_PROP_POS_FRAMES, i)
            ret, frame = cap.read()
            
            if ret:
                # Сохраняем кадр во временный файл
                with tempfile.NamedTemporaryFile(suffix='.jpg', delete=False) as tmp:
                    cv2.imwrite(tmp.name, frame)
                    
                    key_frames.append({
                        "frame_number": i,
                        "timestamp": i / cap.get(cv2.CAP_PROP_FPS),
                        "path": tmp.name,
                        "size": Path(tmp.name).stat().st_size
                    })
                    
            if len(key_frames) >= max_frames:
                break
                
        return key_frames
        
    def _extract_audio_info(self, video_path: Path) -> Dict[str, Any]:
        """Извлечение информации об аудио"""
        try:
            # Используем ffprobe для получения информации об аудио
            cmd = [
                'ffprobe',
                '-v', 'quiet',
                '-print_format', 'json',
                '-show_streams',
                '-select_streams', 'a',
                str(video_path)
            ]
            
            result = subprocess.run(cmd, capture_output=True, text=True)
            
            if result.returncode == 0:
                info = json.loads(result.stdout)
                
                if info.get('streams'):
                    audio_stream = info['streams'][0]
                    return {
                        "codec": audio_stream.get('codec_name', 'unknown'),
                        "sample_rate": audio_stream.get('sample_rate', 'unknown'),
                        "channels": audio_stream.get('channels', 'unknown'),
                        "duration": audio_stream.get('duration', 'unknown'),
                        "bitrate": audio_stream.get('bit_rate', 'unknown')
                    }
                    
        except Exception as e:
            print(f"Warning: Could not extract audio info: {e}")
            
        return {"error": "Audio info not available"}
        
    def _analyze_content(self, cap, key_frames: List[Dict]) -> Dict[str, Any]:
        """Анализ содержания видео"""
        analysis = {
            "scene_changes": 0,
            "brightness_changes": [],
            "motion_level": "low",
            "color_profile": {},
            "estimated_scenes": []
        }
        
        try:
            # Анализ смены сцен (простая версия)
            prev_frame = None
            scene_changes = 0
            
            for i in range(0, int(cap.get(cv2.CAP_PROP_FRAME_COUNT)), 30):  # Каждый 30-й кадр
                cap.set(cv2.CAP_PROP_POS_FRAMES, i)
                ret, frame = cap.read()
                
                if ret and prev_frame is not None:
                    # Сравнение кадров
                    diff = cv2.absdiff(frame, prev_frame)
                    non_zero = np.count_nonzero(diff)
                    
                    if non_zero > (frame.size * 0.1):  # 10% изменений
                        scene_changes += 1
                        
                prev_frame = frame
                
            analysis["scene_changes"] = scene_changes
            
            # Оценка уровня движения
            if scene_changes > 50:
                analysis["motion_level"] = "high"
            elif scene_changes > 20:
                analysis["motion_level"] = "medium"
            else:
                analysis["motion_level"] = "low"
                
            # Анализ ключевых кадров
            if key_frames:
                colors = []
                for frame_info in key_frames[:3]:  # Первые 3 кадра
                    frame = cv2.imread(frame_info['path'])
                    if frame is not None:
                        avg_color = np.mean(frame, axis=(0, 1))
                        colors.append(avg_color.tolist())
                        
                if colors:
                    analysis["color_profile"] = {
                        "average_colors": colors,
                        "color_variety": len(set(tuple(c) for c in colors))
                    }
                    
        except Exception as e:
            print(f"Warning: Video analysis error: {e}")
            
        return analysis
        
    def _get_video_codec(self, cap) -> str:
        """Получение кодека видео"""
        try:
            # Пытаемся получить информацию о кодировщике
            fourcc = int(cap.get(cv2.CAP_PROP_FOURCC))
            codec = "".join([chr((fourcc >> 8 * i) & 0xFF) for i in range(4)])
            return codec.strip('\x00')
        except:
            return "unknown"
            
    def _estimate_bitrate(self, video_path: Path) -> str:
        """Оценка битрейта"""
        try:
            size = video_path.stat().st_size
            duration = self._get_video_duration(video_path)
            
            if duration > 0:
                bitrate = (size * 8) / duration  # биты в секунду
                
                if bitrate > 1000000:
                    return f"{bitrate/1000000:.1f} Mbps"
                elif bitrate > 1000:
                    return f"{bitrate/1000:.1f} Kbps"
                else:
                    return f"{bitrate:.1f} bps"
                    
        except:
            pass
            
        return "unknown"
        
    def _get_video_duration(self, video_path: Path) -> float:
        """Получение длительности видео"""
        try:
            cmd = ['ffprobe', '-v', 'quiet', '-show_entries', 
                   'format=duration', '-of', 'default=noprint_wrappers=1:nokey=1', 
                   str(video_path)]
            
            result = subprocess.run(cmd, capture_output=True, text=True)
            return float(result.stdout.strip())
        except:
            return 0
            
    def extract_subtitles(self, video_path: str, output_path: Optional[str] = None) -> str:
        """Извлечение субтитров"""
        if output_path is None:
            output_path = str(Path(video_path).with_suffix('.srt'))
            
        try:
            cmd = [
                'ffmpeg',
                '-i', video_path,
                '-map', '0:s:0',
                output_path
            ]
            
            subprocess.run(cmd, capture_output=True)
            return output_path
            
        except Exception as e:
            raise Exception(f"Could not extract subtitles: {e}")
            
    def create_thumbnail(self, video_path: str, timestamp: float = 10, 
                        output_path: Optional[str] = None) -> str:
        """Создание превью видео"""
        if output_path is None:
            output_path = str(Path(video_path).with_suffix('.jpg'))
            
        try:
            cmd = [
                'ffmpeg',
                '-ss', str(timestamp),
                '-i', video_path,
                '-vframes', '1',
                '-q:v', '2',
                output_path
            ]
            
            subprocess.run(cmd, capture_output=True)
            return output_path
            
        except Exception as e:
            raise Exception(f"Could not create thumbnail: {e}")
            
    def convert_format(self, video_path: str, output_format: str = 'mp4', 
                      quality: str = 'medium') -> str:
        """Конвертация формата видео"""
        output_path = str(Path(video_path).with_suffix(f'.{output_format}'))
        
        quality_presets = {
            'low': ['-crf', '28', '-preset', 'fast'],
            'medium': ['-crf', '23', '-preset', 'medium'],
            'high': ['-crf', '18', '-preset', 'slow']
        }
        
        try:
            cmd = [
                'ffmpeg',
                '-i', video_path
            ] + quality_presets.get(quality, quality_presets['medium']) + [
                output_path
            ]
            
            subprocess.run(cmd, capture_output=True)
            return output_path
            
        except Exception as e:
            raise Exception(f"Could not convert video: {e}")