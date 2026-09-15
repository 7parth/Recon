"""Unit tests for DiscoveryRepository using an in-memory SQLite database.

Uses ``create_async_engine("sqlite+aiosqlite:///:memory:")`` so tests run
without any external Postgres dependency.

SQLite compatibility note
-------------------------
``DiscoveryPreferencesRecord`` has two ``ARRAY(String)`` columns that are
PostgreSQL-specific.  For SQLite we swap those columns to ``Text`` via a
``TypeDecorator`` that JSON-serialises list values on the way in and
deserialises them on the way out.  This lets us exercise all repository
logic without changing the production models.

Requirements covered: 1.2, 1.3, 5.3
"""

from __future__ import annotations

import json
import uuid
from datetime import datetime, timezone
from typing import Any

import pytest
import pytest_asyncio
import sqlalchemy as sa
from sqlalchemy import event, text
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine
from sqlalchemy.orm import DeclarativeBase

# ── Import all models so Base.metadata is fully populated ─────────────────────
import app.db.models  # noqa: F401 — side-effect import registers all ORM tables
from app.db.database import Base
from app.db.models.application import ApplicationRecord
from app.db.models.discovery import DiscoveryPreferencesRecord, DiscoverySessionRecord
from app.db.repositories.discovery_repo import DiscoveryRepository


# ── JSON-list TypeDecorator for SQLite compatibility ─────────────────────────


class _JsonList(sa.TypeDecorator):
    """Stores a Python ``list`` as a JSON string in SQLite TEXT columns.

    On Postgres the native ARRAY type is used instead, so this decorator is
    only applied when patching the column type for the in-memory test engine.
    """

    impl = sa.Text
    cache_ok = True

    def process_bind_param(self, value: Any, dialect: Any) -> str | None:
        if value is None:
            return "[]"
        return json.dumps(value)

    def process_result_value(self, value: Any, dialect: Any) -> list:
        if value is None:
            return []
        return json.loads(value)


def _patch_array_columns_for_sqlite() -> None:
    """Replace PostgreSQL ARRAY columns on DiscoveryPreferencesRecord with
    ``_JsonList`` so that SQLite can store them as TEXT.

    This must be called *before* ``Base.metadata.create_all`` runs on the
    SQLite engine.  The patch is process-level but safe because the test
    module never shares its engine with the production code path.
    """
    table = DiscoveryPreferencesRecord.__table__
    for col_name in ("preferred_locations", "excluded_companies"):
        col = table.c[col_name]
        col.type = _JsonList()


# Apply the patch at import time (before any test fixture creates the engine).
_patch_array_columns_for_sqlite()


# ── Engine / session fixtures ─────────────────────────────────────────────────


@pytest_asyncio.fixture(scope="module")
async def engine():
    """Create an in-memory SQLite engine with all ORM tables."""
    eng = create_async_engine(
        "sqlite+aiosqlite:///:memory:",
        echo=False,
    )

    # SQLite does not enforce FK constraints by default; enable them so that
    # the discovery_sessions FK on ApplicationRecord is respected.
    @event.listens_for(eng.sync_engine, "connect")
    def _enable_fk(dbapi_conn, _record):
        cursor = dbapi_conn.cursor()
        cursor.execute("PRAGMA foreign_keys=ON")
        cursor.close()

    async with eng.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    yield eng

    await eng.dispose()


@pytest_asyncio.fixture
async def session(engine):
    """Provide a fresh transactional AsyncSession for each test.

    Uses a savepoint (nested transaction) so each test is rolled back on
    teardown without recreating the schema.
    """
    factory = async_sessionmaker(
        bind=engine,
        class_=AsyncSession,
        expire_on_commit=False,
        autoflush=False,
    )
    async with factory() as sess:
        async with sess.begin():
            yield sess
            await sess.rollback()


@pytest_asyncio.fixture
async def repo(session):
    """Return a DiscoveryRepository bound to the test session."""
    return DiscoveryRepository(session)


# ── Helpers ───────────────────────────────────────────────────────────────────


async def _seed_application(
    session: AsyncSession,
    *,
    discovery_session_id: uuid.UUID,
    status: str,
) -> ApplicationRecord:
    """Insert a minimal ApplicationRecord row for counter tests."""
    record = ApplicationRecord(
        id=uuid.uuid4(),
        thread_id=str(uuid.uuid4()),  # unique per row
        status=status,
        discovery_session_id=discovery_session_id,
    )
    session.add(record)
    await session.flush()
    return record


