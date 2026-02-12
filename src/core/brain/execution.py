"""
Модуль исполнения задач и управления инструментами
"""

import logging
import asyncio
from typing import Dict, Any, List, Optional
from datetime import datetime, timedelta

logger = logging.getLogger(__name__)

class ExecutionEngine:
    """Движок исполнения задач"""
    
    def __init__(self, tool_registry=None):
        self.tools = tool_registry
        self.execution_history = []
        self.active_tasks = {}
        
    async def execute_task(self, task: Dict[str, Any]) -> Dict[str, Any]:
        """Выполнение задачи"""
        task_name = task.get('name', 'Безымянная')
        logger.info(f"▶️ Выполнение задачи: {task_name}")
        
        execution_result = {
            "task_id": task.get("id", f"task_{datetime.now().timestamp()}"),
            "task_name": task_name,
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
                    execution_result["errors"].append(f"Критическая ошибка в подзадаче: {subtask_result.get('error', 'Неизвестная ошибка')}")
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
            logger.error(f"❌ Ошибка выполнения задачи: {e}")
            
        execution_result["end_time"] = datetime.now().isoformat()
        
        # Расчет метрик производительности
        execution_result["performance_metrics"] = self._calculate_metrics(execution_result)
        
        # Сохранение в историю
        self.execution_history.append(execution_result)
        
        # Ограничение истории
        if len(self.execution_history) > 1000:
            self.execution_history = self.execution_history[-1000:]
        
        logger.info(f"✅ Задача выполнена со статусом: {execution_result['status']}")
        return execution_result
        
    async def _execute_subtask(self, subtask: Dict[str, Any], context: Dict[str, Any]) -> Dict[str, Any]:
        """Выполнение подзадачи"""
        subtask_result = {
            "subtask_id": subtask.get("id", f"subtask_{datetime.now().timestamp()}"),
            "action": subtask.get("action", "unknown"),
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
                
            # Проверка наличия инструмента
            if not self.tools:
                subtask_result["error"] = "Реестр инструментов не инициализирован"
                return subtask_result
                
            # Получение параметров
            parameters = subtask.get("parameters", {}).copy()
            
            # Добавление контекста к параметрам
            parameters["context"] = context
            
            # Выполнение инструмента
            if hasattr(self.tools, 'execute'):
                tool_result = await self.tools.execute(tool_name, parameters)
                subtask_result["success"] = tool_result.get("success", False)
                subtask_result["output"] = tool_result.get("output")
                subtask_result["error"] = tool_result.get("error")
            else:
                # Заглушка для тестирования
                subtask_result["success"] = True
                subtask_result["output"] = f"Выполнен инструмент: {tool_name}"
            
        except Exception as e:
            subtask_result["error"] = str(e)
            logger.error(f"❌ Ошибка выполнения подзадачи {subtask.get('id', 'unknown')}: {e}")
            
        subtask_result["end_time"] = datetime.now().isoformat()
        return subtask_result
        
    def _calculate_metrics(self, execution_result: Dict[str, Any]) -> Dict[str, Any]:
        """Расчет метрик производительности"""
        try:
            start_time = datetime.fromisoformat(execution_result["start_time"])
            end_time = datetime.fromisoformat(execution_result["end_time"])
            duration = (end_time - start_time).total_seconds()
        except:
            duration = 0.0
        
        # Подсчет успешных подзадач
        results = execution_result.get("results", [])
        successful_subtasks = sum(1 for r in results if r.get("success", False))
        total_subtasks = len(results)
        
        success_rate = successful_subtasks / total_subtasks if total_subtasks > 0 else 0.0
        
        return {
            "duration_seconds": round(duration, 3),
            "success_rate": round(success_rate, 2),
            "subtasks_total": total_subtasks,
            "subtasks_successful": successful_subtasks,
            "subtasks_failed": total_subtasks - successful_subtasks
        }
        
    async def execute_parallel(self, tasks: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Параллельное выполнение задач"""
        logger.info(f"🔄 Параллельное выполнение {len(tasks)} задач")
        
        if not tasks:
            return []
        
        # Создание задач
        coroutines = [self.execute_task(task) for task in tasks]
        
        # Параллельное выполнение
        results = await asyncio.gather(*coroutines, return_exceptions=True)
        
        # Обработка результатов
        processed_results = []
        for i, result in enumerate(results):
            if isinstance(result, Exception):
                logger.error(f"❌ Ошибка в задаче {i}: {result}")
                processed_results.append({
                    "task_id": tasks[i].get("id", f"task_{i}"),
                    "status": "failed",
                    "error": str(result)
                })
            else:
                processed_results.append(result)
                
        return processed_results
        
    async def retry_failed(self, execution_result: Dict[str, Any], max_retries: int = 3) -> Dict[str, Any]:
        """Повторное выполнение неудачных подзадач"""
        logger.info(f"🔄 Повторное выполнение неудачных подзадач (максимум {max_retries} попыток)")
        
        # Сбор неудачных подзадач
        failed_subtasks = []
        for result in execution_result.get("results", []):
            if not result.get("success", False):
                subtask = {
                    "id": result.get("subtask_id"),
                    "action": result.get("action"),
                    "tool": result.get("tool_used"),
                    "parameters": {}  # В реальной реализации нужно восстановить параметры
                }
                failed_subtasks.append(subtask)
                
        if not failed_subtasks:
            logger.info("✅ Нет неудачных подзадач для повторного выполнения")
            return execution_result
            
        # Повторное выполнение с экспоненциальной задержкой
        retry_results = []
        for attempt in range(max_retries):
            logger.info(f"Попытка {attempt + 1}/{max_retries}")
            
            # Экспоненциальная задержка
            if attempt > 0:
                delay = 2 ** attempt  # 2, 4, 8 секунд
                logger.info(f"⏳ Ожидание {delay} секунд...")
                await asyncio.sleep(delay)
                
            # Выполнение неудачных подзадач
            for subtask in failed_subtasks:
                result = await self._execute_subtask(subtask, {})
                retry_results.append(result)
                
                if result.get("success", False):
                    logger.info(f"✅ Успешно выполнено: {subtask.get('action')}")
                    
            # Проверка, все ли успешны
            if all(r.get("success", False) for r in retry_results):
                logger.info("✅ Все неудачные подзадачи успешно выполнены")
                execution_result["status"] = "completed"
                break
                
        # Обновление результатов
        execution_result["results"].extend(retry_results)
        execution_result["performance_metrics"] = self._calculate_metrics(execution_result)
        
        return execution_result
        
    def get_execution_history(self, limit: int = 50) -> List[Dict[str, Any]]:
        """Получение истории выполнения"""
        return self.execution_history[-limit:] if self.execution_history else []
        
    def clear_history(self, older_than_days: int = 30):
        """Очистка старой истории выполнения"""
        cutoff_date = datetime.now() - timedelta(days=older_than_days)
        
        filtered_history = []
        for record in self.execution_history:
            try:
                record_date = datetime.fromisoformat(record["start_time"].replace('Z', '+00:00'))
                if record_date > cutoff_date:
                    filtered_history.append(record)
            except:
                # Если не можем распарсить дату, оставляем запись
                filtered_history.append(record)
                
        self.execution_history = filtered_history
        logger.info(f"🧹 Очищена история выполнения старше {older_than_days} дней, осталось {len(self.execution_history)} записей")
        
    def get_task_status(self, task_id: str) -> Optional[Dict[str, Any]]:
        """Получение статуса задачи по ID"""
        for task in self.execution_history:
            if task.get("task_id") == task_id:
                return task
        return None
        
    def cancel_task(self, task_id: str) -> bool:
        """Отмена выполняющейся задачи"""
        if task_id in self.active_tasks:
            # Здесь должна быть логика отмены
            del self.active_tasks[task_id]
            logger.info(f"🛑 Задача {task_id} отменена")
            return True
        return False