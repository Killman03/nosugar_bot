import random
from typing import List

from config import settings


class MotivationService:
    """Service for providing motivational messages and advice."""
    
    def __init__(self):
        self.success_messages = [
            "🎉 Отличная работа! Ты держишься уже {} дней!",
            "🔥 Невероятно! Твоя сила воли впечатляет!",
            "💪 Каждый день без сахара - это победа!",
            "🌟 Ты становишься сильнее с каждым днем!",
            "🏆 Продолжай в том же духе! Ты молодец!",
            "✨ Твоя настойчивость вдохновляет!",
            "🎯 Еще один день к здоровой жизни!",
            "💎 Ты настоящий алмаз! Продолжай сиять!"
        ]
        
        self.slip_up_messages = [
            "😔 Не переживай, срывы случаются у всех. Главное - не сдаваться!",
            "🔄 Завтра новый день и новые возможности!",
            "💪 Один срыв не отменяет весь твой прогресс!",
            "🌟 Каждая неудача - это урок. Учись и двигайся дальше!",
            "🎯 Помни о своей цели! Ты сильнее, чем думаешь!",
            "💎 Алмаз тоже шлифуется не сразу. Продолжай работу над собой!",
            "🔥 Небольшой огонек может разжечь большой костер мотивации!",
            "✨ Каждый день - это новая возможность стать лучше!"
        ]
        
        self.daily_motivations = [
            "🌅 Доброе утро! Сегодня отличный день для укрепления твоей силы воли!",
            "☀️ Новый день - новые возможности! Ты справишься!",
            "💪 Сегодня ты станешь сильнее, чем вчера!",
            "🎯 Помни о своей цели - здоровое тело и ясный ум!",
            "🌟 Ты на правильном пути! Продолжай движение!",
            "🔥 Твоя решимость зажигает огонь в других!",
            "💎 Каждый день без сахара делает тебя драгоценнее!",
            "✨ Ты создаешь лучшее будущее для себя!"
        ]
        
        self.challenges = [
            "Сегодня пей чай без сахара",
            "Замени сладкий десерт на фрукты",
            "Сделай 10 приседаний вместо перекуса",
            "Выпей стакан воды перед едой",
            "Прогуляйся 15 минут на свежем воздухе",
            "Сделай дыхательные упражнения",
            "Приготовь полезный завтрак",
            "Прочитай 10 страниц книги",
            "Сделай растяжку утром",
            "Попробуй новый полезный рецепт"
        ]
    
    def get_success_message(self, streak_days: int) -> str:
        """Get a random success message with streak information."""
        message = random.choice(self.success_messages)
        return message.format(streak_days)
    
    def get_slip_up_message(self) -> str:
        """Get a random motivational message for slip-ups."""
        return random.choice(self.slip_up_messages)
    
    def get_daily_motivation(self) -> str:
        """Get a random daily motivation message."""
        return random.choice(self.daily_motivations)
    
    async def get_ai_motivation(self, streak_days: int) -> str:
        """Get AI-generated motivation message."""
        try:
            from services.ai_service import AIService
            ai_service = AIService()
            return await ai_service.generate_motivation(streak_days)
        except Exception as e:
            from loguru import logger
            logger.error(f"Error getting AI motivation: {e}")
            return self.get_daily_motivation()
    
    def get_random_challenge(self) -> str:
        """Get a random daily challenge."""
        return random.choice(self.challenges)
    
    def get_payment_reminder(self) -> str:
        """Get payment reminder message."""
        return (
            "💸 Ой! Похоже, ты сорвался! 😅\n\n"
            "Согласно нашим правилам, нужно скинуть 50 сом на номер карты:\n"
            f"💳 {settings.payment_card_number}\n\n"
            "Это поможет тебе лучше контролировать себя в следующий раз! 😉"
        )
    
    def get_streak_celebration(self, streak_days: int) -> str:
        """Get celebration message for milestone streaks."""
        if streak_days == 7:
            return "🎉 Неделя без сахара! Ты настоящий герой! 🌟"
        elif streak_days == 30:
            return "🏆 Месяц без сахара! Ты достиг невероятного результата! 💎"
        elif streak_days == 100:
            return "👑 100 дней! Ты король/королева силы воли! 👑"
        elif streak_days % 7 == 0:
            return f"🎊 {streak_days} дней! Каждую неделю ты становишься сильнее! 💪"
        else:
            return self.get_success_message(streak_days) 