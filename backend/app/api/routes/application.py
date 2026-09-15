"""
api/routes/application.py — Core run lifecycle endpoints.

Endpoints:
  POST /runs/start        — launch a new application run (async, returns thread_id)
  GET  /runs/{thread_id}/status — poll run status
  POST /resume/parse      — parse an uploaded resume file → plain text

Key concept — thread_id and LangGraph checkpoints:
  Every LangGraph run needs a unique thread_id.  This ID is passed to
  graph.invoke() inside {"configurable": {"thread_id": thread_id}}.
  LangGraph uses it to:
    1. Save the graph state after every node (checkpoint).
    2. Look up and restore state when the graph is resumed (after interrupt).
  The thread_id is the bridge between HTTP requests and graph executions.
  We generate it with uuid4() — guaranteed unique across all runs.

Key concept — BackgroundTasks:
  graph.invoke() is blocking and can take 30-60 seconds (3 LLM calls in parallel).
  We don't want the HTTP request to hang that long.
  FastAPI's BackgroundTasks lets us:
    1. Return a 202 Accepted response immediately with the thread_id.
    2. Run graph.invoke() in the background.
  The client polls GET /runs/{thread_id}/status to check progress.
"""

import uuid
import logging
from pathlib import Path
from fastapi import APIRouter, BackgroundTasks, UploadFile, File, HTTPException, Query, Request

from app.api.schemas.application import (
    RunRequest,
    RunStarted,
    RunStatus,
    ResumeParseResponse,
)
from app.graph.tools.resume_parser import parse_resume

from app.db.database import get_async_session
from app.db.supabase import get_supabase_client
from app.db.repositories.application_repo import ApplicationRepository
from app.services.storage_service import StorageService

logger = logging.getLogger(__name__)
router = APIRouter(tags=["runs"])


# ── Resume parse endpoint ─────────────────────────────────────────────────────

@router.post("/resume/parse", response_model=ResumeParseResponse)
async def parse_resume_file(file: UploadFile = File(...)):
    """
    Parse an uploaded PDF or DOCX resume into plain text.
    Also uploads the file to Supabase Storage and returns the public URL.
    """
    if not file.filename:
        raise HTTPException(status_code=400, detail="No filename provided")

    file_bytes = await file.read()

    if not file_bytes:
        raise HTTPException(status_code=400, detail="Uploaded file is empty")

    file_ext = Path(file.filename).suffix.lower()

    try:
        resume_text = parse_resume(file_bytes, file.filename)
    except ValueError as e:
        raise HTTPException(status_code=422, detail=str(e))
    except RuntimeError as e:
        raise HTTPException(status_code=500, detail=str(e))

    # Generate a temporary ID just for storage folder namespacing
    temp_id = str(uuid.uuid4())

    async with get_async_session() as session:
        client = await get_supabase_client()
        storage_svc = StorageService(client, session)
        resume_storage_url = await storage_svc.upload_resume(
            run_id=temp_id,
            file_bytes=file_bytes,
            file_ext=file_ext,
        )

    return ResumeParseResponse(
        resume_text=resume_text,
        resume_storage_url=resume_storage_url,
        char_count=len(resume_text),
    )


# ── Run start endpoint ────────────────────────────────────────────────────────

