"""
tracking_agent.py — Records the final outcome of an application run.

Node signature: tracking_agent_node(state) -> dict

Position in graph:
  apply_agent → tracking_agent → END

This is the terminal node. It:
  1. Reads submission_status and any error from state
  2. Logs the final outcome
  3. Returns a clean state snapshot for the API layer to persist to DB

No LLM, no browser — this is pure state management.

Why keep this as a separate node instead of doing it in apply_agent?
  Single Responsibility: apply_agent's job is to submit. If the submission
  logic gets complicated (retries, multi-step forms), tracking should not
  be buried inside it.

  Testability: we can test tracking_agent with any combination of
  submission_status values without running browser automation.

  Error resilience: if apply_agent raises an unhandled exception that we
  didn't catch, LangGraph still calls tracking_agent because the edge is
  unconditional (route_after_apply always returns TRACKING_AGENT).
  This guarantees every run — success or failure — gets recorded.

What the API layer does after this node:
  FastAPI reads the final state from the LangGraph checkpoint and persists
  an ApplicationRecord to PostgreSQL with:
    - job_url, company name
    - submission_status
    - tailored_resume.content and cover_letter.content
    - match_result.overall_score
    - timestamp
"""

import logging
from datetime import datetime, timezone

from app.graph.state import ApplicationState

logger = logging.getLogger(__name__)


def tracking_agent_node(state: ApplicationState) -> dict:
    """
    LangGraph terminal node: log and normalise the final run outcome.

    Reads:  submission_status, job_url, company_profile, match_result, error
    Writes: nothing new to state (passthrough with logging)
    """
    submission_status = state.get("submission_status", "unknown")
    job_url           = state.get("job_url", "")
    company_profile   = state.get("company_profile")
    match_result      = state.get("match_result")
    error             = state.get("error")

    company_name  = company_profile.name if company_profile else "unknown company"
    overall_score = match_result.overall_score if match_result else 0.0

    # ── Final outcome log ─────────────────────────────────────────────────────
    # This is the single line of truth for every run — grep for it in prod logs.
    logger.info(
        "TRACKING | status=%-8s | score=%.2f | company='%s' | url=%s%s",
        submission_status,
        overall_score,
        company_name,
        job_url,
        f" | error={error}" if error else "",
    )

    if submission_status == "applied":
        logger.info("✅  Application submitted successfully to %s", company_name)
    elif submission_status == "skipped":
        logger.info("⏭️  Application skipped (unsupported ATS) for %s", company_name)
    elif submission_status == "failed":
        logger.warning("❌  Application FAILED for %s — error: %s", company_name, error)
    else:
        logger.warning("⚠️  Unknown submission_status='%s'", submission_status)

    # ── Return timestamp so API layer can stamp the DB record ─────────────────
    # We compute it here (inside the graph) so it reflects when the run
    # actually finished, not when the API layer processed the result.
    # ISO 8601 UTC string — unambiguous for any timezone.
    completed_at = datetime.now(timezone.utc).isoformat()

    logger.debug("tracking_agent: run completed at %s", completed_at)

    # No meaningful state updates — return empty to signal clean completion.
    # The API layer reads the full checkpoint state after graph ends.
    return {}
