"""ReviewRecord ORM model.

Stores the human reviewer's decision for each application run.
"""

from __future__ import annotations

import uuid
from datetime import datetime, timezone

from sqlalchemy import DateTime, ForeignKey, String, Text
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column

from app.db.database import Base


class ReviewRecord(Base):
    """Persisted record of a human reviewer's approval or rejection.

    Columns
    -------
    id
        Primary key (UUID v4).
    application_id
        FK to the ApplicationRecord this review belongs to.
    decision
        ``approved`` | ``rejected``
    feedback
        Free-text feedback when the decision is ``rejected`` — forwarded
        to ``tailoring_agent`` for the re-tailor loop.
    reviewed_at
        UTC timestamp of the decision.
    """

    __tablename__ = "reviews"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4,
        server_default="gen_random_uuid()",
    )
    application_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("applications.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    decision: Mapped[str] = mapped_column(
        String(20),
        nullable=False,
        comment="approved | rejected",
    )
    feedback: Mapped[str | None] = mapped_column(
        Text,
        nullable=True,
        comment="Rejection feedback forwarded to tailoring_agent for re-tailor",
    )
    reviewed_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        server_default="now()",
        nullable=False,
    )
