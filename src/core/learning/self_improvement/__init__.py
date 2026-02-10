"""
Модуль обучения и самообучения для ИИ-агента Елена
"""

from .trainer import ModelTrainer
from .feedback_system import FeedbackSystem
from .metrics_collector import MetricsCollector
from .reinforcement_learner import ReinforcementLearner
from .transfer_learning import TransferLearning
from .self_improvement import SelfImprovementSystem

# Импорт подмодулей
from .self_improvement import (
    SelfCritic,
    KnowledgeCleanup,
    UserAdaptation,
    KnowledgeRefiner,
    SkillLearner
)

__all__ = [
    'ModelTrainer',
    'FeedbackSystem',
    'MetricsCollector',
    'ReinforcementLearner',
    'TransferLearning',
    'SelfImprovementSystem',
    'SelfCritic',
    'KnowledgeCleanup',
    'UserAdaptation',
    'KnowledgeRefiner',
    'SkillLearner'
]

__version__ = '1.0.0'
__author__ = 'Елена ИИ-Агент'
__description__ = 'Модуль обучения, самообучения и адаптации ИИ-агента'