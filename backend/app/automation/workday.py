"""
workday.py — Playwright automation for Workday ATS.

Workday job board URLs follow these patterns:
  https://<company>.wd1.myworkdayjobs.com/en-US/<company>_External/job/<title>/<id>/apply
  https://<company>.wd5.myworkdayjobs.com/...

Workday is the most complex ATS to automate because:
  1. It is a heavy React SPA — fields may not be in the DOM until scrolled into view.
  2. It often requires navigating a multi-step wizard (Personal Info → Experience → Review).
  3. It uses Workday-specific shadow DOM in some older versions.
  4. Login / account creation is sometimes required before the apply form is shown.

Strategy implemented here:
  - Navigate to the apply URL; detect the "Apply" button if not already on the form.
  - Fill basic personal info (name split, email, phone) using label-proximity locators.
  - Upload resume via the file-input element (Workday uses a drag-drop + input hybrid).
  - Handle the multi-step wizard by clicking "Next" / "Save and Continue" until Submit.
  - On each step, fill cover letter if a textarea is present.

Known limitations:
  - Workday requires an account on many postings; this implementation covers
    the "apply as guest" / "apply without creating account" flow.
  - Some companies have custom Workday configurations that add extra steps.
  - Screenshot is captured to workday_error.png on failure for debugging.
"""

import logging
from app.graph.state import CandidateProfile
from app.graph.tools.browser import BrowserSession, safe_fill, safe_click, upload_file

logger = logging.getLogger(__name__)

# Selectors — Workday uses data-automation-id attributes extensively
_SEL = {
    # Personal info
    "legal_name_section": "[data-automation-id='legalNameSection']",
    "first_name":         "[data-automation-id='legalNameSection'] [data-automation-id='firstName']",
    "last_name":          "[data-automation-id='legalNameSection'] [data-automation-id='lastName']",
    "first_name_fallback": "input[data-automation-id='firstName']",
    "last_name_fallback":  "input[data-automation-id='lastName']",
    "email":              "input[data-automation-id='email']",
    "phone":              "input[data-automation-id='phone']",
    # Resume upload — Workday exposes a hidden file input alongside a styled button
    "resume_input":       "input[data-automation-id='file-upload-input-ref']",
    "resume_input_alt":   "input[type='file']",
    # Cover letter textarea (appears on some Workday postings)
    "cover_letter":       "textarea[data-automation-id='coverLetterSection']",
    "cover_letter_alt":   "textarea",
    # LinkedIn
    "linkedin":           "input[data-automation-id='linkedin']",
    # Navigation buttons
    "next_btn":           "button[data-automation-id='bottom-navigation-next-button']",
    "save_continue":      "button[data-automation-id='saveAndContinueButton']",
    "submit_btn":         "button[data-automation-id='bottom-navigation-next-button'][aria-label*='Submit' i]",
    "submit_btn_alt":     "button[aria-label*='Submit' i]",
    # Apply button on the job listing page (before the actual form)
    "apply_btn":          "a[data-automation-id='jobPostingApplyButton'], button[data-automation-id='jobPostingApplyButton']",
    # Confirmation
    "confirmation":       "[data-automation-id='confirmationTitle'], [data-automation-id='applicationSubmitted']",
}

_NEXT_BUTTONS = [
    "button[data-automation-id='bottom-navigation-next-button']",
    "button[aria-label='Next']",
    "button[aria-label='Save and Continue']",
    "[data-automation-id='saveAndContinueButton']",
]

_SUBMIT_SELECTORS = [
    "button[aria-label*='Submit' i]",
    "button[data-automation-id='bottom-navigation-next-button'][aria-label*='Submit' i]",
    "button:has-text('Submit')",
]


def _click_next_or_submit(page) -> bool:
    """Click the first available Next / Save and Continue / Submit button."""
    for sel in _NEXT_BUTTONS + _SUBMIT_SELECTORS:
        try:
            btn = page.locator(sel).first
            if btn.count() > 0 and btn.is_visible():
                btn.click(timeout=5_000)
                return True
        except Exception:
            continue
    return False


