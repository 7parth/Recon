"""
tailoring_agent.py — Generates a tailored resume for the target job.

Node signature: tailoring_agent_node(state) -> dict

Position in graph:
  ats_agent → tailoring_agent → cover_letter_agent
  human_review (rejected) → tailoring_agent  ← re-tailor loop

This node is called in TWO contexts:
  1. First run:   ats_report is populated, rejection_feedback is None
  2. Re-tailor:   rejection_feedback is set by human_review_agent

Key teaching point — conditional prompt selection:
  The same node handles both cases by inspecting state["rejection_feedback"].
  If it's set, we switch to the rejection-aware prompt variant that makes
  user feedback the top priority.  This is a common LangGraph pattern:
  one node, multiple code paths based on state — keeps the graph topology
  simple while the node logic handles branching internally.

Reads:  resume_raw, job_profile, ats_report, match_result,
        rejection_feedback (optional — None on first run)
Writes: tailored_resume (TailoredResume)
"""

import logging
from langchain_core.messages import SystemMessage, HumanMessage

from app.graph.state import ApplicationState, TailoredResume
from app.graph.tools.llm import llm
from app.graph.prompts.tailoring import (
    TAILORING_SYSTEM_PROMPT,
    TAILORING_USER_PROMPT,
    RETAILOR_SYSTEM_PROMPT,
    RETAILOR_USER_PROMPT,
)

logger = logging.getLogger(__name__)


def tailoring_agent_node(state: ApplicationState) -> dict:
    """
    LangGraph node: generate or revise a tailored resume.

    Reads:  state["resume_raw"], state["job_profile"], state["ats_report"],
            state["match_result"], state["rejection_feedback"] (may be None),
            state["tailored_resume"] (may be None on first run)
    Writes: state["tailored_resume"]
    """
    resume_raw   = state.get("resume_raw", "").strip()
    job_profile  = state.get("job_profile")
    ats_report   = state.get("ats_report")
    match_result = state.get("match_result")
    rejection_feedback = state.get("rejection_feedback")
    previous_resume    = state.get("tailored_resume")

    # ── Guards ────────────────────────────────────────────────────────────────
    if not resume_raw:
        return {"error": "tailoring_agent: resume_raw is empty"}
    if job_profile is None:
        return {"error": "tailoring_agent: job_profile missing"}
    if ats_report is None:
        return {"error": "tailoring_agent: ats_report missing — ats_agent must run first"}

    # ── Branch: re-tailor (rejection loop) vs first-run ──────────────────────
    # rejection_feedback is a non-empty string set by human_review_agent when
    # the user clicks "Reject" and provides notes.
    is_retailor = bool(rejection_feedback and rejection_feedback.strip())

    if is_retailor:
        logger.info("tailoring_agent: RE-TAILOR mode (rejection feedback present)")

        # On re-tailor, we revise the *previous tailored resume*, not the raw one.
        # If somehow the previous tailored resume is missing (shouldn't happen),
        # fall back to the raw resume.
        previous_content = previous_resume.content if previous_resume else resume_raw

        messages = [
            SystemMessage(content=RETAILOR_SYSTEM_PROMPT),
            HumanMessage(content=RETAILOR_USER_PROMPT.format(
                previous_resume=previous_content,
                rejection_feedback=rejection_feedback,
                required_skills=", ".join(job_profile.required_skills),
                responsibilities=job_profile.responsibilities,
            )),
        ]
    else:
        logger.info("tailoring_agent: FIRST-RUN mode")

        # Safely extract match fields — match_result may be None if routing
        # somehow bypassed the score check (defensive coding).
        strengths = ", ".join(match_result.strengths) if match_result else "N/A"
        gap_areas = ", ".join(match_result.gap_areas) if match_result else "N/A"

        messages = [
            SystemMessage(content=TAILORING_SYSTEM_PROMPT),
            HumanMessage(content=TAILORING_USER_PROMPT.format(
                resume_raw=resume_raw,
                required_skills=", ".join(job_profile.required_skills),
                responsibilities=job_profile.responsibilities,
                ats_recommendations=ats_report.recommendations,
                strengths=strengths,
                gap_areas=gap_areas,
            )),
        ]

    # ── LLM call ──────────────────────────────────────────────────────────────
    # TailoredResume has two fields:
    #   content:      the full resume text (markdown or plain text)
    #   changes_made: a short paragraph explaining what changed
    structured_llm = llm.with_structured_output(TailoredResume)

    logger.info(
        "tailoring_agent: invoking LLM (%s mode)",
        "re-tailor" if is_retailor else "first-run",
    )

    try:
        result: TailoredResume = structured_llm.invoke(messages)
    except Exception as e:
        logger.error("tailoring_agent: LLM call failed: %s", e)
        return {"error": f"tailoring_agent LLM failed: {e}"}

    logger.info(
        "tailoring_agent: tailored resume generated (%d chars)", len(result.content)
    )

    # Clear rejection_feedback after successful re-tailor so it doesn't
    # persist into the next human review cycle.
    updates = {"tailored_resume": result}
    if is_retailor:
        updates["rejection_feedback"] = None   # type: ignore[assignment]

    return updates
