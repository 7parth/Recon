"""JobRepository — DB queries for JobRecord."""

from __future__ import annotations

import uuid

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.models.job import JobRecord


class JobRepository:
    """Async repository for JobRecord CRUD.

    Example::

        async with get_async_session() as session:
            repo = JobRepository(session)
            record = await repo.create(
                job_url="https://boards.greenhouse.io/acme/jobs/123",
                company_name="Acme Corp",
                job_title="Senior Software Engineer",
                jd_text="We are looking for...",
            )
    """

    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def create(
        self,
        job_url: str | None = None,
        company_name: str | None = None,
        job_title: str | None = None,
        jd_text: str | None = None,
        match_score: float | None = None,
    ) -> JobRecord:
        """Insert a new JobRecord and return it."""
        record = JobRecord(
            job_url=job_url,
            company_name=company_name,
            job_title=job_title,
            jd_text=jd_text,
            match_score=match_score,
        )
        self._session.add(record)
        await self._session.flush()
        return record

    async def get_by_id(self, record_id: uuid.UUID) -> JobRecord | None:
        """Fetch a single job record by primary key."""
        result = await self._session.execute(
            select(JobRecord).where(JobRecord.id == record_id)
        )
        return result.scalar_one_or_none()
