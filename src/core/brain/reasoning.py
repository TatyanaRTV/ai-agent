"""
Модуль логических рассуждений и принятия решений
"""

import logging
from typing import Dict, Any, List, Optional
import json

logger = logging.getLogger(__name__)

class ReasoningEngine:
    """Движок логических рассуждений"""
    
    def __init__(self, memory_manager):
        self.memory = memory_manager
        self.rules = self._load_rules()
        
    async def reason(self, context: Dict[str, Any]) -> Dict[str, Any]:
        """Основной метод рассуждения"""
        logger.info("🤔 Начинаю процесс рассуждения...")
        
        reasoning_result = {
            "input_context": context,
            "conclusions": [],
            "confidence": 0.0,
            "reasoning_steps": [],
            "alternative_explanations": [],
            "timestamp": None
        }
        
        try:
            # 1. Анализ контекста
            analysis = await self._analyze_context(context)
            reasoning_result["reasoning_steps"].append(analysis)
            
            # 2. Применение правил
            rule_conclusions = await self._apply_rules(context)
            reasoning_result["conclusions"].extend(rule_conclusions)
            
            # 3. Дедуктивные рассуждения
            deductive = await self._deductive_reasoning(context)
            reasoning_result["conclusions"].extend(deductive)
            
            # 4. Индуктивные рассуждения
            inductive = await self._inductive_reasoning(context)
            reasoning_result["conclusions"].extend(inductive)
            
            # 5. Оценка уверенности
            confidence = await self._calculate_confidence(reasoning_result)
            reasoning_result["confidence"] = confidence
            
            # 6. Генерация альтернативных объяснений
            alternatives = await self._generate_alternatives(reasoning_result)
            reasoning_result["alternative_explanations"] = alternatives
            
            logger.info(f"✅ Рассуждение завершено. Уверенность: {confidence:.2f}")
            
        except Exception as e:
            logger.error(f"Ошибка в процессе рассуждения: {e}")
            reasoning_result["error"] = str(e)
            
        return reasoning_result
        
    async def _analyze_context(self, context: Dict[str, Any]) -> Dict[str, Any]:
        """Анализ контекста запроса"""
        analysis = {
            "step": "context_analysis",
            "user_intent": None,
            "emotional_tone": None,
            "complexity": None,
            "urgency": None
        }
        
        # Определение намерения пользователя
        if 'text' in context:
            text = context['text'].lower()
            
            # Простые паттерны намерений
            intent_patterns = {
                'question': ['как', 'что', 'где', 'когда', 'почему', 'зачем'],
                'command': ['сделай', 'найди', 'покажи', 'расскажи', 'включи', 'выключи'],
                'request': ['помоги', 'нужно', 'помощь', 'можешь'],
                'informational': ['знаешь', 'интересно', 'расскажи'],
                'social': ['привет', 'пока', 'спасибо', 'извини']
            }
            
            for intent, patterns in intent_patterns.items():
                if any(pattern in text for pattern in patterns):
                    analysis['user_intent'] = intent
                    break
                    
        # Оценка эмоционального тона
        analysis['emotional_tone'] = await self._detect_emotion(context)
        
        # Оценка сложности
        if 'text' in context:
            word_count = len(context['text'].split())
            if word_count < 5:
                analysis['complexity'] = 'low'
            elif word_count < 15:
                analysis['complexity'] = 'medium'
            else:
                analysis['complexity'] = 'high'
                
        # Оценка срочности
        urgency_words = ['срочно', 'быстро', 'немедленно', 'скорее', 'побыстрее']
        if 'text' in context and any(word in context['text'].lower() for word in urgency_words):
            analysis['urgency'] = 'high'
        else:
            analysis['urgency'] = 'low'
            
        return analysis
        
    async def _apply_rules(self, context: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Применение логических правил"""
        conclusions = []
        
        for rule in self.rules:
            try:
                if await self._rule_matches(rule, context):
                    conclusion = {
                        "type": "rule_based",
                        "rule_id": rule.get("id"),
                        "description": rule.get("description"),
                        "conclusion": rule.get("conclusion"),
                        "confidence": rule.get("confidence", 0.7)
                    }
                    conclusions.append(conclusion)
            except Exception as e:
                logger.warning(f"Ошибка применения правила {rule.get('id')}: {e}")
                
        return conclusions
        
    async def _deductive_reasoning(self, context: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Дедуктивные рассуждения (от общего к частному)"""
        conclusions = []
        
        # Пример дедуктивного правила: если A и B, то C
        if 'text' in context:
            text = context['text'].lower()
            
            # Пример: если пользователь спрашивает о погоде и сейчас утро, то он планирует день
            if 'погода' in text and self._is_morning():
                conclusions.append({
                    "type": "deductive",
                    "premise": "Запрос о погоде утром",
                    "conclusion": "Пользователь планирует свой день",
                    "confidence": 0.8
                })
                
        return conclusions
        
    async def _inductive_reasoning(self, context: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Индуктивные рассуждения (от частного к общему)"""
        conclusions = []
        
        # Поиск паттернов в прошлых взаимодействиях
        similar_interactions = await self.memory.find_similar_interactions(context, limit=5)
        
        if similar_interactions:
            # Анализ общих черт
            common_patterns = self._find_common_patterns(similar_interactions)
            
            for pattern in common_patterns:
                conclusions.append({
                    "type": "inductive",
                    "pattern": pattern,
                    "conclusion": f"На основе {len(similar_interactions)} похожих взаимодействий",
                    "confidence": min(0.9, 0.5 + len(similar_interactions) * 0.1)
                })
                
        return conclusions
        
    async def _calculate_confidence(self, reasoning_result: Dict[str, Any]) -> float:
        """Расчет уверенности в выводах"""
        confidence = 0.5  # Базовая уверенность
        
        # Учет количества выводов
        conclusions = reasoning_result.get("conclusions", [])
        if conclusions:
            avg_conclusion_confidence = sum(c.get("confidence", 0.5) for c in conclusions) / len(conclusions)
            confidence = (confidence + avg_conclusion_confidence) / 2
            
        # Учет альтернативных объяснений
        alternatives = reasoning_result.get("alternative_explanations", [])
        if alternatives:
            confidence *= 0.9  # Наличие альтернатив снижает уверенность
            
        return min(1.0, max(0.0, confidence))
        
    async def _generate_alternatives(self, reasoning_result: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Генерация альтернативных объяснений"""
        alternatives = []
        context = reasoning_result.get("input_context", {})
        
        # Альтернативные интерпретации намерения
        if 'text' in context:
            text = context['text'].lower()
            
            # Пример альтернативных интерпретаций
            if 'погода' in text:
                alternatives.append({
                    "interpretation": "Пользователь интересуется погодой для планирования поездки",
                    "confidence": 0.6
                })
                alternatives.append({
                    "interpretation": "Пользователь хочет начать разговор с нейтральной темы",
                    "confidence": 0.4
                })
                
        return alternatives
        
    def _load_rules(self) -> List[Dict[str, Any]]:
        """Загрузка логических правил"""
        rules = [
            {
                "id": "rule_001",
                "description": "Если пользователь здоровается, то нужно ответить приветствием",
                "condition": "any(word in text for word in ['привет', 'здравствуй', 'добрый день'])",
                "conclusion": "Пользователь ожидает приветственного ответа",
                "confidence": 0.95
            },
            {
                "id": "rule_002",
                "description": "Если пользователь спрашивает 'как дела', это социальный ритуал",
                "condition": "'как дела' in text or 'как ты' in text",
                "conclusion": "Пользователь проявляет вежливость, а не требует информации",
                "confidence": 0.85
            },
            {
                "id": "rule_003",
                "description": "Если запрос содержит слово 'срочно', требуется быстрый ответ",
                "condition": "any(word in text for word in ['срочно', 'быстро', 'немедленно'])",
                "conclusion": "Пользователь испытывает срочность, нужно ответить быстро",
                "confidence": 0.9
            }
        ]
        return rules
        
    async def _rule_matches(self, rule: Dict[str, Any], context: Dict[str, Any]) -> bool:
        """Проверка соответствия правила контексту"""
        try:
            if 'text' in context:
                text = context['text'].lower()
                condition = rule.get("condition", "")
                
                # Простая проверка условий (можно заменить на более сложную логику)
                if "'привет'" in condition and any(word in text for word in ['привет', 'здравствуй']):
                    return True
                if "'как дела'" in condition and 'как дела' in text:
                    return True
                if "'срочно'" in condition and any(word in text for word in ['срочно', 'быстро']):
                    return True
                    
        except Exception as e:
            logger.error(f"Ошибка проверки правила: {e}")
            
        return False
        
    async def _detect_emotion(self, context: Dict[str, Any]) -> str:
        """Определение эмоционального тона"""
        if 'text' not in context:
            return 'neutral'
            
        text = context['text'].lower()
        
        positive_words = ['спасибо', 'отлично', 'хорошо', 'прекрасно', 'рад', 'доволен']
        negative_words = ['плохо', 'ужасно', 'грустно', 'злой', 'разочарован', 'сердит']
        
        positive_count = sum(1 for word in positive_words if word in text)
        negative_count = sum(1 for word in negative_words if word in text)
        
        if positive_count > negative_count:
            return 'positive'
        elif negative_count > positive_count:
            return 'negative'
        else:
            return 'neutral'
            
    def _is_morning(self) -> bool:
        """Проверка, сейчас утро или нет"""
        from datetime import datetime
        hour = datetime.now().hour
        return 6 <= hour < 12
        
    def _find_common_patterns(self, interactions: List[Dict[str, Any]]) -> List[str]:
        """Поиск общих паттернов во взаимодействиях"""
        patterns = []
        
        # Простая логика поиска паттернов
        texts = [interaction.get('text', '').lower() for interaction in interactions if 'text' in interaction]
        
        # Поиск общих слов
        from collections import Counter
        all_words = []
        for text in texts:
            all_words.extend(text.split())
            
        word_counts = Counter(all_words)
        common_words = [word for word, count in word_counts.items() if count > 1 and len(word) > 3]
        
        if common_words:
            patterns.append(f"Часто используются слова: {', '.join(common_words[:3])}")
            
        return patterns