"""
Синтезатор речи с женским русским голосом
"""

import pyttsx3
import logging
from typing import Optional, Dict, Any
import tempfile
import os

logger = logging.getLogger(__name__)

class SpeechSynthesizer:
    """Синтезатор речи с поддержкой русского языка"""
    
    def __init__(self, voice_name: str = "Елена", rate: int = 150):
        self.engine = None
        self.voice_name = voice_name
        self.rate = rate
        self._init_engine()
        
    def _init_engine(self):
        """Инициализация движка синтеза речи"""
        try:
            self.engine = pyttsx3.init()
            
            # Настройка параметров
            self.engine.setProperty('rate', self.rate)
            self.engine.setProperty('volume', 0.9)
            
            # Поиск русского женского голоса
            voices = self.engine.getProperty('voices')
            russian_voices = []
            
            for voice in voices:
                # Проверка на русский язык
                if 'russian' in voice.languages or 'ru' in str(voice.languages).lower():
                    russian_voices.append(voice)
                    
            if russian_voices:
                # Предпочтение женскому голосу
                female_voices = [v for v in russian_voices if 'female' in v.name.lower() or 'женский' in v.name.lower()]
                
                if female_voices:
                    selected_voice = female_voices[0]
                else:
                    selected_voice = russian_voices[0]
                    
                self.engine.setProperty('voice', selected_voice.id)
                logger.info(f"Выбран голос: {selected_voice.name}")
            else:
                logger.warning("Русские голоса не найдены, используется голос по умолчанию")
                
            logger.info("✅ Синтезатор речи инициализирован")
            
        except Exception as e:
            logger.error(f"Ошибка инициализации синтезатора речи: {e}")
            raise
            
    def speak(self, text: str, wait: bool = True):
        """Произнесение текста"""
        if not self.engine:
            raise RuntimeError("Синтезатор речи не инициализирован")
            
        try:
            logger.info(f"🗣️ Произнесение: {text[:50]}...")
            
            if wait:
                self.engine.say(text)
                self.engine.runAndWait()
            else:
                self.engine.say(text)
                self.engine.startLoop(False)
                
        except Exception as e:
            logger.error(f"Ошибка синтеза речи: {e}")
            
    def save_to_file(self, text: str, filename: Optional[str] = None) -> str:
        """Сохранение речи в файл"""
        if not self.engine:
            raise RuntimeError("Синтезатор речи не инициализирован")
            
        try:
            if filename is None:
                # Создание временного файла
                temp_dir = tempfile.gettempdir()
                filename = os.path.join(temp_dir, f"speech_{hash(text)}.mp3")
                
            # Сохранение в файл
            self.engine.save_to_file(text, filename)
            self.engine.runAndWait()
            
            logger.info(f"💾 Речь сохранена в файл: {filename}")
            return filename
            
        except Exception as e:
            logger.error(f"Ошибка сохранения речи в файл: {e}")
            raise
            
    def set_rate(self, rate: int):
        """Установка скорости речи"""
        if 50 <= rate <= 300:
            self.rate = rate
            self.engine.setProperty('rate', rate)
            logger.info(f"Скорость речи установлена: {rate}")
        else:
            raise ValueError("Скорость речи должна быть между 50 и 300")
            
    def set_volume(self, volume: float):
        """Установка громкости"""
        if 0.0 <= volume <= 1.0:
            self.engine.setProperty('volume', volume)
            logger.info(f"Громкость установлена: {volume}")
        else:
            raise ValueError("Громкость должна быть между 0.0 и 1.0")
            
    def get_available_voices(self) -> Dict[str, Any]:
        """Получение списка доступных голосов"""
        if not self.engine:
            return {}
            
        voices = self.engine.getProperty('voices')
        voice_list = []
        
        for i, voice in enumerate(voices):
            voice_info = {
                "id": voice.id,
                "name": voice.name,
                "languages": voice.languages,
                "gender": self._detect_gender(voice.name),
                "index": i
            }
            voice_list.append(voice_info)
            
        return {"voices": voice_list}
        
    def _detect_gender(self, voice_name: str) -> str:
        """Определение пола голоса по названию"""
        voice_lower = voice_name.lower()
        
        if any(word in voice_lower for word in ['female', 'женск', 'женский', 'девушк']):
            return "female"
        elif any(word in voice_lower for word in ['male', 'мужск', 'мужской', 'мужчин']):
            return "male"
        else:
            return "unknown"
            
    def set_voice_by_name(self, voice_name: str):
        """Установка голоса по имени"""
        if not self.engine:
            return
            
        voices = self.engine.getProperty('voices')
        
        for voice in voices:
            if voice_name.lower() in voice.name.lower():
                self.engine.setProperty('voice', voice.id)
                self.voice_name = voice.name
                logger.info(f"Установлен голос: {voice.name}")
                return
                
        logger.warning(f"Голос '{voice_name}' не найден")
        
    def stop(self):
        """Остановка синтезатора"""
        if self.engine:
            try:
                self.engine.stop()
                logger.info("Синтезатор речи остановлен")
            except:
                pass
                
    def __del__(self):
        """Деструктор"""
        self.stop()


class RHVoiceSynthesizer(SpeechSynthesizer):
    """Синтезатор речи с использованием RHVoice (более качественный русский голос)"""
    
    def __init__(self, voice_name: str = "Елена"):
        super().__init__(voice_name)
        
    def _init_engine(self):
        """Инициализация RHVoice"""
        try:
            # Проверка наличия RHVoice
            import subprocess
            
            result = subprocess.run(
                ['rhvoice-test', '--help'],
                capture_output=True,
                text=True
            )
            
            if result.returncode != 0:
                logger.warning("RHVoice не установлен, используется pyttsx3")
                super()._init_engine()
                return
                
            self.engine_type = "rhvoice"
            logger.info("✅ RHVoice синтезатор инициализирован")
            
        except Exception as e:
            logger.error(f"Ошибка инициализации RHVoice: {e}")
            super()._init_engine()
            
    def speak(self, text: str, wait: bool = True):
        """Произнесение текста через RHVoice"""
        if hasattr(self, 'engine_type') and self.engine_type == "rhvoice":
            try:
                import subprocess
                
                # Использование RHVoice для синтеза
                cmd = ['rhvoice-client', '-s', self.voice_name, '-r', str(self.rate), '-o', '-']
                process = subprocess.Popen(
                    cmd,
                    stdin=subprocess.PIPE,
                    stdout=subprocess.PIPE,
                    stderr=subprocess.PIPE
                )
                
                # Отправка текста
                stdout, stderr = process.communicate(input=text.encode('utf-8'))
                
                if process.returncode == 0:
                    # Воспроизведение аудио
                    import pygame
                    
                    pygame.mixer.init()
                    
                    # Сохранение во временный файл
                    import tempfile
                    with tempfile.NamedTemporaryFile(suffix='.wav', delete=False) as f:
                        f.write(stdout)
                        temp_file = f.name
                        
                    pygame.mixer.music.load(temp_file)
                    pygame.mixer.music.play()
                    
                    if wait:
                        while pygame.mixer.music.get_busy():
                            import time
                            time.sleep(0.1)
                            
                    # Удаление временного файла
                    import os
                    os.unlink(temp_file)
                    
                    pygame.mixer.quit()
                    
                else:
                    logger.error(f"Ошибка RHVoice: {stderr.decode()}")
                    super().speak(text, wait)
                    
            except Exception as e:
                logger.error(f"Ошибка синтеза RHVoice: {e}")
                super().speak(text, wait)
        else:
            super().speak(text, wait)