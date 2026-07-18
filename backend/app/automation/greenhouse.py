"""
greenhouse.py — Playwright automation for Greenhouse ATS.

Greenhouse job board URLs follow this pattern:
  https://boards.greenhouse.io/<company>/jobs/<job_id>

Implementation status: STUB — full Playwright flow in next sprint.
The submit() function must match the signature expected by apply_agent's dispatcher:
  submit(url: str, resume_text: str, cover_letter_text: str) -> bool
"""

import logging
from app.graph.tools.browser import BrowserSession, safe_fill, safe_click, upload_file

logger = logging.getLogger(__name__)


def submit(url: str, resume_text: str, cover_letter_text: str) -> bool:
    """
    Fill and submit a Greenhouse job application form.

    Args:
        url:               Greenhouse job listing URL.
        resume_text:       Tailored resume content (plain text).
        cover_letter_text: Cover letter content (plain text).

    Returns:
        True on successful submission, False on failure.
    """
    logger.info("greenhouse.submit: starting for url=%s", url)

    # TODO (Sprint 3): Implement full Playwright flow:
    #   1. Navigate to url
    #   2. Click "Apply" button
    #   3. Fill first/last name, email from candidate profile
    #   4. Upload resume via upload_file(page, "input[type='file']", resume_text)
    #   5. Fill cover letter textarea
    #   6. Handle custom questions (if any)
    #   7. Submit and verify confirmation page

    logger.warning("greenhouse.submit: STUB — not yet implemented")
    return False
