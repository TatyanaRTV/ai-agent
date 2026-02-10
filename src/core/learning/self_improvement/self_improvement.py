"""
self_improvement.py - ядро системы самообучения Елены
"""
import logging
import json
import numpy as np
from datetime import datetime
from typing import Dict, List, Any, Optional
from pathlib import Path

logger = logging.getLogger(__name__)

class SelfImprovementSystem:
    """
    Основная система самообучения и самосовершенствования Елены.
    Отвечает за постоянное улучшение знаний и навыков.
    """
    
    def __init__(self, 
                 data_dir: str = "/mnt/ai_data/ai-agent/data",
                 model_dir: str = "/mnt/ai_data/ai-agent/models"):
        """
        Инициализация системы самообучения.
        
        Args:
            data_dir: Директория для данных обучения
            model_dir: Директория для моделей
        """
        self.data_dir = Path(data_dir)
        self.model_dir = Path(model_dir)
        
        # Создаем необходимые директории
        self.learning_data_dir = self.data_dir / "learning"
        self.feedback_dir = self.data_dir / "feedback"
        
        for directory in [self.learning_data_dir, self.feedback_dir]:
            directory.mkdir(parents=True, exist_ok=True)
        
        # Подсистемы
        from .critics import SelfCritic
        from .cleanup import KnowledgeCleanup
        from .adaptation import UserAdaptation
        from .knowledge_refiner import KnowledgeRefiner
        from .skill_learner import SkillLearner
        
        self.critic = SelfCritic()
        self.cleanup = KnowledgeCleanup()
        self.adaptation = UserAdaptation()
        self.refiner = KnowledgeRefiner()
        self.skill_learner = SkillLearner()
        
        # История обучения
        self.learning_history = []
        self.improvements_applied = 0
        
        logger.info("Система самообучения инициализирована")
    
    def analyze_interaction(self, 
                           interaction_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Анализ взаимодействия для обучения.
        
        Args:
            interaction_data: Данные о взаимодействии с пользователем
            
        Returns:
            Результат анализа
        """
        analysis = {
            "timestamp": datetime.now().isoformat(),
            "interaction_id": interaction_data.get("id"),
            "analysis": {}
        }
        
        # 1. Анализ качества ответа
        if "response" in interaction_data and "user_query" in interaction_data:
            response_analysis = self.critic.criticize_response(
                query=interaction_data["user_query"],
                response=interaction_data["response"]
            )
            analysis["analysis"]["response_critique"] = response_analysis
        
        # 2. Анализ знаний
        if "topics" in interaction_data:
            knowledge_analysis = self.refiner.analyze_knowledge_gaps(
                topics=interaction_data["topics"]
            )
            analysis["analysis"]["knowledge_gaps"] = knowledge_analysis
        
        # 3. Анализ навыков
        if "skills_used" in interaction_data:
            skill_analysis = self.skill_learner.analyze_skill_usage(
                skills=interaction_data["skills_used"]
            )
            analysis["analysis"]["skill_analysis"] = skill_analysis
        
        # Сохраняем анализ
        self._save_analysis(analysis)
        
        return analysis
    
    def apply_improvements(self, 
                          analysis_results: Dict[str, Any]) -> Dict[str, Any]:
        """
        Применение улучшений на основе анализа.
        
        Args:
            analysis_results: Результаты анализа
            
        Returns:
            Результат применения улучшений
        """
        improvements_applied = []
        
        # 1. Улучшение знаний
        if "knowledge_gaps" in analysis_results.get("analysis", {}):
            knowledge_improvements = self.refiner.refine_knowledge(
                gaps=analysis_results["analysis"]["knowledge_gaps"]
            )
            improvements_applied.extend(knowledge_improvements)
        
        # 2. Улучшение ответов
        if "response_critique" in analysis_results.get("analysis", {}):
            response_improvements = self.critic.improve_response_patterns(
                critique=analysis_results["analysis"]["response_critique"]
            )
            improvements_applied.extend(response_improvements)
        
        # 3. Очистка устаревших знаний
        cleanup_results = self.cleanup.cleanup_old_knowledge()
        improvements_applied.append({
            "type": "knowledge_cleanup",
            "results": cleanup_results
        })
        
        # 4. Адаптация к пользователю
        adaptation_results = self.adaptation.adapt_to_user_patterns()
        improvements_applied.append({
            "type": "user_adaptation",
            "results": adaptation_results
        })
        
        # 5. Обучение новым навыкам
        if "skill_analysis" in analysis_results.get("analysis", {}):
            skill_improvements = self.skill_learner.learn_new_skills(
                analysis=analysis_results["analysis"]["skill_analysis"]
            )
            improvements_applied.extend(skill_improvements)
        
        # Сохраняем улучшения
        result = {
            "timestamp": datetime.now().isoformat(),
            "improvements_applied": improvements_applied,
            "total_improvements": len(improvements_applied)
        }
        
        self._save_improvements(result)
        self.improvements_applied += len(improvements_applied)
        
        logger.info(f"Применено {len(improvements_applied)} улучшений")
        
        return result
    
    def learn_from_feedback(self, 
                           feedback_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Обучение на основе обратной связи от пользователя.
        
        Args:
            feedback_data: Данные обратной связи
            
        Returns:
            Результат обучения
        """
        learning_result = {
            "timestamp": datetime.now().isoformat(),
            "feedback_type": feedback_data.get("type", "unknown"),
            "learning_outcomes": []
        }
        
        # Сохраняем обратную связь
        feedback_file = self.feedback_dir / f"feedback_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
        with open(feedback_file, 'w', encoding='utf-8') as f:
            json.dump(feedback_data, f, ensure_ascii=False, indent=2)
        
        # Анализируем обратную связь
        if feedback_data.get("type") == "positive":
            # Укрепляем успешные паттерны
            learning_result["learning_outcomes"].append(
                self._reinforce_successful_patterns(feedback_data)
            )
        
        elif feedback_data.get("type") == "negative":
            # Исправляем ошибки
            learning_result["learning_outcomes"].append(
                self._correct_errors(feedback_data)
            )
        
        elif feedback_data.get("type") == "suggestion":
            # Внедряем предложения
            learning_result["learning_outcomes"].append(
                self._implement_suggestions(feedback_data)
            )
        
        # Обновляем метрики
        self._update_learning_metrics(feedback_data)
        
        return learning_result
    
    def _reinforce_successful_patterns(self, feedback_data: Dict[str, Any]) -> Dict[str, Any]:
        """Укрепление успешных паттернов"""
        return {
            "action": "reinforce_patterns",
            "details": "Укрепление успешных паттернов поведения",
            "patterns": feedback_data.get("successful_patterns", [])
        }
    
    def _correct_errors(self, feedback_data: Dict[str, Any]) -> Dict[str, Any]:
        """Исправление ошибок"""
        return {
            "action": "correct_errors",
            "details": "Исправление выявленных ошибок",
            "errors": feedback_data.get("errors", []),
            "corrections": feedback_data.get("corrections", [])
        }
    
    def _implement_suggestions(self, feedback_data: Dict[str, Any]) -> Dict[str, Any]:
        """Внедрение предложений"""
        return {
            "action": "implement_suggestions",
            "details": "Внедрение предложений пользователя",
            "suggestions": feedback_data.get("suggestions", [])
        }
    
    def _save_analysis(self, analysis: Dict[str, Any]):
        """Сохранение анализа"""
        analysis_file = self.learning_data_dir / f"analysis_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
        with open(analysis_file, 'w', encoding='utf-8') as f:
            json.dump(analysis, f, ensure_ascii=False, indent=2)
        
        self.learning_history.append({
            "type": "analysis",
            "file": str(analysis_file),
            "timestamp": analysis["timestamp"]
        })
    
    def _save_improvements(self, improvements: Dict[str, Any]):
        """Сохранение улучшений"""
        improvements_file = self.learning_data_dir / f"improvements_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
        with open(improvements_file, 'w', encoding='utf-8') as f:
            json.dump(improvements, f, ensure_ascii=False, indent=2)
    
    def _update_learning_metrics(self, feedback_data: Dict[str, Any]):
        """Обновление метрик обучения"""
        metrics_file = self.learning_data_dir / "learning_metrics.json"
        
        if metrics_file.exists():
            with open(metrics_file, 'r', encoding='utf-8') as f:
                metrics = json.load(f)
        else:
            metrics = {
                "total_interactions": 0,
                "positive_feedback": 0,
                "negative_feedback": 0,
                "suggestions_received": 0,
                "improvements_applied": 0,
                "knowledge_gaps_filled": 0
            }
        
        # Обновляем метрики
        metrics["total_interactions"] += 1
        
        feedback_type = feedback_data.get("type")
        if feedback_type == "positive":
            metrics["positive_feedback"] += 1
        elif feedback_type == "negative":
            metrics["negative_feedback"] += 1
        elif feedback_type == "suggestion":
            metrics["suggestions_received"] += 1
        
        metrics["improvements_applied"] = self.improvements_applied
        
        # Сохраняем обновленные метрики
        with open(metrics_file, 'w', encoding='utf-8') as f:
            json.dump(metrics, f, ensure_ascii=False, indent=2)
    
    def get_learning_stats(self) -> Dict[str, Any]:
        """Получение статистики обучения"""
        metrics_file = self.learning_data_dir / "learning_metrics.json"
        
        if metrics_file.exists():
            with open(metrics_file, 'r', encoding='utf-8') as f:
                metrics = json.load(f)
        else:
            metrics = {}
        
        return {
            "total_improvements": self.improvements_applied,
            "learning_history_count": len(self.learning_history),
            "metrics": metrics,
            "learning_data_dir": str(self.learning_data_dir),
            "last_analysis": self.learning_history[-1] if self.learning_history else None
        }
    
    def schedule_self_improvement(self, interval_hours: int = 24):
        """
        Планирование регулярного самоулучшения.
        
        Args:
            interval_hours: Интервал в часах
        """
        # Здесь будет логика планирования (например, через cron или APScheduler)
        logger.info(f"Самоулучшение запланировано каждые {interval_hours} часов")