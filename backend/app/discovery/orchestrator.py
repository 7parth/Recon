"""
discovery/orchestrator.py — Discovery session orchestration.

Public interface
----------------
``run_discovery_session(session_id, graph)`` — async background function that
drives one full automated discovery session end-to-end.

Session lifecycle
-----------------
1. Load preferences + resume text for ``"default_user"``.
2. Validate prerequisites: non-empty ``target_role`` and resume text present.
3. For each ``preferred_location``, call ``search_jobs(role, location)``
   (synchronous, runs in a thread pool).  Stop once ``max_jobs_per_session``
   raw URLs are collected.  If **all** locations fail, set ``session_status =
   failed`` and return.  If **some** fail, log and set
   ``completed_with_errors`` at the end.
4. Deduplicate via ``JobDeduplicator``.
5. Persist ``jobs_found`` on the session record.
6. Sequential dispatch loop over the de-duped queue:
     a. Check session status at the top of each iteration — break on
        ``cancelled`` (R6.3, R6.4).
     b. Create an ``ApplicationRecord`` with ``discovery_session_id``.
     c. Call ``pipeline_service.run_single_job``.
     d. Increment ``jobs_processed``.
7. Set terminal ``session_status``:
     - ``completed``             — all done, no search errors.
     - ``completed_with_errors`` — some search locations failed.
     - (``failed`` is set in the top-level except handler.)

Error isolation
---------------
- A per-job pipeline failure is *contained* inside ``run_single_job`` which
  never raises; the loop always continues.
- An unhandled exception anywhere in the orchestrator is caught by the
  outermost ``try/except`` and written to ``session_status = failed``.

Requirements: 2.3, 2.4, 2.6, 3.1, 3.2, 3.3, 3.4, 3.5, 3.6, 3.7,
              4.1–4.9, 6.3, 6.4
"""

from __future__ import annotations

import asyncio
import logging
import uuid
from datetime import datetime, timezone

from app.db.database import get_async_session
from app.db.repositories.application_repo import ApplicationRepository
from app.db.repositories.discovery_repo import DiscoveryRepository
from app.db.repositories.resume_repo import ResumeRepository
from app.db.repositories.user_repository import UserRepository
from app.discovery.deduplicator import JobDeduplicator
from app.graph.tools.search import search_jobs

logger = logging.getLogger(__name__)

USER_ID = "default_user"


async def run_discovery_session(
    session_id: uuid.UUID,
    graph,
) -> None:
    """Drive a full automated discovery session.

    This function is intended to be run as a FastAPI ``BackgroundTask`` (or
    equivalent async background runner).  It **never raises** — every failure
    path is caught and written to the session record so callers always see a
    terminal ``session_status``.

    Parameters
    ----------
    session_id:
        Primary key of an existing ``DiscoverySessionRecord`` that was
        created (with ``session_status = "running"``) by the API route
        before this background task was enqueued.
    graph:
        Compiled LangGraph runnable injected from ``app.state.graph``.
    """
    try:
        await _run_session(session_id, graph)
    except Exception as exc:
        # Top-level safety net — should only be reached if _run_session itself
        # has a bug that escapes its own error handling.
        logger.exception(
            "run_discovery_session: unhandled exception for session_id=%s: %s",
            session_id,
            exc,
        )
        await _fail_session(session_id, str(exc))


# ── Core implementation ───────────────────────────────────────────────────────


