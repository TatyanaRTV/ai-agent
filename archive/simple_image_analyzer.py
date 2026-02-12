"""
ПРОСТОЙ АНАЛИЗАТОР ИЗОБРАЖЕНИЙ
Анализирует картинки и скриншоты
"""

import os
from PIL import Image, ImageGrab
import pytesseract
import time

class SimpleImageAnalyzer:
    """Простой анализатор изображений"""
    
    def __init__(self):
        print("🖼️ Инициализирую анализатор изображений...")
        
        # Проверяем наличие Tesseract OCR
        try:
            pytesseract.get_tesseract_version()
            print("✅ Tesseract OCR установлен")
            self.ocr_available = True
        except:
            print("⚠️ Tesseract OCR не установлен. Установите:")
            print("   Windows: https://github.com/UB-Mannheim/tesseract/wiki")
            print("   Linux: sudo apt install tesseract-ocr tesseract-ocr-rus")
            self.ocr_available = False
    
    def analyze_image(self, image_path):
        """Анализирует изображение"""
        if not os.path.exists(image_path):
            return "❌ Изображение не найдено"
        
        try:
            # Открываем изображение
            img = Image.open(image_path)
            
            info = f"🖼️ Изображение: {os.path.basename(image_path)}\n"
            info += f"📏 Размер: {img.width} x {img.height} пикселей\n"
            info += f"🎨 Формат: {img.format}\n"
            info += f"🌈 Режим: {img.mode}\n"
            
            # Попытка распознать текст
            if self.ocr_available:
                try:
                    text = pytesseract.image_to_string(img, lang='rus+eng')
                    if text.strip():
                        info += f"\n📝 Распознанный текст:\n{text[:500]}..."
                    else:
                        info += "\n📝 Текст не обнаружен"
                except:
                    info += "\n📝 Не удалось распознать текст"
            
            return info
            
        except Exception as e:
            return f"❌ Ошибка анализа изображения: {e}"
    
    def take_screenshot(self, save_path=None):
        """Делает скриншот экрана"""
        try:
            # Делаем скриншот
            screenshot = ImageGrab.grab()
            
            # Сохраняем
            if save_path is None:
                timestamp = time.strftime("%Y%m%d_%H%M%S")
                save_path = f"screenshot_{timestamp}.png"
            
            screenshot.save(save_path)
            
            # Анализируем скриншот
            analysis = self.analyze_image(save_path)
            
            result = f"📸 Скриншот сохранен: {save_path}\n"
            result += f"📏 Размер: {screenshot.width} x {screenshot.height}\n\n"
            result += analysis
            
            return result
            
        except Exception as e:
            return f"❌ Ошибка создания скриншота: {e}"
    
    def batch_analyze(self, folder_path):
        """Анализирует все изображения в папке"""
        if not os.path.exists(folder_path):
            return "❌ Папка не найдена"
        
        image_extensions = ['.jpg', '.jpeg', '.png', '.bmp', '.gif', '.tiff']
        results = []
        
        for filename in os.listdir(folder_path):
            file_ext = os.path.splitext(filename)[1].lower()
            
            if file_ext in image_extensions:
                file_path = os.path.join(folder_path, filename)
                print(f"🖼️ Анализирую: {filename}")
                
                analysis = self.analyze_image(file_path)
                results.append({
                    'filename': filename,
                    'analysis': analysis[:300] + "..." if len(analysis) > 300 else analysis
                })
        
        return results

# Пример использования
if __name__ == "__main__":
    print("🖼️ ТЕСТ АНАЛИЗАТОРА ИЗОБРАЖЕНИЙ")
    print("=" * 40)
    
    analyzer = SimpleImageAnalyzer()
    
    print("\n📸 Тест создания скриншота...")
    
    # Делаем скриншот
    result = analyzer.take_screenshot("test_screenshot.png")
    
    print("\n" + result)
    
    if os.path.exists("test_screenshot.png"):
        print("\n🖼️ Анализ скриншота...")
        analysis = analyzer.analyze_image("test_screenshot.png")
        print("\n" + analysis)
    
    print("\n💡 Пример использования:")
    print("analyzer = SimpleImageAnalyzer()")
    print('result = analyzer.analyze_image("ваше_изображение.jpg")')
    print('print(result)')
    print()
    print('screenshot = analyzer.take_screenshot()')
    print('print(screenshot)')
    
    # Уборка
    if os.path.exists("test_screenshot.png"):
        os.remove("test_screenshot.png")
        print("\n🧹 Удален тестовый скриншот")