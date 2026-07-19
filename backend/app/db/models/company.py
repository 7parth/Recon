"""CompanyRecord ORM model.

Stores company context collected by the company_agent.
"""

from __future__ import annotations

import uuid
from datetime import datetime, timezone

from sqlalchemy import DateTime, String, Text
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column

from app.db.database import Base


class CompanyRecord(Base):
    """Persisted company profile collected by the company agent.

    Columns
    -------
    id
        Primary key (UUID v4).
    name
        Company name — used as a deduplication key for future lookup.
    website
        Primary website URL.
    industry
        Industry or sector (e.g. "SaaS", "Fintech").
    summary
        Short narrative about the company (LLM-generated or scraped).
    culture_notes
        Culture/values notes used to tone-match the cover letter.
    created_at
        UTC timestamp of record creation.
    """

    __tablename__ = "companies"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4,
        server_default="gen_random_uuid()",
    )
    name: Mapped[str] = mapped_column(String(255), nullable=False, index=True)
    website: Mapped[str | None] = mapped_column(Text, nullable=True)
    industry: Mapped[str | None] = mapped_column(String(255), nullable=True)
    summary: Mapped[str | None] = mapped_column(Text, nullable=True)
    culture_notes: Mapped[str | None] = mapped_column(Text, nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        server_default="now()",
        nullable=False,
    )
