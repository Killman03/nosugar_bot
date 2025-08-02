import pytest
from datetime import date, datetime
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine
from sqlalchemy.orm import sessionmaker

from database.models import Base, User, CheckIn, Note, Challenge, Recipe


@pytest.fixture
async def async_engine():
    """Create async engine for testing."""
    engine = create_async_engine(
        "sqlite+aiosqlite:///:memory:",
        echo=False
    )
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    yield engine
    await engine.dispose()


@pytest.fixture
async def async_session(async_engine):
    """Create async session for testing."""
    async_session_factory = sessionmaker(
        async_engine, class_=AsyncSession, expire_on_commit=False
    )
    async with async_session_factory() as session:
        yield session


@pytest.mark.asyncio
async def test_create_user(async_session):
    """Test user creation."""
    user = User(
        user_id=123456789,
        username="test_user",
        first_name="Test",
        last_name="User"
    )
    
    async_session.add(user)
    await async_session.commit()
    await async_session.refresh(user)
    
    assert user.id is not None
    assert user.user_id == 123456789
    assert user.username == "test_user"
    assert user.current_streak == 0
    assert user.longest_streak == 0


@pytest.mark.asyncio
async def test_create_checkin(async_session):
    """Test check-in creation."""
    # Create user first
    user = User(user_id=123456789, username="test_user")
    async_session.add(user)
    await async_session.commit()
    await async_session.refresh(user)
    
    # Create check-in
    checkin = CheckIn(
        user_id=user.id,
        check_date=date.today(),
        success=True
    )
    
    async_session.add(checkin)
    await async_session.commit()
    await async_session.refresh(checkin)
    
    assert checkin.id is not None
    assert checkin.user_id == user.id
    assert checkin.check_date == date.today()
    assert checkin.success is True


@pytest.mark.asyncio
async def test_create_note(async_session):
    """Test note creation."""
    # Create user first
    user = User(user_id=123456789, username="test_user")
    async_session.add(user)
    await async_session.commit()
    await async_session.refresh(user)
    
    # Create note
    note = Note(
        user_id=user.id,
        content="Test note content"
    )
    
    async_session.add(note)
    await async_session.commit()
    await async_session.refresh(note)
    
    assert note.id is not None
    assert note.user_id == user.id
    assert note.content == "Test note content"


@pytest.mark.asyncio
async def test_create_challenge(async_session):
    """Test challenge creation."""
    # Create user first
    user = User(user_id=123456789, username="test_user")
    async_session.add(user)
    await async_session.commit()
    await async_session.refresh(user)
    
    # Create challenge
    challenge = Challenge(
        user_id=user.id,
        challenge_date=date.today(),
        challenge_text="Test challenge"
    )
    
    async_session.add(challenge)
    await async_session.commit()
    await async_session.refresh(challenge)
    
    assert challenge.id is not None
    assert challenge.user_id == user.id
    assert challenge.challenge_date == date.today()
    assert challenge.challenge_text == "Test challenge"
    assert challenge.completed is False


@pytest.mark.asyncio
async def test_create_recipe(async_session):
    """Test recipe creation."""
    # Create user first
    user = User(user_id=123456789, username="test_user")
    async_session.add(user)
    await async_session.commit()
    await async_session.refresh(user)
    
    # Create recipe
    recipe = Recipe(
        user_id=user.id,
        ingredients="chicken, rice, vegetables",
        recipe_text="Test recipe instructions"
    )
    
    async_session.add(recipe)
    await async_session.commit()
    await async_session.refresh(recipe)
    
    assert recipe.id is not None
    assert recipe.user_id == user.id
    assert recipe.ingredients == "chicken, rice, vegetables"
    assert recipe.recipe_text == "Test recipe instructions" 