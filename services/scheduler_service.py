import asyncio
from datetime import datetime, time, timedelta
from typing import List
try:
    from zoneinfo import ZoneInfo
except ImportError:
    # Fallback for older Python versions
    from backports.zoneinfo import ZoneInfo
from loguru import logger

from database.repository import UserRepository, CheckInRepository, ChallengeRepository


class SchedulerService:
    """Service for scheduling daily reminders and weekly challenges."""
    
    def __init__(self):
        self.bot = None
        self.reminder_time = time(19, 0)  # 19:00 Bishkek time
        self.challenge_time = time(7, 0)  # 7:00 Bishkek time
        
        # Try to get Bishkek timezone, fallback to UTC+6 if not available
        try:
            self.bishkek_tz = ZoneInfo("Asia/Bishkek")
        except Exception:
            # Fallback to UTC+6 (Bishkek time)
            from datetime import timezone, timedelta
            self.bishkek_tz = timezone(timedelta(hours=6))
            logger.warning("Asia/Bishkek timezone not found, using UTC+6 as fallback")
        
        self.is_running = False
    
    def set_bot(self, bot):
        """Set bot instance."""
        self.bot = bot
    
    async def start_scheduler(self):
        """Start the reminder scheduler."""
        if self.is_running:
            return
        
        self.is_running = True
        logger.info("Starting daily reminder and weekly challenge scheduler...")
        
        while self.is_running:
            try:
                await self._wait_until_next_task()
                await self._process_scheduled_tasks()
            except Exception as e:
                logger.error(f"Error in scheduler: {e}")
                await asyncio.sleep(60)  # Wait 1 minute before retrying
    
    async def stop_scheduler(self):
        """Stop the reminder scheduler."""
        self.is_running = False
        logger.info("Stopping daily reminder scheduler...")
    
    async def _wait_until_next_task(self):
        """Wait until next scheduled task (reminder or challenge)."""
        now = datetime.now(self.bishkek_tz)
        
        # Calculate next reminder time
        next_reminder = datetime.combine(now.date(), self.reminder_time, tzinfo=self.bishkek_tz)
        if now.time() >= self.reminder_time:
            next_reminder = datetime.combine(
                now.date() + timedelta(days=1), 
                self.reminder_time, 
                tzinfo=self.bishkek_tz
            )
        
        # Calculate next challenge time (Mondays at 7:00)
        days_until_monday = (7 - now.weekday()) % 7  # 0 = Monday
        if days_until_monday == 0 and now.time() >= self.challenge_time:
            days_until_monday = 7  # Next Monday
        
        next_challenge = datetime.combine(
            now.date() + timedelta(days=days_until_monday),
            self.challenge_time,
            tzinfo=self.bishkek_tz
        )
        
        # Choose the earlier task
        if next_reminder < next_challenge:
            next_task = next_reminder
            task_type = "reminder"
        else:
            next_task = next_challenge
            task_type = "challenge"
        
        wait_seconds = (next_task - now).total_seconds()
        logger.info(f"Next {task_type} scheduled for {next_task.strftime('%Y-%m-%d %H:%M')} (waiting {wait_seconds:.0f} seconds)")
        
        await asyncio.sleep(wait_seconds)
    
    async def _process_scheduled_tasks(self):
        """Process scheduled tasks (reminders and challenges)."""
        now = datetime.now(self.bishkek_tz)
        
        # Check if it's time for daily reminders
        if now.time().hour == self.reminder_time.hour and now.time().minute == self.reminder_time.minute:
            await self._send_daily_reminders()
        
        # Check if it's Monday and time for weekly challenges
        if now.weekday() == 0 and now.time().hour == self.challenge_time.hour and now.time().minute == self.challenge_time.minute:
            await self._create_weekly_challenges()
    
    async def _send_daily_reminders(self):
        """Send daily reminders to users who haven't checked in."""
        # Try to get bot from container if not set
        if not self.bot:
            try:
                from di.container import container
                self.bot = container.bot
                logger.info("Bot automatically set from container")
            except Exception as e:
                logger.error(f"Failed to get bot from container: {e}")
                return
        
        if not self.bot:
            logger.error("Bot not set in scheduler")
            return
        
        try:
            # Get session maker from container
            from di.container import container
            session_maker = container.session_maker
            
            async with session_maker() as session:
                user_repo = UserRepository(session)
                checkin_repo = CheckInRepository(session)
                
                # Get all users
                users = await self._get_all_users(user_repo)
                
                for user in users:
                    try:
                        # Check if user has checked in today
                        today_checkin = await checkin_repo.get_today_checkin(user.id)
                        
                        if not today_checkin:
                            # Send reminder
                            await self._send_reminder_to_user(user)
                            logger.info(f"Sent reminder to user {user.user_id}")
                        
                    except Exception as e:
                        logger.error(f"Error sending reminder to user {user.user_id}: {e}")
                
        except Exception as e:
            logger.error(f"Error in daily reminders: {e}")
    
    async def _create_weekly_challenges(self):
        """Create weekly challenges for all users using AI."""
        # Try to get bot from container if not set
        if not self.bot:
            try:
                from di.container import container
                self.bot = container.bot
                logger.info("Bot automatically set from container")
            except Exception as e:
                logger.error(f"Failed to get bot from container: {e}")
                return
        
        if not self.bot:
            logger.error("Bot not set in scheduler")
            return
        
        try:
            # Get session maker and AI service from container
            from di.container import container
            session_maker = container.session_maker
            ai_service = container.ai_service
            
            async with session_maker() as session:
                user_repo = UserRepository(session)
                challenge_repo = ChallengeRepository(session)
                
                # Get all users
                users = await self._get_all_users(user_repo)
                
                # Generate challenge using AI
                challenge_text = await ai_service.generate_weekly_challenge()
                
                logger.info(f"Generated weekly challenge: {challenge_text}")
                
                # Create challenge for all users
                for user in users:
                    try:
                        await challenge_repo.create_challenge(user.id, challenge_text)
                        logger.info(f"Created challenge for user {user.user_id}")
                        
                        # Send notification to user about new challenge
                        await self._send_challenge_notification(user, challenge_text)
                        
                    except Exception as e:
                        logger.error(f"Error creating challenge for user {user.user_id}: {e}")
                
        except Exception as e:
            logger.error(f"Error creating weekly challenges: {e}")
    
    async def _send_challenge_notification(self, user, challenge_text: str):
        """Send notification about new weekly challenge."""
        try:
            text = (
                "🎯 <b>Новый недельный челлендж!</b>\n\n"
                f"{challenge_text}\n\n"
                "💪 Выполни этот челлендж и стань сильнее!\n"
                "🔥 Твоя текущая серия: <b>{}</b> дней"
            ).format(user.current_streak)
            
            from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
            
            keyboard = [
                [InlineKeyboardButton(text="✅ Выполнил", callback_data="challenge_complete")],
                [InlineKeyboardButton(text="📋 Мои челленджи", callback_data="menu_challenge")]
            ]
            
            await self.bot.send_message(
                chat_id=user.user_id,
                text=text,
                reply_markup=InlineKeyboardMarkup(inline_keyboard=keyboard),
                parse_mode="HTML"
            )
            
        except Exception as e:
            logger.error(f"Error sending challenge notification to user {user.user_id}: {e}")
    
    async def _get_all_users(self, user_repo: UserRepository) -> List:
        """Get all users from database."""
        # This is a simplified version - you might want to add pagination
        # for large user bases
        try:
            # Assuming we have a method to get all users
            # You might need to implement this in UserRepository
            from database.models import User
            from sqlalchemy import select
            
            result = await user_repo.session.execute(select(User))
            return result.scalars().all()
        except Exception as e:
            logger.error(f"Error getting users: {e}")
            return []
    
    async def _send_reminder_to_user(self, user):
        """Send reminder message to specific user."""
        try:
            text = (
                "🔔 <b>Напоминание о чек-ине!</b>\n\n"
                "Привет! Не забудь отметить свой прогресс за сегодня.\n\n"
                "Как прошел твой день без сахара?\n\n"
                "🔥 Твоя текущая серия: <b>{}</b> дней\n"
                "🏆 Лучшая серия: <b>{}</b> дней"
            ).format(user.current_streak, user.longest_streak)
            
            from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
            
            keyboard = [
                [
                    InlineKeyboardButton(text="✅ Удержался", callback_data="checkin_success"),
                    InlineKeyboardButton(text="❌ Сорвался", callback_data="checkin_fail")
                ]
            ]
            
            await self.bot.send_message(
                chat_id=user.user_id,
                text=text,
                reply_markup=InlineKeyboardMarkup(inline_keyboard=keyboard),
                parse_mode="HTML"
            )
            
        except Exception as e:
            logger.error(f"Error sending reminder to user {user.user_id}: {e}")
    
    async def send_test_reminder(self, user_id: int):
        """Send test reminder to specific user (for testing)."""
        # Try to get bot from container if not set
        if not self.bot:
            try:
                from di.container import container
                self.bot = container.bot
                logger.info("Bot automatically set from container")
            except Exception as e:
                logger.error(f"Failed to get bot from container: {e}")
                return
        
        if not self.bot:
            logger.error("Bot not set in scheduler")
            return
        
        try:
            text = (
                "🧪 <b>Тестовое напоминание!</b>\n\n"
                "Это тестовое сообщение для проверки системы напоминаний.\n\n"
                "Как прошел твой день без сахара?"
            )
            
            from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
            
            keyboard = [
                [
                    InlineKeyboardButton(text="✅ Удержался", callback_data="checkin_success"),
                    InlineKeyboardButton(text="❌ Сорвался", callback_data="checkin_fail")
                ]
            ]
            
            await self.bot.send_message(
                chat_id=user_id,
                text=text,
                reply_markup=InlineKeyboardMarkup(inline_keyboard=keyboard),
                parse_mode="HTML"
            )
            
            logger.info(f"Sent test reminder to user {user_id}")
            
        except Exception as e:
            logger.error(f"Error sending test reminder to user {user_id}: {e}")
    
    async def create_test_challenge(self, user_id: int):
        """Create test challenge for specific user (for testing)."""
        # Try to get bot from container if not set
        if not self.bot:
            try:
                from di.container import container
                self.bot = container.bot
                logger.info("Bot automatically set from container")
            except Exception as e:
                logger.error(f"Failed to get bot from container: {e}")
                return
        
        if not self.bot:
            logger.error("Bot not set in scheduler")
            return
        
        try:
            # Get session maker and AI service from container
            from di.container import container
            session_maker = container.session_maker
            ai_service = container.ai_service
            
            async with session_maker() as session:
                user_repo = UserRepository(session)
                challenge_repo = ChallengeRepository(session)
                
                # Get user
                user = await user_repo.get_by_telegram_id(user_id)
                if not user:
                    logger.error(f"User {user_id} not found")
                    return
                
                # Generate test challenge
                challenge_text = await ai_service.generate_weekly_challenge()
                
                # Create challenge
                await challenge_repo.create_challenge(user.id, challenge_text)
                
                # Send notification
                await self._send_challenge_notification(user, challenge_text)
                
                logger.info(f"Created test challenge for user {user_id}")
                
        except Exception as e:
            logger.error(f"Error creating test challenge for user {user_id}: {e}")


# Global scheduler instance
scheduler_service = SchedulerService() 