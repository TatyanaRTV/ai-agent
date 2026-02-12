
"""
Telegram интерфейс
"""

# Ленивый импорт - бот загружается только когда реально нужен
def get_telegram_bot():
    from src.interfaces.telegram.bot import TelegramBot
    return TelegramBot

__all__ = ["get_telegram_bot"]