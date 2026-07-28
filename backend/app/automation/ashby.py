"""
ashby.py — Playwright automation for Ashby ATS.

Ashby job board URLs follow this pattern:
  https://jobs.ashbyhq.com/<company>/<job-id>

Ashby is a modern ATS built as a clean React SPA.
Key characteristics:
  - Single-page application — fields render without page navigation.
  - Uses standard HTML5 form elements (no Workday-style shadow DOM).
  - Application form is accessed via a prominent "Apply" button on the listing.
  - Personal info fields use standard name/id attributes.
  - Resume upload accepts a file via a standard <input type="file">.
  - Cover letter is typically a textarea with a label containing "cover letter".
  - LinkedIn, portfolio, and other profile URLs have dedicated fields.
  - Submission lands on a confirmation / "Thanks for applying" state.

Strategy:
  1. Navigate to the listing URL.
  2. Click the "Apply" button to open the modal / form.
  3. Fill personal info fields.
  4. Upload resume.
  5. Fill cover letter + custom profile URLs.
  6. Submit.
"""

import logging
from app.graph.state import CandidateProfile
from app.graph.tools.browser import BrowserSession, safe_fill, safe_click, upload_file

logger = logging.getLogger(__name__)

_SEL = {
    # Apply button on listing page
    "apply_btn":      "a[href*='/apply'], button:has-text('Apply'), a:has-text('Apply Now')",
    # Personal info — Ashby uses standard name attributes
    "first_name":     "input[name='firstName'], input[placeholder*='First' i], input[id*='firstName' i]",
    "last_name":      "input[name='lastName'],  input[placeholder*='Last' i],  input[id*='lastName' i]",
    "email":          "input[name='email'],     input[type='email']",
    "phone":          "input[name='phone'],     input[type='tel']",
    # Resume upload
    "resume_input":   "input[type='file']",
    # Cover letter — label proximity
    "cover_letter":   "textarea[name*='coverLetter' i], textarea[placeholder*='cover' i]",
    # Social links
    "linkedin":       "input[name*='linkedin' i], input[placeholder*='LinkedIn' i]",
    "portfolio":      "input[name*='portfolio' i], input[placeholder*='portfolio' i]",
    # Submit
    "submit_btn":     "button[type='submit'], button:has-text('Submit Application'), button:has-text('Apply')",
    # Confirmation
    "confirmation":   "h1:has-text('Thanks'), h2:has-text('Thanks'), [class*='confirmation' i], [class*='success' i]",
}


def submit(url: str, resume_text: str, cover_letter_text: str, candidate_profile: CandidateProfile) -> bool:
    """
    Fill and submit an Ashby job application.

    Args:
        url:               Ashby job listing URL (jobs.ashbyhq.com/...).
        resume_text:       Tailored resume content.
        cover_letter_text: Cover letter content.
        candidate_profile: Candidate personal/professional info.

    Returns:
        True on successful submission, False on failure.
    """
    logger.info("ashby.submit: starting for url=%s", url)

    with BrowserSession(headless=True) as session:
        page = session.new_page()
        try:
            page.goto(url, wait_until="networkidle", timeout=30_000)

            # ── Click Apply button if on listing page ─────────────────────────
            apply_btn = page.locator(_SEL["apply_btn"]).first
            if apply_btn.count() > 0 and apply_btn.is_visible():
                logger.debug("ashby.submit: clicking Apply button")
                apply_btn.click()
                page.wait_for_load_state("networkidle", timeout=15_000)

            # ── Personal info ─────────────────────────────────────────────────
            safe_fill(page, _SEL["first_name"], candidate_profile.first_name)
            safe_fill(page, _SEL["last_name"],  candidate_profile.last_name)
            safe_fill(page, _SEL["email"],       candidate_profile.email)
            safe_fill(page, _SEL["phone"],       candidate_profile.phone)

            # ── Resume upload ─────────────────────────────────────────────────
            upload_file(page, _SEL["resume_input"], resume_text, filename="resume.txt")

            # ── Cover letter ──────────────────────────────────────────────────
            if cover_letter_text:
                filled = safe_fill(page, _SEL["cover_letter"], cover_letter_text)
                if not filled:
                    # Fallback: find any textarea with a cover-letter-related label
                    labels = page.locator("label").all()
                    for label in labels:
                        try:
                            label_text = label.inner_text().lower()
                            if "cover" in label_text or "letter" in label_text:
                                for_attr = label.get_attribute("for")
                                if for_attr:
                                    page.locator(f"#{for_attr}").fill(cover_letter_text, timeout=3_000)
                                    break
                        except Exception:
                            continue

            # ── Social / portfolio links ──────────────────────────────────────
            if candidate_profile.linkedin_url:
                safe_fill(page, _SEL["linkedin"], candidate_profile.linkedin_url)

            # ── Submit ────────────────────────────────────────────────────────
            submit_btn = page.locator(_SEL["submit_btn"]).first
            if submit_btn.count() == 0 or not submit_btn.is_visible():
                logger.error("ashby.submit: submit button not found")
                return False

            submit_btn.click(timeout=10_000)
            page.wait_for_load_state("networkidle", timeout=20_000)

            # ── Confirmation ──────────────────────────────────────────────────
            confirmation = page.locator(_SEL["confirmation"])
            if confirmation.count() > 0 and confirmation.first.is_visible():
                logger.info("ashby.submit: submitted successfully — confirmation detected")
                return True

            # Check URL change as secondary confirmation
            if "thank" in page.url.lower() or "confirm" in page.url.lower() or "applied" in page.url.lower():
                logger.info("ashby.submit: submitted — confirmation URL detected: %s", page.url)
                return True

            logger.error("ashby.submit: no confirmation detected after submit")
            return False

        except Exception as e:
            logger.error("ashby.submit: failed — %s", e)
            try:
                page.screenshot(path="ashby_error.png")
            except Exception:
                pass
            return False