def submit(url: str, resume_text: str, cover_letter_text: str, candidate_profile: CandidateProfile) -> bool:
    """
    Fill and submit a Workday job application.

    Args:
        url:               Workday job listing or apply URL.
        resume_text:       Tailored resume content (plain text — written to temp .txt file).
        cover_letter_text: Cover letter content.
        candidate_profile: Candidate's personal info.

    Returns:
        True on successful submission, False on failure.
    """
    logger.info("workday.submit: starting for url=%s", url)

    # Ensure we land on the apply form, not the job listing
    if "/apply" not in url:
        url = url.rstrip("/") + "/apply"

    with BrowserSession(headless=True) as session:
        page = session.new_page()
        try:
            page.goto(url, wait_until="networkidle", timeout=30_000)

            # Sometimes we land on the listing page; look for an Apply button
            apply_btn = page.locator(_SEL["apply_btn"])
            if apply_btn.count() > 0:
                logger.debug("workday.submit: found listing page — clicking Apply button")
                apply_btn.first.click()
                page.wait_for_load_state("networkidle", timeout=20_000)

            # ── Step 1: Personal Information ──────────────────────────────────

            # Try data-automation-id selectors first, then fall back to generic
            filled_first = safe_fill(page, _SEL["first_name"], candidate_profile.first_name)
            if not filled_first:
                safe_fill(page, _SEL["first_name_fallback"], candidate_profile.first_name)

            filled_last = safe_fill(page, _SEL["last_name"], candidate_profile.last_name)
            if not filled_last:
                safe_fill(page, _SEL["last_name_fallback"], candidate_profile.last_name)

            safe_fill(page, _SEL["email"], candidate_profile.email)
            safe_fill(page, _SEL["phone"], candidate_profile.phone)

            if candidate_profile.linkedin_url:
                safe_fill(page, _SEL["linkedin"], candidate_profile.linkedin_url)

            # ── Step 2: Resume Upload ─────────────────────────────────────────
            uploaded = upload_file(page, _SEL["resume_input"], resume_text, filename="resume.txt")
            if not uploaded:
                upload_file(page, _SEL["resume_input_alt"], resume_text, filename="resume.txt")

            # ── Step 3: Cover Letter (if present on this step) ────────────────
            if cover_letter_text:
                filled_cl = safe_fill(page, _SEL["cover_letter"], cover_letter_text)
                if not filled_cl:
                    # Try any visible textarea that isn't already filled
                    textareas = page.locator("textarea").all()
                    for ta in textareas:
                        try:
                            if ta.is_visible() and ta.input_value() == "":
                                ta.fill(cover_letter_text, timeout=3_000)
                                break
                        except Exception:
                            continue

            # ── Step 4: Navigate multi-step wizard ────────────────────────────
            # Workday typically has 3-5 steps. We click Next until we reach Submit.
            max_steps = 6
            for step in range(max_steps):
                page.wait_for_load_state("networkidle", timeout=15_000)

                # Check if we're already on the confirmation page
                conf = page.locator(_SEL["confirmation"])
                if conf.count() > 0 and conf.first.is_visible():
                    logger.info("workday.submit: confirmation page detected — SUCCESS")
                    return True

                # Look for a Submit button — if found, click it
                for sub_sel in _SUBMIT_SELECTORS:
                    sub_btn = page.locator(sub_sel)
                    if sub_btn.count() > 0 and sub_btn.first.is_visible():
                        logger.info("workday.submit: clicking Submit on step %d", step + 1)
                        sub_btn.first.click(timeout=10_000)
                        page.wait_for_load_state("networkidle", timeout=20_000)

                        # Verify confirmation
                        conf_after = page.locator(_SEL["confirmation"])
                        if conf_after.count() > 0:
                            logger.info("workday.submit: submitted successfully")
                            return True
                        # Submission clicked but no confirmation yet — fall through
                        break

                # On non-final steps, fill any cover letter textarea that appeared
                if cover_letter_text:
                    safe_fill(page, _SEL["cover_letter"], cover_letter_text)

                # Click Next / Save and Continue
                logger.debug("workday.submit: clicking Next on step %d", step + 1)
                clicked = _click_next_or_submit(page)
                if not clicked:
                    logger.warning("workday.submit: no Next/Submit button found on step %d", step + 1)
                    break

            # Final confirmation check after the loop
            conf_final = page.locator(_SEL["confirmation"])
            if conf_final.count() > 0 and conf_final.first.is_visible():
                logger.info("workday.submit: submitted successfully (post-loop confirmation)")
                return True

            logger.error("workday.submit: reached max steps without confirmation")
            return False

        except Exception as e:
            logger.error("workday.submit: failed — %s", e)
            try:
                page.screenshot(path="workday_error.png")
            except Exception:
                pass
            return False
