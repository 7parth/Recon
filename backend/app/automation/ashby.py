"""ashby.py — Playwright automation stub for Ashby ATS."""
import logging
logger = logging.getLogger(__name__)

from app.graph.state import CandidateProfile

def submit(url: str, resume_text: str, cover_letter_text: str, candidate_profile: CandidateProfile) -> bool:
    """Fill and submit an Ashby job application. STUB."""
    logger.warning("ashby.submit: STUB — not yet implemented for url=%s", url)
    return False
