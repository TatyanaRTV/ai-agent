# critics.py
"""
Компонент самокритики и самоанализа
"""

import logging
from datetime import datetime
from typing import Dict, List, Any
import json

logger = logging.getLogger(__name__)

class SelfCritic:
    """Система самокритики и оценки производительности"""
    
    def __init__(self, memory_manager):
        self.memory = memory_manager
        self.metrics = {}
        self.improvement_history = []
        
    async def analyze_performance(self, interaction_data: Dict[str, Any]) -> Dict[str, Any]:
        """Анализ производительности после взаимодействия"""
        logger.info("🔍 Анализ производительности...")
        
        analysis = {
            "timestamp": datetime.now().isoformat(),
            "interaction_id": interaction_data.get("id"),
            "metrics": {},
            "strengths": [],
            "weaknesses": [],
            "recommendations": []
        }
        
        # Расчет метрик
        analysis["metrics"] = await self._calculate_metrics(interaction_data)
        
        # Идентификация сильных сторон
        analysis["strengths"] = await self._identify_strengths(analysis["metrics"])
        
        # Идентификация слабых сторон
        analysis["weaknesses"] = await self._identify_weaknesses(analysis["metrics"])
        
        # Рекомендации по улучшению
        analysis["recommendations"] = await self._generate_recommendations(
            analysis["strengths"], 
            analysis["weaknesses"]
        )
        
        # Сохранение анализа
        await self.memory.store_performance_analysis(analysis)
        
        return analysis
        
    async def _calculate_metrics(self, interaction_data: Dict[str, Any]) -> Dict[str, float]:
        """Расчет метрик производительности"""
        metrics = {
            "response_time": self._calculate_response_time(interaction_data),
            "accuracy": await self._calculate_accuracy(interaction_data),
            "user_satisfaction": self._estimate_user_satisfaction(interaction_data),
            "task_completion": self._assess_task_completion(interaction_data),
            "efficiency": self._calculate_efficiency(interaction_data),
            "consistency": await self._assess_consistency(interaction_data)
        }
        
        # Обновление истории метрик
        self._update_metrics_history(metrics)
        
        return metrics
        
    async def identify_improvement_areas(self) -> List[Dict[str, Any]]:
        """Идентификация областей для улучшения"""
        logger.info("🎯 Идентификация областей для улучшения...")
        
        areas = []
        
        # Анализ последних метрик
        recent_metrics = await self._get_recent_metrics(limit=50)
        
        if recent_metrics:
            # Области с низкими показателями
            low_performance_areas = self._find_low_performance_areas(recent_metrics)
            
            for area in low_performance_areas:
                improvement_plan = await self._create_improvement_plan(area)
                areas.append({
                    "area": area,
                    "current_score": recent_metrics[-1].get(area, 0),
                    "target_score": improvement_plan["target"],
                    "plan": improvement_plan
                })
                
        # Области для расширения возможностей
        expansion_areas = await self._identify_expansion_areas()
        areas.extend(expansion_areas)
        
        return areas
        
    async def implement_improvements(self, improvement_plan: Dict[str, Any]) -> Dict[str, Any]:
        """Реализация улучшений"""
        logger.info(f"⚙️ Реализация улучшений для области: {improvement_plan['area']}")
        
        results = {
            "improvement_area": improvement_plan["area"],
            "implementation_start": datetime.now().isoformat(),
            "actions_taken": [],
            "results": {},
            "new_capabilities": [],
            "implementation_end": None
        }
        
        try:
            # 1. Анализ текущего состояния
            current_state = await self._analyze_current_state(improvement_plan["area"])
            results["current_state"] = current_state
            
            # 2. Применение улучшений
            for action in improvement_plan.get("actions", []):
                action_result = await self._execute_improvement_action(action)
                results["actions_taken"].append(action)
                results["results"][action["type"]] = action_result
                
                if action_result.get("success"):
                    if "new_capability" in action_result:
                        results["new_capabilities"].append(action_result["new_capability"])
                        
            # 3. Валидация улучшений
            validation_result = await self._validate_improvements(
                improvement_plan["area"], 
                improvement_plan["target_score"]
            )
            results["validation"] = validation_result
            
            # 4. Сохранение результатов
            await self._save_improvement_results(results)
            
        except Exception as e:
            results["error"] = str(e)
            logger.error(f"Ошибка реализации улучшений: {e}")
            
        results["implementation_end"] = datetime.now().isoformat()
        
        # Запись в историю улучшений
        self.improvement_history.append({
            "timestamp": datetime.now().isoformat(),
            "improvement_area": improvement_plan["area"],
            "results": results
        })
        
        return results
        
    def _calculate_response_time(self, interaction_data: Dict[str, Any]) -> float:
        """Расчет времени ответа"""
        start = datetime.fromisoformat(interaction_data.get("start_time", datetime.now().isoformat()))
        end = datetime.fromisoformat(interaction_data.get("end_time", datetime.now().isoformat()))
        return (end - start).total_seconds()
        
    async def _calculate_accuracy(self, interaction_data: Dict[str, Any]) -> float:
        """Расчет точности ответа"""
        # Здесь должна быть логика оценки точности
        # На основе сравнения ожидаемого и фактического результата
        expected = interaction_data.get("expected_outcome")
        actual = interaction_data.get("actual_outcome")
        
        if expected and actual:
            # Простая оценка совпадения
            if str(expected).lower() in str(actual).lower():
                return 1.0
            else:
                return 0.5
                
        return 0.7  # Значение по умолчанию
        
    def _estimate_user_satisfaction(self, interaction_data: Dict[str, Any]) -> float:
        """Оценка удовлетворенности пользователя"""
        # На основе анализа текста ответа пользователя
        user_feedback = interaction_data.get("user_feedback", "")
        user_feedback_lower = user_feedback.lower()
        
        positive_indicators = ['спасибо', 'отлично', 'хорошо', 'помогло']
        negative_indicators = ['плохо', 'неправильно', 'ошибка', 'непонятно']
        
        positive_count = sum(1 for word in positive_indicators if word in user_feedback_lower)
        negative_count = sum(1 for word in negative_indicators if word in user_feedback_lower)
        
        if positive_count > 0 and negative_count == 0:
            return 1.0
        elif positive_count == 0 and negative_count > 0:
            return 0.3
        else:
            return 0.7
            
    def _assess_task_completion(self, interaction_data: Dict[str, Any]) -> float:
        """Оценка завершенности задачи"""
        task_status = interaction_data.get("task_status", "unknown")
        
        completion_scores = {
            "completed": 1.0,
            "partially_completed": 0.7,
            "failed": 0.3,
            "in_progress": 0.5,
            "unknown": 0.5
        }
        
        return completion_scores.get(task_status, 0.5)
        
    def _calculate_efficiency(self, interaction_data: Dict[str, Any]) -> float:
        """Расчет эффективности"""
        response_time = self._calculate_response_time(interaction_data)
        
        # Чем быстрее и точнее, тем эффективнее
        accuracy = self._estimate_user_satisfaction(interaction_data)  # Временная метрика
        
        if response_time < 2:  # менее 2 секунд
            time_score = 1.0
        elif response_time < 5:
            time_score = 0.8
        elif response_time < 10:
            time_score = 0.6
        else:
            time_score = 0.4
            
        efficiency = (time_score + accuracy) / 2
        return efficiency
        
    async def _assess_consistency(self, interaction_data: Dict[str, Any]) -> float:
        """Оценка консистентности"""
        # Сравнение с предыдущими подобными взаимодействиями
        similar_interactions = await self.memory.find_similar_interactions(
            interaction_data,
            limit=5
        )
        
        if not similar_interactions:
            return 0.8  # Невозможно оценить
            
        # Проверка согласованности ответов
        current_response = interaction_data.get("response", "")
        consistency_scores = []
        
        for interaction in similar_interactions:
            previous_response = interaction.get("response", "")
            
            # Простая проверка схожести
            current_words = set(str(current_response).lower().split())
            previous_words = set(str(previous_response).lower().split())
            
            common_words = current_words.intersection(previous_words)
            similarity = len(common_words) / max(len(current_words), len(previous_words))
            
            consistency_scores.append(similarity)
            
        average_consistency = sum(consistency_scores) / len(consistency_scores)
        return average_consistency
        
    def _update_metrics_history(self, metrics: Dict[str, float]):
        """Обновление истории метрик"""
        timestamp = datetime.now().isoformat()
        self.metrics[timestamp] = metrics
        
        # Сохранение только последних 1000 записей
        if len(self.metrics) > 1000:
            oldest_key = sorted(self.metrics.keys())[0]
            del self.metrics[oldest_key]
            
    async def _get_recent_metrics(self, limit: int = 50) -> List[Dict[str, float]]:
        """Получение последних метрик"""
        sorted_keys = sorted(self.metrics.keys(), reverse=True)[:limit]
        return [self.metrics[key] for key in sorted_keys]
        
    def _find_low_performance_areas(self, metrics_history: List[Dict[str, float]]) -> List[str]:
        """Поиск областей с низкой производительностью"""
        if not metrics_history:
            return []
            
        # Анализ средних значений
        latest_metrics = metrics_history[0]
        areas = list(latest_metrics.keys())
        
        low_performance_areas = []
        
        for area in areas:
            values = [metrics.get(area, 0) for metrics in metrics_history if area in metrics]
            if values:
                average = sum(values) / len(values)
                
                if average < 0.7:  # Порог низкой производительности
                    low_performance_areas.append(area)
                    
        return low_performance_areas
        
    async def _create_improvement_plan(self, area: str) -> Dict[str, Any]:
        """Создание плана улучшения для конкретной области"""
        
        improvement_plans = {
            "response_time": {
                "target_score": 0.9,
                "actions": [
                    {
                        "type": "optimization",
                        "description": "Оптимизация алгоритмов обработки",
                        "priority": "high"
                    },
                    {
                        "type": "caching",
                        "description": "Внедрение кэширования результатов",
                        "priority": "medium"
                    },
                    {
                        "type": "parallelization",
                        "description": "Параллельная обработка запросов",
                        "priority": "medium"
                    }
                ]
            },
            "accuracy": {
                "target_score": 0.95,
                "actions": [
                    {
                        "type": "training",
                        "description": "Дополнительное обучение на данных",
                        "priority": "high"
                    },
                    {
                        "type": "verification",
                        "description": "Внедрение системы верификации ответов",
                        "priority": "medium"
                    },
                    {
                        "type": "feedback_loop",
                        "description": "Улучшение цикла обратной связи",
                        "priority": "high"
                    }
                ]
            },
            "user_satisfaction": {
                "target_score": 0.85,
                "actions": [
                    {
                        "type": "personalization",
                        "description": "Персонализация ответов",
                        "priority": "high"
                    },
                    {
                        "type": "emotional_intelligence",
                        "description": "Улучшение эмоционального интеллекта",
                        "priority": "medium"
                    },
                    {
                        "type": "clarity",
                        "description": "Улучшение ясности ответов",
                        "priority": "medium"
                    }
                ]
            }
        }
        
        return improvement_plans.get(area, {
            "target_score": 0.8,
            "actions": [
                {
                    "type": "general_improvement",
                    "description": "Общее улучшение производительности",
                    "priority": "medium"
                }
            ]
        })
        
    async def _identify_expansion_areas(self) -> List[Dict[str, Any]]:
        """Идентификация областей для расширения возможностей"""
        return [
            {
                "area": "multimodal_understanding",
                "description": "Улучшение понимания мультимодальных данных",
                "potential_impact": "high"
            },
            {
                "area": "proactive_assistance",
                "description": "Развитие проактивной помощи",
                "potential_impact": "medium"
            },
            {
                "area": "creative_generation",
                "description": "Развитие творческих способностей",
                "potential_impact": "medium"
            }
        ]
        
    async def _analyze_current_state(self, area: str) -> Dict[str, Any]:
        """Анализ текущего состояния области"""
        recent_metrics = await self._get_recent_metrics(limit=20)
        
        if not recent_metrics:
            return {"status": "unknown", "score": 0.5}
            
        # Извлечение метрик для конкретной области
        area_metrics = [metrics.get(area, 0.5) for metrics in recent_metrics if area in metrics]
        
        if not area_metrics:
            return {"status": "unknown", "score": 0.5}
            
        average = sum(area_metrics) / len(area_metrics)
        
        status = "good" if average >= 0.8 else "needs_improvement" if average >= 0.6 else "poor"
        
        return {
            "status": status,
            "score": average,
            "trend": self._calculate_trend(area_metrics),
            "volatility": self._calculate_volatility(area_metrics)
        }
        
    async def _execute_improvement_action(self, action: Dict[str, Any]) -> Dict[str, Any]:
        """Выполнение действия по улучшению"""
        logger.info(f"Выполнение действия улучшения: {action['type']}")
        
        # Здесь должна быть конкретная реализация каждого типа действий
        action_handlers = {
            "optimization": self._execute_optimization,
            "caching": self._implement_caching,
            "training": self._execute_training,
            "personalization": self._implement_personalization
        }
        
        handler = action_handlers.get(action["type"], self._execute_general_improvement)
        return await handler(action)
        
    async def _validate_improvements(self, area: str, target_score: float) -> Dict[str, Any]:
        """Валидация улучшений"""
        # Повторный расчет метрик после улучшений
        current_state = await self._analyze_current_state(area)
        
        validation = {
            "area": area,
            "previous_score": current_state.get("score", 0.5),
            "target_score": target_score,
            "improvement_achieved": current_state.get("score", 0.5) >= target_score * 0.9,
            "validation_method": "comparative_analysis",
            "confidence": 0.8
        }
        
        return validation
        
    async def _save_improvement_results(self, results: Dict[str, Any]):
        """Сохранение результатов улучшений"""
        # Сохранение в память
        await self.memory.store_improvement_results(results)
        
        # Логирование
        logger.info(f"Результаты улучшений сохранены для области: {results['improvement_area']}")
        
    def _calculate_trend(self, values: List[float]) -> str:
        """Расчет тренда значений"""
        if len(values) < 2:
            return "stable"
            
        first_half = values[:len(values)//2]
        second_half = values[len(values)//2:]
        
        avg_first = sum(first_half) / len(first_half)
        avg_second = sum(second_half) / len(second_half)
        
        if avg_second > avg_first * 1.1:
            return "improving"
        elif avg_second < avg_first * 0.9:
            return "declining"
        else:
            return "stable"
            
    def _calculate_volatility(self, values: List[float]) -> float:
        """Расчет волатильности значений"""
        if len(values) < 2:
            return 0.0
            
        mean = sum(values) / len(values)
        variance = sum((x - mean) ** 2 for x in values) / len(values)
        return variance ** 0.5
        
    # Методы обработчиков действий улучшения
        
    async def _execute_optimization(self, action: Dict[str, Any]) -> Dict[str, Any]:
        """Выполнение оптимизации"""
        # Здесь должна быть конкретная логика оптимизации
        return {
            "success": True,
            "action_type": "optimization",
            "result": "Алгоритмы обработки оптимизированы",
            "performance_gain": "estimated 15%",
            "new_capability": "optimized_processing"
        }
        
    async def _implement_caching(self, action: Dict[str, Any]) -> Dict[str, Any]:
        """Внедрение кэширования"""
        return {
            "success": True,
            "action_type": "caching",
            "result": "Система кэширования внедрена",
            "performance_gain": "estimated 25% для повторяющихся запросов",
            "new_capability": "response_caching"
        }
        
    async def _execute_training(self, action: Dict[str, Any]) -> Dict[str, Any]:
        """Выполнение дополнительного обучения"""
        return {
            "success": True,
            "action_type": "training",
            "result": "Дополнительное обучение завершено",
            "performance_gain": "estimated 10% точности",
            "new_capability": "enhanced_accuracy"
        }
        
    async def _implement_personalization(self, action: Dict[str, Any]) -> Dict[str, Any]:
        """Внедрение персонализации"""
        return {
            "success": True,
            "action_type": "personalization",
            "result": "Система персонализации внедрена",
            "performance_gain": "estimated 20% удовлетворенности пользователей",
            "new_capability": "personalized_responses"
        }
        
    async def _execute_general_improvement(self, action: Dict[str, Any]) -> Dict[str, Any]:
        """Общее улучшение"""
        return {
            "success": True,
            "action_type": action["type"],
            "result": "Общее улучшение выполнено",
            "performance_gain": "estimated 5%",
            "new_capability": "general_enhancement"
        }
        
    async def _identify_strengths(self, metrics: Dict[str, float]) -> List[str]:
        """Идентификация сильных сторон"""
        strengths = []
        
        for metric, value in metrics.items():
            if value >= 0.8:
                strengths.append(metric)
                
        return strengths
        
    async def _identify_weaknesses(self, metrics: Dict[str, float]) -> List[str]:
        """Идентификация слабых сторон"""
        weaknesses = []
        
        for metric, value in metrics.items():
            if value <= 0.6:
                weaknesses.append(metric)
                
        return weaknesses
        
    async def _generate_recommendations(self, strengths: List[str], weaknesses: List[str]) -> List[str]:
        """Генерация рекомендаций по улучшению"""
        recommendations = []
        
        # Рекомендации для слабых сторон
        for weakness in weaknesses:
            if weakness == "response_time":
                recommendations.append("Оптимизировать алгоритмы обработки запросов")
            elif weakness == "accuracy":
                recommendations.append("Провести дополнительное обучение на данных")
            elif weakness == "user_satisfaction":
                recommendations.append("Улучшить персонализацию ответов")
                
        # Рекомендации для развития сильных сторон
        for strength in strengths:
            recommendations.append(f"Продолжать развивать сильную сторону: {strength}")
            
        # Общие рекомендации
        if len(strengths) > len(weaknesses):
            recommendations.append("Экспортировать успешные практики в другие области")
        else:
            recommendations.append("Сосредоточиться на устранении основных недостатков")
            
        return recommendations