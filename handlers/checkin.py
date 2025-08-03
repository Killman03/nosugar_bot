from aiogram import Router, F
from aiogram.types import CallbackQuery, InlineKeyboardMarkup, InlineKeyboardButton
from sqlalchemy.ext.asyncio import AsyncSession
from datetime import datetime

from handlers.base import BaseHandler
from di.dependencies import get_session
from services.user_state_service import UserState


class CheckInHandler(BaseHandler):
    """Handler for daily check-ins."""
    
    def __init__(self):
        super().__init__()
        self.router.callback_query.register(self.handle_checkin, F.data.startswith("checkin_"))
        self.router.callback_query.register(self.handle_challenge, F.data == "challenge_complete")
        self.router.callback_query.register(self.handle_slip_analysis, F.data == "slip_analysis")
    
    async def handle_checkin(self, callback: CallbackQuery):
        """Handle check-in button clicks."""
        async for session in get_session():
            action = callback.data.split("_")[1]
            
            if action == "success":
                await self.process_success_checkin(callback, session)
            elif action == "fail":
                await self.process_fail_checkin(callback, session)
            
            await callback.answer()
    
    async def process_success_checkin(self, callback: CallbackQuery, session: AsyncSession):
        """Process successful check-in."""
        user = await self.get_user(session, callback.from_user.id)
        checkin_repo = await self.get_checkin_repo(session)
        
        # Check if already checked in today
        today_checkin = await checkin_repo.get_today_checkin(user.id)
        if today_checkin:
            text = "Сегодня ты уже отметился! Можешь изменить свой ответ завтра."
            keyboard = self.get_back_keyboard()
            await callback.message.edit_text(text, reply_markup=keyboard)
            return
        
        # Create check-in
        await checkin_repo.create_checkin(user.id, True)
        
        # Update user streak
        old_streak = user.current_streak
        await checkin_repo.update_streak(user.id, True)
        
        # Refresh user object to get updated data
        await session.refresh(user)
        
        # Debug: log streak update
        from loguru import logger
        logger.info(f"User {user.user_id} streak updated: {old_streak} -> {user.current_streak}, longest: {user.longest_streak}")
        
        # Get motivation message
        motivation_service = self.get_motivation_service()
        motivation_text = motivation_service.get_success_message(user.current_streak)
        
        text = (
            f"✅ <b>Отлично! Ты удержался!</b>\n\n"
            f"{motivation_text}\n\n"
            f"🔥 Твоя серия: <b>{user.current_streak}</b> дней\n"
            f"🏆 Лучшая серия: <b>{user.longest_streak}</b> дней"
        )
        
        keyboard = self.get_back_keyboard()
        await callback.message.edit_text(text, reply_markup=keyboard, parse_mode="HTML")
    
    async def process_fail_checkin(self, callback: CallbackQuery, session: AsyncSession):
        """Process failed check-in."""
        user = await self.get_user(session, callback.from_user.id)
        checkin_repo = await self.get_checkin_repo(session)
        
        # Check if already checked in today
        today_checkin = await checkin_repo.get_today_checkin(user.id)
        if today_checkin:
            text = "Сегодня ты уже отметился! Можешь изменить свой ответ завтра."
            keyboard = self.get_back_keyboard()
            await callback.message.edit_text(text, reply_markup=keyboard)
            return
        
        # Create check-in
        await checkin_repo.create_checkin(user.id, False)
        
        # Update user streak
        await checkin_repo.update_streak(user.id, False)
        
        # Refresh user object to get updated data
        await session.refresh(user)
        
        # Get slip-up message and payment reminder
        motivation_service = self.get_motivation_service()
        slip_up_text = motivation_service.get_slip_up_message()
        payment_text = motivation_service.get_payment_reminder()
        
        text = (
            f"❌ <b>Не переживай, срывы бывают у всех!</b>\n\n"
            f"{slip_up_text}\n\n"
            f"💳 <b>Напоминание:</b> {payment_text}\n\n"
            f"🔥 Твоя серия: <b>{user.current_streak}</b> дней\n"
            f"🏆 Лучшая серия: <b>{user.longest_streak}</b> дней\n\n"
            f"💪 Завтра новый день! Начни заново!"
        )
        
        keyboard = [
            [
                InlineKeyboardButton(text="📝 Анализ срыва", callback_data="slip_analysis"),
                InlineKeyboardButton(text="💪 Мотивация", callback_data="menu_motivation")
            ],
            [InlineKeyboardButton(text="🔙 Назад", callback_data="menu_back")]
        ]
        
        await callback.message.edit_text(text, reply_markup=keyboard, parse_mode="HTML")
    
    async def handle_challenge(self, callback: CallbackQuery):
        """Handle challenge completion."""
        async for session in get_session():
            user = await self.get_user(session, callback.from_user.id)
            challenge_repo = await self.get_challenge_repo(session)
            
            today_challenge = await challenge_repo.get_today_challenge(user.id)
            if today_challenge and not today_challenge.completed:
                await challenge_repo.complete_challenge(today_challenge.id)
                
                text = (
                    "🎉 <b>Поздравляю! Челлендж выполнен!</b>\n\n"
                    "Ты молодец! Каждый выполненный челлендж приближает тебя к цели."
                )
                
                keyboard = self.get_back_keyboard()
                await callback.message.edit_text(text, reply_markup=keyboard, parse_mode="HTML")
            else:
                await callback.answer("Челлендж уже выполнен или не найден!")
            
            await callback.answer()
    
    async def handle_slip_analysis(self, callback: CallbackQuery):
        """Handle slip analysis request."""
        async for session in get_session():
            user = await self.get_user(session, callback.from_user.id)
            
            # Set user state to waiting for slip analysis
            user_state_service = self.get_user_state_service()
            user_state_service.set_user_state(callback.from_user.id, UserState.WAITING_FOR_SLIP_ANALYSIS)
            
            text = (
                "📝 <b>Анализ срыва</b>\n\n"
                "Помоги себе стать сильнее! Напиши:\n\n"
                "🔍 <b>Причины срыва:</b>\n"
                "• Что привело к срыву?\n"
                "• Какие эмоции ты испытывал?\n"
                "• Что происходило вокруг?\n\n"
                "💡 <b>План на будущее:</b>\n"
                "• Как избежать такой ситуации?\n"
                "• Что можно сделать по-другому?\n"
                "• Какие альтернативы использовать?\n\n"
                "Просто напиши свой анализ в следующем сообщении."
            )
            
            keyboard = [[InlineKeyboardButton(text="🔙 Отмена", callback_data="menu_back")]]
            await callback.message.edit_text(text, reply_markup=InlineKeyboardMarkup(inline_keyboard=keyboard), parse_mode="HTML")
            
            await callback.answer()
    
    def get_back_keyboard(self) -> InlineKeyboardMarkup:
        """Create back keyboard."""
        keyboard = [[InlineKeyboardButton(text="🔙 Назад", callback_data="menu_back")]]
        return InlineKeyboardMarkup(inline_keyboard=keyboard) 