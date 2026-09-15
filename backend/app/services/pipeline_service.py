"""
services/pipeline_service.py — Shared graph invocation logic.

Extracted from ``api/routes/application._run_graph`` and
``workers/application_tasks._run_pipeline_async`` so both the ad-hoc run
path and the discovery orchestrator can reuse a single implementation.

Public interface
----------------
``run_single_job`` — invoke the LangGraph pipeline for one job URL.

Key design choices
------------------
- Accepts ``approval_status`` so the discovery orchestrator can pass
  ``"approved"`` when ``auto_apply`` is enabled (R4.4).
- Wraps ``graph.ainvoke`` with ``asyncio.wait_for`` to enforce a hard
  timeout (R4.7); timeout is surfaced as a ``"failed"`` return value.
- **Never raises** — every exception path is caught, recorded on the
  ``ApplicationRecord``, and returned as ``"failed"``.
- Does *not* handle pgvector indexing; callers that need it (the
  existing ``_run_graph`` and Celery task) must chain it themselves.
"""

from __future__ import annotations

import asyncio
import logging
from typing import Literal

from app.db.database import get_async_session
from app.db.repositories.application_repo import ApplicationRepository

logger = logging.getLogger(__name__)

# Return type alias for clarity at call sites.
JobOutcome = Literal["pending_review", "applied", "skipped", "failed"]


async def run_single_job(
    *,
    thread_id: str,
    resume_text: str,
    job_url: str,
    match_score_threshold: float | None,
    approval_status: str = "pending",
    graph,
    timeout_seconds: int = 300,
) -> JobOutcome:
    """Invoke the LangGraph pipeline for a single job URL.

    The ``ApplicationRecord`` identified by ``thread_id`` **must already
    exist** in the database before this function is called — the caller is
    responsible for creating it (with ``status = "running"``).

    Parameters
    ----------
    thread_id:
        LangGraph thread ID.  Used as the graph checkpoint key and to
        update the corresponding ``ApplicationRecord``.
    resume_text:
        Full parsed resume text passed into ``ApplicationState.resume_raw``.
    job_url:
        Job posting URL or raw JD text passed into ``ApplicationState.job_url``.
    match_score_threshold:
        Float in [0.0, 1.0] or ``None`` (graph uses default 0.65).
        Already normalised by the caller — stored in DB as 0–100.
    approval_status:
        ``"pending"`` (default) — graph pauses at HUMAN_REVIEW interrupt.
        ``"approved"`` — graph bypasses the interrupt and proceeds to apply
        (used when ``UserSettingsRecord.auto_apply`` is true, R4.4).
    graph:
        Compiled LangGraph graph object with an ``ainvoke`` coroutine.
    timeout_seconds:
        Hard timeout for a single graph invocation.  If exceeded, the
        ``ApplicationRecord`` is marked ``failed`` and ``"failed"`` is
        returned (R4.7).  Defaults to 300 s (5 min).

    Returns
    -------
    ``"pending_review"``
        Graph paused at the HUMAN_REVIEW interrupt.
    ``"applied"`` | ``"skipped"``
        Graph completed with the given terminal submission status.
    ``"failed"``
        Graph timed out, raised an exception, or returned no useful state.
    """
    config = {"configurable": {"thread_id": thread_id}}

    initial_state = {
        "thread_id": thread_id,
        "resume_raw": resume_text,
        "job_url": job_url,
        "match_score_threshold": match_score_threshold,
        "resume_profile": None,
        "job_profile": None,
        "company_profile": None,
        "match_result": None,
        "ats_report": None,
        "tailored_resume": None,
        "cover_letter": None,
        # Supports auto_apply pass-through from the discovery orchestrator (R4.4)
        "approval_status": approval_status,
        "rejection_feedback": None,
        "submission_status": None,
        "error": None,
    }

    try:
        final_state = await asyncio.wait_for(
            graph.ainvoke(initial_state, config=config),
            timeout=timeout_seconds,
        )
    except asyncio.TimeoutError:
        timeout_msg = (
            f"Graph invocation exceeded {timeout_seconds}s timeout for thread_id={thread_id}"
        )
        logger.error("run_single_job: %s", timeout_msg)
        await _mark_failed(thread_id, timeout_msg)
        return "failed"
    except Exception as exc:
        logger.error(
            "run_single_job: thread_id=%s raised unexpected exception: %s",
            thread_id,
            exc,
        )
        await _mark_failed(thread_id, str(exc))
        return "failed"

    # ── Persist display metadata ──────────────────────────────────────────
    try:
        job_profile = final_state.get("job_profile")
        company_profile = final_state.get("company_profile")
        match_result = final_state.get("match_result")

        job_title: str | None = getattr(job_profile, "job_title", None) if job_profile else None
        company_name: str | None = getattr(company_profile, "name", None) if company_profile else None
        match_score: float | None = getattr(match_result, "overall_score", None) if match_result else None

        if any(v is not None for v in (job_title, company_name, match_score)):
            async with get_async_session() as session:
                repo = ApplicationRepository(session)
                await repo.update_display_fields(
                    thread_id,
                    job_title=job_title,
                    company_name=company_name,
                    match_score=match_score,
                )
    except Exception as display_err:
        # Non-fatal — log and continue; status will still be updated below.
        logger.warning(
            "run_single_job: failed to persist display fields for thread_id=%s: %s",
            thread_id,
            display_err,
        )

    # ── Determine and persist terminal status ─────────────────────────────
    submission_status: str | None = final_state.get("submission_status")
    error: str | None = final_state.get("error")

    try:
        async with get_async_session() as session:
            repo = ApplicationRepository(session)
            if submission_status:
                # "applied", "skipped", or "failed"
                await repo.update_status(
                    thread_id,
                    status=submission_status,
                    error_message=error,
                )
            else:
                # Graph paused at the HUMAN_REVIEW interrupt.
                await repo.update_status(thread_id, status="pending_review")
    except Exception as status_err:
        logger.error(
            "run_single_job: failed to persist status for thread_id=%s: %s",
            thread_id,
            status_err,
        )
        # We still return the outcome we determined from the graph state.

    if submission_status in ("applied", "skipped", "failed"):
        return submission_status  # type: ignore[return-value]

    return "pending_review"


# ── Internal helpers ──────────────────────────────────────────────────────────

async def _mark_failed(thread_id: str, error_message: str) -> None:
    """Write ``status = failed`` on the ``ApplicationRecord`` for *thread_id*.

    Swallows any DB errors so the outer exception handler can still return
    ``"failed"`` cleanly without raising.
    """
    try:
        async with get_async_session() as session:
            repo = ApplicationRepository(session)
            await repo.update_status(
                thread_id,
                status="failed",
                error_message=error_message,
            )
    except Exception as db_err:
        logger.error(
            "_mark_failed: could not update DB for thread_id=%s: %s",
            thread_id,
            db_err,
        )
