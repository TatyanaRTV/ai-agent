"""
Интерфейсы взаимодействия с агентом
"""

from src.interfaces.telegram.bot import TelegramBot
from src.interfaces.browser.server import WebInterface
from src.interfaces.voice.interface import VoiceInterface

__all__ = ["TelegramBot", "WebServer", "VoiceInterface"]