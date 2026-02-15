#!/usr/bin/env python3
# Путь: /mnt/ai_data/ai-agent/src/learning/self_improvement.py
"""Модуль самообучения и самокритики Елены"""

from loguru import logger
import json
from datetime import datetime
import gc


class SelfImprovement:
    """Самообучение на основе обратной связи"""

    def __init__(self, memory):
        self.memory = memory
        self.performance_stats = {"total_interactions": 0, "successful": 0, "failed": 0, "average_rating": 0.0}
        logger.info("📚 SelfImprovement инициализирован")

    def learn_from_feedback(self, query: str, response: str, rating: int):
        """
        Сохраняет успешные диалоги в память для улучшения

        Args:
            query: запрос пользователя
            response: ответ Елены
            rating: оценка (1-5)
        """
        try:
            self.performance_stats["total_interactions"] += 1

            if rating >= 4:
                self.performance_stats["successful"] += 1
                # Сохраняем удачный диалог в память
                self.memory.vector.add(
                    f"Q: {query}\nA: {response}",
                    {"type": "positive_dialog", "rating": rating, "timestamp": str(datetime.now())},
                )
                logger.info(f"✅ Диалог сохранён в память (оценка: {rating}/5)")
            else:
                self.performance_stats["failed"] += 1
                logger.info(f"📝 Получена низкая оценка ({rating}/5), требуется улучшение")

            # Обновляем среднюю оценку
            total = self.performance_stats["total_interactions"]
            current_avg = self.performance_stats["average_rating"]
            self.performance_stats["average_rating"] = (current_avg * (total - 1) + rating) / total

        except Exception as e:
            logger.error(f"❌ Ошибка в learn_from_feedback: {e}")

    def self_critique(self, last_actions: list):
        """
        Анализирует недавние действия и предлагает улучшения

        Args:
            last_actions: список последних действий
        """
        try:
            if not last_actions:
                return

            logger.info("🔍 Запуск самокритики...")

            issues = []

            for action in last_actions:
                # Проверяем длинные ответы
                if action.get("type") == "converse":
                    response = action.get("response", "")
                    if len(response) > 500:
                        issues.append({"type": "too_long", "message": "Ответ слишком длинный", "action": action})

                # Проверяем повторяющиеся ошибки
                if action.get("error"):
                    issues.append({"type": "error", "message": action["error"], "action": action})

            if issues:
                logger.warning(f"⚠️ Найдено {len(issues)} проблем:")
                for issue in issues:
                    logger.warning(f"   - {issue['message']}")

                # Сохраняем проблемы для анализа
                self._store_issues(issues)
            else:
                logger.info("✅ Проблем не обнаружено")

        except Exception as e:
            logger.error(f"❌ Ошибка в self_critique: {e}")

    def _store_issues(self, issues):
        """Сохраняет проблемы в память для анализа"""
        try:
            self.memory.vector.add(
                json.dumps(issues, ensure_ascii=False),
                {"type": "self_critique", "timestamp": str(datetime.now()), "count": len(issues)},
            )
        except Exception as e:
            logger.error(f"❌ Ошибка сохранения проблем: {e}")

    def get_stats(self):
        """Получить статистику производительности"""
        try:
            success_rate = 0
            if self.performance_stats["total_interactions"] > 0:
                success_rate = self.performance_stats["successful"] / self.performance_stats["total_interactions"] * 100

            return {**self.performance_stats, "success_rate": f"{success_rate:.1f}%"}
        except Exception as e:
            logger.error(f"❌ Ошибка получения статистики: {e}")
            return {}

    def cleanup(self):
        """Очистка ресурсов"""
        try:
            # Очищаем статистику при необходимости
            gc.collect()
            logger.info("🧹 SelfImprovement: ресурсы очищены")
        except Exception as e:
            logger.error(f"❌ Ошибка очистки: {e}")