async def _run_session(session_id: uuid.UUID, graph) -> None:
    """Internal implementation; called by run_discovery_session."""

    # ── Step 1: Load user settings and resume text ────────────────────────
    preferences = None
    resume_text: str | None = None
    match_score_threshold: float | None = None
    approval_status = "pending"

    async with get_async_session() as session:
        # Discovery preferences
        discovery_repo = DiscoveryRepository(session)
        preferences = await discovery_repo.get_preferences(USER_ID)

        # User settings (match threshold + auto_apply flag)
        user_repo = UserRepository(session)
        user_settings = await user_repo.get_settings(USER_ID)
        if user_settings.match_threshold is not None:
            # DB stores as int 0–100; graph expects float 0.0–1.0
            match_score_threshold = user_settings.match_threshold / 100.0
        if user_settings.auto_apply:
            approval_status = "approved"

        # Resume text — most recently uploaded resume
        resume_repo = ResumeRepository(session)
        resume_record = await resume_repo.get_latest()
        resume_text = resume_record.parsed_text if resume_record else None

    # ── Step 2: Validate prerequisites ───────────────────────────────────
    target_role = (preferences.target_role or "").strip()
    if not target_role:
        msg = (
            "Discovery session cannot start: target_role is empty or whitespace. "
            "Set a target role in Discovery Preferences before running a session."
        )
        logger.warning("run_discovery_session: session_id=%s — %s", session_id, msg)
        await _fail_session(session_id, msg)
        return

    if not resume_text:
        msg = (
            "Discovery session cannot start: no parsed resume text found. "
            "Upload and parse a resume before starting a discovery session."
        )
        logger.warning("run_discovery_session: session_id=%s — %s", session_id, msg)
        await _fail_session(session_id, msg)
        return

    preferred_locations: list[str] = preferences.preferred_locations or []
    excluded_companies: list[str] = preferences.excluded_companies or []
    max_jobs: int = preferences.max_jobs_per_session or 10

    # ── Step 3: Search all locations, stop at max_jobs_per_session ────────
    raw_results = []          # list[SearchResult]
    location_error_count = 0
    location_count = len(preferred_locations)

    # If no locations are configured, do one location-agnostic search.
    search_targets = preferred_locations if preferred_locations else [""]

    for location in search_targets:
        if len(raw_results) >= max_jobs:
            logger.debug(
                "run_discovery_session: session_id=%s — raw URL cap %d reached, "
                "skipping remaining locations",
                session_id,
                max_jobs,
            )
            break

        remaining = max_jobs - len(raw_results)
        try:
            # search_jobs is synchronous (DuckDuckGo); run in a thread pool
            # so we don't block the event loop.
            results = await asyncio.get_event_loop().run_in_executor(
                None,
                lambda loc=location, rem=remaining: search_jobs(target_role, loc, max_results=rem),
            )
            raw_results.extend(results)
            logger.info(
                "run_discovery_session: session_id=%s — location=%r returned %d results "
                "(total raw=%d)",
                session_id,
                location,
                len(results),
                len(raw_results),
            )
        except Exception as search_err:
            location_error_count += 1
            logger.error(
                "run_discovery_session: session_id=%s — search failed for location=%r: %s",
                session_id,
                location,
                search_err,
            )

    # If every location query failed, mark failed and return.
    # (R3.6: if Search_Tool raises for all locations → session_status = failed)
    if location_error_count == len(search_targets) and not raw_results:
        msg = (
            f"All {len(search_targets)} location search(es) failed. "
            "No jobs were discovered."
        )
        logger.error("run_discovery_session: session_id=%s — %s", session_id, msg)
        await _fail_session(session_id, msg)
        return

    # Cap to max_jobs (safety net in case extend went slightly over)
    raw_results = raw_results[:max_jobs]

    # ── Step 4: Deduplicate ───────────────────────────────────────────────
    existing_urls: set[str] = set()
    async with get_async_session() as session:
        app_repo = ApplicationRepository(session)
        existing_urls = await app_repo.list_all_job_urls(user_id=USER_ID)

    deduplicator = JobDeduplicator(
        existing_urls=existing_urls,
        excluded_companies=excluded_companies,
    )
    job_queue: list[str] = deduplicator.filter(raw_results, current_queue=[])

    logger.info(
        "run_discovery_session: session_id=%s — %d raw results → %d after dedup",
        session_id,
        len(raw_results),
        len(job_queue),
    )

    # ── Step 5: Persist jobs_found ────────────────────────────────────────
    async with get_async_session() as session:
        discovery_repo = DiscoveryRepository(session)
        await discovery_repo.set_jobs_found(session_id, len(job_queue))
        await session.commit()

    # ── Step 6: Early return if no jobs to process ────────────────────────
    if not job_queue:
        logger.info(
            "run_discovery_session: session_id=%s — job_queue empty after dedup, "
            "marking completed",
            session_id,
        )
        await _complete_session(
            session_id,
            had_search_errors=(location_error_count > 0),
        )
        return

    # ── Step 7: Sequential dispatch loop ─────────────────────────────────
    from app.services.pipeline_service import run_single_job  # local import avoids circular

    had_dispatch_errors = False

    for job_url in job_queue:

        # ── 7a: Cancellation check ────────────────────────────────────────
        async with get_async_session() as session:
            discovery_repo = DiscoveryRepository(session)
            current_session = await discovery_repo.get_session(session_id)

        if current_session is None:
            logger.error(
                "run_discovery_session: session_id=%s — session record not found mid-loop, "
                "aborting",
                session_id,
            )
            return

        if current_session.session_status == "cancelled":
            logger.info(
                "run_discovery_session: session_id=%s — session cancelled, stopping loop",
                session_id,
            )
            return  # Already cancelled; don't overwrite status

        # ── 7b: Create ApplicationRecord ─────────────────────────────────
        thread_id = str(uuid.uuid4())
        async with get_async_session() as session:
            app_repo = ApplicationRepository(session)
            await app_repo.create(
                thread_id=thread_id,
                status="running",
                job_url=job_url,
                discovery_session_id=session_id,
            )
            await session.commit()

        logger.info(
            "run_discovery_session: session_id=%s — dispatching thread_id=%s url=%s",
            session_id,
            thread_id,
            job_url,
        )

        # ── 7c: Run the pipeline ──────────────────────────────────────────
        # R4.8: if resume_text is absent we already failed early above, so it
        # is always present here.  match_score_threshold may be None (graph
        # uses its default 0.65).
        outcome = await run_single_job(
            thread_id=thread_id,
            resume_text=resume_text,
            job_url=job_url,
            match_score_threshold=match_score_threshold,
            approval_status=approval_status,
            graph=graph,
        )

        if outcome == "failed":
            had_dispatch_errors = True

        logger.info(
            "run_discovery_session: session_id=%s — thread_id=%s outcome=%s",
            session_id,
            thread_id,
            outcome,
        )

        # ── 7d: Increment jobs_processed ─────────────────────────────────
        async with get_async_session() as session:
            discovery_repo = DiscoveryRepository(session)
            await discovery_repo.increment_jobs_processed(session_id)
            await session.commit()

    # ── Step 8: Terminal session status ───────────────────────────────────
    # R3.7 / R4.9: completed_with_errors if any search location or any
    # dispatch job failed; completed if everything went smoothly.
    had_errors = had_dispatch_errors or (location_error_count > 0)
    await _complete_session(session_id, had_search_errors=had_errors)


