#!/usr/bin/env python3
# Путь: /mnt/ai_data/ai-agent/src/core/cognitive_loop.py
"""Основной когнитивный цикл Елены"""

import asyncio
from typing import Any, Dict, Optional, TYPE_CHECKING
from loguru import logger

# Используем TYPE_CHECKING, чтобы избежать циклического импорта ElenaAgent в рантайме
if TYPE_CHECKING:
    from src.core.bootstrap import ElenaAgent


class CognitiveLoop:
    """Когнитивный цикл: восприятие → планирование → действие → обучение"""

    def __init__(self, agent: "ElenaAgent") -> None:
        self.agent = agent
        self.running = False

    async def run(self) -> None:
        """Запуск основного цикла"""
        self.running = True
        logger.info("🔄 Когнитивный цикл запущен")

        while self.running:
            try:
                # 1. Восприятие (слух/зрение/контекст)
                perception = await self._perceive()

                # 2. Планирование - используем components!
                # Аннотируем как Any, чтобы mypy не ругался на отсутствие метода create_plan
                planner: Any = self.agent.components.get("planner")
                if planner and hasattr(planner, "create_plan"):
                    plan = planner.create_plan(perception)
                else:
                    plan = {"actions": []}
                    logger.warning("⚠️ Планировщик не доступен или не имеет метода create_plan")

                # 3. Исполнение
                result = await self._execute(plan)

                # 4. Обучение и самокритика
                self._learn(perception, plan, result)

                # 5. Очистка
                self._cleanup()

                # Небольшая пауза между циклами
                await asyncio.sleep(1)

            except Exception as e:
                logger.error(f"❌ Ошибка в cognitive loop: {e}")
                await asyncio.sleep(1)

    async def _perceive(self) -> Dict[str, Any]:
        """Восприятие мира"""
        perception: Dict[str, Any] = {"text": "", "image": None}

        # Получаем текст из аудио, если компонент доступен
        audio_comp: Any = self.agent.components.get("audio")
        if audio_comp:
            try:
                # Здесь должна быть реальная запись с микрофона
                # Пока используем заглушку для теста
                perception["text"] = "привет"
                logger.debug("🎤 Получен аудио вход")
            except Exception as e:
                logger.error(f"❌ Ошибка аудио: {e}")

        # Получаем изображение, если компонент доступен
        vision_comp: Any = self.agent.components.get("vision")
        if vision_comp:
            try:
                # Заглушка для зрения
                logger.debug("👁️ Получено видео")
            except Exception as e:
                logger.error(f"❌ Ошибка зрения: {e}")

        return perception

    async def _execute(self, plan: Dict[str, Any]) -> Dict[str, Any]:
        """Выполнение плана"""
        result: Dict[str, Any] = {"success": False, "data": None, "response": ""}

        # Получаем инструменты для выполнения
        conversation: Any = self.agent.components.get("conversation")

        if conversation and plan and plan.get("actions"):
            try:
                # Берём первое действие из плана
                actions = plan.get("actions", [])
                action = actions[0] if actions else None

                if action and action.get("type") == "converse":
                    # Генерируем ответ (Ollama/Qwen)
                    response = conversation.generate_response(action.get("text", ""))
                    result = {"success": True, "data": response, "response": response}

                    # Если есть голос, произносим ответ
                    voice: Any = self.agent.components.get("voice")
                    if voice and hasattr(voice, "speak"):
                        voice.speak(response)

            except Exception as e:
                logger.error(f"❌ Ошибка выполнения: {e}")
                result["error"] = str(e)

        return result

    def _learn(self, perception: Dict[str, Any], plan: Dict[str, Any], result: Dict[str, Any]) -> None:
        """Обучение на опыте"""
        # Получаем компонент самообучения
        self_improvement: Any = self.agent.components.get("self_improvement")
        memory: Any = self.agent.components.get("memory")

        if self_improvement and memory and result.get("success"):
            try:
                # Сохраняем успешный диалог в память
                if result.get("response"):
                    # Проверяем наличие метода store, чтобы не упасть в рантайме
                    if hasattr(memory, "store"):
                        memory.store(perception, plan, result)
                        logger.debug("📚 Опыт сохранён в память")
            except Exception as e:
                logger.error(f"❌ Ошибка обучения: {e}")

    def _cleanup(self) -> None:
        """Очистка временных файлов"""
        cleanup: Any = self.agent.components.get("cleanup")
        if cleanup:
            try:
                # Периодическая очистка (логика будет добавлена позже)
                pass
            except Exception as e:
                logger.error(f"❌ Ошибка очистки: {e}")

    def stop(self) -> None:
        """Остановка цикла"""
        self.running = False
        logger.info("⏹️ Когнитивный цикл остановлен")
