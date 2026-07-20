"""workday.py — Playwright automation stub for Workday ATS."""
import logging
logger = logging.getLogger(__name__)

from app.graph.state import CandidateProfile

def submit(url: str, resume_text: str, cover_letter_text: str, candidate_profile: CandidateProfile) -> bool:
    logger.warning("workday.submit: STUB — not yet implemented for url=%s", url)
    return False
