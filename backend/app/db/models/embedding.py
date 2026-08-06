"""ResumeEmbeddingRecord ORM model — stores 384-dim resume embeddings via pgvector.

Each row maps one application run (thread_id) to the embedding vector of its
parsed resume text. Used by the vectorstore layer for candidate similarity search.

Design:
  - ``thread_id`` mirrors ApplicationRecord.thread_id — the same LangGraph run ID.
  - ``embedding`` is a 384-dimensional float32 vector (all-MiniLM-L6-v2 output).
  - Unique constraint on thread_id — one embedding per run, upsert on re-index.
  - IVFFlat index (created in Alembic migration) enables fast approximate cosine search.
"""

from __future__ import annotations

import uuid
from datetime import datetime, timezone

from sqlalchemy import DateTime, String, Text
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column

from pgvector.sqlalchemy import Vector

from app.db.database import Base


class ResumeEmbeddingRecord(Base):
    """One 384-dim embedding vector per application run.

    Columns
    -------
    id
        Primary key (UUID v4).
    thread_id
        LangGraph thread ID — links back to ApplicationRecord.thread_id.
    embedding
        384-dimensional float32 vector from sentence-transformers all-MiniLM-L6-v2.
        Stored with pgvector; queried via cosine distance operator ``<=>``.
    resume_snippet
        Optional short excerpt of the resume (first 500 chars) for display purposes.
    created_at
        UTC timestamp — when this embedding was indexed.
    """

    __tablename__ = "resume_embeddings"

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
        comment="LangGraph thread_id — one embedding per run",
    )
    embedding: Mapped[list] = mapped_column(
        Vector(384),
        nullable=False,
        comment="384-dim float32 embedding from all-MiniLM-L6-v2",
    )
    resume_snippet: Mapped[str | None] = mapped_column(
        Text,
        nullable=True,
        comment="First 500 chars of resume text — for display in similarity search results",
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        server_default="now()",
        nullable=False,
    )