# ── Status helpers ────────────────────────────────────────────────────────────


async def _fail_session(session_id: uuid.UUID, error_message: str) -> None:
    """Write ``session_status = failed`` with an error message.  Never raises."""
    try:
        async with get_async_session() as session:
            repo = DiscoveryRepository(session)
            await repo.update_session_status(
                session_id,
                status="failed",
                error=error_message,
                completed_at=datetime.now(timezone.utc),
            )
            await session.commit()
    except Exception as db_err:
        logger.error(
            "_fail_session: could not update DB for session_id=%s: %s",
            session_id,
            db_err,
        )


async def _complete_session(
    session_id: uuid.UUID,
    *,
    had_search_errors: bool = False,
) -> None:
    """Write ``completed`` or ``completed_with_errors``.  Never raises."""
    status = "completed_with_errors" if had_search_errors else "completed"
    try:
        async with get_async_session() as session:
            repo = DiscoveryRepository(session)
            await repo.update_session_status(
                session_id,
                status=status,
                completed_at=datetime.now(timezone.utc),
            )
            await session.commit()
        logger.info(
            "_complete_session: session_id=%s → status=%s", session_id, status
        )
    except Exception as db_err:
        logger.error(
            "_complete_session: could not update DB for session_id=%s: %s",
            session_id,
            db_err,
        )
