"""AutomationLogRepository — DB queries for AutomationLogRecord.
"""

from __future__ import annotations

from typing import Sequence
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.models.log import AutomationLogRecord


class AutomationLogRepository:
    """Async repository for AutomationLogRecord CRUD."""

    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def create(
        self,
        thread_id: str,
        level: str,
        message: str,
        context: str | None = None,
        ts: str | None = None,
    ) -> AutomationLogRecord:
        """Insert a single automation log entry."""
        record = AutomationLogRecord(
            thread_id=thread_id,
            level=level,
            message=message,
            context=context,
            ts=ts,
        )
        self._session.add(record)
        await self._session.commit()
        return record

    async def get_by_thread_id(
        self,
        thread_id: str,
        limit: int = 500,
    ) -> Sequence[AutomationLogRecord]:
        """Fetch all log records for a given thread_id, ordered by creation time."""
        stmt = (
            select(AutomationLogRecord)
            .where(AutomationLogRecord.thread_id == thread_id)
            .order_by(AutomationLogRecord.created_at.asc())
            .limit(limit)
        )
        result = await self._session.execute(stmt)
        return result.scalars().all()
