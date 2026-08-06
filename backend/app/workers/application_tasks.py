"""
workers/application_tasks.py — Celery task for running the LangGraph pipeline.

Task:
  run_application_pipeline(thread_id, resume_text, job_url, resume_storage_url)
      Executes the full LangGraph graph run in a Celery worker process.
      Mirrors the logic in api/routes/application._run_graph() but runs
      in a background Celery worker instead of a FastAPI BackgroundTask.

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

    Runs in a fresh asyncio event loop (via asyncio.run()).
    Builds a fresh graph + checkpointer for this worker process.
    """
    config = {"configurable": {"thread_id": thread_id}}

    initial_state = {
        "resume_raw": resume_text,
        "job_url": job_url,
        "resume_profile": None,
        "job_profile": None,
        "company_profile": None,
        "match_result": None,
        "ats_report": None,
        "tailored_resume": None,
        "cover_letter": None,
        "approval_status": "pending",
        "rejection_feedback": None,
        "submission_status": None,
        "error": None,
    }

    try:
        async with get_checkpointer() as checkpointer:
            graph = build_graph(checkpointer=checkpointer)
            final_state = await graph.ainvoke(initial_state, config=config)

        submission_status = final_state.get("submission_status")
        error = final_state.get("error")

        job_profile = final_state.get("job_profile")
        company_profile = final_state.get("company_profile")
        match_result = final_state.get("match_result")

        job_title: str | None = getattr(job_profile, "job_title", None) if job_profile else None
        company_name: str | None = getattr(company_profile, "name", None) if company_profile else None
        match_score: float | None = getattr(match_result, "overall_score", None) if match_result else None

        async with get_async_session() as session:
            repo = ApplicationRepository(session)
            if any(v is not None for v in (job_title, company_name, match_score)):
                await repo.update_display_fields(
                    thread_id,
                    job_title=job_title,
                    company_name=company_name,
                    match_score=match_score,
                )
            if submission_status:
                await repo.update_status(thread_id, status=submission_status, error_message=error)
            else:
                # Paused at HUMAN_REVIEW interrupt
                await repo.update_status(thread_id, status="pending_review")

        final_db_status = submission_status or "pending_review"
        logger.info(
            "run_application_pipeline: done thread_id=%s status=%s",
            thread_id,
            final_db_status,
        )
        return {"status": final_db_status, "thread_id": thread_id}

    except Exception as e:
        logger.error(
            "run_application_pipeline: thread_id=%s raised exception: %s",
            thread_id,
            e,
        )
        async with get_async_session() as session:
            repo = ApplicationRepository(session)
            await repo.update_status(thread_id, status="failed", error_message=str(e))
        return {"status": "failed", "thread_id": thread_id, "error": str(e)}
