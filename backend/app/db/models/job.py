"""JobRecord ORM model.

Stores the parsed job description and its source URL.
"""

from __future__ import annotations

import uuid
from datetime import datetime, timezone

from sqlalchemy import DateTime, Float, String, Text
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column

from app.db.database import Base


class JobRecord(Base):
    """Persisted representation of a parsed job description.

    Columns
    -------
    id
        Primary key (UUID v4).
    job_url
        Source URL of the job description (may be null for raw-text input).
    company_name
        Extracted company name (denormalised for quick display).
    job_title
        Extracted job title.
    jd_text
        Normalised plain-text of the job description (used for re-scoring).
    match_score
        Final blended match score from the most recent ``match_agent`` run.
        Stored here so history routes can filter/sort without re-scoring.
    created_at
        UTC timestamp when this JD was first parsed.
    """

    __tablename__ = "jobs"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4,
        server_default="gen_random_uuid()",
    )
    job_url: Mapped[str | None] = mapped_column(Text, nullable=True)
    company_name: Mapped[str | None] = mapped_column(String(255), nullable=True)
    job_title: Mapped[str | None] = mapped_column(String(255), nullable=True)
    jd_text: Mapped[str | None] = mapped_column(
        Text,
        nullable=True,
        comment="Normalised JD text — stored for re-use without re-fetching the URL",
    )
    match_score: Mapped[float | None] = mapped_column(
        Float,
        nullable=True,
        comment="Blended match score (0.0–1.0) from match_agent",
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        server_default="now()",
        nullable=False,
    )
