"""ApplicationRepository — DB queries for ApplicationRecord.

All application history reads and writes live here. No other module
should call ``session.execute(select(ApplicationRecord, ...))`` directly.
"""

from __future__ import annotations

import uuid
from datetime import datetime, timezone
from typing import Sequence

from sqlalchemy import select, update
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.models.application import ApplicationRecord


class ApplicationRepository:
    """Async repository for ApplicationRecord CRUD.

    Instantiate with an ``AsyncSession`` injected from ``get_async_session``.

    Example::

        async with get_async_session() as session:
            repo = ApplicationRepository(session)
            record = await repo.create(thread_id="abc-123")
    """

    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    # ── Create ─────────────────────────────────────────────────────────────

    async def create(
        self,
        thread_id: str,
        resume_id: uuid.UUID | None = None,
        job_id: uuid.UUID | None = None,
        company_id: uuid.UUID | None = None,
        resume_storage_url: str | None = None,
        status: str = "running",
    ) -> ApplicationRecord:
        """Insert a new ApplicationRecord and return it."""
        record = ApplicationRecord(
            thread_id=thread_id,
            resume_id=resume_id,
            job_id=job_id,
            company_id=company_id,
            resume_storage_url=resume_storage_url,
            status=status,
        )
        self._session.add(record)
        await self._session.flush()  # populate id without committing
        return record

    # ── Read ───────────────────────────────────────────────────────────────

    async def get_by_id(self, record_id: uuid.UUID) -> ApplicationRecord | None:
        """Fetch a single record by primary key."""
        result = await self._session.execute(
            select(ApplicationRecord).where(ApplicationRecord.id == record_id)
        )
        return result.scalar_one_or_none()

    async def get_by_thread_id(self, thread_id: str) -> ApplicationRecord | None:
        """Fetch a record by LangGraph thread_id (unique)."""
        result = await self._session.execute(
            select(ApplicationRecord).where(ApplicationRecord.thread_id == thread_id)
        )
        return result.scalar_one_or_none()

    async def list_all(
        self,
        *,
        limit: int = 50,
        offset: int = 0,
        status: str | None = None,
    ) -> Sequence[ApplicationRecord]:
        """Return a paginated list of application records, newest first.

        Parameters
        ----------
        limit
            Maximum number of rows to return (default 50).
        offset
            Number of rows to skip (for pagination).
        status
            Optional status filter (e.g. ``"applied"``).
        """
        stmt = select(ApplicationRecord).order_by(
            ApplicationRecord.created_at.desc()
        )
        if status:
            stmt = stmt.where(ApplicationRecord.status == status)
        stmt = stmt.limit(limit).offset(offset)
        result = await self._session.execute(stmt)
        return result.scalars().all()

    # ── Update ─────────────────────────────────────────────────────────────

    async def update_status(
        self,
        thread_id: str,
        status: str,
        rejection_feedback: str | None = None,
        error_message: str | None = None,
    ) -> ApplicationRecord | None:
        """Update the status (and optionally feedback/error) of a run.

        Returns the updated record, or None if thread_id is not found.
        """
        values: dict = {
            "status": status,
            "updated_at": datetime.now(timezone.utc),
        }
        if rejection_feedback is not None:
            values["rejection_feedback"] = rejection_feedback
        if error_message is not None:
            values["error_message"] = error_message

        await self._session.execute(
            update(ApplicationRecord)
            .where(ApplicationRecord.thread_id == thread_id)
            .values(**values)
        )
        return await self.get_by_thread_id(thread_id)

    async def update_display_fields(
        self,
        thread_id: str,
        job_title: str | None = None,
        company_name: str | None = None,
        match_score: float | None = None,
    ) -> ApplicationRecord | None:
        """Persist display metadata from the final graph state.

        Called by ``_run_graph`` after the pipeline finishes so the history
        page can show job title and company without joining to the jobs table.
        """
        values: dict = {"updated_at": datetime.now(timezone.utc)}
        if job_title is not None:
            values["job_title"] = job_title
        if company_name is not None:
            values["company_name"] = company_name
        if match_score is not None:
            values["match_score"] = match_score

        await self._session.execute(
            update(ApplicationRecord)
            .where(ApplicationRecord.thread_id == thread_id)
            .values(**values)
        )
        return await self.get_by_thread_id(thread_id)

    async def set_document_urls(
        self,
        thread_id: str,
        tailored_resume_url: str | None = None,
        cover_letter_url: str | None = None,
    ) -> ApplicationRecord | None:
        """Store Supabase Storage URLs for generated documents."""
        values: dict = {"updated_at": datetime.now(timezone.utc)}
        if tailored_resume_url is not None:
            values["tailored_resume_url"] = tailored_resume_url
        if cover_letter_url is not None:
            values["cover_letter_url"] = cover_letter_url

        await self._session.execute(
            update(ApplicationRecord)
            .where(ApplicationRecord.thread_id == thread_id)
            .values(**values)
        )
        return await self.get_by_thread_id(thread_id)
