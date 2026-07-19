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
from fastapi import APIRouter, BackgroundTasks, UploadFile, File, HTTPException, Request

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
        client = get_supabase_client()
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
async def start_run(request: Request, body: RunRequest, background_tasks: BackgroundTasks):
    """
    Launch a new application run for the given resume + job URL.
    Returns immediately with a thread_id (202 Accepted).
    """
    thread_id = str(uuid.uuid4())

    async with get_async_session() as session:
        repo = ApplicationRepository(session)
        # We start with status="running" conceptually, but DB default is "pending_review".
        # Let's set it to "running" manually. Wait, "running" is not in the DB comment, 
        # but the column is just String(50). We can use "running".
        await repo.create(
            thread_id=thread_id,
            resume_storage_url=body.resume_storage_url,
        )
        await repo.update_status(thread_id, status="running")

    # Add the graph execution as a background task.
    graph = request.app.state.graph
    background_tasks.add_task(
        _run_graph,
        thread_id=thread_id,
        resume_text=body.resume_text,
        job_url=body.job_url,
        graph=graph,
    )

    logger.info("start_run: launched thread_id=%s for job_url=%s", thread_id, body.job_url)

    return RunStarted(thread_id=thread_id)


async def _run_graph(thread_id: str, resume_text: str, job_url: str, graph):
    """
    Execute the LangGraph graph in the background asynchronously.
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
        final_state = await graph.ainvoke(initial_state, config=config)

        submission_status = final_state.get("submission_status")
        error = final_state.get("error")

        async with get_async_session() as session:
            repo = ApplicationRepository(session)
            if submission_status:
                # submission_status is "applied", "skipped", or "failed"
                await repo.update_status(
                    thread_id, 
                    status=submission_status, 
                    error_message=error
                )
            else:
                # Paused at HUMAN_REVIEW interrupt
                await repo.update_status(thread_id, status="pending_review")

        logger.info(
            "_run_graph: thread=%s finished | submission=%s",
            thread_id,
            submission_status,
        )

    except Exception as e:
        logger.error("_run_graph: thread=%s raised exception: %s", thread_id, e)
        async with get_async_session() as session:
            repo = ApplicationRepository(session)
            await repo.update_status(thread_id, status="failed", error_message=str(e))


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
        )

