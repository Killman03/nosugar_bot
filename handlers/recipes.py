from aiogram import Router, F
from aiogram.types import Message, CallbackQuery, InlineKeyboardMarkup, InlineKeyboardButton
from aiogram.filters import Command
from sqlalchemy.ext.asyncio import AsyncSession

from handlers.base import BaseHandler
from di.dependencies import get_session
from services.user_state_service import UserState


class RecipesHandler(BaseHandler):
    """Handler for recipes functionality."""
    
    def __init__(self):
        super().__init__()
        self.router.message.register(self.recipe_command, Command("recipe"))
        self.router.callback_query.register(self.handle_recipes, F.data.startswith("recipe_"))
    
    async def recipe_command(self, message: Message):
        """Handle /recipe command."""
        async for session in get_session():
            await self.start_recipe_creation(message, session)
    
    async def handle_recipes(self, callback: CallbackQuery):
        """Handle recipes menu actions."""
        async for session in get_session():
            action = callback.data.split("_")[1]
            
            if action == "create":
                await self.start_recipe_creation_from_callback(callback, session)
            elif action == "list":
                await self.show_recipes_list(callback, session)
            
            await callback.answer()
    
    async def start_recipe_creation_from_callback(self, callback: CallbackQuery, session: AsyncSession):
        """Start recipe creation process from callback."""
        # Set user as waiting for recipe ingredients
        user_state_service = self.get_user_state_service()
        user_id = callback.from_user.id
        user_state_service.set_user_state(user_id, UserState.WAITING_FOR_RECIPE_INGREDIENTS)
        
        # Debug: log state setting
        from loguru import logger
        logger.info(f"Set user {user_id} state to WAITING_FOR_RECIPE_INGREDIENTS")
        
        text = (
            "🍳 <b>Создание рецепта без сахара</b>\n\n"
            "Напиши ингредиенты, которые у тебя есть, и я создам для тебя "
            "вкусный рецепт без сахара!\n\n"
            "Например: яблоки, овсянка, корица, мед\n\n"
            "Просто напиши сообщение с ингредиентами."
        )
        
        keyboard = [[InlineKeyboardButton(text="🔙 Отмена", callback_data="menu_back")]]
        await callback.message.edit_text(text, reply_markup=InlineKeyboardMarkup(inline_keyboard=keyboard), parse_mode="HTML")
    
    async def start_recipe_creation(self, message: Message, session: AsyncSession):
        """Start recipe creation process."""
        # Set user as waiting for recipe ingredients
        user_state_service = self.get_user_state_service()
        user_state_service.set_user_state(message.from_user.id, UserState.WAITING_FOR_RECIPE_INGREDIENTS)
        
        text = (
            "🍳 <b>Создание рецепта без сахара</b>\n\n"
            "Напиши ингредиенты, которые у тебя есть, и я создам для тебя "
            "вкусный рецепт без сахара!\n\n"
            "Например: яблоки, овсянка, корица, мед\n\n"
            "Просто напиши сообщение с ингредиентами."
        )
        
        keyboard = [[InlineKeyboardButton(text="🔙 Отмена", callback_data="menu_back")]]
        await message.answer(text, reply_markup=InlineKeyboardMarkup(inline_keyboard=keyboard), parse_mode="HTML")
    
    async def show_recipes_list(self, callback: CallbackQuery, session: AsyncSession):
        """Show user's recipes list."""
        user = await self.get_user(session, callback.from_user.id)
        recipe_repo = await self.get_recipe_repo(session)
        
        recipes = await recipe_repo.get_user_recipes(user.id, limit=10)
        
        if recipes:
            text = "🍳 <b>Твои рецепты без сахара:</b>\n\n"
            for i, recipe in enumerate(recipes, 1):
                date_str = recipe.created_at.strftime("%d.%m.%Y")
                text += f"<b>{i}.</b> {date_str}\n"
                text += f"<i>Ингредиенты:</i> {recipe.ingredients[:50]}{'...' if len(recipe.ingredients) > 50 else ''}\n\n"
        else:
            text = "🍳 У тебя пока нет сохраненных рецептов.\n\nСоздай первый рецепт, чтобы начать готовить без сахара!"
        
        keyboard = [[InlineKeyboardButton(text="🔙 Назад", callback_data="menu_back")]]
        await callback.message.edit_text(text, reply_markup=InlineKeyboardMarkup(inline_keyboard=keyboard), parse_mode="HTML")
    
    def get_user_state_service(self):
        """Get user state service from container."""
        from di.container import container
        return container.user_state_service 