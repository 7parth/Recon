"""
apply_agent.py — Automates form-fill and submission via Playwright.

Node signature: apply_agent_node(state) -> dict

Position in graph:
  human_review (approved) → apply_agent → tracking_agent

This agent only runs after the user explicitly approves (router guarantees it).
It delegates platform detection and dispatch entirely to:
  app.automation.dispatcher.dispatch()

That function:
  1. Detects the ATS from the job URL (URL-pattern matching).
  2. Imports the correct automation module lazily.
  3. Calls module.submit(url, resume_text, cover_letter_text, candidate_profile).
  4. Logs every step via AutomationLogger (streamed to the frontend via SSE).

Reads:  job_url, tailored_resume, cover_letter, resume_profile
Writes: submission_status ("applied" | "failed" | "skipped")
        error (on failure, non-fatal — tracking_agent records the failure)

Supported platforms (via dispatcher):
  ✅  Greenhouse  — boards.greenhouse.io
  ✅  Lever       — jobs.lever.co
  ✅  Workday     — *.myworkdayjobs.com
  ✅  Ashby       — jobs.ashbyhq.com
  ✅  SmartRecruiters — jobs.smartrecruiters.com
  ❌  Unknown     — skipped (user must apply manually)
"""

import logging
from app.graph.state import ApplicationState

logger = logging.getLogger(__name__)


def apply_agent_node(state: ApplicationState) -> dict:
    """
    LangGraph node: detect ATS platform and automate form submission.

    Reads:  state["job_url"], state["tailored_resume"], state["cover_letter"],
            state["resume_profile"]
    Writes: state["submission_status"]  — "applied" | "failed" | "skipped"
            state["error"]              — set on failure (non-fatal)
    """
    job_url           = state.get("job_url", "").strip()
    tailored_resume   = state.get("tailored_resume")
    cover_letter      = state.get("cover_letter")
    candidate_profile = state.get("resume_profile")
    thread_id         = state.get("thread_id")  # may be None if not in state

    # ── Guards ────────────────────────────────────────────────────────────────
    if not job_url:
        return {"submission_status": "failed", "error": "apply_agent: job_url is empty"}
    if tailored_resume is None:
        return {"submission_status": "failed", "error": "apply_agent: tailored_resume missing"}
    if cover_letter is None:
        return {"submission_status": "failed", "error": "apply_agent: cover_letter missing"}
    if candidate_profile is None:
        return {"submission_status": "failed", "error": "apply_agent: candidate_profile missing"}

    # ── Dispatch ──────────────────────────────────────────────────────────────
    # dispatcher.dispatch() handles:
    #   - platform detection
    #   - lazy import of the correct automation module
    #   - AutomationLogger integration (logs stream to frontend via SSE)
    from app.automation.dispatcher import dispatch, detect_platform

    platform = detect_platform(job_url)
    logger.info("apply_agent: detected platform='%s' for url=%s", platform, job_url)

    if platform == "unknown":
        logger.warning(
            "apply_agent: unsupported platform '%s' — skipping. "
            "User approved but this ATS is not yet automated.",
            platform,
        )
        return {
            "submission_status": "skipped",
            "error": f"apply_agent: ATS platform not recognised from URL — manual apply required",
        }

    logger.info("apply_agent: starting browser automation for '%s'", platform)

    try:
        success = dispatch(
            url=job_url,
            resume_text=tailored_resume.content,
            cover_letter_text=cover_letter.content,
            candidate_profile=candidate_profile,
            thread_id=thread_id,
        )
    except Exception as e:
        logger.error("apply_agent: dispatcher raised an exception: %s", e)
        return {
            "submission_status": "failed",
            "error": f"apply_agent automation error ({platform}): {e}",
        }

    if success:
        logger.info("apply_agent: submission SUCCESSFUL for %s", job_url)
        return {"submission_status": "applied", "error": None}
    else:
        logger.warning("apply_agent: submission FAILED for %s", job_url)
        return {
            "submission_status": "failed",
            "error": f"apply_agent: {platform} submission returned failure",
        }
