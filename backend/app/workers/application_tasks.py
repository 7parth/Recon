"""
workers/application_tasks.py — Celery task for running the LangGraph pipeline.

Task:
  run_application_pipeline(thread_id, resume_text, job_url, resume_storage_url)
      Executes the full LangGraph graph run in a Celery worker process.
      Delegates the core graph invocation to ``pipeline_service.run_single_job``
      then chains pgvector indexing via ``index_resume_task``.

Why move to Celery?
  - FastAPI BackgroundTasks share the uvicorn process. If uvicorn restarts,
    in-flight runs are lost.
  - Celery tasks are durably queued in Redis. Worker crashes auto-retry.
  - Separate worker processes = no GIL contention with API request handling.
  - task_track_started=True lets the API return real STARTED status immediately.

Queue: "pipeline"

After the graph run completes, chains index_resume_task to embed + store
the parsed resume text in pgvector for future similarity search.
"""

from __future__ import annotations

import asyncio
import logging

from app.workers.celery_app import celery_app
from app.services.checkpoint_service import get_checkpointer
from app.graph.builder import build_graph
from app.db.database import get_async_session
from app.db.repositories.application_repo import ApplicationRepository
from app.db.repositories.user_repository import UserRepository

logger = logging.getLogger(__name__)



@celery_app.task(
    name="app.workers.application_tasks.run_application_pipeline",
    queue="pipeline",
    bind=True,
    max_retries=0,         # pipeline runs are not safe to auto-retry (LLM + browser state)
    task_track_started=True,
    time_limit=600,        # hard kill after 10 min (covers multi-step ATS forms)
    soft_time_limit=540,   # SIGTERM at 9 min so task can clean up
)
def run_application_pipeline(
    self,
    thread_id: str,
    resume_text: str,
    job_url: str,
    resume_storage_url: str | None = None,
) -> dict:
    """
    Celery task: run the full LangGraph application pipeline.

    1. Builds/retrieves the LangGraph graph (with Postgres checkpointer).
    2. Runs graph.ainvoke() inside asyncio.run().
    3. Updates ApplicationRecord in the DB (status, display fields).
    4. Chains index_resume_task to embed the resume into pgvector.

    Args:
        thread_id:           LangGraph thread ID (must already exist in DB).
        resume_text:         Full parsed resume text.
        job_url:             Job posting URL or raw JD text.
        resume_storage_url:  Optional Supabase Storage URL for the original resume.

    Returns:
        {"status": "completed" | "pending_review" | "failed", "thread_id": <id>}
    """
    logger.info(
        "run_application_pipeline: starting thread_id=%s job_url=%s",
        thread_id,
        job_url,
    )

    result = asyncio.run(
        _run_pipeline_async(
            thread_id=thread_id,
            resume_text=resume_text,
            job_url=job_url,
            resume_storage_url=resume_storage_url,
        )
    )

    # Chain the indexing task regardless of outcome — we always want to index
    # the raw resume even if matching or automation failed.
    from app.workers.indexing_tasks import index_resume_task

    index_resume_task.apply_async(
        kwargs={"thread_id": thread_id, "resume_text": resume_text},
        queue="indexing",
        countdown=5,  # slight delay so pipeline DB writes settle first
    )

    return result


# ── Async implementation ───────────────────────────────────────────────────────

async def _run_pipeline_async(
    thread_id: str,
    resume_text: str,
    job_url: str,
    resume_storage_url: str | None,
) -> dict:
    """
    Async core of run_application_pipeline.

    Builds a fresh graph + checkpointer for this worker process, then
    delegates graph invocation + DB updates to ``pipeline_service.run_single_job``.
    """
    from app.services.pipeline_service import run_single_job

    # Fetch user settings to wire match_score_threshold into graph state.
    # Threshold is stored as an int (0-100) in the DB; graph expects 0.0-1.0.
    # Falls back to None (graph uses its default constant 0.65) if fetch fails.
    match_score_threshold: float | None = None
    try:
        async with get_async_session() as session:
            user_repo = UserRepository(session)
            user_settings = await user_repo.get_settings()
            if user_settings.match_threshold is not None:
                match_score_threshold = user_settings.match_threshold / 100.0
    except Exception as settings_err:
        logger.warning(
            "_run_pipeline_async: could not load user settings (using default threshold): %s",
            settings_err,
        )

    async with get_checkpointer() as checkpointer:
        graph = build_graph(checkpointer=checkpointer)
        outcome = await run_single_job(
            thread_id=thread_id,
            resume_text=resume_text,
            job_url=job_url,
            match_score_threshold=match_score_threshold,
            approval_status="pending",
            graph=graph,
        )

    logger.info(
        "run_application_pipeline: done thread_id=%s status=%s",
        thread_id,
        outcome,
    )
    return {"status": outcome, "thread_id": thread_id}
