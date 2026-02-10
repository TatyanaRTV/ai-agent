"""
ОБРАБОТКА АУДИО ФАЙЛОВ
"""

import wave
import audioop
import tempfile
import json
from pathlib import Path
from typing import Dict, List, Any, Optional
import subprocess
import numpy as np
from datetime import datetime

class AudioProcessor:
    """Процессор аудио файлов"""
    
    def __init__(self):
        self.supported_formats = ['.wav', '.mp3', '.ogg', '.flac', '.m4a', '.aac']
        
    def process_audio(self, audio_path: str) -> Dict[str, Any]:
        """Обработка аудио файла"""
        if not Path(audio_path).exists():
            raise FileNotFoundError(f"Audio file not found: {audio_path}")
            
        audio_path = Path(audio_path)
        
        if audio_path.suffix.lower() not in self.supported_formats:
            raise ValueError(f"Unsupported audio format: {audio_path.suffix}")
            
        print(f"🎵 Обработка аудио: {audio_path.name}")
        
        try:
            # Конвертируем в WAV для анализа
            wav_path = self._convert_to_wav(audio_path)
            
            # Получаем метаданные
            metadata = self._get_audio_metadata(audio_path)
            
            # Анализируем аудио
            analysis = self._analyze_audio(wav_path)
            
            # Удаляем временный файл
            if wav_path != audio_path:
                Path(wav_path).unlink(missing_ok=True)
                
            result = {
                "file_info": metadata,
                "analysis": analysis,
                "processing_time": datetime.now().isoformat(),
                "success": True
            }
            
            return result
            
        except Exception as e:
            raise Exception(f"Error processing audio: {e}")
            
    def _convert_to_wav(self, audio_path: Path) -> str:
        """Конвертация аудио в WAV формат"""
        if audio_path.suffix.lower() == '.wav':
            return str(audio_path)
            
        wav_path = tempfile.mktemp(suffix='.wav')
        
        try:
            cmd = [
                'ffmpeg',
                '-i', str(audio_path),
                '-acodec', 'pcm_s16le',
                '-ac', '1',
                '-ar', '16000',
                wav_path,
                '-y'
            ]
            
            subprocess.run(cmd, capture_output=True)
            return wav_path
            
        except Exception as e:
            raise Exception(f"Could not convert audio to WAV: {e}")
            
    def _get_audio_metadata(self, audio_path: Path) -> Dict[str, Any]:
        """Получение метаданных аудио"""
        try:
            cmd = [
                'ffprobe',
                '-v', 'quiet',
                '-print_format', 'json',
                '-show_format',
                '-show_streams',
                str(audio_path)
            ]
            
            result = subprocess.run(cmd, capture_output=True, text=True)
            
            if result.returncode == 0:
                info = json.loads(result.stdout)
                
                metadata = {
                    "filename": audio_path.name,
                    "path": str(audio_path),
                    "size": audio_path.stat().st_size,
                    "format": audio_path.suffix.lower()[1:],
                }
                
                if info.get('format'):
                    metadata.update({
                        "duration": float(info['format'].get('duration', 0)),
                        "bitrate": info['format'].get('bit_rate', 'unknown'),
                        "encoder": info['format'].get('encoder', 'unknown')
                    })
                    
                if info.get('streams'):
                    stream = info['streams'][0]
                    metadata.update({
                        "codec": stream.get('codec_name', 'unknown'),
                        "sample_rate": stream.get('sample_rate', 'unknown'),
                        "channels": stream.get('channels', 'unknown'),
                        "bits_per_sample": stream.get('bits_per_sample', 'unknown')
                    })
                    
                return metadata
                
        except Exception as e:
            print(f"Warning: Could not get audio metadata: {e}")
            
        # Возвращаем базовую информацию если не удалось получить метаданные
        return {
            "filename": audio_path.name,
            "size": audio_path.stat().st_size,
            "format": audio_path.suffix.lower()[1:],
            "duration": "unknown"
        }
        
    def _analyze_audio(self, wav_path: str) -> Dict[str, Any]:
        """Анализ аудио файла"""
        analysis = {
            "duration": 0,
            "sample_rate": 0,
            "channels": 0,
            "volume_level": "medium",
            "silence_percentage": 0,
            "frequency_analysis": {},
            "detected_features": []
        }
        
        try:
            with wave.open(wav_path, 'rb') as wav_file:
                analysis["sample_rate"] = wav_file.getframerate()
                analysis["channels"] = wav_file.getnchannels()
                analysis["duration"] = wav_file.getnframes() / wav_file.getframerate()
                
                # Чтение аудио данных
                frames = wav_file.readframes(wav_file.getnframes())
                audio_data = np.frombuffer(frames, dtype=np.int16)
                
                # Анализ громкости
                rms = audioop.rms(audio_data, 2)
                analysis["volume_rms"] = rms
                
                if rms > 10000:
                    analysis["volume_level"] = "loud"
                elif rms > 3000:
                    analysis["volume_level"] = "medium"
                else:
                    analysis["volume_level"] = "quiet"
                    
                # Анализ тишины
                silence_threshold = 1000
                silent_samples = np.sum(np.abs(audio_data) < silence_threshold)
                analysis["silence_percentage"] = (silent_samples / len(audio_data)) * 100
                
                # Простой анализ частот
                if len(audio_data) > 0:
                    fft_result = np.fft.fft(audio_data[:4096])
                    frequencies = np.fft.fftfreq(len(fft_result), 1/analysis["sample_rate"])
                    
                    # Находим доминирующие частоты
                    magnitude = np.abs(fft_result)
                    dominant_freq_idx = np.argmax(magnitude[:len(magnitude)//2])
                    dominant_freq = abs(frequencies[dominant_freq_idx])
                    
                    analysis["frequency_analysis"] = {
                        "dominant_frequency": dominant_freq,
                        "is_voice_range": 85 <= dominant_freq <= 255,
                        "frequency_range": {
                            "min": abs(frequencies[0]),
                            "max": abs(frequencies[len(frequencies)//2])
                        }
                    }
                    
                # Определение возможных характеристик
                features = []
                
                if analysis.get("frequency_analysis", {}).get("is_voice_range"):
                    features.append("human_voice_likely")
                    
                if analysis["silence_percentage"] > 50:
                    features.append("high_silence_content")
                    
                if rms > 15000:
                    features.append("loud_audio")
                    
                analysis["detected_features"] = features
                
        except Exception as e:
            print(f"Warning: Audio analysis error: {e}")
            
        return analysis
        
    def extract_audio_from_video(self, video_path: str, output_path: Optional[str] = None) -> str:
        """Извлечение аудио из видео"""
        if output_path is None:
            output_path = str(Path(video_path).with_suffix('.mp3'))
            
        try:
            cmd = [
                'ffmpeg',
                '-i', video_path,
                '-q:a', '0',
                '-map', 'a',
                output_path,
                '-y'
            ]
            
            subprocess.run(cmd, capture_output=True)
            return output_path
            
        except Exception as e:
            raise Exception(f"Could not extract audio: {e}")
            
    def convert_format(self, audio_path: str, output_format: str = 'mp3', 
                      bitrate: str = '192k') -> str:
        """Конвертация формата аудио"""
        output_path = str(Path(audio_path).with_suffix(f'.{output_format}'))
        
        try:
            cmd = [
                'ffmpeg',
                '-i', audio_path,
                '-b:a', bitrate,
                output_path,
                '-y'
            ]
            
            subprocess.run(cmd, capture_output=True)
            return output_path
            
        except Exception as e:
            raise Exception(f"Could not convert audio: {e}")
            
    def normalize_audio(self, audio_path: str, target_level: float = -1.0) -> str:
        """Нормализация громкости аудио"""
        output_path = tempfile.mktemp(suffix=Path(audio_path).suffix)
        
        try:
            cmd = [
                'ffmpeg',
                '-i', audio_path,
                '-af', f'volume={target_level}dB',
                output_path,
                '-y'
            ]
            
            subprocess.run(cmd, capture_output=True)
            return output_path
            
        except Exception as e:
            raise Exception(f"Could not normalize audio: {e}")
            
    def trim_audio(self, audio_path: str, start_time: float, end_time: float) -> str:
        """Обрезка аудио"""
        duration = end_time - start_time
        output_path = tempfile.mktemp(suffix=Path(audio_path).suffix)
        
        try:
            cmd = [
                'ffmpeg',
                '-i', audio_path,
                '-ss', str(start_time),
                '-t', str(duration),
                output_path,
                '-y'
            ]
            
            subprocess.run(cmd, capture_output=True)
            return output_path
            
        except Exception as e:
            raise Exception(f"Could not trim audio: {e}")
            
    def concatenate_audio(self, audio_files: List[str], output_path: str) -> str:
        """Конкатенация аудио файлов"""
        try:
            # Создаем временный файл со списком
            list_file = tempfile.mktemp(suffix='.txt')
            
            with open(list_file, 'w') as f:
                for audio_file in audio_files:
                    f.write(f"file '{audio_file}'\n")
                    
            cmd = [
                'ffmpeg',
                '-f', 'concat',
                '-safe', '0',
                '-i', list_file,
                '-c', 'copy',
                output_path,
                '-y'
            ]
            
            subprocess.run(cmd, capture_output=True)
            
            # Удаляем временный файл
            Path(list_file).unlink()
            
            return output_path
            
        except Exception as e:
            raise Exception(f"Could not concatenate audio: {e}")