"""
Модуль логических рассуждений и принятия решений
"""

import logging
from typing import Dict, Any, List, Optional
from datetime import datetime
from collections import Counter
import json

logger = logging.getLogger(__name__)

class ReasoningEngine:
    """Движок логических рассуждений"""
    
    def __init__(self, memory_manager=None):
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
            "timestamp": datetime.now().isoformat(),
            "error": None
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
            
            # 4. Индуктивные рассуждения (только если есть память)
            if self.memory:
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
            error_msg = f"Ошибка в процессе рассуждения: {e}"
            logger.error(f"❌ {error_msg}")
            reasoning_result["error"] = str(e)
            
        return reasoning_result
        
    async def _analyze_context(self, context: Dict[str, Any]) -> Dict[str, Any]:
        """Анализ контекста запроса"""
        analysis = {
            "step": "context_analysis",
            "user_intent": None,
            "emotional_tone": None,
            "complexity": None,
            "urgency": None,
            "timestamp": datetime.now().isoformat()
        }
        
        # Определение намерения пользователя
        if 'text' in context:
            text = context['text'].lower()
            
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
        else:
            analysis['complexity'] = 'unknown'
                
        # Оценка срочности
        if 'text' in context:
            urgency_words = ['срочно', 'быстро', 'немедленно', 'скорее', 'побыстрее']
            analysis['urgency'] = 'high' if any(word in context['text'].lower() for word in urgency_words) else 'low'
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
                logger.warning(f"⚠️ Ошибка применения правила {rule.get('id', 'unknown')}: {e}")
                
        return conclusions
        
    async def _deductive_reasoning(self, context: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Дедуктивные рассуждения (от общего к частному)"""
        conclusions = []
        
        if 'text' in context:
            text = context['text'].lower()
            
            if 'погода' in text and self._is_morning():
                conclusions.append({
                    "type": "deductive",
                    "premise": "Запрос о погоде утром",
                    "conclusion": "Пользователь планирует свой день",
                    "confidence": 0.8
                })
                
            if 'помоги' in text and 'проблем' in text:
                conclusions.append({
                    "type": "deductive",
                    "premise": "Запрос помощи с проблемой",
                    "conclusion": "Пользователь нуждается в решении конкретной задачи",
                    "confidence": 0.75
                })
                
        return conclusions
        
    async def _inductive_reasoning(self, context: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Индуктивные рассуждения (от частного к общему)"""
        conclusions = []
        
        if not self.memory:
            return conclusions
            
        try:
            # Поиск похожих взаимодействий
            if hasattr(self.memory, 'find_similar_interactions'):
                similar_interactions = await self.memory.find_similar_interactions(context, limit=5)
            else:
                similar_interactions = []
            
            if similar_interactions:
                common_patterns = self._find_common_patterns(similar_interactions)
                
                for pattern in common_patterns:
                    conclusions.append({
                        "type": "inductive",
                        "pattern": pattern,
                        "conclusion": f"На основе {len(similar_interactions)} похожих взаимодействий",
                        "confidence": min(0.9, 0.5 + len(similar_interactions) * 0.1)
                    })
                    
        except Exception as e:
            logger.warning(f"⚠️ Ошибка индуктивного рассуждения: {e}")
                
        return conclusions
        
    async def _calculate_confidence(self, reasoning_result: Dict[str, Any]) -> float:
        """Расчет уверенности в выводах"""
        confidence = 0.5  # Базовая уверенность
        
        conclusions = reasoning_result.get("conclusions", [])
        if conclusions:
            avg_conclusion_confidence = sum(c.get("confidence", 0.5) for c in conclusions) / len(conclusions)
            confidence = (confidence + avg_conclusion_confidence) / 2
            
        alternatives = reasoning_result.get("alternative_explanations", [])
        if alternatives:
            confidence *= 0.9  # Наличие альтернатив снижает уверенность
            
        return min(1.0, max(0.0, confidence))
        
    async def _generate_alternatives(self, reasoning_result: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Генерация альтернативных объяснений"""
        alternatives = []
        context = reasoning_result.get("input_context", {})
        
        if 'text' in context:
            text = context['text'].lower()
            
            if 'погода' in text:
                alternatives.append({
                    "interpretation": "Пользователь интересуется погодой для планирования поездки",
                    "confidence": 0.6
                })
                alternatives.append({
                    "interpretation": "Пользователь хочет начать разговор с нейтральной темы",
                    "confidence": 0.4
                })
                
            if 'помощь' in text or 'помоги' in text:
                alternatives.append({
                    "interpretation": "Пользователь столкнулся с проблемой и ищет решение",
                    "confidence": 0.8
                })
                alternatives.append({
                    "interpretation": "Пользователь проверяет функциональность ассистента",
                    "confidence": 0.3
                })
                
        return alternatives
        
    def _load_rules(self) -> List[Dict[str, Any]]:
        """Загрузка логических правил"""
        return [
            {
                "id": "rule_001",
                "description": "Если пользователь здоровается, то нужно ответить приветствием",
                "condition": "привет",
                "conclusion": "Пользователь ожидает приветственного ответа",
                "confidence": 0.95
            },
            {
                "id": "rule_002",
                "description": "Если пользователь спрашивает 'как дела', это социальный ритуал",
                "condition": "как дела",
                "conclusion": "Пользователь проявляет вежливость, а не требует информации",
                "confidence": 0.85
            },
            {
                "id": "rule_003",
                "description": "Если запрос содержит слово 'срочно', требуется быстрый ответ",
                "condition": "срочно",
                "conclusion": "Пользователь испытывает срочность, нужно ответить быстро",
                "confidence": 0.9
            },
            {
                "id": "rule_004",
                "description": "Если пользователь благодарит, нужно ответить вежливостью",
                "condition": "спасибо",
                "conclusion": "Пользователь удовлетворён ответом",
                "confidence": 0.95
            }
        ]
        
    async def _rule_matches(self, rule: Dict[str, Any], context: Dict[str, Any]) -> bool:
        """Проверка соответствия правила контексту"""
        try:
            if 'text' not in context:
                return False
                
            text = context['text'].lower()
            condition = rule.get("condition", "").lower()
            
            return condition in text if condition else False
                
        except Exception as e:
            logger.error(f"❌ Ошибка проверки правила: {e}")
            return False
        
    async def _detect_emotion(self, context: Dict[str, Any]) -> str:
        """Определение эмоционального тона"""
        if 'text' not in context:
            return 'neutral'
            
        text = context['text'].lower()
        
        positive_words = ['спасибо', 'отлично', 'хорошо', 'прекрасно', 'рад', 'доволен', 'супер']
        negative_words = ['плохо', 'ужасно', 'грустно', 'злой', 'разочарован', 'сердит', 'нервы']
        
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
        hour = datetime.now().hour
        return 6 <= hour < 12
        
    def _find_common_patterns(self, interactions: List[Dict[str, Any]]) -> List[str]:
        """Поиск общих паттернов во взаимодействиях"""
        patterns = []
        
        texts = []
        for interaction in interactions:
            if isinstance(interaction, dict):
                if 'text' in interaction:
                    texts.append(interaction['text'].lower())
                elif 'content' in interaction:
                    texts.append(interaction['content'].lower())
                elif 'query' in interaction:
                    texts.append(interaction['query'].lower())
        
        if not texts:
            return patterns
            
        all_words = []
        for text in texts:
            words = text.split()
            all_words.extend([w for w in words if len(w) > 3])
            
        if not all_words:
            return patterns
            
        word_counts = Counter(all_words)
        common_words = [word for word, count in word_counts.most_common(5) if count > 1]
        
        if common_words:
            patterns.append(f"Часто используются слова: {', '.join(common_words[:3])}")
            
        return patterns
        
    def get_rules_summary(self) -> Dict[str, Any]:
        """Получение сводки по правилам"""
        return {
            "total_rules": len(self.rules),
            "rules": [
                {
                    "id": r["id"],
                    "description": r["description"],
                    "confidence": r["confidence"]
                }
                for r in self.rules
            ]
        }