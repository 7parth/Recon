"""
lever.py — Playwright automation for Lever ATS.

Lever job board URLs follow this pattern:
  https://jobs.lever.co/<company>/<job_id>

Implementation status: STUB — full Playwright flow in next sprint.
"""

import logging

logger = logging.getLogger(__name__)


def submit(url: str, resume_text: str, cover_letter_text: str) -> bool:
    """Fill and submit a Lever job application. STUB — not yet implemented."""
    logger.warning("lever.submit: STUB — not yet implemented for url=%s", url)
    return False
