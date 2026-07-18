"""
human_review_agent.py — Validates the human approval decision after the interrupt.

Node signature: human_review_agent_node(state) -> dict

How the interrupt works (critical concept):
─────────────────────────────────────────────
  The graph was compiled with interrupt_before=[HUMAN_REVIEW] in builder.py.
  This means LangGraph STOPS execution automatically BEFORE this node runs.
  
  Flow:
    1. cover_letter_agent finishes, writes state["cover_letter"].
    2. LangGraph sees the next node is HUMAN_REVIEW → pauses, saves checkpoint.
    3. Graph returns control to the caller (FastAPI) with state snapshot.
    4. FastAPI surfaces tailored_resume + cover_letter to the user for review.
    5. User clicks "Approve" or "Reject" (with feedback) via the API.
    6. FastAPI resumes the graph by calling:
         graph.invoke(
             {"approval_status": "approved"},   ← or "rejected" + feedback
             config={"configurable": {"thread_id": <thread_id>}},
         )
    7. LangGraph loads the checkpoint, merges the new state values,
       and NOW runs human_review_agent_node.
    8. This node validates the decision is present, then returns.
    9. router.route_after_review() reads approval_status and routes next.

This node's job:
  Validate that approval_status has been set by the API before we proceed.
  It's a safety net — the graph should never reach here without it, but
  if something goes wrong in the API layer, this catches it gracefully.

No LLM call needed here — this is pure state validation.
"""

import logging
from app.graph.state import ApplicationState

logger = logging.getLogger(__name__)


def human_review_agent_node(state: ApplicationState) -> dict:
    """
    LangGraph node: validate human approval decision post-interrupt.

    By the time this runs, the graph was already paused and resumed
    with the user's decision injected into state.

    Reads:  state["approval_status"]    — "approved" | "rejected"
            state["rejection_feedback"] — optional, only if rejected
    Writes: nothing (passthrough — router.route_after_review reads approval_status)
    """
    approval_status    = state.get("approval_status")
    rejection_feedback = state.get("rejection_feedback")

    # ── Validate decision is present ──────────────────────────────────────────
    if approval_status not in ("approved", "rejected"):
        # This should not happen in normal flow — the API should always set it
        # before resuming. If it does happen, fail loudly so it's debuggable.
        error_msg = (
            f"human_review_agent: invalid or missing approval_status='{approval_status}'. "
            "The graph was resumed without a valid human decision. "
            "Expected 'approved' or 'rejected'."
        )
        logger.error(error_msg)
        return {"error": error_msg}

    # ── Validate rejection has feedback ───────────────────────────────────────
    if approval_status == "rejected":
        if not rejection_feedback or not rejection_feedback.strip():
            # Soft warning — rejection without feedback is allowed but
            # tailoring_agent will have nothing to act on. Log and continue.
            logger.warning(
                "human_review_agent: rejection without feedback — "
                "tailoring_agent will re-tailor without specific guidance"
            )
        else:
            logger.info(
                "human_review_agent: REJECTED with feedback (%d chars)",
                len(rejection_feedback),
            )
    else:
        logger.info("human_review_agent: APPROVED — proceeding to apply_agent")

    # ── Passthrough — no state changes needed ─────────────────────────────────
    # The router reads approval_status directly from state.
    # Return empty dict = no updates; LangGraph merges nothing.
    return {}
