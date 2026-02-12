"""
ПРОСТОЙ ЗАПУСК ЕЛЕНЫ
Этот файл запускает ИИ-агента Елена. Просто запустите его!
"""

import os
from datetime import datetime

# Подключаем голосовой модуль
try:
    from simple_voice import SimpleVoice
    voice = SimpleVoice()
    VOICE_AVAILABLE = True
    print("✅ Голос Елены загружен")
except:
    voice = None
    VOICE_AVAILABLE = False

print("=" * 50)
print("🎀  ЗАПУСК ИИ-АГЕНТА ЕЛЕНА  🎀")
print("=" * 50)
print(f"Дата и время: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")

# Создаём папки
folders = ['data', 'data/logs', 'data/temp', 'data/vectors', 'data/cache', 'models', 'configs', 'logs']
for folder in folders:
    os.makedirs(folder, exist_ok=True)

class SimpleElena:
    def __init__(self):
        self.name = "Елена"
        self.birthday = "5 февраля 2026"
        self.creator = "Татьяна"
        self.voice = voice if VOICE_AVAILABLE else None

    def speak(self, text):
        if self.voice:
            self.voice.speak(text)
        else:
            print(f"💬 {text}")

    def start(self):
        print(f"👋 Привет! Я {self.name}, ваш ИИ-помощник!")
        print(f"📅 Мой день рождения: {self.birthday}")
        print(f"👩 Создатель: {self.creator}\n")
        self.speak("Привет! Я Елена, ваш голосовой помощник!")

        print("\n💬 Команды:")
        print("   • info — информация о системе")
        print("   • выход — завершение")
        print("   • Enter — повторить приветствие\n")

        while True:
            try:
                cmd = input("Вы: ").strip().lower()
                if cmd in ['выход', 'exit', 'quit', 'стоп']:
                    self.speak("До свидания! Буду ждать вас!")
                    break
                elif cmd == 'info':
                    print(f"\n🤖 {self.name} | 🎤 Голос: {'✅' if self.voice else '❌'}\n")
                elif cmd == '':
                    self.speak("Я вас слушаю. Чем могу помочь?")
                else:
                    self.speak("Я поняла ваш вопрос. В полной версии отвечу подробнее.")
            except KeyboardInterrupt:
                self.speak("До встречи!")
                break

if __name__ == "__main__":
    SimpleElena().start()