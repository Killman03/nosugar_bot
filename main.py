import asyncio
import sys
from contextlib import asynccontextmanager

from aiogram import Bot, Dispatcher
from aiogram.fsm.storage.memory import MemoryStorage
from loguru import logger

from config import settings
from database.connection import create_tables, get_session_maker
from di.container import container
from handlers.start import StartHandler
from handlers.checkin import CheckInHandler
from handlers.notes import NotesHandler
from handlers.recipes import RecipesHandler
from handlers.text import TextHandler


# Configure logging
logger.remove()
logger.add(
    sys.stdout,
    format="<green>{time:YYYY-MM-DD HH:mm:ss}</green> | <level>{level: <8}</level> | <cyan>{name}</cyan>:<cyan>{function}</cyan>:<cyan>{line}</cyan> - <level>{message}</level>",
    level=settings.log_level
)
logger.add(
    "logs/bot.log",
    rotation="1 day",
    retention="7 days",
    format="{time:YYYY-MM-DD HH:mm:ss} | {level: <8} | {name}:{function}:{line} - {message}",
    level="INFO"
)


@asynccontextmanager
async def lifespan():
    """Application lifespan manager."""
    logger.info("Starting bot...")
    
    # Create database tables
    try:
        await create_tables()
        logger.info("Database tables created successfully")
    except Exception as e:
        logger.error(f"Failed to create database tables: {e}")
        raise
    
    logger.info("Bot started successfully")
    yield
    
    # Stop scheduler
    try:
        await container.scheduler_service.stop_scheduler()
        logger.info("Scheduler stopped successfully")
    except Exception as e:
        logger.error(f"Failed to stop scheduler: {e}")
    
    logger.info("Bot stopped")


async def main():
    """Main function."""
    # Initialize bot and session maker
    bot = Bot(token=settings.bot_token)
    session_maker = get_session_maker()
    
    # Setup DI container
    container.setup(bot, session_maker)
    
    # Initialize handlers with DI
    start_handler = StartHandler()
    checkin_handler = CheckInHandler()
    notes_handler = NotesHandler()
    recipes_handler = RecipesHandler()
    text_handler = TextHandler()
    
    # Include routers
    container.dispatcher.include_router(start_handler.router)
    container.dispatcher.include_router(checkin_handler.router)
    container.dispatcher.include_router(notes_handler.router)
    container.dispatcher.include_router(recipes_handler.router)
    container.dispatcher.include_router(text_handler.router)
    
    # Set up lifespan
    container.dispatcher.lifespan = lifespan
    
    # Setup scheduler after container is fully initialized
    try:
        scheduler = container.scheduler_service
        scheduler.set_bot(container.bot)
        # Start scheduler in background
        asyncio.create_task(scheduler.start_scheduler())
        logger.info("Daily reminder scheduler started successfully")
    except Exception as e:
        logger.error(f"Failed to start scheduler: {e}")
    
    # Start polling
    try:
        logger.info("Starting bot polling...")
        await container.dispatcher.start_polling(container.bot)
    except KeyboardInterrupt:
        logger.info("Bot stopped by user")
    except Exception as e:
        logger.error(f"Bot error: {e}")
    finally:
        await container.bot.session.close()


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        logger.info("Bot stopped by user")
    except Exception as e:
        logger.error(f"Fatal error: {e}")
        sys.exit(1) 