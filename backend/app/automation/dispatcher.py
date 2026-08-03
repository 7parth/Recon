"""
automation/dispatcher.py — ATS platform detection and dispatch.

This module is called by apply_agent to:
  1. Detect which ATS platform a job URL belongs to.
  2. Route to the correct automation module's submit() function.
  3. Log every step via AutomationLogger for SSE streaming.

Platform detection is URL-pattern based — fast, no network call needed.

Supported platforms:
  ✅  Greenhouse      — boards.greenhouse.io
  ✅  Lever           — jobs.lever.co
  ✅  Workday         — *.wd1.myworkdayjobs.com / *.wd5.myworkdayjobs.com
  ✅  Ashby           — jobs.ashbyhq.com
  ✅  SmartRecruiters — jobs.smartrecruiters.com
  ✅  LinkedIn        — linkedin.com/jobs (Easy Apply, requires stored session)

Any URL that doesn't match a known pattern returns platform="unknown"
and submit() returns False (skipped, not a hard failure).
"""

from __future__ import annotations

import logging
import re
from typing import Literal, Optional

from app.graph.state import CandidateProfile
from app.utils.logger import AutomationLogger, get_automation_logger

logger = logging.getLogger(__name__)

Platform = Literal["greenhouse", "lever", "workday", "ashby", "smartrecruiters", "linkedin", "unknown"]

# ── URL pattern → platform ────────────────────────────────────────────────────

_PATTERNS: list[tuple[re.Pattern, Platform]] = [
    (re.compile(r"boards\.greenhouse\.io", re.I),        "greenhouse"),
    (re.compile(r"jobs\.lever\.co", re.I),               "lever"),
    (re.compile(r"myworkdayjobs\.com", re.I),             "workday"),
    (re.compile(r"jobs\.ashbyhq\.com", re.I),             "ashby"),
    (re.compile(r"jobs\.smartrecruiters\.com", re.I),     "smartrecruiters"),
    # LinkedIn Easy Apply — must come AFTER other linkedin.com subdomains if any were added
    (re.compile(r"linkedin\.com/jobs", re.I),             "linkedin"),
]


def detect_platform(url: str) -> Platform:
    """
    Detect ATS platform from URL.

    Returns one of: greenhouse | lever | workday | ashby | smartrecruiters | unknown.

    Examples:
        detect_platform("https://boards.greenhouse.io/acme/jobs/123") → "greenhouse"
        detect_platform("https://jobs.lever.co/stripe/abc")           → "lever"
        detect_platform("https://example.com/careers")                → "unknown"
    """
    for pattern, platform in _PATTERNS:
        if pattern.search(url):
            return platform
    return "unknown"


# ── Main dispatcher ───────────────────────────────────────────────────────────

def dispatch(
    url: str,
    resume_text: str,
    cover_letter_text: str,
    candidate_profile: CandidateProfile,
    thread_id: Optional[str] = None,
) -> bool:
    """
    Detect platform from URL and call the appropriate submit() automation.

    Args:
        url:               Job application URL.
        resume_text:       Tailored resume text.
        cover_letter_text: Cover letter text.
        candidate_profile: Candidate personal/professional info.
        thread_id:         LangGraph run thread ID — used to tag automation logs.

    Returns:
        True  → application submitted successfully.
        False → submission failed or platform not supported (skipped).
    """
    log: AutomationLogger = get_automation_logger(thread_id or "no-thread")

    platform = detect_platform(url)
    log.info(f"Detected platform: {platform}", context="dispatcher.py")

    if platform == "unknown":
        log.warn(
            f"No automation available for URL: {url}. Skipping.",
            context="dispatcher.py",
        )
        logger.warning("dispatcher.dispatch: unknown platform for url=%s — skipping", url)
        return False

    log.info(f"Launching {platform} automation", context="dispatcher.py")

    try:
        if platform == "greenhouse":
            from app.automation.greenhouse import submit
        elif platform == "lever":
            from app.automation.lever import submit
        elif platform == "workday":
            from app.automation.workday import submit
        elif platform == "ashby":
            from app.automation.ashby import submit
        elif platform == "smartrecruiters":
            from app.automation.smartrecruiters import submit
        elif platform == "linkedin":
            from app.automation.linkedin import submit
        else:
            # Unreachable given the pattern list, but satisfies type checker.
            log.error(f"Unhandled platform: {platform}", context="dispatcher.py")
            return False

        success = submit(
            url=url,
            resume_text=resume_text,
            cover_letter_text=cover_letter_text,
            candidate_profile=candidate_profile,
        )

        if success:
            log.success(f"Application submitted via {platform}", context="dispatcher.py")
        else:
            log.error(f"{platform}.submit() returned False", context="dispatcher.py")

        return success

    except Exception as e:
        log.error(f"dispatcher raised exception: {e}", context="dispatcher.py")
        logger.exception("dispatcher.dispatch: exception for url=%s platform=%s", url, platform)
        return False
