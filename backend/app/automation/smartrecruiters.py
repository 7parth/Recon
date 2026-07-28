"""
smartrecruiters.py — Playwright automation for SmartRecruiters ATS.

SmartRecruiters job board URLs follow this pattern:
  https://jobs.smartrecruiters.com/<Company>/<job-id>

SmartRecruiters characteristics:
  - Standard React SPA with a clean HTML5 form structure.
  - "Apply Now" button on the listing opens a multi-section form (or a new URL).
  - Personal info section uses data-smarttoken or standard name attributes.
  - Resume upload supports both file-input and a "Upload from Computer" button.
  - Cover letter appears as a textarea in the application form.
  - LinkedIn and other profile URLs have dedicated fields.
  - Custom questions are per-job; we only fill universal fields.
  - Confirmation page shows "Your application has been submitted".

Strategy:
  1. Navigate to listing → click "Apply Now".
  2. Fill personal info (first, last, email, phone).
  3. Upload resume.
  4. Fill cover letter and social links.
  5. Submit and verify confirmation.
"""

import logging
from app.graph.state import CandidateProfile
from app.graph.tools.browser import BrowserSession, safe_fill, safe_click, upload_file

logger = logging.getLogger(__name__)

_SEL = {
    # Apply button on listing
    "apply_btn":      "a[data-cy='btn-apply'], button[data-cy='btn-apply'], a:has-text('Apply Now'), button:has-text('Apply Now')",
    # Personal info
    "first_name":     "input[name='firstName'], input[id='firstName'], input[placeholder*='First' i]",
    "last_name":      "input[name='lastName'],  input[id='lastName'],  input[placeholder*='Last' i]",
    "email":          "input[name='email'],     input[type='email']",
    "phone":          "input[name='phone'],     input[type='tel']",
    # Resume
    "resume_btn":     "button:has-text('Upload from Computer'), label:has-text('Upload') input[type='file']",
    "resume_input":   "input[type='file']",
    # Cover letter
    "cover_letter":   "textarea[name*='coverLetter' i], textarea[data-cy*='coverLetter' i], textarea[placeholder*='cover' i]",
    # Social
    "linkedin":       "input[name*='linkedin' i], input[placeholder*='LinkedIn' i]",
    # Submit
    "submit_btn":     "button[data-cy='btn-submit'], button[type='submit']:has-text('Submit'), button:has-text('Send Application')",
    # Confirmation
    "confirmation":   "[data-cy='application-submitted'], h1:has-text('submitted'), h2:has-text('submitted'), h1:has-text('Thank'), p:has-text('successfully submitted')",
}


def submit(url: str, resume_text: str, cover_letter_text: str, candidate_profile: CandidateProfile) -> bool:
    """
    Fill and submit a SmartRecruiters job application.

    Args:
        url:               SmartRecruiters job listing URL.
        resume_text:       Tailored resume content.
        cover_letter_text: Cover letter text.
        candidate_profile: Candidate personal/professional info.

    Returns:
        True on successful submission, False on failure.
    """
    logger.info("smartrecruiters.submit: starting for url=%s", url)

    with BrowserSession(headless=True) as session:
        page = session.new_page()
        try:
            page.goto(url, wait_until="networkidle", timeout=30_000)

            # ── Click Apply Now if on listing page ────────────────────────────
            apply_btn = page.locator(_SEL["apply_btn"]).first
            if apply_btn.count() > 0 and apply_btn.is_visible():
                logger.debug("smartrecruiters.submit: clicking Apply Now")
                apply_btn.click()
                page.wait_for_load_state("networkidle", timeout=20_000)

            # ── Personal info ─────────────────────────────────────────────────
            safe_fill(page, _SEL["first_name"], candidate_profile.first_name)
            safe_fill(page, _SEL["last_name"],  candidate_profile.last_name)
            safe_fill(page, _SEL["email"],       candidate_profile.email)
            safe_fill(page, _SEL["phone"],       candidate_profile.phone)

            # ── Resume upload ─────────────────────────────────────────────────
            uploaded = upload_file(page, _SEL["resume_input"], resume_text, filename="resume.txt")
            if not uploaded:
                logger.warning("smartrecruiters.submit: primary resume upload failed — trying fallback")
                # Some SR instances have a styled upload button; click it to open picker
                safe_click(page, "button:has-text('Upload from Computer')")
                upload_file(page, "input[type='file']", resume_text, filename="resume.txt")

            # ── Cover letter ──────────────────────────────────────────────────
            if cover_letter_text:
                filled = safe_fill(page, _SEL["cover_letter"], cover_letter_text)
                if not filled:
                    # Probe all textareas
                    textareas = page.locator("textarea").all()
                    for ta in textareas:
                        try:
                            if ta.is_visible() and (ta.input_value() or "") == "":
                                ta.fill(cover_letter_text, timeout=3_000)
                                break
                        except Exception:
                            continue

            # ── LinkedIn ──────────────────────────────────────────────────────
            if candidate_profile.linkedin_url:
                safe_fill(page, _SEL["linkedin"], candidate_profile.linkedin_url)

            # ── Submit ────────────────────────────────────────────────────────
            submit_btn = page.locator(_SEL["submit_btn"]).first
            if submit_btn.count() == 0 or not submit_btn.is_visible():
                # Scroll to bottom — submit button may be below the fold
                page.evaluate("window.scrollTo(0, document.body.scrollHeight)")
                page.wait_for_timeout(1_000)
                submit_btn = page.locator(_SEL["submit_btn"]).first

            if submit_btn.count() == 0 or not submit_btn.is_visible():
                logger.error("smartrecruiters.submit: submit button not found")
                return False

            submit_btn.click(timeout=10_000)
            page.wait_for_load_state("networkidle", timeout=25_000)

            # ── Confirmation ──────────────────────────────────────────────────
            confirmation = page.locator(_SEL["confirmation"])
            if confirmation.count() > 0 and confirmation.first.is_visible():
                logger.info("smartrecruiters.submit: submitted successfully")
                return True

            if any(kw in page.url.lower() for kw in ["thank", "confirm", "submitted", "success"]):
                logger.info("smartrecruiters.submit: confirmation URL: %s", page.url)
                return True

            logger.error("smartrecruiters.submit: no confirmation after submit")
            return False

        except Exception as e:
            logger.error("smartrecruiters.submit: failed — %s", e)
            try:
                page.screenshot(path="smartrecruiters_error.png")
            except Exception:
                pass
            return False
