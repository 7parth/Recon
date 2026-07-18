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
from fastapi import APIRouter, BackgroundTasks, UploadFile, File, HTTPException

from app.graph.builder import graph
from app.api.schemas.application import (
    RunRequest,
    RunStarted,
    RunStatus,
    ResumeParseResponse,
)
from app.graph.tools.resume_parser import parse_resume

logger = logging.getLogger(__name__)
router = APIRouter(tags=["runs"])

# In-memory run registry: thread_id → status dict
# TODO: replace with DB-backed storage once app/db/ is implemented
_runs: dict[str, dict] = {}


# ── Resume parse endpoint ─────────────────────────────────────────────────────

@router.post("/resume/parse", response_model=ResumeParseResponse)
async def parse_resume_file(file: UploadFile = File(...)):
    """
    Parse an uploaded PDF or DOCX resume into plain text.

    The client calls this first, gets back resume_text, then includes
    resume_text in POST /runs/start.

    Why separate parse from run-start?
      - Parsing is fast (<1s). Running the graph is slow (30-60s).
      - Separating them lets the client preview the parsed text and
        confirm it's correct before launching an expensive graph run.
      - The parsed text can be reused across multiple job runs without
        re-uploading the file each time.
    """
    if not file.filename:
        raise HTTPException(status_code=400, detail="No filename provided")

    file_bytes = await file.read()

    if not file_bytes:
        raise HTTPException(status_code=400, detail="Uploaded file is empty")

    try:
        resume_text = parse_resume(file_bytes, file.filename)
    except ValueError as e:
        raise HTTPException(status_code=422, detail=str(e))
    except RuntimeError as e:
        raise HTTPException(status_code=500, detail=str(e))

    return ResumeParseResponse(
        resume_text=resume_text,
        char_count=len(resume_text),
    )


# ── Run start endpoint ────────────────────────────────────────────────────────

@router.post("/runs/start", response_model=RunStarted, status_code=202)
async def start_run(request: RunRequest, background_tasks: BackgroundTasks):
    """
    Launch a new application run for the given resume + job URL.

    Returns immediately with a thread_id (202 Accepted).
    The graph runs in the background — poll /runs/{thread_id}/status.

    The 202 status code means "accepted for processing, not yet complete" —
    semantically correct for a long-running async operation.
    """
    thread_id = str(uuid.uuid4())

    # Register the run as "running" before launching the background task
    # so polling starts working immediately.
    _runs[thread_id] = {"status": "running", "error": None, "submission_status": None}

    # Add the graph execution as a background task.
    # FastAPI runs this after the response is sent — no blocking.
    background_tasks.add_task(
        _run_graph,
        thread_id=thread_id,
        resume_text=request.resume_text,
        job_url=request.job_url,
    )

    logger.info("start_run: launched thread_id=%s for job_url=%s", thread_id, request.job_url)

    return RunStarted(thread_id=thread_id)


def _run_graph(thread_id: str, resume_text: str, job_url: str):
    """
    Execute the LangGraph graph in the background.

    This is a regular (sync) function, not async — BackgroundTasks runs it
    in a thread pool automatically.  LangGraph's sync runner is used here.

    The graph will pause at the HUMAN_REVIEW interrupt.  When it does,
    the status is updated to "awaiting_review" and graph.invoke() returns.
    The review route then reads the checkpoint state and surfaces it to the client.
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
        # graph.invoke() runs until it hits the interrupt_before=[HUMAN_REVIEW]
        # or reaches END.  Either way it returns the final state snapshot.
        final_state = graph.invoke(initial_state, config=config)

        submission_status = final_state.get("submission_status")
        error = final_state.get("error")

        if submission_status:
            # Graph ran to completion (post-approval) or was skipped
            _runs[thread_id] = {
                "status": "completed",
                "submission_status": submission_status,
                "error": error,
            }
        else:
            # Graph paused at HUMAN_REVIEW interrupt — waiting for review
            _runs[thread_id]["status"] = "awaiting_review"

        logger.info(
            "_run_graph: thread=%s finished | status=%s | submission=%s",
            thread_id,
            _runs[thread_id]["status"],
            submission_status,
        )

    except Exception as e:
        logger.error("_run_graph: thread=%s raised exception: %s", thread_id, e)
        _runs[thread_id] = {"status": "failed", "error": str(e), "submission_status": None}


# ── Status polling endpoint ───────────────────────────────────────────────────

@router.get("/runs/{thread_id}/status", response_model=RunStatus)
async def get_run_status(thread_id: str):
    """
    Poll the status of a run.

    Statuses:
      running         — graph is executing (parallel agents, LLM calls in progress)
      awaiting_review — graph paused at HUMAN_REVIEW; fetch /runs/{id}/review to see docs
      completed       — run finished (applied / failed / skipped)
      failed          — unhandled error during graph execution
    """
    run = _runs.get(thread_id)
    if not run:
        raise HTTPException(status_code=404, detail=f"No run found for thread_id={thread_id}")

    return RunStatus(
        thread_id=thread_id,
        status=run["status"],
        submission_status=run.get("submission_status"),
        error=run.get("error"),
    )
