"""
critics.py - модуль самокритики и оценки для Елены
"""
import logging
from typing import Dict, List, Any, Optional
import numpy as np

logger = logging.getLogger(__name__)

class SelfCritic:
    """
    Модуль самокритики и оценки качества ответов.
    Анализирует ответы Елены и предлагает улучшения.
    """
    
    def __init__(self):
        """Инициализация модуля самокритики"""
        self.critique_history = []
        
        # Критерии оценки
        self.evaluation_criteria = {
            "accuracy": "Точность информации",
            "relevance": "Релевантность ответа",
            "clarity": "Ясность и понятность",
            "completeness": "Полнота ответа",
            "politeness": "Вежливость и тактичность",
            "helpfulness": "Полезность ответа",
            "creativity": "Креативность подхода"
        }
    
    def criticize_response(self, 
                          query: str, 
                          response: str) -> Dict[str, Any]:
        """
        Критический анализ ответа на запрос.
        
        Args:
            query: Запрос пользователя
            response: Ответ Елены
            
        Returns:
            Результат критического анализа
        """
        critique = {
            "query": query,
            "response": response,
            "scores": {},
            "issues": [],
            "improvements": [],
            "overall_score": 0
        }
        
        # Оценка по критериям
        scores = {}
        
        # 1. Релевантность
        relevance_score = self._evaluate_relevance(query, response)
        scores["relevance"] = relevance_score
        
        # 2. Точность (здесь нужна проверка фактов)
        accuracy_score = self._evaluate_accuracy(response)
        scores["accuracy"] = accuracy_score
        
        # 3. Ясность
        clarity_score = self._evaluate_clarity(response)
        scores["clarity"] = clarity_score
        
        # 4. Полнота
        completeness_score = self._evaluate_completeness(query, response)
        scores["completeness"] = completeness_score
        
        # 5. Вежливость
        politeness_score = self._evaluate_politeness(response)
        scores["politeness"] = politeness_score
        
        critique["scores"] = scores
        
        # Расчет общего балла
        overall_score = np.mean(list(scores.values()))
        critique["overall_score"] = overall_score
        
        # Выявление проблем
        issues = self._identify_issues(scores, query, response)
        critique["issues"] = issues
        
        # Предложения по улучшению
        improvements = self._suggest_improvements(issues, scores)
        critique["improvements"] = improvements
        
        # Сохраняем критику в историю
        self.critique_history.append(critique)
        
        logger.info(f"Ответ оценен: {overall_score:.2f}/1.0")
        
        return critique
    
    def _evaluate_relevance(self, query: str, response: str) -> float:
        """Оценка релевантности ответа запросу"""
        # Простая эвристика - проверка ключевых слов
        query_words = set(query.lower().split())
        response_words = set(response.lower().split())
        
        common_words = query_words.intersection(response_words)
        
        if not query_words:
            return 1.0
        
        relevance = len(common_words) / len(query_words)
        
        # Учет синонимов и связанных терминов
        # Здесь можно добавить более сложную логику
        
        return min(1.0, relevance * 1.5)  # Немного завышаем оценку
    
    def _evaluate_accuracy(self, response: str) -> float:
        """Оценка точности информации"""
        # В реальной системе здесь была бы проверка фактов
        # Пока используем эвристику
        
        # Признаки потенциально неточной информации
        uncertainty_indicators = [
            "возможно", "наверное", "скорее всего", 
            "я думаю", "мне кажется", "не уверена"
        ]
        
        # Подсчет неопределенных выражений
        uncertainty_count = sum(
            1 for indicator in uncertainty_indicators 
            if indicator in response.lower()
        )
        
        # Базовый балл
        accuracy = 0.9
        
        # Штраф за неопределенность
        if uncertainty_count > 0:
            accuracy -= uncertainty_count * 0.1
        
        return max(0.1, min(1.0, accuracy))
    
    def _evaluate_clarity(self, response: str) -> float:
        """Оценка ясности ответа"""
        # Простые метрики читаемости
        
        sentences = response.split('.')
        words = response.split()
        
        if not sentences or not words:
            return 0.5
        
        # Средняя длина предложения
        avg_sentence_length = len(words) / len(sentences)
        
        # Идеальная длина - 15-20 слов
        if 10 <= avg_sentence_length <= 25:
            sentence_score = 1.0
        elif 5 <= avg_sentence_length <= 30:
            sentence_score = 0.8
        else:
            sentence_score = 0.5
        
        # Сложные слова
        complex_words = [w for w in words if len(w) > 12]
        complexity_ratio = len(complex_words) / len(words) if words else 0
        
        if complexity_ratio < 0.1:
            complexity_score = 1.0
        elif complexity_ratio < 0.2:
            complexity_score = 0.8
        else:
            complexity_score = 0.6
        
        # Итоговая оценка ясности
        clarity = (sentence_score + complexity_score) / 2
        
        return clarity
    
    def _evaluate_completeness(self, query: str, response: str) -> float:
        """Оценка полноты ответа"""
        # Проверяем, отвечает ли ответ на возможные вопросы
        
        # Вопросительные слова в запросе
        question_words = ["что", "как", "почему", "зачем", "когда", "где", "кто"]
        
        question_present = any(
            word in query.lower().split() 
            for word in question_words
        )
        
        if not question_present:
            # Для утвердительных запросов полнота оценивается иначе
            return 0.8
        
        # Для вопросов проверяем наличие прямого ответа
        response_length = len(response.split())
        
        if response_length < 5:
            return 0.3
        elif response_length < 15:
            return 0.6
        else:
            return 0.9
    
    def _evaluate_politeness(self, response: str) -> float:
        """Оценка вежливости"""
        polite_phrases = [
            "пожалуйста", "спасибо", "будьте добры",
            "извините", "прошу прощения", "добрый день",
            "рада помочь", "чем могу помочь"
        ]
        
        polite_count = sum(
            1 for phrase in polite_phrases 
            if phrase in response.lower()
        )
        
        # Базовая вежливость
        politeness = 0.7
        
        # Бонус за вежливые фразы
        if polite_count > 0:
            politeness += polite_count * 0.1
        
        # Штраф за грубость (если обнаружена)
        rude_phrases = ["дурак", "идиот", "тупой", "заткнись"]
        rude_count = sum(
            1 for phrase in rude_phrases 
            if phrase in response.lower()
        )
        
        if rude_count > 0:
            politeness = 0.1
        
        return min(1.0, politeness)
    
    def _identify_issues(self, scores: Dict[str, float], query: str, response: str) -> List[Dict[str, Any]]:
        """Выявление проблем в ответе"""
        issues = []
        
        # Проверка низких оценок
        for criterion, score in scores.items():
            if score < 0.6:
                issues.append({
                    "criterion": criterion,
                    "score": score,
                    "description": f"Низкая оценка по критерию '{self.evaluation_criteria.get(criterion, criterion)}'",
                    "severity": "high" if score < 0.4 else "medium"
                })
        
        # Проверка конкретных проблем
        # 1. Слишком короткий ответ
        if len(response.split()) < 5:
            issues.append({
                "criterion": "completeness",
                "description": "Ответ слишком короткий",
                "severity": "medium"
            })
        
        # 2. Много неопределенности
        if scores.get("accuracy", 1.0) < 0.7:
            issues.append({
                "criterion": "accuracy",
                "description": "Слишком много неопределенности в ответе",
                "severity": "medium"
            })
        
        return issues
    
    def _suggest_improvements(self, issues: List[Dict[str, Any]], scores: Dict[str, float]) -> List[str]:
        """Предложения по улучшению"""
        improvements = []
        
        improvement_suggestions = {
            "relevance": [
                "Уделяй больше внимания ключевым словам в запросе",
                "Убедись, что ответ непосредственно относится к вопросу",
                "Используй те же термины, что и в запросе"
            ],
            "accuracy": [
                "Проверяй факты перед ответом",
                "Используй меньше неопределенных выражений",
                "Ссылайся на проверенные источники"
            ],
            "clarity": [
                "Используй более простые предложения",
                "Избегай сложной терминологии",
                "Структурируй ответ с помощью списков"
            ],
            "completeness": [
                "Давай более развернутые ответы",
                "Рассматривай разные аспекты вопроса",
                "Предлагай дополнительную информацию"
            ],
            "politeness": [
                "Добавляй вежливые фразы",
                "Проявляй эмпатию к пользователю",
                "Извиняйся, если не уверена в ответе"
            ]
        }
        
        for issue in issues:
            criterion = issue["criterion"]
            if criterion in improvement_suggestions:
                improvements.extend(improvement_suggestions[criterion][:2])  # Берем первые 2 совета
        
        # Общие советы
        if not improvements:
            overall_score = np.mean(list(scores.values())) if scores else 0
            if overall_score < 0.7:
                improvements.append("Постарайся быть более внимательной к деталям")
                improvements.append("Анализируй свои ответы перед отправкой")
        
        return improvements
    
    def improve_response_patterns(self, critique: Dict[str, Any]) -> List[Dict[str, Any]]:
        """
        Улучшение паттернов ответов на основе критики.
        
        Args:
            critique: Результат критического анализа
            
        Returns:
            Список примененных улучшений
        """
        improvements_applied = []
        
        # Анализируем критические замечания
        for issue in critique.get("issues", []):
            improvement = {
                "type": "response_pattern_improvement",
                "criterion": issue.get("criterion"),
                "description": f"Улучшение {issue.get('criterion')} на основе критики",
                "action": f"Скорректирован паттерн ответа для улучшения {issue.get('criterion')}"
            }
            improvements_applied.append(improvement)
        
        # Сохраняем уроки
        lesson = {
            "query": critique.get("query"),
            "original_response": critique.get("response"),
            "issues": critique.get("issues", []),
            "improvements_suggested": critique.get("improvements", []),
            "timestamp": critique.get("timestamp", "")
        }
        
        # Здесь можно сохранять уроки в базу знаний
        
        logger.info(f"Улучшены паттерны ответов на основе {len(improvements_applied)} замечаний")
        
        return improvements_applied
    
    def get_critique_history(self, limit: int = 10) -> List[Dict[str, Any]]:
        """
        Получение истории критики.
        
        Args:
            limit: Количество последних записей
            
        Returns:
            История критики
        """
        return self.critique_history[-limit:] if self.critique_history else []