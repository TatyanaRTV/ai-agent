#!/usr/bin/env python3
# Путь: /mnt/ai_data/ai-agent/src/engines/vision_engine.py
"""Зрительный модуль Елены на базе nanoLLaVA - стабильная и легкая модель"""

import mss
from PIL import Image
from pathlib import Path
from datetime import datetime
import torch
import transformers
from transformers import AutoModelForCausalLM, AutoTokenizer
from loguru import logger
import warnings

# Отключаем лишние предупреждения
transformers.logging.set_verbosity_error()
transformers.logging.disable_progress_bar()
warnings.filterwarnings("ignore")


class VisionEngine:
    """
    Зрительный движок Елены на базе nanoLLaVA.
    Надежная работа с актуальными версиями библиотек.
    """

    def __init__(self, config):
        """
        Инициализация зрительного движка

        Args:
            config: словарь с конфигурацией
        """
        self.config = config
        self.device = self._get_device()

        # Директория для сохранения скриншотов
        self.screenshot_dir = Path(config["paths"]["data"]) / "screenshots"
        self.screenshot_dir.mkdir(parents=True, exist_ok=True)

        # Инициализация захвата экрана
        self.sct = mss.mss()

        # Модель для анализа
        self.model = None
        self.tokenizer = None

        # Загружаем nanoLLaVA
        self._try_load_nanollava()

        if self.model:
            logger.success(f"✅ nanoLLaVA загружен на устройстве {self.device}")
        else:
            logger.warning("👁️ nanoLLaVA не загружен (скриншоты без анализа)")

    def _get_device(self):
        """Определение доступного устройства"""
        if torch.cuda.is_available():
            logger.info("🚀 Используется CUDA (GPU)")
            return "cuda"
        else:
            logger.info("💻 Используется CPU")
            return "cpu"

    def _try_load_nanollava(self):
        """Загрузка модели nanoLLaVA"""
        try:
            model_name = "qnguyen3/nanoLLaVA"  # или "qnguyen3/nanoLLaVA-1.5" для улучшенной версии

            logger.info(f"📥 Загрузка nanoLLaVA...")

            # Устанавливаем устройство по умолчанию для torch
            torch.set_default_device(self.device)

            # Загружаем модель и токенизатор
            self.model = AutoModelForCausalLM.from_pretrained(
                model_name,
                torch_dtype=torch.float16 if self.device == "cuda" else torch.float32,
                device_map="auto" if self.device == "cuda" else None,
                trust_remote_code=True,
            )

            self.tokenizer = AutoTokenizer.from_pretrained(model_name, trust_remote_code=True)

            logger.success("✅ nanoLLaVA загружен успешно")

        except Exception as e:
            logger.warning(f"⚠️ nanoLLaVA не загружен: {e}")
            self.model = None
            self.tokenizer = None

    def capture_screen(self, monitor=1):
        """
        Сделать скриншот экрана

        Args:
            monitor: номер монитора (1, 2, ...)

        Returns:
            PIL Image или None
        """
        try:
            screenshot = self.sct.grab(self.sct.monitors[monitor])
            img = Image.frombytes("RGB", screenshot.size, screenshot.rgb)

            # Сохраняем для истории
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            save_path = self.screenshot_dir / f"screenshot_{timestamp}.png"
            img.save(save_path)
            logger.debug(f"📸 Скриншот сохранён: {save_path}")

            return img

        except Exception as e:
            logger.error(f"❌ Ошибка захвата экрана: {e}")
            return None

    def describe(self, image: Image.Image, prompt: str = "Опиши это изображение подробно на русском языке"):
        """
        Анализ изображения с помощью nanoLLaVA

        Args:
            image: PIL Image
            prompt: запрос для описания

        Returns:
            описание изображения
        """
        if self.model is None or self.tokenizer is None:
            return self._basic_description(image)

        try:
            # Формируем промпт в формате ChatML
            messages = [{"role": "user", "content": f"<image>\n{prompt}"}]

            text = self.tokenizer.apply_chat_template(messages, tokenize=False, add_generation_prompt=True)

            # Разбиваем по токену изображения
            text_chunks = [self.tokenizer(chunk).input_ids for chunk in text.split("<image>")]
            input_ids = torch.tensor(text_chunks[0] + [-200] + text_chunks[1], dtype=torch.long).unsqueeze(0)

            if self.device == "cuda":
                input_ids = input_ids.cuda()

            # Обрабатываем изображение
            image_tensor = self.model.process_images([image], self.model.config).to(dtype=self.model.dtype)
            if self.device == "cuda":
                image_tensor = image_tensor.cuda()

            # Генерируем ответ
            with torch.no_grad():
                output_ids = self.model.generate(
                    input_ids, images=image_tensor, max_new_tokens=200, use_cache=True, temperature=0.7, do_sample=True
                )[0]

            # Декодируем ответ
            answer = self.tokenizer.decode(output_ids[input_ids.shape[1] :], skip_special_tokens=True).strip()

            logger.info(f"📝 nanoLLaVA: {answer[:100]}...")
            return answer

        except Exception as e:
            logger.error(f"❌ Ошибка анализа изображения: {e}")
            return self._basic_description(image)

    def _basic_description(self, image):
        """Базовое описание без ML модели"""
        try:
            width, height = image.size
            mode = image.mode

            desc = f"Изображение размером {width}x{height} пикселей, {mode}"

            if mode == "L":
                desc += ", чёрно-белое"
            elif mode == "RGB":
                desc += ", цветное"
            elif mode == "RGBA":
                desc += ", цветное с прозрачностью"

            return desc

        except Exception:
            return "Не удалось получить информацию об изображении"

    def unload_model(self):
        """Выгрузка модели из памяти"""
        if self.model is not None:
            self.model = self.model.cpu()
            del self.model
            del self.tokenizer
            self.model = None
            self.tokenizer = None

            if torch.cuda.is_available():
                torch.cuda.empty_cache()
                torch.cuda.synchronize()

            import gc

            gc.collect()
            logger.info("🧹 nanoLLaVA выгружен из памяти")

    def is_model_loaded(self):
        """Проверка, загружена ли модель"""
        return self.model is not None and self.tokenizer is not None
