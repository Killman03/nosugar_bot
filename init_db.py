import asyncio
import sys
from loguru import logger

from config import settings
from database.connection import create_tables, drop_tables
from database.models import Base


async def init_database():
    """Initialize database tables."""
    try:
        logger.info("Creating database tables...")
        await create_tables()
        logger.info("Database tables created successfully!")
        
        # Test connection
        from database.connection import async_session_factory
        async with async_session_factory() as session:
            logger.info("Database connection test successful!")
            
    except Exception as e:
        logger.error(f"Failed to initialize database: {e}")
        raise


async def reset_database():
    """Reset database (drop and recreate tables)."""
    try:
        logger.info("Dropping existing tables...")
        await drop_tables()
        logger.info("Tables dropped successfully!")
        
        logger.info("Creating new tables...")
        await create_tables()
        logger.info("Database reset completed successfully!")
        
    except Exception as e:
        logger.error(f"Failed to reset database: {e}")
        raise


if __name__ == "__main__":
    import sys
    
    if len(sys.argv) > 1 and sys.argv[1] == "reset":
        asyncio.run(reset_database())
    else:
        asyncio.run(init_database()) 