"""ResumeRepository — DB queries for ResumeRecord."""

from __future__ import annotations

import uuid

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.models.resume import ResumeRecord


class ResumeRepository:
    """Async repository for ResumeRecord CRUD.

    Example::

        async with get_async_session() as session:
            repo = ResumeRepository(session)
            record = await repo.create(
                storage_url="https://xxx.supabase.co/storage/v1/object/public/...",
                parsed_text="John Doe\\nSoftware Engineer...",
                candidate_name="John Doe",
                candidate_email="john@example.com",
            )
    """

    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def create(
        self,
        storage_url: str | None = None,
        parsed_text: str | None = None,
        candidate_name: str | None = None,
        candidate_email: str | None = None,
    ) -> ResumeRecord:
        """Insert a new ResumeRecord and return it."""
        record = ResumeRecord(
            storage_url=storage_url,
            parsed_text=parsed_text,
            candidate_name=candidate_name,
            candidate_email=candidate_email,
        )
        self._session.add(record)
        await self._session.flush()
        return record

    async def get_by_id(self, record_id: uuid.UUID) -> ResumeRecord | None:
        """Fetch a single resume record by primary key."""
        result = await self._session.execute(
            select(ResumeRecord).where(ResumeRecord.id == record_id)
        )
        return result.scalar_one_or_none()
