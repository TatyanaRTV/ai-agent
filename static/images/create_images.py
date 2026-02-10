"""
create_images.py - создание изображений для интерфейса Елены
"""
from PIL import Image, ImageDraw, ImageFont
import os

def create_logo(output_path="static/images/logo.png"):
    """Создание логотипа Елены"""
    # Создаем изображение
    img = Image.new('RGBA', (512, 512), color=(255, 255, 255, 0))
    draw = ImageDraw.Draw(img)
    
    # Рисуем круг (голова)
    draw.ellipse([50, 50, 462, 462], fill=(255, 182, 193, 200), outline=(255, 105, 180, 255))
    
    # Рисуем волосы
    draw.ellipse([100, 30, 412, 200], fill=(139, 69, 19, 200))
    
    # Рисуем глаза
    draw.ellipse([180, 200, 230, 250], fill=(0, 0, 0, 255))
    draw.ellipse([280, 200, 330, 250], fill=(0, 0, 0, 255))
    
    # Рисуем улыбку
    draw.arc([200, 300, 312, 380], 0, 180, fill=(255, 0, 0, 255), width=5)
    
    # Добавляем текст
    try:
        font = ImageFont.truetype("arial.ttf", 40)
    except:
        font = ImageFont.load_default()
    
    draw.text((150, 400), "ЕЛЕНА", fill=(75, 0, 130, 255), font=font)
    draw.text((180, 450), "AI Assistant", fill=(100, 149, 237, 255), font=font)
    
    # Сохраняем
    img.save(output_path)
    print(f"✅ Логотип создан: {output_path}")

def create_icon(name, symbol, output_dir="static/images/icons"):
    """Создание иконки"""
    img = Image.new('RGBA', (64, 64), color=(255, 255, 255, 0))
    draw = ImageDraw.Draw(img)
    
    # Рисуем фон
    draw.rounded_rectangle([5, 5, 59, 59], radius=10, fill=(106, 17, 203, 100))
    
    # Добавляем символ
    try:
        font = ImageFont.truetype("arial.ttf", 30)
    except:
        font = ImageFont.load_default()
    
    draw.text((20, 15), symbol, fill=(255, 255, 255, 255), font=font)
    
    # Сохраняем
    os.makedirs(output_dir, exist_ok=True)
    output_path = os.path.join(output_dir, f"{name}.png")
    img.save(output_path)
    print(f"✅ Иконка создана: {output_path}")

def create_all_images():
    """Создание всех изображений"""
    print("🎨 Создание графических ресурсов для Елены...")
    
    # Создаем структуру папок
    os.makedirs("static/images", exist_ok=True)
    os.makedirs("static/images/icons", exist_ok=True)
    os.makedirs("static/images/emojis", exist_ok=True)
    
    # Создаем логотип
    create_logo()
    
    # Создаем основные иконки
    icons = [
        ("home", "🏠"),
        ("chat", "💬"),
        ("voice", "🎤"),
        ("document", "📄"),
        ("settings", "⚙️"),
        ("help", "❓"),
        ("user", "👤"),
        ("ai", "🤖"),
        ("upload", "📤"),
        ("download", "📥")
    ]
    
    for name, symbol in icons:
        create_icon(name, symbol)
    
    print("✅ Все изображения созданы!")

if __name__ == "__main__":
    create_all_images()