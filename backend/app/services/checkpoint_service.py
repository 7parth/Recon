"""CheckpointService — LangGraph persistence via Supabase PostgreSQL.

Provides an ``AsyncPostgresSaver`` configured to use the direct Supabase
PostgreSQL connection. This allows LangGraph to persist application state
across nodes, enabling the ``human_review_agent`` interrupt to survive
server restarts.

Usage (in graph/builder.py or api routes)::

    from app.services.checkpoint_service import get_checkpointer

    async with get_checkpointer() as checkpointer:
        # Pass to graph invoke, or use directly to list threads
        result = await graph.ainvoke(state, config={"configurable": {"thread_id": "123"}})
"""

from __future__ import annotations

from collections.abc import AsyncGenerator
from contextlib import asynccontextmanager

from langgraph.checkpoint.postgres.aio import AsyncPostgresSaver
from psycopg_pool import AsyncConnectionPool

from app.config import get_settings


@asynccontextmanager
async def get_checkpointer() -> AsyncGenerator[AsyncPostgresSaver, None]:
    """Provide a LangGraph checkpointer connected to Supabase Postgres.

    Uses ``psycopg_pool`` to manage connections as required by
    ``AsyncPostgresSaver``.  The pool is scoped to this context manager.

    Example::

        async with get_checkpointer() as checkpointer:
            # checkpointer is ready (tables created if they didn't exist)
            state = await checkpointer.aget_tuple(config)
    """
    settings = get_settings()
    # Use the dedicated psycopg3 connection string if available.
    # Fall back to replacing the asyncpg scheme for backward compatibility.
    if settings.checkpoint_database_url:
        conn_str = settings.checkpoint_database_url
    else:
        conn_str = settings.database_url.replace(
            "postgresql+asyncpg://", "postgresql://"
        )

    # Use a small pool size since this is just for checkpoints
    async with AsyncConnectionPool(
        conninfo=conn_str,
        max_size=5,
        timeout=5.0,
        kwargs={"autocommit": True, "connect_timeout": 5},
    ) as pool:
        checkpointer = AsyncPostgresSaver(pool)
        # Ensure the LangGraph tables exist (checkpoints, checkpoint_writes, etc.)
        await checkpointer.setup()
        yield checkpointer