# ── Preferences tests (R1.2, R1.3) ───────────────────────────────────────────


@pytest.mark.asyncio
async def test_get_preferences_returns_defaults_when_no_row(repo):
    """R1.3 — get_preferences returns a transient default record when no DB
    row exists for the given user_id.  The returned object must have:
    - target_role == ""
    - preferred_locations == []
    - excluded_companies == []
    - max_jobs_per_session == 10
    - id is None (not persisted)
    """
    prefs = await repo.get_preferences("nonexistent_user_test")

    assert prefs.id is None, "Transient default should have id=None"
    assert prefs.target_role == ""
    assert prefs.preferred_locations == []
    assert prefs.excluded_companies == []
    assert prefs.max_jobs_per_session == 10


@pytest.mark.asyncio
async def test_upsert_preferences_creates_row_on_first_call(repo, session):
    """R1.2 — upsert_preferences inserts a new row when none exists."""
    user_id = f"user_create_{uuid.uuid4().hex[:8]}"

    prefs = await repo.upsert_preferences(
        user_id=user_id,
        target_role="Software Engineer",
        preferred_locations=["San Francisco", "Remote"],
        max_jobs_per_session=20,
    )

    assert prefs.id is not None
    assert prefs.user_id == user_id
    assert prefs.target_role == "Software Engineer"
    assert prefs.preferred_locations == ["San Francisco", "Remote"]
    assert prefs.max_jobs_per_session == 20


@pytest.mark.asyncio
async def test_upsert_preferences_overwrites_existing_values(repo):
    """R1.2 — upsert_preferences updates a row when one already exists and
    refreshes updated_at to a timestamp at least as recent as before.
    """
    user_id = f"user_update_{uuid.uuid4().hex[:8]}"

    # Initial insert
    first = await repo.upsert_preferences(
        user_id=user_id,
        target_role="Data Scientist",
        max_jobs_per_session=5,
    )
    first_updated_at = first.updated_at

    # Overwrite
    second = await repo.upsert_preferences(
        user_id=user_id,
        target_role="ML Engineer",
        max_jobs_per_session=15,
        excluded_companies=["BigCorp"],
    )

    assert second.target_role == "ML Engineer"
    assert second.max_jobs_per_session == 15
    assert second.excluded_companies == ["BigCorp"]
    # updated_at must be refreshed (>= previous value)
    assert second.updated_at >= first_updated_at


@pytest.mark.asyncio
async def test_upsert_preferences_partial_update_preserves_other_fields(repo):
    """R1.2 — when only some fields are provided, existing values are kept."""
    user_id = f"user_partial_{uuid.uuid4().hex[:8]}"

    await repo.upsert_preferences(
        user_id=user_id,
        target_role="Backend Engineer",
        preferred_locations=["New York"],
        max_jobs_per_session=10,
    )

    # Only update the role; locations and cap should be unchanged.
    updated = await repo.upsert_preferences(
        user_id=user_id,
        target_role="Senior Backend Engineer",
    )

    assert updated.preferred_locations == ["New York"]
    assert updated.max_jobs_per_session == 10


# ── Session lifecycle tests ───────────────────────────────────────────────────


@pytest.mark.asyncio
async def test_create_session_returns_running_session(repo):
    """create_session inserts a row with session_status='running'."""
    session_record = await repo.create_session("default_user")

    assert session_record.id is not None
    assert session_record.session_status == "running"
    assert session_record.user_id == "default_user"
    assert session_record.started_at is not None


@pytest.mark.asyncio
async def test_get_active_session_returns_running_session(repo):
    """get_active_session returns the running session for a user."""
    user_id = f"user_active_{uuid.uuid4().hex[:8]}"

    # No active session yet
    none_result = await repo.get_active_session(user_id)
    assert none_result is None

    # Create a running session
    created = await repo.create_session(user_id)

    # Now get_active_session should return it
    active = await repo.get_active_session(user_id)
    assert active is not None
    assert active.id == created.id
    assert active.session_status == "running"


