"""DiscoveryRepository — DB queries for discovery preferences and sessions.

All reads and writes for ``DiscoveryPreferencesRecord`` and
``DiscoverySessionRecord`` live here.  Counter queries that aggregate over
``ApplicationRecord`` rows also live here so the route layer never builds
raw SQL directly.
"""

from __future__ import annotations

import uuid
from dataclasses import dataclass
from datetime import datetime, timezone

from sqlalchemy import func, select, update
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.models.application import ApplicationRecord
from app.db.models.discovery import DiscoveryPreferencesRecord, DiscoverySessionRecord


# ── SessionCounters ────────────────────────────────────────────────────────────


@dataclass(frozen=True)
class SessionCounters:
    """Live per-status counts for a single discovery session.

    Derived by a GROUP BY query over ``ApplicationRecord`` rows linked to
    the session — never cached, always reflects the current DB state.

    Attributes
    ----------
    jobs_pending_review
        Applications awaiting human review (status = ``pending_review``).
    jobs_applied
        Applications successfully submitted (status = ``applied``).
    jobs_skipped
        Applications skipped by match scoring (status = ``skipped``).
    jobs_failed
        Applications that hit an error or timeout (status = ``failed``).
    """

    jobs_pending_review: int = 0
    jobs_applied: int = 0
    jobs_skipped: int = 0
    jobs_failed: int = 0


# ── DiscoveryRepository ────────────────────────────────────────────────────────


