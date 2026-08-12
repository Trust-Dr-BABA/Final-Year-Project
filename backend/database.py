"""
database.py — SQLAlchemy async session factory and dependency.
"""

import os

from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine
from sqlalchemy.orm import DeclarativeBase

DATABASE_URL = os.getenv("DATABASE_URL", "postgresql+asyncpg://fyp_user:fyp_password@localhost:5432/fyp_db")

engine = create_async_engine(DATABASE_URL, echo=False, pool_pre_ping=True)

AsyncSessionLocal = async_sessionmaker(
    bind=engine,
    class_=AsyncSession,
    expire_on_commit=False,
)


class Base(DeclarativeBase):
    """Base class for all SQLAlchemy models."""
    pass


# FastAPI dependency that yields an async database session.
async def get_db() -> AsyncSession:
    async with AsyncSessionLocal() as session:
        yield session


# Check whether the database is reachable; used by GET /health, never raises.
async def check_db_reachable() -> bool:
    try:
        async with engine.connect() as conn:
            await conn.execute(text("SELECT 1"))
        return True
    except Exception:
        return False
