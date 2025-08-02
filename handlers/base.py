from typing import Optional
from aiogram import Router, F
from aiogram.types import Message, CallbackQuery
from aiogram.filters import Command
from sqlalchemy.ext.asyncio import AsyncSession

from di.dependencies import (
    get_session,
    get_motivation_service,
    get_recipe_service,
    get_user_repository,
    get_checkin_repository,
    get_note_repository,
    get_challenge_repository,
    get_recipe_repository
)
from database.repository import UserRepository, CheckInRepository, NoteRepository, ChallengeRepository, RecipeRepository
from services.motivation_service import MotivationService
from services.recipe_service import RecipeService


class BaseHandler:
    """Base handler class with common functionality using DI."""
    
    def __init__(self):
        self.router = Router()
        # Register common back handler
        self.router.callback_query.register(self.handle_back, F.data == "menu_back")
    
    async def handle_back(self, callback: CallbackQuery):
        """Handle back button - common for all handlers."""
        from loguru import logger
        logger.info(f"BaseHandler handle_back called with data: {callback.data}")
        
        async for session in get_session():
            # Get or create user
            user = await self.get_user(session, callback.from_user.id)
            
            # Update user info if needed
            if user.username != callback.from_user.username:
                user.username = callback.from_user.username
                user.first_name = callback.from_user.first_name
                user.last_name = callback.from_user.last_name
                await session.commit()
            
            welcome_text = (
                f"👋 Привет, {callback.from_user.first_name}!\n\n"
                "🍭 Я помогу тебе отказаться от сахара и вести здоровый образ жизни!\n\n"
                "📊 Твоя текущая серия: <b>{}</b> дней\n"
                "🏆 Лучшая серия: <b>{}</b> дней\n\n"
                "Выбери действие:"
            ).format(user.current_streak, user.longest_streak)
            
            # Import StartHandler to get main menu keyboard
            from handlers.start import StartHandler
            start_handler = StartHandler()
            keyboard = start_handler.get_main_menu_keyboard()
            
            await callback.message.edit_text(welcome_text, reply_markup=keyboard, parse_mode="HTML")
            await callback.answer()
    
    async def get_user(self, session: AsyncSession, telegram_user_id: int):
        """Get or create user from database."""
        user_repo = get_user_repository(session)
        return await user_repo.get_or_create_user(telegram_user_id)
    
    async def get_user_with_repo(self, session: AsyncSession, telegram_user_id: int):
        """Get user and repository instance."""
        user_repo = get_user_repository(session)
        user = await user_repo.get_or_create_user(telegram_user_id)
        return user, user_repo
    
    async def get_checkin_repo(self, session: AsyncSession) -> CheckInRepository:
        """Get check-in repository instance."""
        return get_checkin_repository(session)
    
    async def get_note_repo(self, session: AsyncSession) -> NoteRepository:
        """Get note repository instance."""
        return get_note_repository(session)
    
    async def get_challenge_repo(self, session: AsyncSession) -> ChallengeRepository:
        """Get challenge repository instance."""
        return get_challenge_repository(session)
    
    async def get_recipe_repo(self, session: AsyncSession) -> RecipeRepository:
        """Get recipe repository instance."""
        return get_recipe_repository(session)
    
    def get_motivation_service(self) -> MotivationService:
        """Get motivation service instance."""
        return get_motivation_service()
    
    def get_recipe_service(self) -> RecipeService:
        """Get recipe service instance."""
        return get_recipe_service() 