class DiscoveryRepository:
    """Async repository for discovery preferences and session CRUD.

    Instantiate with an ``AsyncSession`` injected from ``get_async_session``.

    Example::

        async with get_async_session() as session:
            repo = DiscoveryRepository(session)
            prefs = await repo.get_preferences("default_user")
    """

    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    # ── Preferences ───────────────────────────────────────────────────────────

    async def get_preferences(
        self, user_id: str = "default_user"
    ) -> DiscoveryPreferencesRecord:
        """Return stored preferences for *user_id*.

        If no row exists, returns a transient default record (not persisted).
        Callers can distinguish "no row" from "row with default values" by
        checking whether ``record.id`` is ``None``.
        """
        result = await self._session.execute(
            select(DiscoveryPreferencesRecord).where(
                DiscoveryPreferencesRecord.user_id == user_id
            )
        )
        row = result.scalar_one_or_none()
        if row is not None:
            return row

        # Return an unsaved default so callers always get a usable object.
        return DiscoveryPreferencesRecord(
            user_id=user_id,
            target_role="",
            preferred_locations=[],
            excluded_companies=[],
            max_jobs_per_session=10,
        )

    async def upsert_preferences(
        self,
        *,
        user_id: str = "default_user",
        target_role: str | None = None,
        preferred_locations: list[str] | None = None,
        excluded_companies: list[str] | None = None,
        max_jobs_per_session: int | None = None,
    ) -> DiscoveryPreferencesRecord:
        """Insert or update the preferences row for *user_id*.

        Only the fields explicitly passed (non-``None``) are updated.
        ``updated_at`` is always refreshed.

        Returns the persisted record.
        """
        existing = await self._session.execute(
            select(DiscoveryPreferencesRecord).where(
                DiscoveryPreferencesRecord.user_id == user_id
            )
        )
        record = existing.scalar_one_or_none()

        if record is None:
            record = DiscoveryPreferencesRecord(user_id=user_id)
            self._session.add(record)

        if target_role is not None:
            record.target_role = target_role
        if preferred_locations is not None:
            record.preferred_locations = preferred_locations
        if excluded_companies is not None:
            record.excluded_companies = excluded_companies
        if max_jobs_per_session is not None:
            record.max_jobs_per_session = max_jobs_per_session

        record.updated_at = datetime.now(timezone.utc)

        await self._session.flush()
        await self._session.refresh(record)
        return record

    # ── Sessions ──────────────────────────────────────────────────────────────

    async def create_session(
        self, user_id: str = "default_user"
    ) -> DiscoverySessionRecord:
        """Insert a new session with ``session_status = "running"``."""
        record = DiscoverySessionRecord(
            user_id=user_id,
            session_status="running",
            started_at=datetime.now(timezone.utc),
        )
        self._session.add(record)
        await self._session.flush()
        await self._session.refresh(record)
        return record

    async def get_session(
        self, session_id: uuid.UUID
    ) -> DiscoverySessionRecord | None:
        """Fetch a session by primary key; returns ``None`` if not found."""
        result = await self._session.execute(
            select(DiscoverySessionRecord).where(
                DiscoverySessionRecord.id == session_id
            )
        )
        return result.scalar_one_or_none()

    async def get_active_session(
        self, user_id: str = "default_user"
    ) -> DiscoverySessionRecord | None:
        """Return the running session for *user_id*, or ``None`` if absent."""
        result = await self._session.execute(
            select(DiscoverySessionRecord).where(
                DiscoverySessionRecord.user_id == user_id,
                DiscoverySessionRecord.session_status == "running",
            )
        )
        return result.scalar_one_or_none()

    async def list_sessions(
        self,
        user_id: str = "default_user",
        limit: int = 20,
    ) -> list[DiscoverySessionRecord]:
        """Return up to *limit* sessions for *user_id*, newest first."""
        result = await self._session.execute(
            select(DiscoverySessionRecord)
            .where(DiscoverySessionRecord.user_id == user_id)
            .order_by(DiscoverySessionRecord.started_at.desc())
            .limit(limit)
        )
        return list(result.scalars().all())

    # ── Session updates ───────────────────────────────────────────────────────

    async def update_session_status(
        self,
        session_id: uuid.UUID,
        status: str,
        error: str | None = None,
        completed_at: datetime | None = None,
    ) -> None:
        """Set *status* (and optionally *error* / *completed_at*) on a session."""
        values: dict = {"session_status": status}
        if error is not None:
            values["error_message"] = error
        if completed_at is not None:
            values["completed_at"] = completed_at

        await self._session.execute(
            update(DiscoverySessionRecord)
            .where(DiscoverySessionRecord.id == session_id)
            .values(**values)
        )

    async def increment_jobs_processed(self, session_id: uuid.UUID) -> None:
        """Atomically increment ``jobs_processed`` by 1.

        Uses a server-side expression to avoid a read-modify-write race.
        """
        await self._session.execute(
            update(DiscoverySessionRecord)
            .where(DiscoverySessionRecord.id == session_id)
            .values(
                jobs_processed=DiscoverySessionRecord.jobs_processed + 1
            )
        )

    async def set_jobs_found(self, session_id: uuid.UUID, count: int) -> None:
        """Set the ``jobs_found`` column after de-duplication is complete."""
        await self._session.execute(
            update(DiscoverySessionRecord)
            .where(DiscoverySessionRecord.id == session_id)
            .values(jobs_found=count)
        )

    # ── Counters ──────────────────────────────────────────────────────────────

    async def get_session_counters(
        self, session_id: uuid.UUID
    ) -> SessionCounters:
        """Return live per-status counts for *session_id*.

        Runs a single GROUP BY query over ``ApplicationRecord`` rows whose
        ``discovery_session_id`` matches *session_id*:

        .. code-block:: sql

            SELECT status, COUNT(*)
            FROM applications
            WHERE discovery_session_id = :session_id
            GROUP BY status

        Statuses not present in the result default to ``0``.  The returned
        ``SessionCounters`` is immutable (frozen dataclass); callers that
        need fresh counts should call this method again rather than caching.

        Requirements: 5.3
        """
        result = await self._session.execute(
            select(ApplicationRecord.status, func.count().label("cnt"))
            .where(ApplicationRecord.discovery_session_id == session_id)
            .group_by(ApplicationRecord.status)
        )
        rows = result.all()  # list of (status, count) tuples

        counts: dict[str, int] = {status: cnt for status, cnt in rows}

        return SessionCounters(
            jobs_pending_review=counts.get("pending_review", 0),
            jobs_applied=counts.get("applied", 0),
            jobs_skipped=counts.get("skipped", 0),
            jobs_failed=counts.get("failed", 0),
        )
