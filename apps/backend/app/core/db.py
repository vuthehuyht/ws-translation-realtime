"""Database Module: Async SQLAlchemy 2.0 Engine & Session Management.

Provides async connection pooling, transactional context managers,
and FastAPI dependency injection for PostgreSQL 16 (via asyncpg).
"""

import logging
from collections.abc import AsyncGenerator
from typing import Any

from sqlalchemy.ext.asyncio import (
    AsyncEngine,
    AsyncSession,
    async_sessionmaker,
    create_async_engine,
)

from app.core.config import get_settings

logger = logging.getLogger(__name__)

_engine: AsyncEngine | None = None
_session_factory: async_sessionmaker[AsyncSession] | None = None


def get_engine() -> AsyncEngine:
    """Retrieve or initialize the singleton AsyncEngine instance."""
    global _engine
    if _engine is None:
        settings = get_settings()
        engine_kwargs: dict[str, Any] = {
            "echo": settings.db.echo,
            "future": True,
        }

        # Apply pool configurations only for network databases (skip for SQLite in-memory tests)
        if not settings.database_url.startswith("sqlite"):
            engine_kwargs.update(
                {
                    "pool_size": settings.db.pool_size,
                    "max_overflow": settings.db.max_overflow,
                    "pool_timeout": settings.db.pool_timeout,
                    "pool_pre_ping": True,
                }
            )

        _engine = create_async_engine(settings.database_url, **engine_kwargs)
        logger.info(
            "Initialized AsyncEngine for database: %s", settings.database_url.split("@")[-1]
        )
    return _engine


def get_session_factory() -> async_sessionmaker[AsyncSession]:
    """Retrieve or initialize the async sessionmaker factory."""
    global _session_factory
    if _session_factory is None:
        engine = get_engine()
        _session_factory = async_sessionmaker(
            bind=engine,
            class_=AsyncSession,
            autoflush=False,
            autocommit=False,
            expire_on_commit=False,
        )
    return _session_factory


async def get_db() -> AsyncGenerator[AsyncSession, None]:
    """FastAPI dependency that yields an isolated AsyncSession per request."""
    session_factory = get_session_factory()
    async with session_factory() as session:
        try:
            yield session
            await session.commit()
        except Exception:
            await session.rollback()
            raise
        finally:
            await session.close()


async def close_db_connections() -> None:
    """Dispose of engine connections on application shutdown."""
    global _engine, _session_factory
    if _engine is not None:
        await _engine.dispose()
        _engine = None
        _session_factory = None
        logger.info("Disposed database connection engine pool.")
