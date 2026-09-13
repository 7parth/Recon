"""
api/routes/review.py — Human review checkpoint endpoints.

This is the most critical part of the API — it implements the mandatory
human-in-the-loop checkpoint.

Endpoints:
  GET  /runs/{thread_id}/review   — fetch the draft docs awaiting approval
  POST /runs/{thread_id}/approve  — submit the approval/rejection decision

How the interrupt/resume works end-to-end:
  1. _run_graph() in application.py calls graph.invoke() and pauses at
     the HUMAN_REVIEW interrupt. The LangGraph checkpoint saves all state.
  2. Status is set to "awaiting_review".
  3. Client polls status, sees "awaiting_review", calls GET /review.
  4. This endpoint reads the checkpoint state via graph.get_state(config)
     and builds a ReviewPayload from it.
  5. Client displays tailored_resume and cover_letter to the user.
  6. User clicks Approve or Reject (with feedback).
  7. Client calls POST /approve with the decision.
  8. This endpoint calls graph.invoke() AGAIN with the same thread_id.
     LangGraph loads the checkpoint, merges the new state values
     (approval_status, rejection_feedback), and resumes from human_review_agent.
  9. human_review_agent validates the decision, router routes to apply_agent
     (approved) or tailoring_agent (rejected).
"""

import logging
from fastapi import APIRouter, HTTPException, BackgroundTasks, Request

from app.api.schemas.application import (
    ApproveRequest,
    ReviewPayload,
    RunStatus,
    MatchSummary,
)

from app.db.database import get_async_session
from app.db.repositories.application_repo import ApplicationRepository

logger = logging.getLogger(__name__)
router = APIRouter(tags=["review"])


@router.get("/runs/{thread_id}/review", response_model=ReviewPayload)
async def get_review(thread_id: str, request: Request):
    """
    Fetch the tailored documents awaiting human approval.
    Reads the LangGraph checkpoint state using request.app.state.graph.aget_state().
    """
    async with get_async_session() as session:
        repo = ApplicationRepository(session)
        run = await repo.get_by_thread_id(thread_id)
        if not run:
            raise HTTPException(status_code=404, detail=f"No run found for thread_id={thread_id}")

        if run.status != "pending_review":
            raise HTTPException(
                status_code=409,
                detail=f"Run is not awaiting review (status={run.status}). "
                       "Wait for status=awaiting_review before fetching review.",
            )

    config = {"configurable": {"thread_id": thread_id}}

    # Read checkpoint state without running any nodes
    snapshot = await request.app.state.graph.aget_state(config)
    state = snapshot.values

    # Extract required fields — these must be present if we're at HUMAN_REVIEW
    tailored_resume = state.get("tailored_resume")
    cover_letter    = state.get("cover_letter")
    match_result    = state.get("match_result")
    ats_report      = state.get("ats_report")
    company_profile = state.get("company_profile")
    job_profile     = state.get("job_profile")

    if tailored_resume is None or cover_letter is None:
        raise HTTPException(
            status_code=500,
            detail="Checkpoint is missing tailored_resume or cover_letter — graph may have failed.",
        )

    ats_coverage = ats_report.keyword_match if ats_report else 0.0

    return ReviewPayload(
        thread_id=thread_id,
        company_name=company_profile.name if company_profile else None,
        job_title=job_profile.job_title if job_profile else None,
        job_url=state.get("job_url", ""),
        match_score=match_result.overall_score if match_result else 0.0,
        ats_keyword_coverage=ats_coverage,
        ats_score=round(ats_coverage * 100, 1),   # 0–100 % for display
        tailored_resume=tailored_resume.content,
        cover_letter=cover_letter.content,
        match_summary=MatchSummary(
            overall_score=match_result.overall_score if match_result else 0.0,
            strengths=match_result.strengths if match_result else [],
            weaknesses=match_result.weaknesses if match_result else [],
            gap_areas=match_result.gap_areas if match_result else [],
        ),
        ats_recommendations=ats_report.recommendations if ats_report else "",
        matched_keywords=ats_report.matched_keywords if ats_report else [],
        missing_keywords=ats_report.missing_keywords if ats_report else [],
    )


@router.post("/runs/{thread_id}/approve", response_model=RunStatus)
async def submit_review_decision(
    thread_id: str,
    decision: ApproveRequest,
    request: Request,
    background_tasks: BackgroundTasks,
):
    """
    Submit the human approval or rejection decision.
    """
    async with get_async_session() as session:
        repo = ApplicationRepository(session)
        run = await repo.get_by_thread_id(thread_id)
        if not run:
            raise HTTPException(status_code=404, detail=f"No run found for thread_id={thread_id}")

        if run.status != "pending_review":
            raise HTTPException(
                status_code=409,
                detail=f"Run is not awaiting review (status={run.status})",
            )

        # Validate rejection has feedback
        if not decision.approved and not (decision.feedback and decision.feedback.strip()):
            raise HTTPException(
                status_code=422,
                detail="feedback is required when approved=False. "
                       "Provide specific notes to guide the re-tailor.",
            )

        # Mark as running again before background task starts
        await repo.update_status(thread_id, status="running")

    # Build state update to merge into checkpoint
    state_update: dict = {
        "approval_status": "approved" if decision.approved else "rejected",
        "rejection_feedback": decision.feedback if not decision.approved else None,
    }

    # Resume graph in background
    graph = request.app.state.graph
    background_tasks.add_task(
        _resume_graph,
        thread_id=thread_id,
        state_update=state_update,
        is_approval=decision.approved,
        graph=graph,
    )

    action = "approved → applying" if decision.approved else "rejected → re-tailoring"
    logger.info("submit_review_decision: thread=%s | action=%s", thread_id, action)

    return RunStatus(thread_id=thread_id, status="running")


async def _resume_graph(thread_id: str, state_update: dict, is_approval: bool, graph):
    """
    Resume the graph asynchronously after a human review decision.
    """
    config = {"configurable": {"thread_id": thread_id}}

    try:
        final_state = await graph.ainvoke(state_update, config=config)

        submission_status = final_state.get("submission_status")

        async with get_async_session() as session:
            repo = ApplicationRepository(session)
            if is_approval:
                # Approval path always goes to completion
                await repo.update_status(
                    thread_id,
                    status=submission_status or "failed",
                    error_message=final_state.get("error")
                )
            else:
                # Rejection path loops back to another HUMAN_REVIEW interrupt
                if submission_status:
                    await repo.update_status(
                        thread_id,
                        status=submission_status,
                        error_message=final_state.get("error")
                    )
                else:
                    # Paused at HUMAN_REVIEW again (re-tailor complete, new review)
                    await repo.update_status(thread_id, status="pending_review")

        logger.info(
            "_resume_graph: thread=%s | submission=%s",
            thread_id, submission_status,
        )

    except Exception as e:
        logger.error("_resume_graph: thread=%s raised exception: %s", thread_id, e)
        async with get_async_session() as session:
            repo = ApplicationRepository(session)
            await repo.update_status(thread_id, status="failed", error_message=str(e))

