"""
Router — conditional edge functions for the Recon LangGraph.

Each function receives the current ApplicationState and returns a string
constant (node name or END) that LangGraph uses to pick the next edge.

Graph execution order:
  START
    → planner
    → [resume_agent, job_agent, company_agent]   (fan-out, parallel)
    → match_agent
    → (route_after_match)
        ↳ score < threshold  → END          (skip: poor fit)
        ↳ score ≥ threshold  → ats_agent
    → ats_agent
    → tailoring_agent
    → cover_letter_agent
    → human_review (interrupt)
    → (route_after_review)
        ↳ approved  → apply_agent
        ↳ rejected  → tailoring_agent       (re-tailor loop)
    → apply_agent
    → tracking_agent
    → END

Error short-circuit:
  Any node may set state["error"]; route_on_error returns END.
"""

from app.graph.state import ApplicationState
from app.graph.constants import (
    RESUME_AGENT,
    JOB_AGENT,
    COMPANY_AGENT,
    MATCH_AGENT,
    ATS_AGENT,
    TAILORING_AGENT,
    APPLY_AGENT,
    TRACKING_AGENT,
    END,
    APPROVED,
    REJECTED,
    MATCH_SCORE_THRESHOLD,
)


# ── Entry router (after planner) ─────────────────────────────────────────────

def route_after_planner(state: ApplicationState) -> list[str] | str:
    """
    After the planner validates inputs, fan out to the three independent
    parsing agents in parallel.  If the planner set an error, go to END.
    """
    if state.get("error"):
        return END
    # LangGraph supports returning a list to trigger parallel branches.
    return [RESUME_AGENT, JOB_AGENT, COMPANY_AGENT]


# ── Match threshold gate ─────────────────────────────────────────────────────

def route_after_match(state: ApplicationState) -> str:
    """
    Skip weak-fit jobs; only proceed to ATS optimisation when score is
    above the configured threshold.
    """
    if state.get("error"):
        return END

    match = state.get("match_result")
    if match is None or match.overall_score < MATCH_SCORE_THRESHOLD:
        return END  # auto-skip: too weak a fit

    return ATS_AGENT


# ── Human-review gate ────────────────────────────────────────────────────────

def route_after_review(state: ApplicationState) -> str:
    """
    Approved  → submit via apply_agent.
    Rejected  → loop back to tailoring_agent with rejection_feedback.
    Anything else (still pending / error) → END.
    """
    if state.get("error"):
        return END

    status = state.get("approval_status")
    if status == APPROVED:
        return APPLY_AGENT
    if status == REJECTED:
        return TAILORING_AGENT  # re-tailor with feedback

    return END  # pending / unknown — should not normally reach here


# ── Post-apply ───────────────────────────────────────────────────────────────

def route_after_apply(state: ApplicationState) -> str:
    """Always move to tracking regardless of submission outcome."""
    return TRACKING_AGENT
