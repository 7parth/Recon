"""Application configuration via pydantic-settings.

All settings are loaded from environment variables (or .env file).
Never hardcode secrets — add them to .env and reference them here.
"""

from __future__ import annotations

from functools import lru_cache

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",
    )

    # ── LLM ──────────────────────────────────────────────────────────────────
    nvidia_api_key: str = Field("", description="NVIDIA AI Endpoints API key")
    nvidia_model: str = Field(
        "meta/llama-4-maverick-17b-128e-instruct",
        description="NVIDIA model name; see context/issues/01-issue.md for options",
    )

    # ── Supabase ──────────────────────────────────────────────────────────────
    supabase_url: str = Field("", description="Supabase project URL (https://xxx.supabase.co)")
    supabase_anon_key: str = Field("", description="Supabase anon/public key")
    supabase_service_role_key: str = Field(
        "",
        description="Supabase service role key (server-side only, never expose to browser)",
    )
    supabase_storage_bucket: str = Field(
        "resumes",
        description="Default Supabase Storage bucket for resume uploads",
    )
    supabase_checkpoint_bucket: str = Field(
        "checkpoints",
        description="Supabase Storage bucket for LangGraph checkpoint blobs (future use)",
    )

    # ── Database ─────────────────────────────────────────────────────────────
    # Use the direct Postgres connection string from Supabase project settings.
    # Format: postgresql+asyncpg://postgres:<password>@db.<project-ref>.supabase.co:5432/postgres
    database_url: str = Field(
        "",
        description=(
            "Async SQLAlchemy connection string for Supabase PostgreSQL. "
            "Find this in: Supabase dashboard → Project Settings → Database → Connection string (URI mode). "
            "Replace the scheme with postgresql+asyncpg://"
        ),
    )

    # ── App ───────────────────────────────────────────────────────────────────
    environment: str = Field("development", description="development | production")
    log_level: str = Field("INFO", description="Python logging level")

    # ── Celery / Redis ────────────────────────────────────────────────────────
    celery_broker_url: str = Field(
        "redis://localhost:6379/0",
        description="Celery broker URL (Redis)",
    )
    celery_result_backend: str = Field(
        "redis://localhost:6379/0",
        description="Celery result backend URL (Redis)",
    )


@lru_cache(maxsize=1)
def get_settings() -> Settings:
    """Return a cached Settings singleton.

    Usage in FastAPI dependencies::

        from app.config import get_settings

        def some_dep(settings: Settings = Depends(get_settings)):
            ...
    """
    return Settings()
