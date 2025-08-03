from typing import AsyncGenerator
from aiogram import Bot, Dispatcher
from aiogram.fsm.storage.memory import MemoryStorage
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker

from database.connection import get_session
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
from services.user_state_service import UserStateService
from services.scheduler_service import scheduler_service


class Container:
    """Dependency injection container."""
    
    def __init__(self):
        self._bot: Bot | None = None
        self._dispatcher: Dispatcher | None = None
        self._storage: MemoryStorage | None = None
        self._session_maker: async_sessionmaker | None = None
        
        # Services
        self._motivation_service: MotivationService | None = None
        self._recipe_service: RecipeService | None = None
        self._ai_service: AIService | None = None
        self._user_state_service: UserStateService | None = None
        self._scheduler_service = scheduler_service
    
    @property
    def bot(self) -> Bot:
        """Get bot instance."""
        if self._bot is None:
            raise RuntimeError("Bot not initialized")
        return self._bot
    
    @property
    def dispatcher(self) -> Dispatcher:
        """Get dispatcher instance."""
        if self._dispatcher is None:
            raise RuntimeError("Dispatcher not initialized")
        return self._dispatcher
    
    @property
    def storage(self) -> MemoryStorage:
        """Get storage instance."""
        if self._storage is None:
            raise RuntimeError("Storage not initialized")
        return self._storage
    
    @property
    def session_maker(self) -> async_sessionmaker:
        """Get session maker instance."""
        if self._session_maker is None:
            raise RuntimeError("Session maker not initialized")
        return self._session_maker
    
    @property
    def motivation_service(self) -> MotivationService:
        """Get motivation service instance."""
        if self._motivation_service is None:
            self._motivation_service = MotivationService()
        return self._motivation_service
    
    @property
    def recipe_service(self) -> RecipeService:
        """Get recipe service instance."""
        if self._recipe_service is None:
            self._recipe_service = RecipeService()
        return self._recipe_service
    
    @property
    def ai_service(self) -> AIService:
        """Get AI service instance."""
        if self._ai_service is None:
            self._ai_service = AIService()
        return self._ai_service
    
    @property
    def user_state_service(self) -> UserStateService:
        """Get user state service instance."""
        if self._user_state_service is None:
            self._user_state_service = UserStateService()
        return self._user_state_service
    
    @property
    def scheduler_service(self):
        """Get scheduler service instance."""
        return self._scheduler_service
    
    def setup(self, bot: Bot, session_maker: async_sessionmaker):
        """Setup container with bot and session maker."""
        self._bot = bot
        self._storage = MemoryStorage()
        self._dispatcher = Dispatcher(storage=self._storage)
        self._session_maker = session_maker
    
    async def get_session(self) -> AsyncGenerator[AsyncSession, None]:
        """Get database session."""
        async with self.session_maker() as session:
            yield session
    
    def get_user_repository(self, session: AsyncSession) -> UserRepository:
        """Get user repository."""
        return UserRepository(session)
    
    def get_checkin_repository(self, session: AsyncSession) -> CheckInRepository:
        """Get check-in repository."""
        return CheckInRepository(session)
    
    def get_note_repository(self, session: AsyncSession) -> NoteRepository:
        """Get note repository."""
        return NoteRepository(session)
    
    def get_challenge_repository(self, session: AsyncSession) -> ChallengeRepository:
        """Get challenge repository."""
        return ChallengeRepository(session)
    
    def get_recipe_repository(self, session: AsyncSession) -> RecipeRepository:
        """Get recipe repository."""
        return RecipeRepository(session)


# Global container instance
container = Container() 