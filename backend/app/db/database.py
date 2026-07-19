"""Async SQLAlchemy engine and session factory.

The engine connects to Supabase PostgreSQL via the direct connection string
configured in DATABASE_URL. No local Postgres is required — Supabase hosts it.

Usage (via FastAPI dependency injection — see app/dependencies.py)::

    async with get_async_session() as session:
        result = await session.execute(select(ApplicationRecord))
        records = result.scalars().all()
"""

from __future__ import annotations

from collections.abc import AsyncGenerator
from contextlib import asynccontextmanager

from sqlalchemy.ext.asyncio import (
    AsyncSession,
    async_sessionmaker,
    create_async_engine,
)
from sqlalchemy.orm import DeclarativeBase

from app.config import get_settings


class Base(DeclarativeBase):
    """Shared declarative base for all ORM models.

    All models in ``app/db/models/`` inherit from this class so that
    Alembic can discover them through ``Base.metadata``.
    """


def _build_engine():
    """Create the async engine singleton.

    Called once at import time. The engine is reused for the lifetime
    of the process (connection-pool aware).

    Supabase Postgres notes:
    - Supabase uses connection pooling via PgBouncer on port 6543 (transaction mode).
      For SQLAlchemy async use the *direct* connection on port 5432 (session mode)
      so that server-side prepared statements work correctly.
    - Set ``pool_pre_ping=True`` so stale connections are recycled automatically.
    """
    settings = get_settings()
    return create_async_engine(
        settings.database_url,
        echo=settings.environment == "development",
        pool_pre_ping=True,
        pool_size=5,
        max_overflow=10,
    )


# Module-level singletons
engine = _build_engine()

AsyncSessionLocal = async_sessionmaker(
    bind=engine,
    class_=AsyncSession,
    expire_on_commit=False,
    autoflush=False,
    autocommit=False,
)


@asynccontextmanager
async def get_async_session() -> AsyncGenerator[AsyncSession, None]:
    """Async context manager that provides a transactional DB session.

    Commits on success, rolls back on any exception, always closes the session.

    Example::

        async with get_async_session() as session:
            session.add(record)
            # commit happens automatically on exit
    """
    async with AsyncSessionLocal() as session:
        try:
            yield session
            await session.commit()
        except Exception:
            await session.rollback()
            raise
        finally:
            await session.close()
