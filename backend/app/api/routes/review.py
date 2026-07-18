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
from fastapi import APIRouter, HTTPException, BackgroundTasks

from app.graph.builder import graph
from app.api.schemas.application import (
    ApproveRequest,
    ReviewPayload,
    RunStatus,
    MatchSummary,
)

logger = logging.getLogger(__name__)
router = APIRouter(tags=["review"])

# Import the run registry from application.py to share state.
# In production this would be a DB, but for now we share the dict.
from app.api.routes.application import _runs


@router.get("/runs/{thread_id}/review", response_model=ReviewPayload)
async def get_review(thread_id: str):
    """
    Fetch the tailored documents awaiting human approval.

    Only valid when the run's status is "awaiting_review".
    Reads the LangGraph checkpoint state using graph.get_state().

    New concept — graph.get_state():
      This reads the latest saved checkpoint for a thread WITHOUT running
      any nodes.  It's a pure state read — cheap, safe to call multiple times.
      The returned StateSnapshot has a .values dict with the full graph state.
    """
    run = _runs.get(thread_id)
    if not run:
        raise HTTPException(status_code=404, detail=f"No run found for thread_id={thread_id}")

    if run["status"] != "awaiting_review":
        raise HTTPException(
            status_code=409,
            detail=f"Run is not awaiting review (status={run['status']}). "
                   "Wait for status=awaiting_review before fetching review.",
        )

    config = {"configurable": {"thread_id": thread_id}}

    # Read checkpoint state without running any nodes
    snapshot = graph.get_state(config)
    state = snapshot.values

    # Extract required fields — these must be present if we're at HUMAN_REVIEW
    tailored_resume = state.get("tailored_resume")
    cover_letter    = state.get("cover_letter")
    match_result    = state.get("match_result")
    ats_report      = state.get("ats_report")
    company_profile = state.get("company_profile")

    if tailored_resume is None or cover_letter is None:
        raise HTTPException(
            status_code=500,
            detail="Checkpoint is missing tailored_resume or cover_letter — graph may have failed.",
        )

    return ReviewPayload(
        thread_id=thread_id,
        company_name=company_profile.name if company_profile else None,
        job_url=state.get("job_url", ""),
        match_score=match_result.overall_score if match_result else 0.0,
        ats_keyword_coverage=ats_report.keyword_match if ats_report else 0.0,
        tailored_resume=tailored_resume.content,
        cover_letter=cover_letter.content,
        match_summary=MatchSummary(
            overall_score=match_result.overall_score if match_result else 0.0,
            strengths=match_result.strengths if match_result else [],
            weaknesses=match_result.weaknesses if match_result else [],
            gap_areas=match_result.gap_areas if match_result else [],
        ),
        ats_recommendations=ats_report.recommendations if ats_report else "",
    )


@router.post("/runs/{thread_id}/approve", response_model=RunStatus)
async def submit_review_decision(
    thread_id: str,
    decision: ApproveRequest,
    background_tasks: BackgroundTasks,
):
    """
    Submit the human approval or rejection decision.

    On approval:   graph resumes → apply_agent → tracking_agent → END
    On rejection:  graph resumes → tailoring_agent (re-tailor) → cover_letter
                   → HUMAN_REVIEW interrupt again (new review cycle)

    The graph is resumed by calling graph.invoke() with the SAME thread_id
    and an updated state dict.  LangGraph merges these values into the
    checkpoint and continues execution from human_review_agent.
    """
    run = _runs.get(thread_id)
    if not run:
        raise HTTPException(status_code=404, detail=f"No run found for thread_id={thread_id}")

    if run["status"] != "awaiting_review":
        raise HTTPException(
            status_code=409,
            detail=f"Run is not awaiting review (status={run['status']})",
        )

    # Validate rejection has feedback
    if not decision.approved and not (decision.feedback and decision.feedback.strip()):
        raise HTTPException(
            status_code=422,
            detail="feedback is required when approved=False. "
                   "Provide specific notes to guide the re-tailor.",
        )

    # Build state update to merge into checkpoint
    state_update: dict = {
        "approval_status": "approved" if decision.approved else "rejected",
        "rejection_feedback": decision.feedback if not decision.approved else None,
    }

    # Mark as running again before background task starts
    _runs[thread_id]["status"] = "running"

    # Resume graph in background (same pattern as initial run)
    background_tasks.add_task(
        _resume_graph,
        thread_id=thread_id,
        state_update=state_update,
        is_approval=decision.approved,
    )

    action = "approved → applying" if decision.approved else "rejected → re-tailoring"
    logger.info("submit_review_decision: thread=%s | action=%s", thread_id, action)

    return RunStatus(thread_id=thread_id, status="running")


def _resume_graph(thread_id: str, state_update: dict, is_approval: bool):
    """
    Resume the graph after a human review decision.

    Calls graph.invoke() with the same thread_id — LangGraph loads the checkpoint,
    merges state_update, and continues from human_review_agent.
    """
    config = {"configurable": {"thread_id": thread_id}}

    try:
        final_state = graph.invoke(state_update, config=config)

        submission_status = final_state.get("submission_status")

        if is_approval:
            # Approval path always goes to completion
            _runs[thread_id] = {
                "status": "completed",
                "submission_status": submission_status or "failed",
                "error": final_state.get("error"),
            }
        else:
            # Rejection path loops back to another HUMAN_REVIEW interrupt
            if submission_status:
                _runs[thread_id] = {
                    "status": "completed",
                    "submission_status": submission_status,
                    "error": final_state.get("error"),
                }
            else:
                # Paused at HUMAN_REVIEW again (re-tailor complete, new review)
                _runs[thread_id]["status"] = "awaiting_review"

        logger.info(
            "_resume_graph: thread=%s | submission=%s",
            thread_id, submission_status,
        )

    except Exception as e:
        logger.error("_resume_graph: thread=%s raised exception: %s", thread_id, e)
        _runs[thread_id] = {"status": "failed", "error": str(e), "submission_status": None}
