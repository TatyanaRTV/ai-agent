"""
ПРОСТОЙ ГОЛОСОВОЙ МОДУЛЬ
Говорит и слушает (если есть микрофон)
"""

import speech_recognition as sr
import os
import time

class SimpleVoice:
    """Простой голосовой помощник"""
    
    def __init__(self):
        print("🎤 Инициализирую голосовой модуль...")
        
        # Инициализация синтезатора речи (RHVoice Елена)
        try:
            # Проверяем наличие RHVoice
            result = os.system("which RHVoice-test > /dev/null 2>&1")
            self.rhvoice_available = (result == 0)
            
            if self.rhvoice_available:
                print("✅ RHVoice Елена найден!")
            else:
                print("⚠️ RHVoice не найден, голосовая озвучка недоступна")
                self.rhvoice_available = False
                
        except Exception as e:
            print(f"⚠️ Ошибка инициализации голоса: {e}")
            self.rhvoice_available = False
        
        # Инициализация распознавания речи
        try:
            self.recognizer = sr.Recognizer()
            print("✅ Распознавание речи готово!")
        except:
            print("⚠️ Распознавание речи недоступно")
            self.recognizer = None
    
    def speak(self, text):
        """Произнести текст голосом Елены"""
        if self.rhvoice_available:
            try:
                print(f"🔊 Елена: {text}")
                os.system(f'echo "{text}" | RHVoice-test -p elena -r 85 -o out.wav && aplay -q out.wav')
                os.system("rm -f out.wav")  # Удаляем временный файл
            except Exception as e:
                print(f"❌ Ошибка озвучки: {e}")
                print(f"💬: {text}")
        else:
            print(f"💬 (Без голоса): {text}")
    
    def listen(self):
        """Слушать голос команду"""
        if not self.recognizer:
            return None
        
        try:
            with sr.Microphone() as source:
                print("🎤 Слушаю... (говорите сейчас)")
                
                # Настройка для уменьшения шума
                self.recognizer.adjust_for_ambient_noise(source, duration=0.5)
                
                # Слушаем
                audio = self.recognizer.listen(source, timeout=5, phrase_time_limit=5)
                
                # Распознаем
                try:
                    text = self.recognizer.recognize_google(audio, language="ru-RU")
                    print(f"🎤 Вы сказали: {text}")
                    return text
                except sr.UnknownValueError:
                    print("🎤 Не поняла, что вы сказали")
                    return None
                except sr.RequestError:
                    print("🎤 Ошибка подключения к сервису распознавания")
                    return None
                    
        except Exception as e:
            print(f"🎤 Ошибка микрофона: {e}")
            return None
    
    def test_voice(self):
        """Тест голоса Елены"""
        print("\n🔊 ТЕСТ ГОЛОСА ЕЛЕНЫ")
        print("=" * 30)
        
        test_phrases = [
            "Привет! Я Елена, ваш голосовой помощник.",
            "Рада вас слышать!",
            "Как у вас дела сегодня?",
            "Чем могу помочь?",
            "До свидания! Возвращайтесь скорее."
        ]
        
        for phrase in test_phrases:
            self.speak(phrase)
            time.sleep(1)
        
        print("\n✅ Тест голоса завершен!")
    
    def test_listen(self):
        """Тест распознавания речи"""
        if not self.recognizer:
            print("❌ Распознавание речи недоступно")
            return
        
        print("\n🎤 ТЕСТ РАСПОЗНАВАНИЯ РЕЧИ")
        print("=" * 40)
        print("Говорите после сигнала...")
        
        for i in range(3):
            print(f"\nПопытка {i+1}/3...")
            text = self.listen()
            
            if text:
                self.speak(f"Вы сказали: {text}")
            else:
                self.speak("Я не расслышала, повторите пожалуйста")
            
            time.sleep(1)
        
        print("\n✅ Тест распознавания завершен!")

# Простой пример использования
if __name__ == "__main__":
    print("🎤 ТЕСТ ПРОСТОГО ГОЛОСОВОГО МОДУЛЯ")
    print("=" * 40)
    
    voice = SimpleVoice()
    
    # Тест голоса
    voice.test_voice()
    
    # Спросить, тестировать ли распознавание
    answer = input("\nПротестировать распознавание речи? (да/нет): ")
    
    if answer.lower() in ['да', 'yes', 'y']:
        voice.test_listen()
    
    print("\n🎤 Голосовой модуль готов к работе!")
    print("\nПример использования:")
    print("1. voice.speak('Привет, как дела?')")
    print("2. text = voice.listen()")
    print("3. if text: print(f'Вы сказали: {text}')")