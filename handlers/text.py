from aiogram import Router, F
from aiogram.types import Message
from sqlalchemy.ext.asyncio import AsyncSession

from handlers.base import BaseHandler
from di.dependencies import get_session


class TextHandler(BaseHandler):
    """Handler for text messages."""
    
    def __init__(self):
        super().__init__()
        self.router.message.register(self.handle_text)
    
    async def handle_text(self, message: Message):
        """Handle text messages."""
        async for session in get_session():
            text = message.text.lower().strip()
            
            if "хочу сладкого" in text or "хочу сладкое" in text:
                await self.handle_sweet_craving(message, session)
            elif "мотивация" in text:
                await self.handle_motivation_request(message, session)
            elif "статистика" in text or "статистик" in text:
                await self.handle_stats_request(message, session)
            elif "помощь" in text or "help" in text:
                await self.handle_help_request(message, session)
    
    async def handle_sweet_craving(self, message: Message, session: AsyncSession):
        """Handle sweet craving messages."""
        user = await self.get_user(session, message.from_user.id)
        
        # Get alternative snacks
        recipe_service = self.get_recipe_service()
        alternatives = recipe_service.get_alternative_snacks()
        
        # Get motivation message
        motivation_service = self.get_motivation_service()
        motivation = motivation_service.get_success_message(user.current_streak)
        
        text = (
            f"🍭 <b>Понимаю, хочется сладкого!</b>\n\n"
            f"💪 {motivation}\n\n"
            f"🍎 <b>Вместо сладкого попробуй:</b>\n"
            f"{alternatives}\n\n"
            f"🔥 Твоя серия: <b>{user.current_streak}</b> дней\n"
            f"💪 Ты справишься! Держись!"
        )
        
        await message.answer(text, parse_mode="HTML")
    
    async def handle_motivation_request(self, message: Message, session: AsyncSession):
        """Handle motivation request."""
        user = await self.get_user(session, message.from_user.id)
        
        motivation_service = self.get_motivation_service()
        motivation = motivation_service.get_daily_motivation()
        
        text = (
            f"💪 <b>Мотивация дня:</b>\n\n"
            f"{motivation}\n\n"
            f"🔥 Твоя серия: <b>{user.current_streak}</b> дней\n"
            f"🏆 Лучшая серия: <b>{user.longest_streak}</b> дней"
        )
        
        await message.answer(text, parse_mode="HTML")
    
    async def handle_stats_request(self, message: Message, session: AsyncSession):
        """Handle statistics request."""
        user = await self.get_user(session, message.from_user.id)
        checkin_repo = await self.get_checkin_repo(session)
        
        stats = await checkin_repo.get_user_stats(user.id)
        
        text = (
            f"📊 <b>Твоя статистика:</b>\n\n"
            f"🎯 Текущая серия: <b>{user.current_streak}</b> дней\n"
            f"🏆 Лучшая серия: <b>{user.longest_streak}</b> дней\n"
            f"✅ Успешных дней: <b>{stats['success_count']}</b>\n"
            f"❌ Срывов: <b>{stats['fail_count']}</b>\n"
            f"📈 Процент успеха: <b>{stats['success_rate']:.1f}%</b>\n"
            f"📅 Всего дней: <b>{stats['total_days']}</b>"
        )
        
        await message.answer(text, parse_mode="HTML")
    
    async def handle_help_request(self, message: Message, session: AsyncSession):
        """Handle help request."""
        text = (
            "ℹ️ <b>Помощь</b>\n\n"
            "🍭 <b>Бот для отказа от сахара</b>\n\n"
            "<b>Основные команды:</b>\n"
            "/start - Главное меню\n"
            "/note - Добавить заметку\n"
            "/recipe - Найти рецепт\n\n"
            "<b>Функции:</b>\n"
            "✅ Ежедневные чек-ины\n"
            "📊 Статистика прогресса\n"
            "🍳 Рецепты без сахара\n"
            "🎯 Ежедневные челленджи\n"
            "📝 Дневник заметок\n"
            "💪 Мотивационные сообщения\n\n"
            "Просто напиши 'хочу сладкого' для альтернатив!"
        )
        
        await message.answer(text, parse_mode="HTML") 