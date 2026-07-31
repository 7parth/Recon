"""UserProfileRecord and UserSettingsRecord ORM models.

Stores user profile information and pipeline preferences in Supabase PostgreSQL.
"""

from __future__ import annotations

import uuid
from datetime import datetime, timezone

from sqlalchemy import Boolean, DateTime, Integer, String, Text
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column

from app.db.database import Base


class UserProfileRecord(Base):
    """Persisted user candidate profile.

    Columns
    -------
    id
        Primary key (UUID v4).
    user_id
        User identifier string (default: 'default_user').
    first_name
        Candidate first name.
    last_name
        Candidate last name.
    email
        Candidate contact email.
    phone
        Candidate contact phone number.
    linkedin_url
        LinkedIn profile link.
    portfolio_url
        Portfolio website link.
    updated_at
        UTC timestamp of last update.
    """

    __tablename__ = "user_profiles"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4,
        server_default="gen_random_uuid()",
    )
    user_id: Mapped[str] = mapped_column(String(255), nullable=False, unique=True, default="default_user", index=True)
    first_name: Mapped[str | None] = mapped_column(String(255), nullable=True)
    last_name: Mapped[str | None] = mapped_column(String(255), nullable=True)
    email: Mapped[str | None] = mapped_column(String(255), nullable=True)
    phone: Mapped[str | None] = mapped_column(String(255), nullable=True)
    linkedin_url: Mapped[str | None] = mapped_column(Text, nullable=True)
    portfolio_url: Mapped[str | None] = mapped_column(Text, nullable=True)
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        server_default="now()",
        onupdate=lambda: datetime.now(timezone.utc),
        nullable=False,
    )


class UserSettingsRecord(Base):
    """Persisted user pipeline settings and configuration.

    Columns
    -------
    id
        Primary key (UUID v4).
    user_id
        User identifier string (default: 'default_user').
    match_threshold
        Minimum match score percentage threshold (0-100).
    nvidia_model
        Selected LLM model identifier.
    embedding_model
        Selected embedding model identifier.
    auto_apply
        Boolean flag to skip human review and automatically apply.
    enable_notifications
        Boolean flag to enable email or browser notifications.
    updated_at
        UTC timestamp of last update.
    """

    __tablename__ = "user_settings"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4,
        server_default="gen_random_uuid()",
    )
    user_id: Mapped[str] = mapped_column(String(255), nullable=False, unique=True, default="default_user", index=True)
    match_threshold: Mapped[int] = mapped_column(Integer, nullable=False, default=70)
    nvidia_model: Mapped[str] = mapped_column(String(255), nullable=False, default="meta/llama-4-scout-17b-16e-instruct")
    embedding_model: Mapped[str] = mapped_column(String(255), nullable=False, default="sentence-transformers/all-MiniLM-L6-v2")
    auto_apply: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    enable_notifications: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True)
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        server_default="now()",
        onupdate=lambda: datetime.now(timezone.utc),
        nullable=False,
    )
