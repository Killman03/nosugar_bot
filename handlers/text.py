from aiogram import Router, F
from aiogram.types import Message, InlineKeyboardButton, InlineKeyboardMarkup
from sqlalchemy.ext.asyncio import AsyncSession

from handlers.base import BaseHandler
from di.dependencies import get_session
from services.user_state_service import UserState


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
            else:
                # Check if user is in recipe or note creation mode
                await self.check_user_state(message, session)
    
    async def check_user_state(self, message: Message, session: AsyncSession):
        """Check if user is in recipe or note creation mode."""
        user_id = message.from_user.id
        user_state_service = self.get_user_state_service()
        
        # Debug: log user state
        from loguru import logger
        current_state = user_state_service.get_user_state(user_id)
        logger.info(f"User {user_id} state: {current_state}")
        
        # Check if user is waiting for recipe ingredients
        if user_state_service.is_waiting_for_recipe(user_id):
            logger.info(f"User {user_id} is waiting for recipe ingredients")
            await self.create_recipe_from_text(message, session)
            user_state_service.clear_user_state(user_id)
        # Check if user is waiting for note content
        elif user_state_service.is_waiting_for_note(user_id):
            logger.info(f"User {user_id} is waiting for note content")
            await self.create_note_from_text(message, session)
            user_state_service.clear_user_state(user_id)
        # Check if user is waiting for slip analysis
        elif user_state_service.is_waiting_for_slip_analysis(user_id):
            logger.info(f"User {user_id} is waiting for slip analysis")
            await self.create_slip_analysis_from_text(message, session)
            user_state_service.clear_user_state(user_id)
        else:
            # Default response for unrecognized text
            logger.info(f"User {user_id} is in idle state, showing unknown text message")
            await self.handle_unknown_text(message, session)
    
    async def handle_unknown_text(self, message: Message, session: AsyncSession):
        """Handle unrecognized text messages."""
        text = (
            "🤔 Не понимаю, что ты хочешь сказать.\n\n"
            "Попробуй:\n"
            "• Написать 'хочу сладкого' для альтернатив\n"
            "• Использовать кнопки в меню\n"
            "• Написать 'помощь' для справки"
        )
        await message.answer(text)
    
    async def create_note_from_text(self, message: Message, session: AsyncSession):
        """Create note from text message."""
        user = await self.get_user(session, message.from_user.id)
        note_repo = await self.get_note_repo(session)
        
        # Send processing message
        processing_message = await message.answer(
            "⏳ <b>Сохраняю заметку...</b>",
            parse_mode="HTML"
        )
        
        try:
            # Create note
            await note_repo.create_note(user.id, message.text)
            
            # Delete processing message
            await processing_message.delete()
            
            text = (
                "✅ <b>Заметка сохранена!</b>\n\n"
                "Твои мысли важны для отслеживания прогресса. "
                "Продолжай вести дневник своих успехов!"
            )
            
            await message.answer(text, parse_mode="HTML")
            
        except Exception as e:
            from loguru import logger
            logger.error(f"Error creating note: {e}")
            
            # Delete processing message and send error
            await processing_message.delete()
            
            text = (
                "❌ <b>Не удалось сохранить заметку</b>\n\n"
                "Попробуй еще раз или обратись к администратору."
            )
            
            await message.answer(text, parse_mode="HTML")
    
    async def create_recipe_from_text(self, message: Message, session: AsyncSession):
        """Create recipe from text message."""
        user = await self.get_user(session, message.from_user.id)
        recipe_repo = await self.get_recipe_repo(session)
        
        # Send waiting message
        waiting_message = await message.answer(
            "⏳ <b>Генерирую рецепт...</b>\n\n"
            "Пожалуйста, подождите немного, пока ИИ создает для вас вкусный рецепт без сахара! 🍳",
            parse_mode="HTML"
        )
        
        try:
            # Generate recipe using AI service
            ai_service = self.get_ai_service()
            recipe_text = await ai_service.generate_recipe(message.text)
            
            # Save recipe to database
            await recipe_repo.create_recipe(user.id, message.text, recipe_text)
            
            # Delete waiting message and send recipe
            await waiting_message.delete()
            
            text = (
                "🍳 <b>Вот твой рецепт без сахара!</b>\n\n"
                f"<b>Ингредиенты:</b> {message.text}\n\n"
                f"<b>Рецепт:</b>\n{recipe_text}"
            )
            
            await message.answer(text, parse_mode="HTML")
            
        except Exception as e:
            from loguru import logger
            logger.error(f"Error creating recipe: {e}")
            
            # Delete waiting message and send error
            await waiting_message.delete()
            
            text = (
                "❌ <b>Не удалось создать рецепт</b>\n\n"
                "Попробуй еще раз или обратись к администратору."
            )
            
            await message.answer(text, parse_mode="HTML")
    
    async def handle_sweet_craving(self, message: Message, session: AsyncSession):
        """Handle sweet craving messages."""
        user = await self.get_user(session, message.from_user.id)
        
        # Get alternative snacks
        recipe_service = self.get_recipe_service()
        alternatives = await recipe_service.get_alternative_snacks()
        
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

    async def create_slip_analysis_from_text(self, message: Message, session: AsyncSession):
        """Create slip analysis from text message."""
        user = await self.get_user(session, message.from_user.id)
        note_repo = await self.get_note_repo(session)
        
        # Send processing message
        processing_message = await message.answer(
            "⏳ <b>Сохраняю анализ срыва...</b>",
            parse_mode="HTML"
        )
        
        try:
            # Create note with slip analysis prefix
            analysis_text = f"📝 АНАЛИЗ СРЫВА:\n\n{message.text}"
            await note_repo.create_note(user.id, analysis_text)
            
            # Delete processing message
            await processing_message.delete()
            
            text = (
                "✅ <b>Анализ срыва сохранен!</b>\n\n"
                "Отличная работа! Анализируя причины срывов, ты становишься сильнее.\n\n"
                "💡 <b>Советы:</b>\n"
                "• Перечитывай этот анализ перед сложными ситуациями\n"
                "• Используй план, который ты составил\n"
                "• Помни: каждый срыв - это урок\n\n"
                "💪 Завтра новый день! Ты справишься!"
            )
            
            keyboard = [
                [
                    InlineKeyboardButton(text="💪 Мотивация", callback_data="menu_motivation"),
                    InlineKeyboardButton(text="🍳 Рецепты", callback_data="menu_recipes")
                ],
                [InlineKeyboardButton(text="🔙 Главное меню", callback_data="menu_back")]
            ]
            
            await message.answer(text, reply_markup=InlineKeyboardMarkup(inline_keyboard=keyboard), parse_mode="HTML")
            
        except Exception as e:
            from loguru import logger
            logger.error(f"Error creating slip analysis: {e}")
            
            # Delete processing message and send error
            await processing_message.delete()
            
            text = (
                "❌ <b>Не удалось сохранить анализ срыва</b>\n\n"
                "Попробуй еще раз или обратись к администратору."
            )
            
            await message.answer(text, parse_mode="HTML")

    def get_user_state_service(self):
        """Get user state service from container."""
        from di.container import container
        return container.user_state_service 