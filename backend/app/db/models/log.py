"""AutomationLogRecord ORM model — persisted automation events.

Stores structured logs emitted by AutomationLogger so logs survive server restarts.
"""

from __future__ import annotations

import uuid
from datetime import datetime, timezone

from sqlalchemy import DateTime, String, Text, text
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column

from app.db.database import Base


class AutomationLogRecord(Base):
    """Persisted log entry for automation runs.

    Columns
    -------
    id
        Primary key (UUID v4).
    thread_id
        LangGraph checkpoint thread ID (indexed for fast query per run).
    level
        INFO | DEBUG | WARN | ERROR | SUCCESS
    message
        Log text content.
    context
        Originating component/file (e.g. "greenhouse.py", "browser.py").
    ts
        Formatted timestamp string (HH:MM:SS.mmm).
    created_at
        UTC timestamp of creation.
    """

    __tablename__ = "automation_logs"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4,
        server_default=text("gen_random_uuid()"),
    )
    thread_id: Mapped[str] = mapped_column(
        String(255),
        nullable=False,
        index=True,
    )
    level: Mapped[str] = mapped_column(
        String(50),
        nullable=False,
    )
    message: Mapped[str] = mapped_column(
        Text,
        nullable=False,
    )
    context: Mapped[str | None] = mapped_column(
        String(255),
        nullable=True,
    )
    ts: Mapped[str | None] = mapped_column(
        String(50),
        nullable=True,
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        server_default=text("now()"),
        nullable=False,
        index=True,
    )
