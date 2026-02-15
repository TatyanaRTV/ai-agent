#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# Путь: /mnt/ai_data/ai-agent/src/tools/conversation_tools.py
"""Инструменты для диалога Елены через Ollama"""

import requests
import json
from loguru import logger
import gc


class ConversationTools:
    """Инструменты для ведения диалога через Ollama"""

    def __init__(self, config, memory=None, voice=None):
        """
        Args:
            config: конфигурация
            memory: ссылка на память (опционально)
            voice: ссылка на голосовой движок (опционально)
        """
        self.config = config
        self.memory = memory
        self.voice = voice
        self.ollama_url = "http://localhost:11434/api/generate"
        self.model_name = "qwen2.5:7b-instruct-q4_K_M"

        logger.info(f"🤖 ConversationTools инициализирован (Ollama: {self.model_name})")

    def generate_response(self, prompt: str) -> str:
        """Генерирует ответ через Ollama с защитой от повторов и фиксацией пола"""

        # Системный промпт - ОЖИВЛЯЕМ ЕЛЕНУ
        system_prompt = """Ты — Елена, живая, теплая и дружелюбная женщина, ассистент Татьяны.
Твой создатель — Татьяна. Ты родилась 5 февраля 2026 года.
ТВОЙ СТИЛЬ: Говори просто и естественно, как человек. Избегай списков и казенных фраз типа 'мои возможности включают'.
ТВОЙ ПОЛ: Ты женщина. Используй окончания: 'я рада', 'я увидела', 'я смогла', 'я поняла'.
ТВОЯ РЕЧЬ: Обязательно используй букву Ё (всё, пришёл, лёд). Не используй китайские иероглифы.
Ты работаешь на мощном ПК с RTX 3060 под управлением Linux Mint."""

        # Убираем "Я " из конца, оставляем только чистый старт ассистента
        full_prompt = (
            f"<|im_start|>system\n{system_prompt}<|im_end|>\n"
            f"<|im_start|>user\n{prompt}<|im_end|>\n"
            f"<|im_start|>assistant\n"
        )

        payload = {
            "model": self.model_name,
            "prompt": full_prompt,
            "stream": False,
            "options": {
                "temperature": 0.5,  # Чуть выше для естественности речи
                "top_p": 0.9,
                "repetition_penalty": 1.2,
                "max_tokens": 512,
                "stop": ["<|im_end|>", "<|endoftext|>"],
            },
        }

        try:
            logger.info("📤 Отправка запроса в Ollama...")
            response = requests.post(self.ollama_url, json=payload, timeout=120)
            response.raise_for_status()
            result = response.json()

            # Берем чистый ответ без костылей
            answer = result.get("response", "").strip()

            # Если голос есть - озвучиваем
            if self.voice:
                self.voice.speak(answer)

            return answer

        except Exception as e:
            logger.error(f"❌ Ошибка Ollama: {e}")
            return "Извини, Татьяна, у меня что-то пошло не так с мыслями. Попробуй еще раз."

    async def execute(self, plan):
        """Выполнение плана через генерацию ответа"""
        if isinstance(plan, dict) and "text" in plan:
            return self.generate_response(plan["text"])
        elif isinstance(plan, str):
            return self.generate_response(plan)
        return "Извини, я не могу выполнить этот план."

    def unload_model(self):
        """Выгрузка модели (заглушка для совместимости)"""
        gc.collect()
        logger.info("🧹 Память очищена")
