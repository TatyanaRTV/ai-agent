"""
Движок компьютерного зрения для анализа экрана
"""

import logging
from PIL import Image
import torch
from transformers import AutoModelForCausalLM, AutoTokenizer
import mss
import numpy as np

logger = logging.getLogger(__name__)

class VisionEngine:
    """Движок компьютерного зрения"""
    
    def __init__(self, model_name="vikhyatk/moondream2"):
        self.model_name = model_name
        self.device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
        
        logger.info(f"👁️ Загрузка модели зрения: {model_name}")
        
        try:
            self.tokenizer = AutoTokenizer.from_pretrained(model_name)
            self.model = AutoModelForCausalLM.from_pretrained(
                model_name,
                trust_remote_code=True,
                torch_dtype=torch.float16
            ).to(self.device)
            self.model.eval()
        except Exception as e:
            logger.error(f"Ошибка загрузки модели зрения: {e}")
            raise
            
    def capture_screen(self):
        """Захват текущего экрана"""
        with mss.mss() as sct:
            monitor = sct.monitors[1]
            screenshot = sct.grab(monitor)
            img = Image.frombytes("RGB", screenshot.size, screenshot.rgb)
            return img
            
    def analyze_screen(self, question="Что ты видишь на экране?"):
        """Анализ текущего экрана"""
        try:
            # Захват экрана
            image = self.capture_screen()
            
            # Подготовка изображения
            enc_image = self.model.encode_image(image)
            
            # Генерация ответа
            answer = self.model.answer_question(
                enc_image,
                question,
                self.tokenizer
            )
            
            return {
                "analysis": answer,
                "image_size": image.size,
                "timestamp": torch.cuda.get_device_properties(0).total_memory if torch.cuda.is_available() else None
            }
            
        except Exception as e:
            logger.error(f"Ошибка анализа экрана: {e}")
            return {"error": str(e)}
            
    def analyze_image(self, image_path, question=None):
        """Анализ конкретного изображения"""
        try:
            image = Image.open(image_path).convert("RGB")
            
            if question is None:
                question = "Опиши подробно, что ты видишь на этом изображении?"
                
            enc_image = self.model.encode_image(image)
            answer = self.model.answer_question(enc_image, question, self.tokenizer)
            
            return {
                "description": answer,
                "image_path": image_path,
                "dimensions": image.size
            }
            
        except Exception as e:
            logger.error(f"Ошибка анализа изображения {image_path}: {e}")
            return {"error": str(e)}