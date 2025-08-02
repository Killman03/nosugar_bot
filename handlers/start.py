from aiogram import Router, F
from aiogram.types import Message, InlineKeyboardMarkup, InlineKeyboardButton, CallbackQuery
from aiogram.filters import Command
from sqlalchemy.ext.asyncio import AsyncSession

from handlers.base import BaseHandler
from di.dependencies import get_session


class StartHandler(BaseHandler):
    """Handler for /start command and main menu."""
    
    def __init__(self):
        super().__init__()
        self.router.message.register(self.start_command, Command("start"))
        self.router.callback_query.register(self.handle_menu, F.data.startswith("menu_"))
    
    async def start_command(self, message: Message):
        """Handle /start command."""
        async for session in get_session():
            # Get or create user
            user = await self.get_user(session, message.from_user.id)
            
            # Update user info if needed
            if user.username != message.from_user.username:
                user.username = message.from_user.username
                user.first_name = message.from_user.first_name
                user.last_name = message.from_user.last_name
                await session.commit()
            
            welcome_text = (
                f"👋 Привет, {message.from_user.first_name}!\n\n"
                "🍭 Я помогу тебе отказаться от сахара и вести здоровый образ жизни!\n\n"
                "📊 Твоя текущая серия: <b>{}</b> дней\n"
                "🏆 Лучшая серия: <b>{}</b> дней\n\n"
                "Выбери действие:"
            ).format(user.current_streak, user.longest_streak)
            
            keyboard = self.get_main_menu_keyboard()
            
            await message.answer(welcome_text, reply_markup=keyboard, parse_mode="HTML")
    
    def get_main_menu_keyboard(self) -> InlineKeyboardMarkup:
        """Create main menu keyboard."""
        keyboard = [
            [
                InlineKeyboardButton(text="✅ Чек-ин", callback_data="menu_checkin"),
                InlineKeyboardButton(text="📊 Статистика", callback_data="menu_stats")
            ],
            [
                InlineKeyboardButton(text="🍳 Рецепты", callback_data="menu_recipes"),
                InlineKeyboardButton(text="🎯 Челлендж", callback_data="menu_challenge")
            ],
            [
                InlineKeyboardButton(text="📝 Заметки", callback_data="menu_notes"),
                InlineKeyboardButton(text="💪 Мотивация", callback_data="menu_motivation")
            ],
            [
                InlineKeyboardButton(text="ℹ️ Помощь", callback_data="menu_help")
            ]
        ]
        return InlineKeyboardMarkup(inline_keyboard=keyboard)
    
    async def handle_menu(self, callback: CallbackQuery):
        """Handle menu button clicks."""
        async for session in get_session():
            action = callback.data.split("_")[1]
            
            if action == "checkin":
                await self.show_checkin_menu(callback, session)
            elif action == "stats":
                await self.show_stats(callback, session)
            elif action == "recipes":
                await self.show_recipes_menu(callback, session)
            elif action == "challenge":
                await self.show_challenge(callback, session)
            elif action == "notes":
                await self.show_notes_menu(callback, session)
            elif action == "motivation":
                await self.show_motivation(callback, session)
            elif action == "help":
                await self.show_help(callback, session)
            
            await callback.answer()
    
    async def show_checkin_menu(self, callback: CallbackQuery, session: AsyncSession):
        """Show check-in menu."""
        user = await self.get_user(session, callback.from_user.id)
        checkin_repo = await self.get_checkin_repo(session)
        
        today_checkin = await checkin_repo.get_today_checkin(user.id)
        
        if today_checkin:
            text = (
                f"Сегодня ты уже отметился: {'✅ Удержался' if today_checkin.success else '❌ Сорвался'}\n\n"
                f"Твоя серия: {user.current_streak} дней"
            )
        else:
            text = (
                f"Сегодня ты еще не отмечался!\n\n"
                f"Твоя серия: {user.current_streak} дней\n\n"
                "Как прошел твой день?"
            )
        
        keyboard = [
            [
                InlineKeyboardButton(text="✅ Удержался", callback_data="checkin_success"),
                InlineKeyboardButton(text="❌ Сорвался", callback_data="checkin_fail")
            ],
            [InlineKeyboardButton(text="🔙 Назад", callback_data="menu_back")]
        ]
        
        await callback.message.edit_text(text, reply_markup=InlineKeyboardMarkup(inline_keyboard=keyboard))
    
    async def show_stats(self, callback: CallbackQuery, session: AsyncSession):
        """Show user statistics."""
        user = await self.get_user(session, callback.from_user.id)
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
        
        keyboard = [[InlineKeyboardButton(text="🔙 Назад", callback_data="menu_back")]]
        await callback.message.edit_text(text, reply_markup=InlineKeyboardMarkup(inline_keyboard=keyboard), parse_mode="HTML")
    
    async def show_recipes_menu(self, callback: CallbackQuery, session: AsyncSession):
        """Show recipes menu."""
        text = (
            "🍳 <b>Рецепты без сахара</b>\n\n"
            "Здесь ты можешь найти рецепты полезных блюд без сахара.\n\n"
            "Выбери действие:"
        )
        
        keyboard = [
            [
                InlineKeyboardButton(text="🔍 Найти рецепт", callback_data="recipe_create"),
                InlineKeyboardButton(text="📋 Мои рецепты", callback_data="recipe_list")
            ],
            [InlineKeyboardButton(text="🔙 Назад", callback_data="menu_back")]
        ]
        
        await callback.message.edit_text(text, reply_markup=InlineKeyboardMarkup(inline_keyboard=keyboard), parse_mode="HTML")
    
    async def show_challenge(self, callback: CallbackQuery, session: AsyncSession):
        """Show daily challenge."""
        user = await self.get_user(session, callback.from_user.id)
        challenge_repo = await self.get_challenge_repo(session)
        
        today_challenge = await challenge_repo.get_today_challenge(user.id)
        
        if today_challenge:
            status = "✅ Выполнено" if today_challenge.completed else "⏳ В процессе"
            text = (
                f"🎯 <b>Сегодняшний челлендж:</b>\n\n"
                f"{today_challenge.description}\n\n"
                f"Статус: {status}"
            )
            
            keyboard = []
            if not today_challenge.completed:
                keyboard.append([InlineKeyboardButton(text="✅ Выполнил", callback_data="challenge_complete")])
            keyboard.append([InlineKeyboardButton(text="🔙 Назад", callback_data="menu_back")])
        else:
            text = "🎯 Сегодня нет активного челленджа!"
            keyboard = [[InlineKeyboardButton(text="🔙 Назад", callback_data="menu_back")]]
        
        await callback.message.edit_text(text, reply_markup=InlineKeyboardMarkup(inline_keyboard=keyboard), parse_mode="HTML")
    
    async def show_notes_menu(self, callback: CallbackQuery, session: AsyncSession):
        """Show notes menu."""
        text = (
            "📝 <b>Заметки</b>\n\n"
            "Здесь ты можешь вести дневник своих успехов и записывать мысли.\n\n"
            "Выбери действие:"
        )
        
        keyboard = [
            [
                InlineKeyboardButton(text="✏️ Новая заметка", callback_data="note_create"),
                InlineKeyboardButton(text="📋 Мои заметки", callback_data="note_list")
            ],
            [InlineKeyboardButton(text="🔙 Назад", callback_data="menu_back")]
        ]
        
        await callback.message.edit_text(text, reply_markup=InlineKeyboardMarkup(inline_keyboard=keyboard), parse_mode="HTML")
    
    async def show_motivation(self, callback: CallbackQuery, session: AsyncSession):
        """Show motivation message."""
        motivation_service = self.get_motivation_service()
        text = motivation_service.get_daily_motivation()
        
        keyboard = [[InlineKeyboardButton(text="🔙 Назад", callback_data="menu_back")]]
        await callback.message.edit_text(text, reply_markup=InlineKeyboardMarkup(inline_keyboard=keyboard))
    
    async def show_help(self, callback: CallbackQuery, session: AsyncSession):
        """Show help information."""
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
        
        keyboard = [[InlineKeyboardButton(text="🔙 Назад", callback_data="menu_back")]]
        await callback.message.edit_text(text, reply_markup=InlineKeyboardMarkup(inline_keyboard=keyboard), parse_mode="HTML") 