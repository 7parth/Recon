"""
apply_agent.py — Automates form-fill and submission via Playwright.

Node signature: apply_agent_node(state) -> dict

Position in graph:
  human_review (approved) → apply_agent → tracking_agent

This agent only runs after the user explicitly approves (router guarantees it).
It detects the ATS platform from the job URL and dispatches to the correct
automation module in app/automation/.

Dispatcher pattern:
  Different ATS platforms (Greenhouse, Lever, Workday, Ashby) have different
  HTML structures, field names, and submission flows.  Rather than one giant
  function with if/elif chains, we use a dispatcher dict:
    { "greenhouse" → greenhouse_submit, "lever" → lever_submit, ... }
  Each module owns its own Playwright logic and is tested independently.
  Adding a new ATS = add one entry to the dict, implement the module.

Why not call Playwright directly here?
  The agent layer should stay thin — it reads state, calls tools, writes state.
  Browser automation logic is a tool, same as jd_parser or resume_parser.
  Keeping it in app/automation/ means it can be tested without running LangGraph.

Reads:  job_url, tailored_resume, cover_letter, resume_raw
Writes: submission_status ("applied" | "failed" | "skipped")
        error (on failure, non-fatal — tracking_agent records the failure)
"""

import logging
from app.graph.state import ApplicationState

logger = logging.getLogger(__name__)


# ── ATS platform detector ─────────────────────────────────────────────────────

def _detect_platform(url: str) -> str:
    """
    Detect the ATS platform from the job URL.

    Returns a string key matching the dispatcher, or "unknown".

    Examples:
      "https://boards.greenhouse.io/acme/jobs/123" → "greenhouse"
      "https://jobs.lever.co/acme/abc-123"        → "lever"
      "https://acme.wd1.myworkdayjobs.com/..."     → "workday"
      "https://jobs.ashbyhq.com/acme/..."          → "ashby"
    """
    url_lower = url.lower()
    if "greenhouse.io" in url_lower:
        return "greenhouse"
    if "lever.co" in url_lower:
        return "lever"
    if "myworkdayjobs.com" in url_lower or "workday.com" in url_lower:
        return "workday"
    if "ashbyhq.com" in url_lower:
        return "ashby"
    if "smartrecruiters.com" in url_lower:
        return "smartrecruiters"
    return "unknown"


# ── Dispatcher ────────────────────────────────────────────────────────────────
# Each value is a callable: submit_fn(url, tailored_resume, cover_letter) -> bool
# Imported lazily inside the node to avoid loading Playwright at startup.

def _get_dispatcher() -> dict:
    """
    Build the platform → submit function mapping.

    Lazy imports mean Playwright is only loaded when apply_agent actually runs,
    not when the module is imported (which would slow FastAPI startup).
    """
    from app.automation.greenhouse import submit as greenhouse_submit
    from app.automation.lever import submit as lever_submit
    from app.automation.workday import submit as workday_submit
    from app.automation.ashby import submit as ashby_submit
    from app.automation.smartrecruiters import submit as sr_submit

    return {
        "greenhouse":    greenhouse_submit,
        "lever":         lever_submit,
        "workday":       workday_submit,
        "ashby":         ashby_submit,
        "smartrecruiters": sr_submit,
    }


# ── Main node ─────────────────────────────────────────────────────────────────

def apply_agent_node(state: ApplicationState) -> dict:
    """
    LangGraph node: automate form-fill and submit the approved application.

    Reads:  state["job_url"], state["tailored_resume"], state["cover_letter"]
    Writes: state["submission_status"]  — "applied" | "failed" | "skipped"
            state["error"]              — set on failure (non-fatal; tracking records it)
    """
    job_url         = state.get("job_url", "").strip()
    tailored_resume = state.get("tailored_resume")
    cover_letter    = state.get("cover_letter")
    candidate_profile = state.get("resume_profile")

    # ── Guards ────────────────────────────────────────────────────────────────
    if not job_url:
        return {"submission_status": "failed", "error": "apply_agent: job_url is empty"}
    if tailored_resume is None:
        return {"submission_status": "failed", "error": "apply_agent: tailored_resume missing"}
    if cover_letter is None:
        return {"submission_status": "failed", "error": "apply_agent: cover_letter missing"}
    if candidate_profile is None:
        return {"submission_status": "failed", "error": "apply_agent: candidate_profile missing"}

    # ── Detect platform ───────────────────────────────────────────────────────
    platform = _detect_platform(job_url)
    logger.info("apply_agent: detected platform='%s' for url=%s", platform, job_url)

    dispatcher = _get_dispatcher()

    if platform not in dispatcher:
        logger.warning(
            "apply_agent: unsupported platform '%s' — skipping submission. "
            "The user approved but this ATS is not yet automated.",
            platform,
        )
        # "skipped" means: user approved, but we couldn't automate it.
        # The user will need to apply manually.  Not a failure — tracking records it.
        return {
            "submission_status": "skipped",
            "error": f"apply_agent: ATS platform '{platform}' not yet supported for automation",
        }

    # ── Execute submission ────────────────────────────────────────────────────
    submit_fn = dispatcher[platform]

    logger.info("apply_agent: starting browser automation for '%s'", platform)

    try:
        success = submit_fn(
            url=job_url,
            resume_text=tailored_resume.content,
            cover_letter_text=cover_letter.content,
            candidate_profile=candidate_profile,
        )
    except Exception as e:
        logger.error("apply_agent: browser automation raised an exception: %s", e)
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
