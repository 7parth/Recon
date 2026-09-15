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
            "Async SQLAlchemy (asyncpg) connection string for Supabase PostgreSQL. "
            "Use the Session Pooler URL from: Supabase dashboard → Project Settings → Database. "
            "Format: postgresql+asyncpg://postgres.PROJECT_REF:PASSWORD@aws-X-REGION.pooler.supabase.com:5432/postgres"
        ),
    )
    checkpoint_database_url: str = Field(
        "",
        description=(
            "psycopg3 connection string for LangGraph AsyncPostgresSaver. "
            "Same as DATABASE_URL but with scheme 'postgresql://' (no asyncpg). "
            "Format: postgresql://postgres.PROJECT_REF:PASSWORD@aws-X-REGION.pooler.supabase.com:5432/postgres"
        ),
    )

    # ── App ───────────────────────────────────────────────────────────────────
    environment: str = Field("development", description="development | production")
    log_level: str = Field("INFO", description="Python logging level")

    # ── Discovery ─────────────────────────────────────────────────────────────
    discovery_schedule_utc_hour: int = Field(
        9,
        ge=0,
        le=23,
        description="UTC hour (0–23) for daily discovery trigger",
    )

    # ── Celery / Redis ────────────────────────────────────────────────────────
    celery_broker_url: str = Field(
        "redis://localhost:6379/0",
        description="Celery broker URL (Redis)",
    )
    celery_result_backend: str = Field(
        "redis://localhost:6379/0",
        description="Celery result backend URL (Redis)",
    )

    # ── LinkedIn ──────────────────────────────────────────────────────────────
    linkedin_session_path: str = Field(
        ".linkedin_session.json",
        description=(
            "Path to the Playwright browser storage-state file used for LinkedIn Easy Apply. "
            "Relative to the backend/ working directory, or absolute. "
            "Bootstrap once with: python -m app.automation.linkedin_login"
        ),
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
