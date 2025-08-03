from aiogram import Router, F
from aiogram.types import Message, CallbackQuery, InlineKeyboardMarkup, InlineKeyboardButton, ReplyKeyboardMarkup, KeyboardButton
from aiogram.filters import Command
from sqlalchemy.ext.asyncio import AsyncSession

from handlers.base import BaseHandler
from di.dependencies import get_session


class StartHandler(BaseHandler):
    """Handler for /start command and main menu."""
    
    def __init__(self):
        super().__init__()
        self.router.message.register(self.start_command, Command("start"))
        self.router.message.register(self.test_reminder_command, Command("test_reminder"))
        self.router.message.register(self.test_challenge_command, Command("test_challenge"))
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
            
            # Show inline keyboard for menu options
            inline_keyboard = self.get_main_menu_keyboard()
            
            # Show reply keyboard with Start button
            reply_keyboard = self.get_reply_keyboard()
            
            await message.answer(
                welcome_text, 
                reply_markup=reply_keyboard,
                parse_mode="HTML"
            )
            
            # Send inline keyboard as separate message
            await message.answer(
                "Выбери действие из меню ниже:",
                reply_markup=inline_keyboard
            )
    
    async def test_reminder_command(self, message: Message):
        """Handle /test_reminder command for testing reminders."""
        try:
            scheduler = self.get_scheduler_service()
            await scheduler.send_test_reminder(message.from_user.id)
            
            await message.answer(
                "🧪 <b>Тестовое напоминание отправлено!</b>\n\n"
                "Проверь, получил ли ты сообщение с напоминанием.",
                parse_mode="HTML"
            )
        except Exception as e:
            from loguru import logger
            logger.error(f"Error sending test reminder: {e}")
            await message.answer("❌ Ошибка при отправке тестового напоминания.")
    
    async def test_challenge_command(self, message: Message):
        """Handle /test_challenge command for testing challenge creation."""
        try:
            scheduler = self.get_scheduler_service()
            await scheduler.create_test_challenge(message.from_user.id)
            
            await message.answer(
                "🧪 <b>Тестовый челлендж создан!</b>\n\n"
                "Проверь, получил ли ты сообщение с новым челленджем.",
                parse_mode="HTML"
            )
        except Exception as e:
            from loguru import logger
            logger.error(f"Error creating test challenge: {e}")
            await message.answer("❌ Ошибка при создании тестового челленджа.")
    
    def get_scheduler_service(self):
        """Get scheduler service from container."""
        from di.container import container
        return container.scheduler_service
    
    def get_main_menu_keyboard(self) -> InlineKeyboardMarkup:
        """Create main menu keyboard."""
        keyboard = [
            [
                InlineKeyboardButton(text="✅ Чек-ин", callback_data="menu_checkin"),
                InlineKeyboardButton(text="📊 Статистика", callback_data="menu_stats")
            ],
            [
                InlineKeyboardButton(text="🍳 Рецепты", callback_data="menu_recipes"),
                InlineKeyboardButton(text="📝 Заметки", callback_data="menu_notes")
            ],
            [
                InlineKeyboardButton(text="🎯 Челленджи", callback_data="menu_challenge"),
                InlineKeyboardButton(text="💪 Мотивация", callback_data="menu_motivation")
            ],
            [
                InlineKeyboardButton(text="🍭 Хочу сладкого", callback_data="menu_sweet_craving"),
                InlineKeyboardButton(text="📝 Анализ срыва", callback_data="menu_slip_analysis")
            ],
            [
                InlineKeyboardButton(text="ℹ️ Помощь", callback_data="menu_help")
            ]
        ]
        return InlineKeyboardMarkup(inline_keyboard=keyboard)
    
    def get_reply_keyboard(self) -> ReplyKeyboardMarkup:
        """Create reply keyboard with Start button."""
        keyboard = [
            [KeyboardButton(text="/start")]
        ]
        return ReplyKeyboardMarkup(keyboard=keyboard, resize_keyboard=True, one_time_keyboard=False)
    
    async def handle_menu(self, callback: CallbackQuery):
        """Handle menu button clicks."""
        async for session in get_session():
            # Debug logging
            from loguru import logger
            logger.info(f"Callback data: {callback.data}")
            
            # Handle different menu actions
            if callback.data == "menu_checkin":
                await self.show_checkin_menu(callback, session)
            elif callback.data == "menu_stats":
                await self.show_stats(callback, session)
            elif callback.data == "menu_recipes":
                await self.show_recipes_menu(callback, session)
            elif callback.data == "menu_notes":
                await self.show_notes_menu(callback, session)
            elif callback.data == "menu_challenge":
                await self.show_challenge(callback, session)
            elif callback.data == "menu_motivation":
                await self.show_motivation(callback, session)
            elif callback.data == "menu_sweet_craving":
                logger.info("Handling sweet_craving action")
                await self.show_sweet_craving(callback, session)
            elif callback.data == "menu_slip_analysis":
                await self.show_slip_analysis_menu(callback, session)
            elif callback.data == "menu_help":
                await self.show_help(callback, session)
            elif callback.data == "menu_back":
                # Clear user state and return to main menu
                user_state_service = self.get_user_state_service()
                user_state_service.clear_user_state(callback.from_user.id)
                await self.show_main_menu(callback, session)
            else:
                logger.warning(f"Unknown menu callback data: {callback.data}")
            
            await callback.answer()
    
    async def show_main_menu(self, callback: CallbackQuery, session: AsyncSession):
        """Show main menu."""
        user = await self.get_user(session, callback.from_user.id)
        
        # Refresh user object to get latest data
        await session.refresh(user)
        
        # Debug: log user data
        from loguru import logger
        logger.info(f"User {user.user_id} data in main menu: current_streak={user.current_streak}, longest_streak={user.longest_streak}")
        
        welcome_text = (
            f"👋 Привет, {callback.from_user.first_name}!\n\n"
            "🍭 Я помогу тебе отказаться от сахара и вести здоровый образ жизни!\n\n"
            "📊 Твоя текущая серия: <b>{}</b> дней\n"
            "🏆 Лучшая серия: <b>{}</b> дней\n\n"
            "Выбери действие:"
        ).format(user.current_streak, user.longest_streak)
        
        # Show inline keyboard for menu options
        inline_keyboard = self.get_main_menu_keyboard()
        
        # Show reply keyboard with Start button
        reply_keyboard = self.get_reply_keyboard()
        
        await callback.message.edit_text(
            welcome_text, 
            reply_markup=reply_keyboard,
            parse_mode="HTML"
        )
        
        # Send inline keyboard as separate message
        await callback.message.answer(
            "Выбери действие из меню ниже:",
            reply_markup=inline_keyboard
        )
    
    async def show_checkin_menu(self, callback: CallbackQuery, session: AsyncSession):
        """Show check-in menu."""
        user = await self.get_user(session, callback.from_user.id)
        checkin_repo = await self.get_checkin_repo(session)
        
        # Check if user has already checked in today
        today_checkin = await checkin_repo.get_today_checkin(user.id)
        
        if today_checkin:
            status = "✅ Удержался" if today_checkin.success else "❌ Сорвался"
            text = (
                f"📊 <b>Сегодняшний чек-ин</b>\n\n"
                f"Статус: {status}\n"
                f"🔥 Твоя серия: <b>{user.current_streak}</b> дней\n"
                f"🏆 Лучшая серия: <b>{user.longest_streak}</b> дней\n\n"
                "Завтра можно будет отметить новый день!"
            )
            
            keyboard = [
                [
                    InlineKeyboardButton(text="🍳 Рецепты", callback_data="menu_recipes"),
                    InlineKeyboardButton(text="💪 Мотивация", callback_data="menu_motivation")
                ],
                [InlineKeyboardButton(text="🔙 Назад", callback_data="menu_back")]
            ]
        else:
            text = (
                f"✅ <b>Ежедневный чек-ин</b>\n\n"
                "Как прошел твой день без сахара?\n\n"
                f"🔥 Твоя серия: <b>{user.current_streak}</b> дней\n"
                f"🏆 Лучшая серия: <b>{user.longest_streak}</b> дней"
            )
            
            keyboard = [
                [
                    InlineKeyboardButton(text="✅ Удержался", callback_data="checkin_success"),
                    InlineKeyboardButton(text="❌ Сорвался", callback_data="checkin_fail")
                ],
                [
                    InlineKeyboardButton(text="🍳 Рецепты", callback_data="menu_recipes"),
                    InlineKeyboardButton(text="💪 Мотивация", callback_data="menu_motivation")
                ],
                [InlineKeyboardButton(text="🔙 Назад", callback_data="menu_back")]
            ]
        
        await callback.message.edit_text(text, reply_markup=InlineKeyboardMarkup(inline_keyboard=keyboard), parse_mode="HTML")
    
    async def show_stats(self, callback: CallbackQuery, session: AsyncSession):
        """Show user statistics."""
        user = await self.get_user(session, callback.from_user.id)
        checkin_repo = await self.get_checkin_repo(session)
        
        stats = await checkin_repo.get_user_stats(user.id)
        
        text = (
            f"�� <b>Твоя статистика</b>\n\n"
            f"🔥 Текущая серия: <b>{user.current_streak}</b> дней\n"
            f"🏆 Лучшая серия: <b>{user.longest_streak}</b> дней\n"
            f"📅 Всего дней: <b>{stats['total_days']}</b>\n"
            f"✅ Успешных дней: <b>{stats['success_count']}</b>\n"
            f"❌ Срывов: <b>{stats['fail_count']}</b>\n"
            f"📈 Процент успеха: <b>{stats['success_rate']:.1f}%</b>\n\n"
            f"💪 Продолжай в том же духе!"
        )
        
        keyboard = [
            [
                InlineKeyboardButton(text="✅ Чек-ин", callback_data="menu_checkin"),
                InlineKeyboardButton(text="🍳 Рецепты", callback_data="menu_recipes")
            ],
            [
                InlineKeyboardButton(text="📝 Заметки", callback_data="menu_notes"),
                InlineKeyboardButton(text="🎯 Челленджи", callback_data="menu_challenge")
            ],
            [InlineKeyboardButton(text="🔙 Назад", callback_data="menu_back")]
        ]
        
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
                f"{today_challenge.challenge_text}\n\n"
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
        
        keyboard = [
            [
                InlineKeyboardButton(text="✅ Чек-ин", callback_data="menu_checkin"),
                InlineKeyboardButton(text="🍳 Рецепты", callback_data="menu_recipes")
            ],
            [
                InlineKeyboardButton(text="🍭 Хочу сладкого", callback_data="menu_sweet_craving"),
                InlineKeyboardButton(text="🎯 Челленджи", callback_data="menu_challenge")
            ],
            [InlineKeyboardButton(text="🔙 Назад", callback_data="menu_back")]
        ]
        
        await callback.message.edit_text(text, reply_markup=InlineKeyboardMarkup(inline_keyboard=keyboard))
    
    async def show_help(self, callback: CallbackQuery, session: AsyncSession):
        """Show help information."""
        text = (
            "ℹ️ <b>Помощь</b>\n\n"
            "🍭 <b>Бот для отказа от сахара</b>\n\n"
            "<b>Основные функции:</b>\n"
            "✅ Ежедневные чек-ины\n"
            "📊 Статистика прогресса\n"
            "🍳 Рецепты без сахара\n"
            "🎯 Ежедневные челленджи\n"
            "📝 Дневник заметок\n"
            "💪 Мотивационные сообщения\n\n"
            "<b>Быстрые команды:</b>\n"
            "• Напиши 'хочу сладкого' для альтернатив\n"
            "• Используй кнопки меню для навигации\n"
            "• Нажми '🍭 Хочу сладкого' для быстрого доступа"
        )
        
        keyboard = [
            [
                InlineKeyboardButton(text="✅ Чек-ин", callback_data="menu_checkin"),
                InlineKeyboardButton(text="📊 Статистика", callback_data="menu_stats")
            ],
            [
                InlineKeyboardButton(text="🍳 Рецепты", callback_data="menu_recipes"),
                InlineKeyboardButton(text="📝 Заметки", callback_data="menu_notes")
            ],
            [
                InlineKeyboardButton(text="🎯 Челленджи", callback_data="menu_challenge"),
                InlineKeyboardButton(text="💪 Мотивация", callback_data="menu_motivation")
            ],
            [InlineKeyboardButton(text="🔙 Назад", callback_data="menu_back")]
        ]
        
        await callback.message.edit_text(text, reply_markup=InlineKeyboardMarkup(inline_keyboard=keyboard), parse_mode="HTML")
    
    async def show_sweet_craving(self, callback: CallbackQuery, session: AsyncSession):
        """Show alternatives to sweets."""
        try:
            user = await self.get_user(session, callback.from_user.id)
            
            # Send waiting message first
            waiting_message = await callback.message.edit_text(
                "⏳ <b>Ищу альтернативы сладкому...</b>\n\n"
                "Пожалуйста, подождите немного, пока я подбираю для вас полезные альтернативы! 🍎",
                parse_mode="HTML"
            )
            
            # Get alternative snacks
            recipe_service = self.get_recipe_service()
            alternatives = await recipe_service.get_alternative_snacks()
            
            text = (
                "🍭 <b>Хочешь сладкого? Попробуй эти альтернативы!</b>\n\n"
                f"{alternatives}\n\n"
                "💪 Помни: каждый раз, когда ты выбираешь здоровую альтернативу, "
                "ты становишься сильнее!"
            )
            
            keyboard = [
                [
                    InlineKeyboardButton(text="🍳 Найти рецепт", callback_data="recipe_create"),
                    InlineKeyboardButton(text="💪 Мотивация", callback_data="menu_motivation")
                ],
                [InlineKeyboardButton(text="🔙 Назад", callback_data="menu_back")]
            ]
            
            await callback.message.edit_text(text, reply_markup=InlineKeyboardMarkup(inline_keyboard=keyboard), parse_mode="HTML")
            
        except Exception as e:
            from loguru import logger
            logger.error(f"Error in show_sweet_craving: {e}")
            
            # Fallback message
            text = (
                "🍭 <b>Хочешь сладкого? Попробуй эти альтернативы!</b>\n\n"
                "Вместо сладкого попробуйте:\n\n"
                "🍎 Яблоко с корицей\n"
                "🥜 Горсть орехов (миндаль, грецкие орехи)\n"
                "🥑 Авокадо с солью и перцем\n"
                "🥕 Морковные палочки с хумусом\n"
                "🍓 Клубника или другие ягоды\n"
                "🥚 Вареное яйцо\n"
                "🧀 Кусочек сыра\n"
                "🥬 Листья салата с оливковым маслом\n"
                "🌰 Семечки подсолнуха или тыквы\n"
                "🥛 Греческий йогурт без добавок\n\n"
                "💪 Помни: каждый раз, когда ты выбираешь здоровую альтернативу, "
                "ты становишься сильнее!"
            )
            
            keyboard = [
                [
                    InlineKeyboardButton(text="🍳 Найти рецепт", callback_data="recipe_create"),
                    InlineKeyboardButton(text="💪 Мотивация", callback_data="menu_motivation")
                ],
                [InlineKeyboardButton(text="🔙 Назад", callback_data="menu_back")]
            ]
            
            await callback.message.edit_text(text, reply_markup=InlineKeyboardMarkup(inline_keyboard=keyboard), parse_mode="HTML")

    async def show_slip_analysis_menu(self, callback: CallbackQuery, session: AsyncSession):
        """Show slip analysis menu."""
        text = (
            "📝 <b>Анализ срыва</b>\n\n"
            "Этот инструмент поможет тебе:\n\n"
            "🔍 <b>Понять причины срыва</b>\n"
            "• Что привело к срыву?\n"
            "• Какие эмоции ты испытывал?\n"
            "• Что происходило вокруг?\n\n"
            "💡 <b>Составить план на будущее</b>\n"
            "• Как избежать такой ситуации?\n"
            "• Что можно сделать по-другому?\n"
            "• Какие альтернативы использовать?\n\n"
            "📚 <b>Создать базу знаний</b>\n"
            "• Все анализы сохраняются в заметках\n"
            "• Можно перечитывать перед сложными ситуациями\n"
            "• Отслеживать прогресс в понимании триггеров\n\n"
            "Нажми кнопку ниже, чтобы начать анализ:"
        )
        
        keyboard = [
            [InlineKeyboardButton(text="📝 Начать анализ срыва", callback_data="slip_analysis")],
            [
                InlineKeyboardButton(text="📋 Мои заметки", callback_data="note_list"),
                InlineKeyboardButton(text="💪 Мотивация", callback_data="menu_motivation")
            ],
            [InlineKeyboardButton(text="🔙 Назад", callback_data="menu_back")]
        ]
        
        await callback.message.edit_text(text, reply_markup=InlineKeyboardMarkup(inline_keyboard=keyboard), parse_mode="HTML")

 