#!/usr/bin/env python3
# Путь: /mnt/ai_data/ai-agent/src/planning/planner_stage2.py
"""Планировщик второго уровня для Елены"""

from loguru import logger
import json

class Planner:
    """Планировщик действий Елены"""
    
    def __init__(self, config):
        self.config = config
        self.current_plan = None
        self.plan_history = []
        logger.info("📋 Planner инициализирован")
    
    def create_plan(self, perception):
        """
        Создаёт план действий на основе восприятия
        
        Args:
            perception: словарь с данными восприятия (текст, изображение и т.д.)
            
        Returns:
            план действий
        """
        plan = {
            'id': len(self.plan_history) + 1,
            'actions': [],
            'context': perception
        }
        
        # Анализируем, что пришло
        if perception.get("text"):
            text = perception["text"].lower()
            
            # Определяем тип запроса
            if any(word in text for word in ['привет', 'здравствуй', 'добрый']):
                plan['actions'].append({
                    'type': 'greet',
                    'text': perception["text"]
                })
            elif any(word in text for word in ['пока', 'до свидания', 'до встречи']):
                plan['actions'].append({
                    'type': 'farewell',
                    'text': perception["text"]
                })
            elif any(word in text for word in ['помоги', 'сделай', 'выполни']):
                plan['actions'].append({
                    'type': 'execute_task',
                    'text': perception["text"]
                })
            else:
                plan['actions'].append({
                    'type': 'converse',
                    'text': perception["text"]
                })
        
        if perception.get("image"):
            plan['actions'].append({
                'type': 'analyze_image',
                'image': perception["image"]
            })
        
        # Если ничего не распознано
        if not plan['actions']:
            plan['actions'].append({
                'type': 'idle',
                'message': 'Ожидание команд'
            })
        
        # Сохраняем план в историю
        self.plan_history.append(plan)
        self.current_plan = plan
        
        logger.debug(f"📝 Создан план: {json.dumps(plan, default=str, ensure_ascii=False)}")
        return plan
    
    def get_next_action(self, plan=None):
        """Получить следующее действие из плана"""
        if plan is None:
            plan = self.current_plan
        
        if plan and plan['actions']:
            return plan['actions'].pop(0)
        return None
    
    def evaluate_plan(self, plan, result):
        """Оценить выполнение плана для самообучения"""
        success = result.get('success', False)
        self.plan_history[-1]['evaluation'] = {
            'success': success,
            'result': result
        }
        
        if success:
            logger.info(f"✅ План {plan['id']} выполнен успешно")
        else:
            logger.warning(f"⚠️ План {plan['id']} выполнен с ошибками")