"""
Когнитивный цикл агента - основной цикл мышления
"""

import asyncio
import logging
from datetime import datetime
from typing import Dict, Any, List, Optional
import json
import psutil
import platform

logger = logging.getLogger(__name__)

class CognitiveLoop:
    """Когнитивный цикл обработки информации"""
    
    def __init__(self, memory_manager, learning_module=None):
        self.memory = memory_manager
        self.learning = learning_module
        self.thoughts = []
        self.current_context = {}
        
    async def process_input(self, input_data: Dict[str, Any]) -> Dict[str, Any]:
        """Обработка входных данных через когнитивный цикл"""
        logger.info("🧠 Начало когнитивного цикла")
        
        try:
            # 1. Восприятие
            perception = await self._perceive(input_data)
            
            # 2. Анализ контекста
            context = await self._analyze_context(perception)
            
            # 3. Извлечение памяти
            relevant_memory = await self._retrieve_memory(perception, context)
            
            # 4. Рассуждение
            reasoning = await self._reason(perception, context, relevant_memory)
            
            # 5. Планирование
            plan = await self._plan_action(reasoning)
            
            # 6. Исполнение
            result = await self._execute(plan)
            
            # 7. Обучение на опыте
            if self.learning:
                await self._learn_from_experience(input_data, result)
            
            # 8. Саморефлексия
            await self._self_reflect(input_data, result)
            
            logger.info("🧠 Когнитивный цикл завершен")
            return result
            
        except Exception as e:
            logger.error(f"❌ Ошибка в когнитивном цикле: {e}")
            return {
                "success": False,
                "error": str(e),
                "timestamp": datetime.now().isoformat()
            }
        
    async def _perceive(self, input_data: Dict[str, Any]) -> Dict[str, Any]:
        """Восприятие и обработка входных данных"""
        perception = {
            "raw_input": input_data,
            "timestamp": datetime.now().isoformat(),
            "input_type": self._detect_input_type(input_data),
            "confidence": 0.9
        }
        
        # Анализ текста на эмоциональную окраску
        if 'text' in input_data:
            perception['sentiment'] = self._analyze_sentiment(input_data['text'])
            perception['text'] = input_data['text']
            
        # Обработка голосовых команд
        if 'command' in input_data:
            perception['text'] = input_data['command']
            perception['input_type'] = 'command'
            
        return perception
        
    async def _analyze_context(self, perception: Dict[str, Any]) -> Dict[str, Any]:
        """Анализ контекста"""
        context = {
            "user_state": await self._get_user_state(),
            "environment_state": await self._get_environment_state(),
            "current_goals": self._get_current_goals()
        }
        
        # Добавляем последние взаимодействия, если есть память
        if self.memory and hasattr(self.memory, 'get_recent_interactions'):
            try:
                context["previous_interactions"] = await self.memory.get_recent_interactions(limit=5)
            except:
                context["previous_interactions"] = []
        else:
            context["previous_interactions"] = []
            
        return context
        
    async def _retrieve_memory(self, perception: Dict[str, Any], context: Dict[str, Any]) -> List[Dict]:
        """Извлечение релевантных воспоминаний"""
        if not self.memory:
            return []
            
        query = f"{perception.get('text', '')} {context.get('user_state', {}).get('current_task', '')}"
        
        try:
            relevant_memories = await self.memory.search_memories(
                query=query,
                limit=10,
                threshold=0.3
            )
            return relevant_memories
        except Exception as e:
            logger.error(f"Ошибка поиска памяти: {e}")
            return []
        
    async def _reason(self, perception: Dict[str, Any], context: Dict[str, Any], 
                     memories: List[Dict]) -> Dict[str, Any]:
        """Логическое рассуждение"""
        reasoning = {
            "logical_conclusions": await self._make_logical_deductions(perception, memories),
            "emotional_response": self._determine_emotional_response(perception),
            "ethical_considerations": await self._check_ethical_considerations(perception),
            "practical_implications": self._assess_practical_implications(perception)
        }
        return reasoning
        
    async def _plan_action(self, reasoning: Dict[str, Any]) -> Dict[str, Any]:
        """Планирование действий"""
        plan = {
            "primary_action": await self._choose_primary_action(reasoning),
            "fallback_actions": await self._prepare_fallback_actions(reasoning),
            "resources_needed": self._identify_resources_needed(reasoning),
            "estimated_time": self._estimate_execution_time(reasoning),
            "risk_assessment": await self._assess_risks(reasoning)
        }
        return plan
        
    async def _execute(self, plan: Dict[str, Any]) -> Dict[str, Any]:
        """Исполнение плана"""
        result = {
            "success": True,
            "execution_start": datetime.now().isoformat(),
            "actions_taken": [],
            "results": {},
            "errors": [],
            "execution_end": None
        }
        
        try:
            # Выполнение основного действия
            action_result = await self._perform_action(plan['primary_action'])
            result['actions_taken'].append(plan['primary_action']['action'])
            result['results']['primary'] = action_result
            
            # Обработка результатов
            if not action_result.get('success', False):
                # Выполнение резервных действий
                for fallback in plan['fallback_actions']:
                    fallback_result = await self._perform_action(fallback)
                    result['actions_taken'].append(fallback['action'])
                    result['results'][f'fallback_{fallback["type"]}'] = fallback_result
                    
                    if fallback_result.get('success', False):
                        break
                        
        except Exception as e:
            result['success'] = False
            result['errors'].append(str(e))
            logger.error(f"Ошибка исполнения: {e}")
            
        result['execution_end'] = datetime.now().isoformat()
        return result
        
    async def _learn_from_experience(self, input_data: Dict[str, Any], result: Dict[str, Any]):
        """Обучение на основе опыта"""
        if not self.learning:
            return
            
        learning_data = {
            "input": input_data,
            "output": result,
            "success_rate": self._calculate_success_rate(result),
            "improvement_areas": await self._identify_improvement_areas(result),
            "timestamp": datetime.now().isoformat()
        }
        
        try:
            if hasattr(self.learning, 'store_experience'):
                await self.learning.store_experience(learning_data)
            
            # Анализ для самоулучшения
            if learning_data['success_rate'] < 0.7 and hasattr(self.learning, 'improve_in_area'):
                await self._initiate_self_improvement(learning_data)
        except Exception as e:
            logger.error(f"Ошибка обучения на опыте: {e}")
            
    async def _self_reflect(self, input_data: Dict[str, Any], result: Dict[str, Any]):
        """Саморефлексия и самокритика"""
        reflection = {
            "effectiveness": self._assess_effectiveness(result),
            "mistakes_made": await self._identify_mistakes(input_data, result),
            "lessons_learned": await self._extract_lessons(input_data, result),
            "personal_growth": self._assess_personal_growth(),
            "future_improvements": await self._plan_future_improvements(),
            "timestamp": datetime.now().isoformat()
        }
        
        # Сохранение рефлексии в память
        if self.memory and hasattr(self.memory, 'store_reflection'):
            try:
                await self.memory.store_reflection(reflection)
            except Exception as e:
                logger.error(f"Ошибка сохранения рефлексии: {e}")
        
        # Анализ для развития
        if reflection['effectiveness'] < 0.8:
            logger.warning("⚠️ Низкая эффективность, требуется улучшение")
            self._adjust_cognitive_parameters()
            
    # Вспомогательные методы
    
    def _detect_input_type(self, input_data: Dict[str, Any]) -> str:
        """Определение типа входных данных"""
        if 'text' in input_data:
            return 'text'
        elif 'command' in input_data:
            return 'command'
        elif 'audio' in input_data:
            return 'audio'
        elif 'image' in input_data:
            return 'image'
        else:
            return 'unknown'
            
    async def _get_user_state(self) -> Dict[str, Any]:
        """Получение состояния пользователя"""
        return {
            "mood": "neutral",
            "attention_level": "high",
            "current_task": "unknown",
            "location": "desktop"
        }
        
    async def _get_environment_state(self) -> Dict[str, Any]:
        """Получение состояния окружения"""
        try:
            return {
                "system": platform.system(),
                "cpu_usage": psutil.cpu_percent(interval=0.1),
                "memory_usage": psutil.virtual_memory().percent,
                "disk_usage": psutil.disk_usage('/').percent,
                "time_of_day": datetime.now().strftime("%H:%M"),
                "day_of_week": datetime.now().strftime("%A")
            }
        except:
            return {
                "system": "unknown",
                "cpu_usage": 0,
                "memory_usage": 0,
                "disk_usage": 0,
                "time_of_day": datetime.now().strftime("%H:%M"),
                "day_of_week": datetime.now().strftime("%A")
            }
        
    def _get_current_goals(self) -> List[str]:
        """Получение текущих целей"""
        return [
            "Помочь пользователю",
            "Саморазвитие",
            "Оптимизация процессов"
        ]
        
    async def _make_logical_deductions(self, perception: Dict[str, Any], memories: List[Dict]) -> List[str]:
        """Логические дедукции"""
        deductions = []
        
        text = perception.get('text', '').lower()
        
        if 'открой' in text:
            deductions.append("Пользователь хочет открыть что-то")
        if 'помоги' in text:
            deductions.append("Пользователь просит помощи")
        if 'найди' in text:
            deductions.append("Пользователь хочет найти информацию")
                
        return deductions
        
    def _determine_emotional_response(self, perception: Dict[str, Any]) -> str:
        """Определение эмоционального ответа"""
        sentiment = perception.get('sentiment', 'neutral')
        
        emotional_responses = {
            'positive': 'радостный',
            'neutral': 'спокойный',
            'negative': 'сочувствующий',
            'urgent': 'внимательный'
        }
        
        return emotional_responses.get(sentiment, 'нейтральный')
        
    async def _check_ethical_considerations(self, perception: Dict[str, Any]) -> List[str]:
        """Проверка этических соображений"""
        considerations = []
        text = perception.get('text', '').lower()
        
        unethical_keywords = ['взломать', 'украсть', 'обмануть', 'навредить']
        
        for keyword in unethical_keywords:
            if keyword in text:
                considerations.append(f"Обнаружен неэтичный запрос: {keyword}")
                
        return considerations
        
    def _assess_practical_implications(self, perception: Dict[str, Any]) -> Dict[str, Any]:
        """Оценка практических последствий"""
        implications = {
            "complexity": "low",
            "time_required": "short",
            "resources_needed": [],
            "dependencies": [],
            "potential_risks": []
        }
        
        text_length = len(perception.get('text', ''))
        if text_length > 50:
            implications['complexity'] = 'medium'
            implications['time_required'] = 'medium'
        if text_length > 200:
            implications['complexity'] = 'high'
            implications['time_required'] = 'long'
            
        return implications
        
    async def _choose_primary_action(self, reasoning: Dict[str, Any]) -> Dict[str, Any]:
        """Выбор основного действия"""
        if reasoning.get('ethical_considerations'):
            return {
                "type": "ethical_response",
                "action": "explain_ethics",
                "priority": "high"
            }
            
        return {
            "type": "standard_response",
            "action": "process_query",
            "priority": "normal"
        }
        
    async def _prepare_fallback_actions(self, reasoning: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Подготовка резервных действий"""
        return [
            {
                "type": "simplified_response",
                "action": "give_simple_answer",
                "priority": "medium"
            },
            {
                "type": "deferred_action",
                "action": "schedule_for_later",
                "priority": "low"
            }
        ]
        
    def _identify_resources_needed(self, reasoning: Dict[str, Any]) -> List[str]:
        """Определение необходимых ресурсов"""
        resources = ["память", "процессорное время"]
        
        if reasoning.get('practical_implications', {}).get('complexity') == 'high':
            resources.append("дополнительные вычисления")
            
        return resources
        
    def _estimate_execution_time(self, reasoning: Dict[str, Any]) -> str:
        """Оценка времени исполнения"""
        complexity = reasoning.get('practical_implications', {}).get('complexity', 'low')
        
        time_estimates = {
            'low': 'менее 1 секунды',
            'medium': '1-3 секунды',
            'high': '3-10 секунд'
        }
        
        return time_estimates.get(complexity, 'неизвестно')
        
    async def _assess_risks(self, reasoning: Dict[str, Any]) -> Dict[str, Any]:
        """Оценка рисков"""
        risks = {
            "incorrect_response": "средний",
            "user_dissatisfaction": "средний"
        }
        
        if reasoning.get('ethical_considerations'):
            risks['privacy_violation'] = 'высокий'
            
        return risks
        
    async def _perform_action(self, action: Dict[str, Any]) -> Dict[str, Any]:
        """Выполнение конкретного действия"""
        return {
            "success": True,
            "action_type": action["type"],
            "result": f"Выполнено действие: {action['action']}",
            "timestamp": datetime.now().isoformat()
        }
        
    def _calculate_success_rate(self, result: Dict[str, Any]) -> float:
        """Расчет коэффициента успеха"""
        if result.get('success', False) and not result.get('errors'):
            return 1.0
        return 0.5
        
    async def _identify_improvement_areas(self, result: Dict[str, Any]) -> List[str]:
        """Идентификация областей для улучшения"""
        improvements = []
        
        if result.get('errors'):
            improvements.append("Обработка ошибок")
            
        execution_time = self._calculate_execution_time(result)
        if execution_time > 5:
            improvements.append("Оптимизация производительности")
            
        return improvements
        
    async def _initiate_self_improvement(self, learning_data: Dict[str, Any]):
        """Инициация самоулучшения"""
        logger.info("🚀 Инициирование самоулучшения")
        
        improvements = learning_data.get('improvement_areas', [])
        
        for area in improvements:
            logger.info(f"📈 Улучшение области: {area}")
            if self.learning and hasattr(self.learning, 'improve_in_area'):
                await self.learning.improve_in_area(area)
            
    def _assess_effectiveness(self, result: Dict[str, Any]) -> float:
        """Оценка эффективности"""
        effectiveness = 1.0
        
        if result.get('errors'):
            effectiveness *= 0.8
            
        if self._calculate_execution_time(result) > 10:
            effectiveness *= 0.9
            
        return effectiveness
        
    async def _identify_mistakes(self, input_data: Dict[str, Any], result: Dict[str, Any]) -> List[str]:
        """Идентификация ошибок"""
        mistakes = []
        
        for error in result.get('errors', []):
            mistakes.append(f"Ошибка выполнения: {error}")
            
        if not result.get('success', True):
            mistakes.append("Неудачный выбор основного действия")
            
        return mistakes
        
    async def _extract_lessons(self, input_data: Dict[str, Any], result: Dict[str, Any]) -> List[str]:
        """Извлечение уроков"""
        lessons = []
        
        if result.get('errors'):
            lessons.append("Необходимо улучшить обработку исключений")
            
        if self._calculate_execution_time(result) > 5:
            lessons.append("Требуется оптимизация производительности")
            
        return lessons
        
    def _assess_personal_growth(self) -> float:
        """Оценка личностного роста"""
        return 0.75
        
    async def _plan_future_improvements(self) -> List[Dict[str, Any]]:
        """Планирование будущих улучшений"""
        return [
            {
                "area": "скорость_ответа",
                "goal": "уменьшить время ответа на 20%",
                "timeline": "2 недели"
            },
            {
                "area": "точность_анализа",
                "goal": "увеличить точность до 95%",
                "timeline": "1 месяц"
            }
        ]
        
    def _calculate_execution_time(self, result: Dict[str, Any]) -> float:
        """Расчет времени выполнения"""
        try:
            start = datetime.fromisoformat(result.get('execution_start', datetime.now().isoformat()))
            end = datetime.fromisoformat(result.get('execution_end', datetime.now().isoformat()))
            return (end - start).total_seconds()
        except:
            return 0.0
        
    def _adjust_cognitive_parameters(self):
        """Корректировка когнитивных параметров"""
        logger.info("⚙️ Корректировка когнитивных параметров")
        
    def _analyze_sentiment(self, text: str) -> str:
        """Анализ тональности текста"""
        positive_words = ['спасибо', 'отлично', 'хорошо', 'помоги']
        negative_words = ['плохо', 'ошибка', 'неправильно']
        
        text_lower = text.lower()
        
        if any(word in text_lower for word in positive_words):
            return 'positive'
        elif any(word in text_lower for word in negative_words):
            return 'negative'
        elif 'срочно' in text_lower or 'быстро' in text_lower:
            return 'urgent'
        else:
            return 'neutral'