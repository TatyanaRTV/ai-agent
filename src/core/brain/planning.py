"""
Модуль планирования последовательности действий
"""

import logging
from typing import Dict, Any, List, Optional
from datetime import datetime
import asyncio

logger = logging.getLogger(__name__)

class PlanningModule:
    """Модуль планирования действий агента"""
    
    def __init__(self, memory_manager, tool_executor):
        self.memory = memory_manager
        self.tools = tool_executor
        self.current_plan = None
        self.plan_history = []
        
    async def create_plan(self, goal: str, context: Dict[str, Any] = None) -> Dict[str, Any]:
        """Создание плана для достижения цели"""
        logger.info(f"🎯 Создание плана для цели: {goal}")
        
        if context is None:
            context = {}
            
        plan = {
            "goal": goal,
            "created_at": datetime.now().isoformat(),
            "context": context,
            "steps": [],
            "priority": "medium",
            "estimated_duration": None,
            "status": "created",
            "progress": 0.0
        }
        
        # Генерация шагов плана
        steps = await self._generate_steps(goal, context)
        plan["steps"] = steps
        
        # Оценка продолжительности
        plan["estimated_duration"] = self._estimate_duration(steps)
        
        # Определение приоритета
        plan["priority"] = self._determine_priority(goal, context)
        
        self.current_plan = plan
        self.plan_history.append(plan)
        
        logger.info(f"✅ План создан: {len(steps)} шагов, продолжительность: {plan['estimated_duration']}")
        return plan
        
    async def execute_plan(self, plan: Dict[str, Any]) -> Dict[str, Any]:
        """Выполнение плана"""
        logger.info(f"🚀 Начинаю выполнение плана: {plan['goal']}")
        
        plan["status"] = "executing"
        plan["started_at"] = datetime.now().isoformat()
        results = []
        
        try:
            for i, step in enumerate(plan["steps"]):
                logger.info(f"📋 Шаг {i+1}/{len(plan['steps'])}: {step['action']}")
                
                # Выполнение шага
                result = await self._execute_step(step, plan["context"])
                
                # Обновление прогресса
                plan["progress"] = (i + 1) / len(plan["steps"])
                
                # Сохранение результата
                step["result"] = result
                step["completed_at"] = datetime.now().isoformat()
                
                results.append(result)
                
                # Проверка на необходимость остановки
                if not result.get("success", False):
                    logger.warning(f"Шаг {i+1} завершился с ошибкой: {result.get('error')}")
                    
                    # Продолжать или прервать зависит от критичности шага
                    if step.get("critical", False):
                        plan["status"] = "failed"
                        plan["error"] = f"Критический шаг {i+1} завершился с ошибкой"
                        break
                        
                # Небольшая пауза между шагами
                await asyncio.sleep(0.1)
                
            # Завершение плана
            if plan["status"] != "failed":
                plan["status"] = "completed"
                plan["completed_at"] = datetime.now().isoformat()
                plan["progress"] = 1.0
                
                logger.info(f"✅ План выполнен успешно: {plan['goal']}")
                
        except Exception as e:
            plan["status"] = "failed"
            plan["error"] = str(e)
            logger.error(f"❌ Ошибка выполнения плана: {e}")
            
        plan["results"] = results
        return plan
        
    async def _generate_steps(self, goal: str, context: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Генерация шагов для достижения цели"""
        steps = []
        
        # Простая логика генерации шагов на основе цели
        goal_lower = goal.lower()
        
        if "погод" in goal_lower:
            steps = await self._generate_weather_steps(goal, context)
        elif "документ" in goal_lower or "файл" in goal_lower:
            steps = await self._generate_document_steps(goal, context)
        elif "изображен" in goal_lower or "картин" in goal_lower:
            steps = await self._generate_image_steps(goal, context)
        elif "найди" in goal_lower or "поиск" in goal_lower:
            steps = await self._generate_search_steps(goal, context)
        else:
            # Общий план для неизвестных целей
            steps = [
                {
                    "id": 1,
                    "action": "Анализ запроса пользователя",
                    "tool": "reasoning",
                    "parameters": {"query": goal},
                    "critical": True
                },
                {
                    "id": 2,
                    "action": "Поиск информации в памяти",
                    "tool": "memory_search",
                    "parameters": {"query": goal},
                    "critical": False
                },
                {
                    "id": 3,
                    "action": "Формирование ответа",
                    "tool": "response_generator",
                    "parameters": {"context": context},
                    "critical": True
                }
            ]
            
        return steps
        
    async def _generate_weather_steps(self, goal: str, context: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Генерация шагов для запроса погоды"""
        return [
            {
                "id": 1,
                "action": "Извлечение локации из запроса",
                "tool": "location_extractor",
                "parameters": {"text": goal},
                "critical": True
            },
            {
                "id": 2,
                "action": "Поиск информации о погоде",
                "tool": "weather_lookup",
                "parameters": {"location": "{step1_result}"},
                "critical": True
            },
            {
                "id": 3,
                "action": "Форматирование ответа о погоде",
                "tool": "response_formatter",
                "parameters": {"weather_data": "{step2_result}"},
                "critical": False
            }
        ]
        
    async def _generate_document_steps(self, goal: str, context: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Генерация шагов для работы с документами"""
        return [
            {
                "id": 1,
                "action": "Определение типа документа",
                "tool": "document_type_detector",
                "parameters": {"goal": goal},
                "critical": True
            },
            {
                "id": 2,
                "action": "Поиск документа в файловой системе",
                "tool": "file_search",
                "parameters": {"query": goal},
                "critical": True
            },
            {
                "id": 3,
                "action": "Чтение и анализ документа",
                "tool": "document_reader",
                "parameters": {"file_path": "{step2_result}"},
                "critical": True
            },
            {
                "id": 4,
                "action": "Формирование сводки по документу",
                "tool": "summarizer",
                "parameters": {"content": "{step3_result}"},
                "critical": False
            }
        ]
        
    async def _generate_image_steps(self, goal: str, context: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Генерация шагов для работы с изображениями"""
        return [
            {
                "id": 1,
                "action": "Определение типа задачи с изображением",
                "tool": "image_task_detector",
                "parameters": {"goal": goal},
                "critical": True
            },
            {
                "id": 2,
                "action": "Поиск изображения",
                "tool": "image_search",
                "parameters": {"query": goal},
                "critical": True
            },
            {
                "id": 3,
                "action": "Анализ изображения",
                "tool": "image_analyzer",
                "parameters": {"image_path": "{step2_result}"},
                "critical": True
            },
            {
                "id": 4,
                "action": "Описание изображения",
                "tool": "image_describer",
                "parameters": {"analysis": "{step3_result}"},
                "critical": False
            }
        ]
        
    async def _generate_search_steps(self, goal: str, context: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Генерация шагов для поиска информации"""
        return [
            {
                "id": 1,
                "action": "Анализ поискового запроса",
                "tool": "query_analyzer",
                "parameters": {"query": goal},
                "critical": True
            },
            {
                "id": 2,
                "action": "Поиск в локальной памяти",
                "tool": "memory_search",
                "parameters": {"query": goal},
                "critical": False
            },
            {
                "id": 3,
                "action": "Поиск в интернете (если нужно)",
                "tool": "web_search",
                "parameters": {"query": goal},
                "critical": False,
                "condition": "not step2_result"
            },
            {
                "id": 4,
                "action": "Синтез результатов поиска",
                "tool": "result_synthesizer",
                "parameters": {"results": ["{step2_result}", "{step3_result}"]},
                "critical": True
            }
        ]
        
    def _estimate_duration(self, steps: List[Dict[str, Any]]) -> str:
        """Оценка продолжительности выполнения плана"""
        # Простая эвристика: каждый шаг занимает 1-5 секунд
        total_seconds = len(steps) * 3
        
        if total_seconds < 60:
            return f"{total_seconds} секунд"
        else:
            minutes = total_seconds // 60
            seconds = total_seconds % 60
            return f"{minutes} минут {seconds} секунд"
            
    def _determine_priority(self, goal: str, context: Dict[str, Any]) -> str:
        """Определение приоритета плана"""
        goal_lower = goal.lower()
        
        # Ключевые слова для высокого приоритета
        high_priority_words = ['срочно', 'быстро', 'немедленно', 'важно', 'критично']
        
        if any(word in goal_lower for word in high_priority_words):
            return "high"
            
        # Ключевые слова для низкого приоритета
        low_priority_words = ['когда-нибудь', 'не срочно', 'потом', 'в свободное время']
        
        if any(word in goal_lower for word in low_priority_words):
            return "low"
            
        return "medium"
        
    async def _execute_step(self, step: Dict[str, Any], context: Dict[str, Any]) -> Dict[str, Any]:
        """Выполнение одного шага плана"""
        result = {
            "step_id": step["id"],
            "action": step["action"],
            "success": False,
            "started_at": datetime.now().isoformat(),
            "completed_at": None,
            "output": None,
            "error": None
        }
        
        try:
            # Получение инструмента
            tool_name = step.get("tool")
            if not tool_name:
                result["error"] = "Инструмент не указан"
                return result
                
            # Получение параметров
            parameters = step.get("parameters", {})
            
            # Замена переменных из предыдущих шагов
            parameters = self._resolve_parameters(parameters, context)
            
            # Выполнение инструмента
            tool_result = await self.tools.execute_tool(tool_name, parameters)
            
            result["success"] = tool_result.get("success", False)
            result["output"] = tool_result.get("output")
            result["error"] = tool_result.get("error")
            
        except Exception as e:
            result["error"] = str(e)
            logger.error(f"Ошибка выполнения шага {step['id']}: {e}")
            
        result["completed_at"] = datetime.now().isoformat()
        return result
        
    def _resolve_parameters(self, parameters: Dict[str, Any], context: Dict[str, Any]) -> Dict[str, Any]:
        """Замена переменных в параметрах на реальные значения"""
        # В данной упрощенной версии просто возвращаем параметры как есть
        # В полной версии здесь должна быть логика подстановки значений из предыдущих шагов
        return parameters
        
    async def adjust_plan(self, plan: Dict[str, Any], feedback: Dict[str, Any]) -> Dict[str, Any]:
        """Корректировка плана на основе обратной связи"""
        logger.info(f"🔄 Корректировка плана на основе обратной связи")
        
        # Анализ обратной связи
        if feedback.get("success") is False:
            # Добавление шагов для исправления ошибок
            correction_steps = await self._generate_correction_steps(feedback)
            plan["steps"].extend(correction_steps)
            
            # Обновление оценки продолжительности
            plan["estimated_duration"] = self._estimate_duration(plan["steps"])
            
        return plan
        
    async def _generate_correction_steps(self, feedback: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Генерация шагов для исправления ошибок"""
        error = feedback.get("error", "")
        error_lower = error.lower()
        
        steps = []
        
        if "не найден" in error_lower or "не существует" in error_lower:
            steps.append({
                "id": 999,  # Высокий ID для корректировочных шагов
                "action": "Альтернативный поиск информации",
                "tool": "alternative_search",
                "parameters": {"original_error": error},
                "critical": False
            })
            
        elif "ошибка доступа" in error_lower or "permission denied" in error_lower:
            steps.append({
                "id": 999,
                "action": "Проверка прав доступа",
                "tool": "permission_checker",
                "parameters": {"error": error},
                "critical": True
            })
            
        elif "недостаточно памяти" in error_lower or "memory" in error_lower:
            steps.append({
                "id": 999,
                "action": "Очистка временной памяти",
                "tool": "memory_cleaner",
                "parameters": {},
                "critical": True
            })
            
        return steps
        
    def get_current_progress(self) -> float:
        """Получение текущего прогресса выполнения плана"""
        if self.current_plan:
            return self.current_plan.get("progress", 0.0)
        return 0.0
        
    def get_plan_history(self, limit: int = 10) -> List[Dict[str, Any]]:
        """Получение истории планов"""
        return self.plan_history[-limit:] if self.plan_history else []