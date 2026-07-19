"""ApplicationRecord ORM model — the central history table.

Each row represents one full application run: one resume against one job.
Documents (tailored resume, cover letter) live in Supabase Storage;
this table holds their public URLs alongside status and metadata.
"""

from __future__ import annotations

import uuid
from datetime import datetime, timezone

from sqlalchemy import DateTime, Float, ForeignKey, String, Text
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.database import Base


class ApplicationRecord(Base):
    """Central history record for one application run.

    Design decisions (see context/issues/02-issue.md):
    - ``resume_storage_url``, ``tailored_resume_url``, ``cover_letter_url``
      are Supabase Storage public URLs — not text blobs.
    - ``thread_id`` links this record to the LangGraph checkpoint in Supabase
      Postgres, so the review queue can resume interrupted runs.
    - Foreign keys to ``resumes``, ``jobs``, ``companies`` tables for
      relational integrity. Nullable because a run may fail before all
      agents complete.

    Columns
    -------
    id
        Primary key (UUID v4).
    thread_id
        LangGraph checkpoint thread ID — used to resume an interrupted run.
    resume_id / job_id / company_id
        FK references to the parsed entities for this run.
    status
        ``pending_review`` | ``approved`` | ``rejected`` | ``applied``
        | ``failed`` | ``skipped``
    match_score
        Blended score (0.0–1.0) from match_agent.
    resume_storage_url
        Supabase Storage URL for the **original** resume used in this run.
    tailored_resume_url
        Supabase Storage URL for the **tailored** resume generated for this run.
    cover_letter_url
        Supabase Storage URL for the cover letter generated for this run.
    rejection_feedback
        User's rejection note (if status is ``rejected``).
    error_message
        Last error message if the run failed.
    created_at / updated_at
        UTC timestamps — updated_at is refreshed on every status change.
    """

    __tablename__ = "applications"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4,
        server_default="gen_random_uuid()",
    )
    thread_id: Mapped[str] = mapped_column(
        String(255),
        nullable=False,
        unique=True,
        index=True,
        comment="LangGraph checkpoint thread_id — used to resume interrupted runs",
    )
    resume_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("resumes.id", ondelete="SET NULL"),
        nullable=True,
        index=True,
    )
    job_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("jobs.id", ondelete="SET NULL"),
        nullable=True,
        index=True,
    )
    company_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("companies.id", ondelete="SET NULL"),
        nullable=True,
    )

    # ── Status ────────────────────────────────────────────────────────────────
    status: Mapped[str] = mapped_column(
        String(50),
        nullable=False,
        default="pending_review",
        server_default="'pending_review'",
        index=True,
        comment="pending_review | approved | rejected | applied | failed | skipped",
    )

    # ── Scores ────────────────────────────────────────────────────────────────
    match_score: Mapped[float | None] = mapped_column(
        Float,
        nullable=True,
        comment="Blended match score (0.0–1.0) from match_agent",
    )

    # ── Storage URLs (documents live in Supabase Storage, not in this table) ─
    resume_storage_url: Mapped[str | None] = mapped_column(
        Text,
        nullable=True,
        comment="Supabase Storage URL for the original resume file",
    )
    tailored_resume_url: Mapped[str | None] = mapped_column(
        Text,
        nullable=True,
        comment="Supabase Storage URL for the tailored resume generated for this run",
    )
    cover_letter_url: Mapped[str | None] = mapped_column(
        Text,
        nullable=True,
        comment="Supabase Storage URL for the cover letter generated for this run",
    )

    # ── Review ────────────────────────────────────────────────────────────────
    rejection_feedback: Mapped[str | None] = mapped_column(
        Text,
        nullable=True,
        comment="User's rejection note — triggers re-tailor loop when set",
    )

    # ── Error ─────────────────────────────────────────────────────────────────
    error_message: Mapped[str | None] = mapped_column(Text, nullable=True)

    # ── Timestamps ───────────────────────────────────────────────────────────
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        server_default="now()",
        nullable=False,
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        onupdate=lambda: datetime.now(timezone.utc),
        server_default="now()",
        nullable=False,
    )
