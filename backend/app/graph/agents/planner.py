"""
Planner Agent — supervisor / entry node for the Recon graph.

Responsibilities:
  - Validate that required inputs (resume_raw, job_url) are present.
  - Set initial approval_status to "pending" if not already set.
  - Surface any upstream error so the graph can route to END cleanly.
  - Does NOT call the LLM; all routing decisions live in router.py.

LangGraph calls this node first (START → planner). After it returns, the
conditional edge in builder.py decides which agent runs next.
"""

import logging
from app.graph.state import ApplicationState

logger = logging.getLogger(__name__)


def planner_node(state: ApplicationState) -> ApplicationState:
    """
    Entry / supervisor node.  Validates inputs and seeds defaults.

    Returns an updated state dict (LangGraph merges it into the graph state).
    """
    updates: dict = {}

    # ── 1. Input validation ──────────────────────────────────────────────────
    missing = []
    if not state.get("resume_raw", "").strip():
        missing.append("resume_raw")
    if not state.get("job_url", "").strip():
        missing.append("job_url")

    if missing:
        msg = f"Planner: missing required inputs: {', '.join(missing)}"
        logger.error(msg)
        updates["error"] = msg
        return updates  # router will send to END on error

    # ── 2. Seed defaults ─────────────────────────────────────────────────────
    if state.get("approval_status") is None:
        updates["approval_status"] = "pending"

    # Clear any stale error from a previous retry
    if state.get("error"):
        updates["error"] = None

    logger.info(
        "Planner: inputs validated. job_url=%s | resume_raw length=%d",
        state["job_url"],
        len(state["resume_raw"]),
    )

    return updates
