from aiogram import Router, F
from aiogram.types import Message, CallbackQuery, InlineKeyboardMarkup, InlineKeyboardButton
from aiogram.filters import Command
from sqlalchemy.ext.asyncio import AsyncSession

from handlers.base import BaseHandler
from di.dependencies import get_session


class NotesHandler(BaseHandler):
    """Handler for notes functionality."""
    
    def __init__(self):
        super().__init__()
        self.router.message.register(self.note_command, Command("note"))
        self.router.callback_query.register(self.handle_notes, F.data.startswith("note_"))
    
    async def note_command(self, message: Message):
        """Handle /note command."""
        async for session in get_session():
            await self.start_note_creation(message, session)
    
    async def handle_notes(self, callback: CallbackQuery):
        """Handle notes menu actions."""
        async for session in get_session():
            action = callback.data.split("_")[1]
            
            if action == "create":
                await self.start_note_creation(callback.message, session)
            elif action == "list":
                await self.show_notes_list(callback, session)
            
            await callback.answer()
    
    async def start_note_creation(self, message: Message, session: AsyncSession):
        """Start note creation process."""
        text = (
            "📝 <b>Создание новой заметки</b>\n\n"
            "Напиши свои мысли, чувства или достижения за сегодня.\n"
            "Это поможет тебе отслеживать свой прогресс!\n\n"
            "Просто напиши сообщение с текстом заметки."
        )
        
        keyboard = [[InlineKeyboardButton(text="🔙 Назад", callback_data="menu_back")]]
        await message.answer(text, reply_markup=InlineKeyboardMarkup(inline_keyboard=keyboard), parse_mode="HTML")
    
    async def show_notes_list(self, callback: CallbackQuery, session: AsyncSession):
        """Show user's notes list."""
        user = await self.get_user(session, callback.from_user.id)
        note_repo = await self.get_note_repo(session)
        
        notes = await note_repo.get_user_notes(user.id, limit=10)
        
        if notes:
            text = "📝 <b>Твои последние заметки:</b>\n\n"
            for i, note in enumerate(notes, 1):
                date_str = note.created_at.strftime("%d.%m.%Y")
                text += f"<b>{i}.</b> {date_str}\n{note.content[:100]}{'...' if len(note.content) > 100 else ''}\n\n"
        else:
            text = "📝 У тебя пока нет заметок.\n\nСоздай первую заметку, чтобы начать вести дневник!"
        
        keyboard = [[InlineKeyboardButton(text="🔙 Назад", callback_data="menu_back")]]
        await callback.message.edit_text(text, reply_markup=InlineKeyboardMarkup(inline_keyboard=keyboard), parse_mode="HTML") 