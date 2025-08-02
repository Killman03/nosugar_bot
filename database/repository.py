from datetime import date, datetime
from typing import Optional, List
from sqlalchemy import select, func, desc
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from database.models import User, CheckIn, Note, Challenge, Recipe


class UserRepository:
    """Repository for user operations."""
    
    def __init__(self, session: AsyncSession):
        self.session = session
    
    async def get_by_telegram_id(self, telegram_user_id: int) -> Optional[User]:
        """Get user by Telegram user ID."""
        result = await self.session.execute(
            select(User).where(User.user_id == telegram_user_id)
        )
        return result.scalar_one_or_none()
    
    async def create_user(self, telegram_user_id: int, username: Optional[str] = None,
                         first_name: Optional[str] = None, last_name: Optional[str] = None) -> User:
        """Create a new user."""
        user = User(
            user_id=telegram_user_id,
            username=username,
            first_name=first_name,
            last_name=last_name
        )
        self.session.add(user)
        await self.session.commit()
        await self.session.refresh(user)
        return user
    
    async def get_or_create_user(self, telegram_user_id: int, username: Optional[str] = None,
                                first_name: Optional[str] = None, last_name: Optional[str] = None) -> User:
        """Get existing user or create new one."""
        user = await self.get_by_telegram_id(telegram_user_id)
        if user is None:
            user = await self.create_user(telegram_user_id, username, first_name, last_name)
        return user
    
    async def update_streak(self, user_id: int, current_streak: int, longest_streak: int) -> None:
        """Update user's streak information."""
        await self.session.execute(
            select(User).where(User.id == user_id)
        )
        user = await self.session.get(User, user_id)
        if user:
            user.current_streak = current_streak
            user.longest_streak = max(user.longest_streak, longest_streak)
            user.updated_at = datetime.utcnow()
            await self.session.commit()


class CheckInRepository:
    """Repository for check-in operations."""
    
    def __init__(self, session: AsyncSession):
        self.session = session
    
    async def get_today_checkin(self, user_id: int) -> Optional[CheckIn]:
        """Get today's check-in for user."""
        today = date.today()
        result = await self.session.execute(
            select(CheckIn).where(
                CheckIn.user_id == user_id,
                CheckIn.check_date == today
            )
        )
        return result.scalar_one_or_none()
    
    async def create_checkin(self, user_id: int, success: bool) -> CheckIn:
        """Create a new check-in."""
        checkin = CheckIn(
            user_id=user_id,
            check_date=date.today(),
            success=success
        )
        self.session.add(checkin)
        await self.session.commit()
        await self.session.refresh(checkin)
        return checkin
    
    async def update_streak(self, user_id: int, success: bool) -> None:
        """Update user streak based on check-in result."""
        user = await self.session.get(User, user_id)
        if user:
            if success:
                user.current_streak += 1
                user.longest_streak = max(user.longest_streak, user.current_streak)
            else:
                user.current_streak = 0
            
            user.total_days += 1
            if not success:
                user.total_slip_ups += 1
            
            user.updated_at = datetime.utcnow()
            await self.session.commit()
    
    async def get_user_stats(self, user_id: int) -> dict:
        """Get user statistics."""
        # Total days
        total_days_result = await self.session.execute(
            select(func.count(CheckIn.id)).where(CheckIn.user_id == user_id)
        )
        total_days = total_days_result.scalar() or 0
        
        # Success days
        success_days_result = await self.session.execute(
            select(func.count(CheckIn.id)).where(
                CheckIn.user_id == user_id,
                CheckIn.success == True
            )
        )
        success_days = success_days_result.scalar() or 0
        
        # Slip ups
        slip_ups_result = await self.session.execute(
            select(func.count(CheckIn.id)).where(
                CheckIn.user_id == user_id,
                CheckIn.success == False
            )
        )
        slip_ups = slip_ups_result.scalar() or 0
        
        return {
            "total_days": total_days,
            "success_count": success_days,
            "fail_count": slip_ups,
            "success_rate": (success_days / total_days * 100) if total_days > 0 else 0
        }
    
    async def get_current_streak(self, user_id: int) -> int:
        """Calculate current streak for user."""
        result = await self.session.execute(
            select(CheckIn)
            .where(CheckIn.user_id == user_id)
            .order_by(desc(CheckIn.check_date))
        )
        checkins = result.scalars().all()
        
        if not checkins:
            return 0
        
        streak = 0
        current_date = date.today()
        
        for checkin in checkins:
            if checkin.success:
                streak += 1
            else:
                break
        
        return streak


class NoteRepository:
    """Repository for note operations."""
    
    def __init__(self, session: AsyncSession):
        self.session = session
    
    async def create_note(self, user_id: int, content: str) -> Note:
        """Create a new note."""
        note = Note(
            user_id=user_id,
            content=content
        )
        self.session.add(note)
        await self.session.commit()
        await self.session.refresh(note)
        return note
    
    async def get_user_notes(self, user_id: int, limit: int = 10) -> List[Note]:
        """Get user's recent notes."""
        result = await self.session.execute(
            select(Note)
            .where(Note.user_id == user_id)
            .order_by(desc(Note.created_at))
            .limit(limit)
        )
        return result.scalars().all()


class ChallengeRepository:
    """Repository for challenge operations."""
    
    def __init__(self, session: AsyncSession):
        self.session = session
    
    async def get_today_challenge(self, user_id: int) -> Optional[Challenge]:
        """Get today's challenge for user."""
        today = date.today()
        result = await self.session.execute(
            select(Challenge).where(
                Challenge.user_id == user_id,
                Challenge.challenge_date == today
            )
        )
        return result.scalar_one_or_none()
    
    async def create_challenge(self, user_id: int, challenge_text: str) -> Challenge:
        """Create a new challenge."""
        challenge = Challenge(
            user_id=user_id,
            challenge_date=date.today(),
            challenge_text=challenge_text
        )
        self.session.add(challenge)
        await self.session.commit()
        await self.session.refresh(challenge)
        return challenge
    
    async def complete_challenge(self, challenge_id: int) -> None:
        """Mark challenge as completed."""
        challenge = await self.session.get(Challenge, challenge_id)
        if challenge:
            challenge.completed = True
            await self.session.commit()


class RecipeRepository:
    """Repository for recipe operations."""
    
    def __init__(self, session: AsyncSession):
        self.session = session
    
    async def create_recipe(self, user_id: int, ingredients: str, recipe_text: str) -> Recipe:
        """Create a new recipe."""
        recipe = Recipe(
            user_id=user_id,
            ingredients=ingredients,
            recipe_text=recipe_text
        )
        self.session.add(recipe)
        await self.session.commit()
        await self.session.refresh(recipe)
        return recipe
    
    async def get_user_recipes(self, user_id: int, limit: int = 5) -> List[Recipe]:
        """Get user's recent recipes."""
        result = await self.session.execute(
            select(Recipe)
            .where(Recipe.user_id == user_id)
            .order_by(desc(Recipe.created_at))
            .limit(limit)
        )
        return result.scalars().all() 