@router.post("/runs/start", response_model=RunStarted, status_code=202)
async def start_run(
    request: Request,
    body: RunRequest,
    background_tasks: BackgroundTasks,
    use_celery: bool = Query(
        default=False,
        description=(
            "If true, dispatch the pipeline to a Celery worker (requires Redis). "
            "If false (default), run as a FastAPI BackgroundTask."
        ),
    ),
):
    """
    Launch a new application run for the given resume + job URL.
    Returns immediately with a thread_id (202 Accepted).

    Query param:
      use_celery=true — dispatch to Celery worker queue (needs Redis + worker running).
      use_celery=false (default) — run as a FastAPI BackgroundTask (default, no Redis needed).
    """
    thread_id = str(uuid.uuid4())

    async with get_async_session() as session:
        repo = ApplicationRepository(session)
        await repo.create(
            thread_id=thread_id,
            resume_storage_url=body.resume_storage_url,
            status="running",
        )

    if use_celery:
        # ── Celery path: durable, survives server restarts ────────────────
        try:
            from app.workers.application_tasks import run_application_pipeline
            run_application_pipeline.apply_async(
                kwargs={
                    "thread_id": thread_id,
                    "resume_text": body.resume_text,
                    "job_url": body.effective_job_url,
                    "resume_storage_url": body.resume_storage_url,
                },
                queue="pipeline",
            )
            logger.info(
                "start_run [celery]: queued thread_id=%s for job_url=%s",
                thread_id,
                body.effective_job_url,
            )
        except Exception as e:
            # If Redis is unavailable, fall back to BackgroundTasks and warn.
            logger.warning(
                "start_run: Celery dispatch failed (%s) — falling back to BackgroundTask", e
            )
            graph = request.app.state.graph
            background_tasks.add_task(
                _run_graph,
                thread_id=thread_id,
                resume_text=body.resume_text,
                job_url=body.effective_job_url,
                graph=graph,
            )
    else:
        # ── Default path: FastAPI BackgroundTask ──────────────────────────
        graph = request.app.state.graph
        background_tasks.add_task(
            _run_graph,
            thread_id=thread_id,
            resume_text=body.resume_text,
            job_url=body.effective_job_url,
            graph=graph,
        )
        logger.info(
            "start_run [background]: launched thread_id=%s for job_url=%s",
            thread_id,
            body.effective_job_url,
        )

    return RunStarted(thread_id=thread_id)


async def _run_graph(thread_id: str, resume_text: str, job_url: str, graph):
    """
    Execute the LangGraph graph in the background asynchronously.

    Delegates the core graph invocation + DB status updates to
    ``pipeline_service.run_single_job``, then chains pgvector indexing.
    """
    # Fetch user settings to wire match_score_threshold into graph state.
    # Threshold is stored as an int (0-100) in the DB; graph expects 0.0-1.0.
    # Falls back to None (graph uses its default constant 0.65) if fetch fails.
    match_score_threshold: float | None = None
    try:
        async with get_async_session() as session:
            from app.db.repositories.user_repository import UserRepository
            user_repo = UserRepository(session)
            user_settings = await user_repo.get_settings()
            if user_settings.match_threshold is not None:
                match_score_threshold = user_settings.match_threshold / 100.0
    except Exception as settings_err:
        logger.warning(
            "_run_graph: could not load user settings (using default threshold): %s", settings_err
        )

    from app.services.pipeline_service import run_single_job

    outcome = await run_single_job(
        thread_id=thread_id,
        resume_text=resume_text,
        job_url=job_url,
        match_score_threshold=match_score_threshold,
        approval_status="pending",
        graph=graph,
    )

    logger.info("_run_graph: thread=%s finished with outcome=%s", thread_id, outcome)

    # ── Index resume in pgvector for similarity search ────────────────────
    # Fire-and-forget async task. Errors here are non-fatal.
    try:
        from app.vectorstore.indexing import index_resume
        import asyncio

        asyncio.get_running_loop().create_task(
            index_resume(thread_id=thread_id, resume_text=resume_text)
        )
    except Exception as idx_err:
        logger.warning("_run_graph: pgvector indexing failed (non-fatal): %s", idx_err)


# ── Status polling endpoint ───────────────────────────────────────────────────

@router.get("/runs/{thread_id}/status", response_model=RunStatus)
async def get_run_status(thread_id: str):
    """
    Poll the status of a run from the database.
    """
    async with get_async_session() as session:
        repo = ApplicationRepository(session)
        run = await repo.get_by_thread_id(thread_id)
        
        if not run:
            raise HTTPException(status_code=404, detail=f"No run found for thread_id={thread_id}")

        # Map DB status back to API response schema if needed.
        # DB status: running, pending_review, applied, skipped, failed
        # API status expects: running, awaiting_review, completed, failed, skipped
        api_status = run.status
        if run.status == "pending_review":
            api_status = "awaiting_review"
        elif run.status in ("applied", "skipped"):
            api_status = "completed"

        return RunStatus(
            thread_id=thread_id,
            status=api_status,
            submission_status=run.status if run.status in ("applied", "skipped", "failed") else None,
            error=run.error_message,
            job_title=run.job_title,
            company=run.company_name,
            match_score=run.match_score,
            started_at=run.created_at,
        )

