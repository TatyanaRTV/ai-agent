"""
Модуль исполнения задач и управления инструментами
"""

import logging
import asyncio
from typing import Dict, Any, List, Optional
from datetime import datetime

logger = logging.getLogger(__name__)

class ExecutionEngine:
    """Движок исполнения задач"""
    
    def __init__(self, tool_registry):
        self.tools = tool_registry
        self.execution_history = []
        self.active_tasks = {}
        
    async def execute_task(self, task: Dict[str, Any]) -> Dict[str, Any]:
        """Выполнение задачи"""
        logger.info(f"▶️ Выполнение задачи: {task.get('name', 'Безымянная')}")
        
        execution_result = {
            "task_id": task.get("id"),
            "task_name": task.get("name"),
            "status": "pending",
            "start_time": datetime.now().isoformat(),
            "end_time": None,
            "results": [],
            "errors": [],
            "performance_metrics": {}
        }
        
        try:
            execution_result["status"] = "running"
            
            # Выполнение подзадач
            subtasks = task.get("subtasks", [])
            
            for subtask in subtasks:
                subtask_result = await self._execute_subtask(subtask, task.get("context", {}))
                execution_result["results"].append(subtask_result)
                
                # Проверка на критическую ошибку
                if not subtask_result.get("success", False) and subtask.get("critical", False):
                    execution_result["status"] = "failed"
                    execution_result["errors"].append(f"Критическая ошибка в подзадаче: {subtask_result.get('error')}")
                    break
                    
            # Определение финального статуса
            if execution_result["status"] != "failed":
                if all(r.get("success", False) for r in execution_result["results"]):
                    execution_result["status"] = "completed"
                else:
                    execution_result["status"] = "partial"
                    
        except Exception as e:
            execution_result["status"] = "failed"
            execution_result["errors"].append(str(e))
            logger.error(f"Ошибка выполнения задачи: {e}")
            
        execution_result["end_time"] = datetime.now().isoformat()
        
        # Расчет метрик производительности
        execution_result["performance_metrics"] = self._calculate_metrics(execution_result)
        
        # Сохранение в историю
        self.execution_history.append(execution_result)
        
        logger.info(f"✅ Задача выполнена со статусом: {execution_result['status']}")
        return execution_result
        
    async def _execute_subtask(self, subtask: Dict[str, Any], context: Dict[str, Any]) -> Dict[str, Any]:
        """Выполнение подзадачи"""
        subtask_result = {
            "subtask_id": subtask.get("id"),
            "action": subtask.get("action"),
            "success": False,
            "start_time": datetime.now().isoformat(),
            "end_time": None,
            "output": None,
            "error": None,
            "tool_used": subtask.get("tool")
        }
        
        try:
            # Получение инструмента
            tool_name = subtask.get("tool")
            if not tool_name:
                subtask_result["error"] = "Инструмент не указан"
                return subtask_result
                
            # Получение параметров
            parameters = subtask.get("parameters", {})
            
            # Добавление контекста к параметрам
            parameters["context"] = context
            
            # Выполнение инструмента
            tool_result = await self.tools.execute(tool_name, parameters)
            
            subtask_result["success"] = tool_result.get("success", False)
            subtask_result["output"] = tool_result.get("output")
            subtask_result["error"] = tool_result.get("error")
            
        except Exception as e:
            subtask_result["error"] = str(e)
            logger.error(f"Ошибка выполнения подзадачи {subtask.get('id')}: {e}")
            
        subtask_result["end_time"] = datetime.now().isoformat()
        return subtask_result
        
    def _calculate_metrics(self, execution_result: Dict[str, Any]) -> Dict[str, Any]:
        """Расчет метрик производительности"""
        start_time = datetime.fromisoformat(execution_result["start_time"])
        end_time = datetime.fromisoformat(execution_result["end_time"])
        
        duration = (end_time - start_time).total_seconds()
        
        # Подсчет успешных подзадач
        successful_subtasks = sum(1 for r in execution_result["results"] if r.get("success", False))
        total_subtasks = len(execution_result["results"])
        
        success_rate = successful_subtasks / total_subtasks if total_subtasks > 0 else 0.0
        
        return {
            "duration_seconds": duration,
            "success_rate": success_rate,
            "subtasks_total": total_subtasks,
            "subtasks_successful": successful_subtasks,
            "subtasks_failed": total_subtasks - successful_subtasks
        }
        
    async def execute_parallel(self, tasks: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Параллельное выполнение задач"""
        logger.info(f"🔄 Параллельное выполнение {len(tasks)} задач")
        
        # Создание задач
        coroutines = [self.execute_task(task) for task in tasks]
        
        # Параллельное выполнение
        results = await asyncio.gather(*coroutines, return_exceptions=True)
        
        # Обработка результатов
        processed_results = []
        for i, result in enumerate(results):
            if isinstance(result, Exception):
                logger.error(f"Ошибка в задаче {i}: {result}")
                processed_results.append({
                    "task_id": tasks[i].get("id"),
                    "status": "failed",
                    "error": str(result)
                })
            else:
                processed_results.append(result)
                
        return processed_results
        
    async def retry_failed(self, execution_result: Dict[str, Any], max_retries: int = 3) -> Dict[str, Any]:
        """Повторное выполнение неудачных подзадач"""
        logger.info(f"🔄 Повторное выполнение неудачных подзадач (максимум {max_retries} попыток)")
        
        original_task = {
            "id": execution_result["task_id"],
            "name": execution_result["task_name"],
            "subtasks": []
        }
        
        # Сбор неудачных подзадач
        failed_subtasks = []
        for result in execution_result["results"]:
            if not result.get("success", False):
                # Восстановление описания подзадачи из истории
                subtask = {
                    "id": result["subtask_id"],
                    "action": result["action"],
                    "tool": result["tool_used"]
                }
                failed_subtasks.append(subtask)
                
        if not failed_subtasks:
            logger.info("✅ Нет неудачных подзадач для повторного выполнения")
            return execution_result
            
        # Повторное выполнение с экспоненциальной задержкой
        for attempt in range(max_retries):
            logger.info(f"Попытка {attempt + 1}/{max_retries}")
            
            # Экспоненциальная задержка
            if attempt > 0:
                delay = 2 ** attempt  # 2, 4, 8 секунд
                await asyncio.sleep(delay)
                
            # Выполнение неудачных подзадач
            for subtask in failed_subtasks:
                # Здесь должна быть логика повторного выполнения
                # В упрощенной версии просто логируем
                logger.info(f"Повторное выполнение подзадачи: {subtask['action']}")
                
            # Проверка успешности
            # В реальной реализации здесь должна быть проверка результатов
            
        return execution_result
        
    def get_execution_history(self, limit: int = 50) -> List[Dict[str, Any]]:
        """Получение истории выполнения"""
        return self.execution_history[-limit:] if self.execution_history else []
        
    def clear_history(self, older_than_days: int = 30):
        """Очистка старой истории выполнения"""
        cutoff_date = datetime.now().replace(day=datetime.now().day - older_than_days)
        
        filtered_history = []
        for record in self.execution_history:
            record_date = datetime.fromisoformat(record["start_time"].replace('Z', '+00:00'))
            if record_date > cutoff_date:
                filtered_history.append(record)
                
        self.execution_history = filtered_history
        logger.info(f"🧹 Очищена история выполнения старше {older_than_days} дней")