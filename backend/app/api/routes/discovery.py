"""api/routes/discovery.py — REST endpoints for discovery preferences and sessions.

Endpoints
---------
GET  /discovery/preferences                      — read stored preferences
PUT  /discovery/preferences                      — partial update (R8.1–8.4)
POST /discovery/sessions                         — start a new session (202, R2.1–2.6)
GET  /discovery/sessions                         — list last 20 sessions (R5.2)
GET  /discovery/sessions/{session_id}            — session detail with live counters (R5.1, 5.3)
POST /discovery/sessions/{session_id}/cancel     — cancel a running session (R6.1, 6.2)

Requirements: 2.1–2.6, 5.1–5.3, 6.1–6.2, 8.1–8.4
"""

from __future__ import annotations

import uuid
import logging
from datetime import datetime, timezone

from fastapi import APIRouter, BackgroundTasks, HTTPException, Request

from app.api.schemas.discovery import (
    DiscoveryPreferencesResponse,
    DiscoveryPreferencesUpdate,
    DiscoverySessionResponse,
    StartSessionResponse,
)
from app.db.database import get_async_session
from app.db.repositories.discovery_repo import DiscoveryRepository
from app.db.repositories.resume_repo import ResumeRepository

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/discovery", tags=["discovery"])


# ── Helpers ───────────────────────────────────────────────────────────────────


def _build_session_response(record, counters=None) -> DiscoverySessionResponse:
    """Map a ``DiscoverySessionRecord`` + optional ``SessionCounters`` → response schema."""
    return DiscoverySessionResponse(
        session_id=record.id,
        session_status=record.session_status,
        jobs_found=record.jobs_found,
        jobs_processed=record.jobs_processed,
        jobs_pending_review=counters.jobs_pending_review if counters else 0,
        jobs_applied=counters.jobs_applied if counters else 0,
        jobs_skipped=counters.jobs_skipped if counters else 0,
        jobs_failed=counters.jobs_failed if counters else 0,
        started_at=record.started_at,
        completed_at=record.completed_at,
    )


# ── Preferences ───────────────────────────────────────────────────────────────


@router.get("/preferences", response_model=DiscoveryPreferencesResponse)
async def get_preferences():
    """Return the current discovery preferences for the default user.

    If no preferences row exists, returns defaults without persisting them (R1.3).

    Requirements: 8.1
    """
    async with get_async_session() as session:
        repo = DiscoveryRepository(session)
        record = await repo.get_preferences("default_user")
        return DiscoveryPreferencesResponse.model_validate(record)


@router.put("/preferences", response_model=DiscoveryPreferencesResponse)
async def update_preferences(body: DiscoveryPreferencesUpdate):
    """Partially update discovery preferences for the default user.

    Only fields present in the request body are written; omitted fields are
    left unchanged.

    Validates:
    - ``max_jobs_per_session`` range 1–50 enforced by Pydantic schema (R8.3).
    - ``preferred_locations`` length ≤ 5 enforced here (R8.4).

    Requirements: 8.1, 8.2, 8.3, 8.4
    """
    if body.preferred_locations is not None and len(body.preferred_locations) > 5:
        raise HTTPException(
            status_code=422,
            detail="preferred_locations may contain at most 5 entries.",
        )

    async with get_async_session() as session:
        repo = DiscoveryRepository(session)
        record = await repo.upsert_preferences(
            user_id="default_user",
            target_role=body.target_role,
            preferred_locations=body.preferred_locations,
            excluded_companies=body.excluded_companies,
            max_jobs_per_session=body.max_jobs_per_session,
        )
        return DiscoveryPreferencesResponse.model_validate(record)


# ── Sessions — start ──────────────────────────────────────────────────────────


