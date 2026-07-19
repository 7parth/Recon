"""ResumeRecord ORM model.

Stores the parsed candidate profile and a reference to the original
resume file in Supabase Storage. The raw file bytes are never stored in
the DB — only the public storage URL.
"""

from __future__ import annotations

import uuid
from datetime import datetime, timezone

from sqlalchemy import DateTime, String, Text
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column

from app.db.database import Base


class ResumeRecord(Base):
    """Persisted representation of a candidate's uploaded resume.

    Columns
    -------
    id
        Primary key (UUID v4, server-default).
    storage_url
        Public Supabase Storage URL for the original resume file.
        Set by ``StorageService.upload_resume()`` after the file is uploaded.
    parsed_text
        Plain-text content extracted by the resume parser.
        Kept in the DB for search and re-use across runs without re-parsing.
    candidate_name
        Extracted full name (denormalised for quick display).
    candidate_email
        Extracted email (denormalised for quick display).
    created_at
        UTC timestamp of the upload.
    """

    __tablename__ = "resumes"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4,
        server_default="gen_random_uuid()",
    )
    storage_url: Mapped[str | None] = mapped_column(
        Text,
        nullable=True,
        comment="Supabase Storage public URL for the original resume file",
    )
    parsed_text: Mapped[str | None] = mapped_column(
        Text,
        nullable=True,
        comment="Plain-text extracted from the resume — used for re-parsing without re-upload",
    )
    candidate_name: Mapped[str | None] = mapped_column(String(255), nullable=True)
    candidate_email: Mapped[str | None] = mapped_column(String(255), nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        server_default="now()",
        nullable=False,
    )
