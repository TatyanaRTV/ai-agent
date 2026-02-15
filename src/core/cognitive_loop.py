#!/usr/bin/env python3
# Путь: /mnt/ai_data/ai-agent/src/core/cognitive_loop.py
"""Основной когнитивный цикл Елены"""

import asyncio
from loguru import logger


class CognitiveLoop:
    """Когнитивный цикл: восприятие → планирование → действие → обучение"""
    
    def __init__(self, agent):
        self.agent = agent
        self.running = False
    
    async def run(self):
        """Запуск основного цикла"""
        self.running = True
        logger.info("🔄 Когнитивный цикл запущен")
        
        while self.running:
            try:
                # 1. Восприятие (слух/зрение/контекст)
                perception = await self._perceive()
                
                # 2. Планирование - используем components!
                planner = self.agent.components.get('planner')
                if planner:
                    plan = planner.create_plan(perception)
                else:
                    plan = {"actions": []}
                    logger.warning("⚠️ Планировщик не доступен")
                
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
    
    async def _perceive(self):
        """Восприятие мира"""
        perception = {"text": "", "image": None}
        
        # Получаем текст из аудио, если компонент доступен
        audio_comp = self.agent.components.get('audio')
        if audio_comp:
            try:
                # Здесь должна быть реальная запись с микрофона
                # Пока используем заглушку для теста
                perception["text"] = "привет"
                logger.debug("🎤 Получен аудио вход")
            except Exception as e:
                logger.error(f"❌ Ошибка аудио: {e}")
        
        # Получаем изображение, если компонент доступен
        vision_comp = self.agent.components.get('vision')
        if vision_comp:
            try:
                # Заглушка для зрения
                logger.debug("👁️ Получено видео")
            except Exception as e:
                logger.error(f"❌ Ошибка зрения: {e}")
        
        return perception
    
    async def _execute(self, plan):
        """Выполнение плана"""
        result = {"success": False, "data": None, "response": ""}
        
        # Получаем инструменты для выполнения
        conversation = self.agent.components.get('conversation')
        
        if conversation and plan and plan.get('actions'):
            try:
                # Берём первое действие из плана
                action = plan['actions'][0] if plan['actions'] else None
                
                if action and action.get('type') == 'converse':
                    response = conversation.generate_response(action.get('text', ''))
                    result = {
                        "success": True, 
                        "data": response,
                        "response": response
                    }
                    
                    # Если есть голос, произносим ответ
                    voice = self.agent.components.get('voice')
                    if voice:
                        voice.speak(response)
                        
            except Exception as e:
                logger.error(f"❌ Ошибка выполнения: {e}")
                result["error"] = str(e)
        
        return result
    
    def _learn(self, perception, plan, result):
        """Обучение на опыте"""
        # Получаем компонент самообучения
        self_improvement = self.agent.components.get('self_improvement')
        memory = self.agent.components.get('memory')
        
        if self_improvement and memory and result.get('success'):
            try:
                # Сохраняем успешный диалог в память
                if result.get('response'):
                    memory.store(perception, plan, result)
                    logger.debug("📚 Опыт сохранён в память")
            except Exception as e:
                logger.error(f"❌ Ошибка обучения: {e}")
    
    def _cleanup(self):
        """Очистка временных файлов"""
        cleanup = self.agent.components.get('cleanup')
        if cleanup:
            try:
                # Периодическая очистка
                pass
            except Exception as e:
                logger.error(f"❌ Ошибка очистки: {e}")
    
    def stop(self):
        """Остановка цикла"""
        self.running = False
        logger.info("⏹️ Когнитивный цикл остановлен")