"""Supabase async client singleton.

Provides the Supabase Python client configured with the service role key
for server-side operations (storage uploads, auth admin).

Rules (from code-standards.md):
- Never import this module from graph nodes or agents.
- Only use this client from ``app/services/`` and ``app/storage/`` modules.
- The service role key bypasses Row Level Security — use it only server-side.

Usage::

    from app.db.supabase import get_supabase_client

    client = get_supabase_client()
    response = await client.storage.from_("resumes").upload(path, data)
"""

from __future__ import annotations

from functools import lru_cache

from supabase._async.client import AsyncClient
from supabase import acreate_client

from app.config import get_settings


@lru_cache(maxsize=1)
def _get_cached_settings():
    """Isolated settings fetch so lru_cache works cleanly."""
    return get_settings()


async def get_supabase_client() -> AsyncClient:
    """Create (or reuse) the Supabase async client.

    The client is initialised with the **service role key** which grants
    full access bypassing Row Level Security — suitable for server-side
    storage uploads and admin operations.

    Note: ``acreate_client`` is awaitable; call this once at startup and
    store the result, rather than calling it on every request.
    """
    settings = _get_cached_settings()
    return await acreate_client(
        supabase_url=settings.supabase_url,
        supabase_key=settings.supabase_service_role_key,
    )
