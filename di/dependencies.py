from typing import AsyncGenerator
from sqlalchemy.ext.asyncio import AsyncSession

from di.container import container
from database.repository import (
    UserRepository, 
    CheckInRepository, 
    NoteRepository, 
    ChallengeRepository, 
    RecipeRepository
)
from services.motivation_service import MotivationService
from services.recipe_service import RecipeService
from services.ai_service import AIService


async def get_session() -> AsyncGenerator[AsyncSession, None]:
    """Get database session dependency."""
    async with container.session_maker() as session:
        yield session


def get_motivation_service() -> MotivationService:
    """Get motivation service dependency."""
    return container.motivation_service


def get_recipe_service() -> RecipeService:
    """Get recipe service dependency."""
    return container.recipe_service


def get_ai_service() -> AIService:
    """Get AI service dependency."""
    return container.ai_service


def get_user_repository(session: AsyncSession) -> UserRepository:
    """Get user repository dependency."""
    return container.get_user_repository(session)


def get_checkin_repository(session: AsyncSession) -> CheckInRepository:
    """Get check-in repository dependency."""
    return container.get_checkin_repository(session)


def get_note_repository(session: AsyncSession) -> NoteRepository:
    """Get note repository dependency."""
    return container.get_note_repository(session)


def get_challenge_repository(session: AsyncSession) -> ChallengeRepository:
    """Get challenge repository dependency."""
    return container.get_challenge_repository(session)


def get_recipe_repository(session: AsyncSession) -> RecipeRepository:
    """Get recipe repository dependency."""
    return container.get_recipe_repository(session) 