@router.post("/sessions", response_model=StartSessionResponse, status_code=202)
async def start_session(request: Request, background_tasks: BackgroundTasks):
    """Queue a new discovery session and return 202 immediately.

    Pre-flight checks (in order):
    1. Reject with 409 if a session is already ``running`` (R2.2).
    2. Reject with 422 if ``target_role`` is empty or whitespace (R2.3).
    3. Reject with 422 if no parsed resume text is stored (R2.4).

    On success, inserts a ``running`` session record and enqueues
    ``run_discovery_session`` as a FastAPI BackgroundTask.

    Requirements: 2.1–2.6
    """
    async with get_async_session() as session:
        discovery_repo = DiscoveryRepository(session)
        resume_repo = ResumeRepository(session)

        # R2.2 — reject if a session is already running
        active = await discovery_repo.get_active_session("default_user")
        if active is not None:
            raise HTTPException(
                status_code=409,
                detail={
                    "message": "A discovery session is already running.",
                    "active_session_id": str(active.id),
                },
            )

        # R2.3 — target_role must be set and non-whitespace
        prefs = await discovery_repo.get_preferences("default_user")
        if not prefs.target_role or not prefs.target_role.strip():
            raise HTTPException(
                status_code=422,
                detail="target_role must be set before starting a discovery session.",
            )

        # R2.4 — a parsed resume must exist
        resume = await resume_repo.get_latest()
        if resume is None or not resume.parsed_text:
            raise HTTPException(
                status_code=422,
                detail="A parsed resume must be uploaded before starting a discovery session.",
            )

        # Create session record (auto-committed when context exits)
        new_session = await discovery_repo.create_session("default_user")
        session_id = new_session.id

    # Enqueue orchestrator as a background task (R2.5)
    # Import deferred to avoid circular imports at module load time.
    from app.discovery.orchestrator import run_discovery_session  # noqa: PLC0415

    graph = request.app.state.graph
    background_tasks.add_task(run_discovery_session, session_id, graph)

    logger.info("start_session: queued discovery session %s", session_id)
    return StartSessionResponse(
        session_id=session_id,
        session_status="running",
        message="Discovery session started. Poll GET /discovery/sessions/{session_id} for progress.",
    )


# ── Sessions — list ───────────────────────────────────────────────────────────


@router.get("/sessions", response_model=list[DiscoverySessionResponse])
async def list_sessions():
    """Return the 20 most-recent discovery sessions, ordered newest first.

    Counter fields (``jobs_pending_review`` etc.) are set to ``0`` on list
    responses for performance; fetch the detail endpoint for live counts.

    Requirements: 5.2
    """
    async with get_async_session() as session:
        repo = DiscoveryRepository(session)
        records = await repo.list_sessions("default_user", limit=20)
        return [_build_session_response(r) for r in records]


# ── Sessions — detail ─────────────────────────────────────────────────────────


@router.get("/sessions/{session_id}", response_model=DiscoverySessionResponse)
async def get_session(session_id: uuid.UUID):
    """Return full session detail including live per-status application counts.

    Counter fields are populated via a live GROUP BY query (R5.3).
    Returns 404 if the session does not exist.

    Requirements: 5.1, 5.3
    """
    async with get_async_session() as session:
        repo = DiscoveryRepository(session)

        record = await repo.get_session(session_id)
        if record is None:
            raise HTTPException(status_code=404, detail="Session not found")

        counters = await repo.get_session_counters(session_id)
        return _build_session_response(record, counters)


# ── Sessions — cancel ─────────────────────────────────────────────────────────


@router.post("/sessions/{session_id}/cancel")
async def cancel_session(session_id: uuid.UUID):
    """Cancel a running discovery session.

    - 404 if the session does not exist.
    - 409 if the session is not currently ``running`` (R6.2) — includes
      ``current_status`` in the response body.
    - 200 with ``{"session_id": ..., "session_status": "cancelled"}`` on
      success (R6.1).

    Writes ``session_status = "cancelled"`` and ``completed_at = utcnow()``.
    The orchestrator's per-iteration DB-read cancellation check handles the
    actual stop — no in-process signal is needed.

    Requirements: 6.1, 6.2
    """
    async with get_async_session() as session:
        repo = DiscoveryRepository(session)

        record = await repo.get_session(session_id)
        if record is None:
            raise HTTPException(status_code=404, detail="Session not found")

        if record.session_status != "running":
            raise HTTPException(
                status_code=409,
                detail={
                    "detail": "Session is not running",
                    "current_status": record.session_status,
                },
            )

        await repo.update_session_status(
            session_id,
            status="cancelled",
            completed_at=datetime.now(timezone.utc),
        )
        # session auto-commits on context exit (get_async_session commits on success)

    logger.info("cancel_session: session %s cancelled", session_id)
    return {"session_id": str(session_id), "session_status": "cancelled"}
