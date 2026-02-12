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
    
    def __init__(self, memory_manager=None, tool_executor=None):
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
            "id": f"plan_{datetime.now().timestamp()}",
            "goal": goal,
            "created_at": datetime.now().isoformat(),
            "context": context,
            "steps": [],
            "priority": "medium",
            "estimated_duration": None,
            "status": "created",
            "progress": 0.0,
            "results": [],
            "error": None
        }
        
        try:
            # Генерация шагов плана
            steps = await self._generate_steps(goal, context)
            plan["steps"] = steps
            
            # Оценка продолжительности
            plan["estimated_duration"] = self._estimate_duration(steps)
            
            # Определение приоритета
            plan["priority"] = self._determine_priority(goal, context)
            
            self.current_plan = plan
            self.plan_history.append(plan)
            
            # Ограничение истории
            if len(self.plan_history) > 100:
                self.plan_history = self.plan_history[-100:]
            
            logger.info(f"✅ План создан: {len(steps)} шагов")
            
        except Exception as e:
            plan["status"] = "failed"
            plan["error"] = str(e)
            logger.error(f"❌ Ошибка создания плана: {e}")
            
        return plan
        
    async def execute_plan(self, plan: Dict[str, Any]) -> Dict[str, Any]:
        """Выполнение плана"""
        logger.info(f"🚀 Начинаю выполнение плана: {plan.get('goal', 'Без цели')}")
        
        plan["status"] = "executing"
        plan["started_at"] = datetime.now().isoformat()
        results = []
        
        try:
            steps = plan.get("steps", [])
            for i, step in enumerate(steps):
                logger.info(f"📋 Шаг {i+1}/{len(steps)}: {step.get('action', 'Действие')}")
                
                # Выполнение шага
                result = await self._execute_step(step, plan.get("context", {}))
                
                # Обновление прогресса
                plan["progress"] = (i + 1) / len(steps) if steps else 0.0
                
                # Сохранение результата
                step["result"] = result
                step["completed_at"] = datetime.now().isoformat()
                
                results.append(result)
                
                # Проверка на необходимость остановки
                if not result.get("success", False):
                    logger.warning(f"⚠️ Шаг {i+1} завершился с ошибкой: {result.get('error', 'Неизвестная ошибка')}")
                    
                    if step.get("critical", False):
                        plan["status"] = "failed"
                        plan["error"] = f"Критический шаг {i+1} завершился с ошибкой"
                        break
                        
                await asyncio.sleep(0.1)
                
            # Завершение плана
            if plan.get("status") != "failed":
                plan["status"] = "completed"
                plan["completed_at"] = datetime.now().isoformat()
                plan["progress"] = 1.0
                
                logger.info(f"✅ План выполнен успешно")
                
        except Exception as e:
            plan["status"] = "failed"
            plan["error"] = str(e)
            logger.error(f"❌ Ошибка выполнения плана: {e}")
            
        plan["results"] = results
        return plan
        
    async def _generate_steps(self, goal: str, context: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Генерация шагов для достижения цели"""
        steps = []
        
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
                "action": "Формирование ответа о погоде",
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
                "action": "Поиск документа",
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
                "action": "Поиск в интернете",
                "tool": "web_search",
                "parameters": {"query": goal},
                "critical": False
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
        if not steps:
            return "0 секунд"
            
        total_seconds = len(steps) * 3
        
        if total_seconds < 60:
            return f"{total_seconds} секунд"
        else:
            minutes = total_seconds // 60
            seconds = total_seconds % 60
            return f"{minutes} мин {seconds} сек"
            
    def _determine_priority(self, goal: str, context: Dict[str, Any]) -> str:
        """Определение приоритета плана"""
        goal_lower = goal.lower()
        
        high_priority_words = ['срочно', 'быстро', 'немедленно', 'важно', 'критично']
        if any(word in goal_lower for word in high_priority_words):
            return "high"
            
        low_priority_words = ['когда-нибудь', 'не срочно', 'потом', 'в свободное время']
        if any(word in goal_lower for word in low_priority_words):
            return "low"
            
        return "medium"
        
    async def _execute_step(self, step: Dict[str, Any], context: Dict[str, Any]) -> Dict[str, Any]:
        """Выполнение одного шага плана"""
        result = {
            "step_id": step.get("id", 0),
            "action": step.get("action", "unknown"),
            "success": False,
            "started_at": datetime.now().isoformat(),
            "completed_at": None,
            "output": None,
            "error": None
        }
        
        try:
            if not self.tools:
                # Заглушка для тестирования без инструментов
                result["success"] = True
                result["output"] = f"Выполнено действие: {step.get('action')}"
                result["completed_at"] = datetime.now().isoformat()
                return result
                
            tool_name = step.get("tool")
            if not tool_name:
                result["error"] = "Инструмент не указан"
                result["completed_at"] = datetime.now().isoformat()
                return result
                
            parameters = step.get("parameters", {})
            
            if hasattr(self.tools, 'execute_tool'):
                tool_result = await self.tools.execute_tool(tool_name, parameters)
                result["success"] = tool_result.get("success", False)
                result["output"] = tool_result.get("output")
                result["error"] = tool_result.get("error")
            else:
                # Заглушка для тестирования
                result["success"] = True
                result["output"] = f"Выполнен инструмент: {tool_name}"
                
        except Exception as e:
            result["error"] = str(e)
            logger.error(f"❌ Ошибка выполнения шага {step.get('id', 'unknown')}: {e}")
            
        result["completed_at"] = datetime.now().isoformat()
        return result
        
    async def adjust_plan(self, plan: Dict[str, Any], feedback: Dict[str, Any]) -> Dict[str, Any]:
        """Корректировка плана на основе обратной связи"""
        logger.info(f"🔄 Корректировка плана на основе обратной связи")
        
        if feedback.get("success") is False:
            correction_steps = await self._generate_correction_steps(feedback)
            if correction_steps:
                plan["steps"].extend(correction_steps)
                plan["estimated_duration"] = self._estimate_duration(plan.get("steps", []))
            
        return plan
        
    async def _generate_correction_steps(self, feedback: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Генерация шагов для исправления ошибок"""
        error = feedback.get("error", "")
        error_lower = error.lower()
        
        steps = []
        
        if "не найден" in error_lower or "не существует" in error_lower:
            steps.append({
                "id": 999,
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
        
    def get_plan_by_id(self, plan_id: str) -> Optional[Dict[str, Any]]:
        """Получение плана по ID"""
        for plan in self.plan_history:
            if plan.get("id") == plan_id:
                return plan
        return None
        
    def cancel_current_plan(self) -> bool:
        """Отмена текущего плана"""
        if self.current_plan:
            self.current_plan["status"] = "cancelled"
            self.current_plan["completed_at"] = datetime.now().isoformat()
            logger.info(f"🛑 План отменён: {self.current_plan.get('id')}")
            self.current_plan = None
            return True
        return False