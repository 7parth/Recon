"""ORM models for discovery preferences and sessions.

DiscoveryPreferencesRecord — per-user stored preferences for the automated
discovery pipeline (target role, locations, exclusions, daily cap).

DiscoverySessionRecord — one batch run of the discovery pipeline.  Each
row tracks lifecycle status and aggregate counters; per-job detail lives
on ApplicationRecord rows linked via the `discovery_session_id` FK.
"""

from __future__ import annotations

import uuid
from datetime import datetime, timezone
from typing import TYPE_CHECKING

from sqlalchemy import (
    CheckConstraint,
    DateTime,
    Integer,
    String,
    Text,
)
from sqlalchemy.dialects.postgresql import ARRAY, UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.database import Base

if TYPE_CHECKING:
    from app.db.models.application import ApplicationRecord


class DiscoveryPreferencesRecord(Base):
    """Stored discovery preferences for a single user.

    Columns
    -------
    id
        Primary key (UUID v4).
    user_id
        User identifier (default: ``"default_user"``); unique — one row per user.
    target_role
        The job role/title string used as the search query.
    preferred_locations
        PostgreSQL TEXT[] — up to 5 location strings.  Enforced at the
        route/schema layer, not the DB layer.
    excluded_companies
        PostgreSQL TEXT[] — company name substrings to skip.
    max_jobs_per_session
        Hard cap on raw URLs per session (1–50 enforced by CHECK constraint).
    updated_at
        UTC timestamp of last write.
    """

    __tablename__ = "discovery_preferences"
    __table_args__ = (
        CheckConstraint(
            "max_jobs_per_session BETWEEN 1 AND 50",
            name="ck_discovery_preferences_max_jobs",
        ),
    )

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4,
        server_default="gen_random_uuid()",
    )
    user_id: Mapped[str] = mapped_column(
        String(255),
        nullable=False,
        unique=True,
        index=True,
        default="default_user",
        comment="One preferences row per user; default_user for single-user deployments",
    )
    target_role: Mapped[str] = mapped_column(
        String(200),
        nullable=False,
        default="",
        server_default="''",
        comment="Job role / search query string",
    )
    preferred_locations: Mapped[list[str]] = mapped_column(
        ARRAY(String(100)),
        nullable=False,
        default=list,
        server_default="'{}'",
        comment="Up to 5 location strings; enforced at the API layer",
    )
    excluded_companies: Mapped[list[str]] = mapped_column(
        ARRAY(String(200)),
        nullable=False,
        default=list,
        server_default="'{}'",
        comment="Company name substrings to exclude from results (case-insensitive match)",
    )
    max_jobs_per_session: Mapped[int] = mapped_column(
        Integer,
        nullable=False,
        default=10,
        server_default="10",
        comment="Hard cap on raw URLs per discovery session (1–50)",
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        default=lambda: datetime.now(timezone.utc),
        onupdate=lambda: datetime.now(timezone.utc),
        server_default="now()",
    )


class DiscoverySessionRecord(Base):
    """One execution of the automated discovery pipeline.

    Columns
    -------
    id
        Primary key (UUID v4).
    user_id
        Owning user (not a FK — mirrors the pattern used by ApplicationRecord).
    session_status
        ``running`` | ``completed`` | ``failed`` | ``cancelled``
        | ``completed_with_errors``
    jobs_found
        Count of de-duplicated URLs in the job queue (set before dispatch loop).
    jobs_processed
        Count of jobs that have reached a terminal state (incremented each
        iteration by the orchestrator).
    error_message
        Top-level error string if status is ``failed``.
    started_at
        UTC timestamp when the session was created.
    completed_at
        UTC timestamp when the session reached a terminal state; NULL while
        running.

    Relationships
    -------------
    applications
        All ``ApplicationRecord`` rows linked to this session.  Used for
        counter queries and eager loading.
    """

    __tablename__ = "discovery_sessions"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4,
        server_default="gen_random_uuid()",
    )
    user_id: Mapped[str] = mapped_column(
        String(255),
        nullable=False,
        index=True,
        default="default_user",
        comment="Owning user — not a FK, mirrors ApplicationRecord.user_id pattern",
    )
    session_status: Mapped[str] = mapped_column(
        String(50),
        nullable=False,
        default="running",
        server_default="'running'",
        index=True,
        comment="running | completed | failed | cancelled | completed_with_errors",
    )
    jobs_found: Mapped[int] = mapped_column(
        Integer,
        nullable=False,
        default=0,
        server_default="0",
        comment="De-duplicated URL count — set once before dispatch loop",
    )
    jobs_processed: Mapped[int] = mapped_column(
        Integer,
        nullable=False,
        default=0,
        server_default="0",
        comment="Incremented by orchestrator after each job reaches a terminal state",
    )
    error_message: Mapped[str | None] = mapped_column(
        Text,
        nullable=True,
        comment="Top-level error if status = failed",
    )
    started_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        default=lambda: datetime.now(timezone.utc),
        server_default="now()",
    )
    completed_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
        comment="NULL while running; set when session reaches a terminal state",
    )

    # ── Relationships ─────────────────────────────────────────────────────────
    applications: Mapped[list[ApplicationRecord]] = relationship(
        "ApplicationRecord",
        back_populates="discovery_session",
        foreign_keys="ApplicationRecord.discovery_session_id",
    )