@pytest.mark.asyncio
async def test_update_session_status_changes_status(repo):
    """update_session_status transitions the session to the given status."""
    user_id = f"user_status_{uuid.uuid4().hex[:8]}"
    session_record = await repo.create_session(user_id)

    completed_at = datetime.now(timezone.utc)
    await repo.update_session_status(
        session_record.id,
        status="completed",
        completed_at=completed_at,
    )

    # After status update the session is no longer "running"
    active = await repo.get_active_session(user_id)
    assert active is None

    # Fetch it directly to confirm the status changed
    fetched = await repo.get_session(session_record.id)
    assert fetched is not None
    assert fetched.session_status == "completed"


@pytest.mark.asyncio
async def test_update_session_status_sets_error_message(repo):
    """update_session_status persists the error_message when provided."""
    user_id = f"user_err_{uuid.uuid4().hex[:8]}"
    session_record = await repo.create_session(user_id)

    await repo.update_session_status(
        session_record.id,
        status="failed",
        error="Something went wrong",
    )

    fetched = await repo.get_session(session_record.id)
    assert fetched is not None
    assert fetched.session_status == "failed"
    assert fetched.error_message == "Something went wrong"


@pytest.mark.asyncio
async def test_full_session_lifecycle(repo):
    """End-to-end lifecycle: create → verify active → complete → verify gone."""
    user_id = f"user_lifecycle_{uuid.uuid4().hex[:8]}"

    # 1. No active session at the start
    assert await repo.get_active_session(user_id) is None

    # 2. Create session — should appear as active
    sess = await repo.create_session(user_id)
    assert (await repo.get_active_session(user_id)).id == sess.id

    # 3. Mark as completed — should no longer be active
    await repo.update_session_status(sess.id, status="completed")
    assert await repo.get_active_session(user_id) is None

    # 4. Raw fetch still works
    finished = await repo.get_session(sess.id)
    assert finished.session_status == "completed"


# ── Session counter tests (R5.3) ─────────────────────────────────────────────


@pytest.mark.asyncio
async def test_get_session_counters_returns_zeros_for_empty_session(repo):
    """R5.3 — counters are all zero when no ApplicationRecord rows exist."""
    user_id = f"user_counter_empty_{uuid.uuid4().hex[:8]}"
    sess = await repo.create_session(user_id)

    counters = await repo.get_session_counters(sess.id)

    assert counters.jobs_pending_review == 0
    assert counters.jobs_applied == 0
    assert counters.jobs_skipped == 0
    assert counters.jobs_failed == 0


@pytest.mark.asyncio
async def test_get_session_counters_correct_counts(repo, session):
    """R5.3 — counters reflect the actual per-status counts for the session."""
    user_id = f"user_counter_{uuid.uuid4().hex[:8]}"
    sess = await repo.create_session(user_id)

    # Seed: 2 pending_review, 1 applied, 3 skipped, 1 failed
    await _seed_application(session, discovery_session_id=sess.id, status="pending_review")
    await _seed_application(session, discovery_session_id=sess.id, status="pending_review")
    await _seed_application(session, discovery_session_id=sess.id, status="applied")
    await _seed_application(session, discovery_session_id=sess.id, status="skipped")
    await _seed_application(session, discovery_session_id=sess.id, status="skipped")
    await _seed_application(session, discovery_session_id=sess.id, status="skipped")
    await _seed_application(session, discovery_session_id=sess.id, status="failed")

    counters = await repo.get_session_counters(sess.id)

    assert counters.jobs_pending_review == 2
    assert counters.jobs_applied == 1
    assert counters.jobs_skipped == 3
    assert counters.jobs_failed == 1


@pytest.mark.asyncio
async def test_get_session_counters_only_counts_own_session(repo, session):
    """R5.3 — counters do not include rows belonging to a different session."""
    user_id = f"user_isolation_{uuid.uuid4().hex[:8]}"
    sess_a = await repo.create_session(user_id)
    sess_b = await repo.create_session(user_id)

    # Applications in session A
    await _seed_application(session, discovery_session_id=sess_a.id, status="applied")
    await _seed_application(session, discovery_session_id=sess_a.id, status="applied")

    # Application in session B — must not appear in A's counters
    await _seed_application(session, discovery_session_id=sess_b.id, status="applied")

    counters_a = await repo.get_session_counters(sess_a.id)
    assert counters_a.jobs_applied == 2

    counters_b = await repo.get_session_counters(sess_b.id)
    assert counters_b.jobs_applied == 1
