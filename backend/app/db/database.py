import os
import logging
from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker, AsyncSession
from app.db.models import Base

logger = logging.getLogger("db")

DATABASE_URL = os.getenv("DATABASE_URL", "postgresql+asyncpg://detective:password@localhost:5432/detective_analytics")

engine = create_async_engine(DATABASE_URL, echo=False)

AsyncSessionLocal = async_sessionmaker(
    bind=engine,
    class_=AsyncSession,
    expire_on_commit=False,
)

async def init_db():
    """Initialize database tables."""
    try:
        async with engine.begin() as conn:
            await conn.run_sync(Base.metadata.create_all)
        logger.info("Database initialized successfully.")
    except Exception as e:
        logger.error(f"Failed to initialize database: {e}")

async def get_db():
    """Dependency for getting DB session."""
    async with AsyncSessionLocal() as session:
        yield session

async def close_db():
    """Close DB connections."""
    await engine.dispose()
