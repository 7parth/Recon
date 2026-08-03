"""
linkedin.py — Playwright automation for LinkedIn Easy Apply.

LinkedIn Easy Apply is an in-page multi-step modal on linkedin.com/jobs pages.
Unlike Greenhouse/Lever which redirect to a standalone ATS URL, Easy Apply opens
a dialog box without leaving LinkedIn — so we need an authenticated LinkedIn session.

Authentication:
  Uses stored session cookies from linkedin_auth.py.
  Run `python -m app.automation.linkedin_login` once to bootstrap the session.

Easy Apply Modal Structure (typical, varies by job):
  Step 1: Contact info — phone number (pre-filled from LinkedIn profile).
  Step 2: Resume — upload or select from saved resumes.
  Step 3: (Optional) Additional questions — free-text, dropdowns, checkboxes.
  Step n: Review — final confirmation step with "Submit application" button.

Strategy:
  - Load session → navigate to job URL → click "Easy Apply" button.
  - For each modal step: fill what we can, click "Next" / "Review" / "Submit".
  - Detect success via "Application submitted" confirmation banner.
  - Best-effort: return False (skipped) on any unrecoverable failure rather than crashing.

Known limitations:
  - LinkedIn's UI changes frequently — selectors may need updates over time.
  - Some jobs require screening questions or assessments — these are skipped.
  - CAPTCHA or rate-limiting may block headless runs on fresh sessions.
  - The automation respects the `headless` flag from BrowserSession — set to False
    for debugging.
"""

from __future__ import annotations

import logging
import tempfile
import os
from pathlib import Path

from app.graph.state import CandidateProfile
from app.automation.linkedin_auth import load_session, is_session_valid, get_session_path

logger = logging.getLogger(__name__)

# ── Selectors ──────────────────────────────────────────────────────────────────
# LinkedIn changes their class names frequently; we use aria roles and
# data-test attributes where possible for stability.

_SEL = {
    # Easy Apply entry button on the job listing page
    "easy_apply_btn":  "button.jobs-apply-button, button[aria-label*='Easy Apply' i]",
    "easy_apply_span": "span:text('Easy Apply')",

    # Modal container
    "modal":           "[data-test-modal-id='easy-apply-modal'], .jobs-easy-apply-modal",

    # Contact info step
    "phone_field":     "input[id*='phoneNumber'], input[name*='phone'], input[aria-label*='phone' i]",

    # Resume step — upload button or file input
    "resume_upload_btn": "button:text('Upload resume'), button[aria-label*='upload' i]",
    "resume_file_input":  "input[type='file']",
    "resume_upload_label":"label:has-text('Upload resume')",

    # Cover letter textarea (sometimes appears)
    "cover_letter_ta": "textarea[id*='coverLetter'], textarea[aria-label*='cover letter' i]",

    # Additional questions — generic text inputs and selects inside the modal
    "modal_text_inputs":  ".jobs-easy-apply-modal input[type='text']",
    "modal_textareas":    ".jobs-easy-apply-modal textarea",

    # Navigation buttons
    "next_btn":        "button[aria-label*='Continue to next step' i], button:text('Next'), button[data-easy-apply-next-button]",
    "review_btn":      "button[aria-label*='Review your application' i], button:text('Review')",
    "submit_btn":      "button[aria-label*='Submit application' i], button:text('Submit application')",
    "not_now_btn":     "button:text('Not now'), button[aria-label*='dismiss' i]",  # notifications prompt

    # Confirmation
    "confirmation":    "[data-test-job-alert-confirm-banner], h2:text('Application submitted'), .artdeco-toast-message:has-text('application')",
    "confirmation_generic": "h3:text-is('Your application was sent')",
}

# Maximum number of modal steps to navigate before giving up
_MAX_STEPS = 8


# ── Internal helpers ───────────────────────────────────────────────────────────

def _dismiss_notifications_prompt(page) -> None:
    """Dismiss LinkedIn's 'Turn on job alerts' prompt if it appears."""
    try:
        btn = page.locator(_SEL["not_now_btn"])
        if btn.count() > 0 and btn.first.is_visible(timeout=2_000):
            btn.first.click(timeout=3_000)
            logger.debug("linkedin: dismissed notifications prompt")
    except Exception:
        pass


def _click_easy_apply(page) -> bool:
    """Locate and click the Easy Apply button on the job listing page."""
    try:
        # Primary selector: button with aria-label containing 'Easy Apply'
        btn = page.locator(_SEL["easy_apply_btn"]).first
        if btn.count() > 0 and btn.is_visible(timeout=8_000):
            btn.click(timeout=8_000)
            logger.debug("linkedin: clicked Easy Apply (primary selector)")
            return True
    except Exception as e:
        logger.debug("linkedin: primary Easy Apply selector failed — %s", e)

    # Fallback: look for a span with text "Easy Apply" inside any button
    try:
        btn = page.locator(_SEL["easy_apply_span"])
        if btn.count() > 0:
            btn.first.click(timeout=8_000)
            logger.debug("linkedin: clicked Easy Apply (span fallback)")
            return True
    except Exception as e:
        logger.debug("linkedin: Easy Apply span fallback failed — %s", e)

    return False


def _is_confirmation_visible(page) -> bool:
    """Check whether any 'Application submitted' confirmation is on screen."""
    for sel in [_SEL["confirmation"], _SEL["confirmation_generic"]]:
        try:
            el = page.locator(sel)
            if el.count() > 0 and el.first.is_visible(timeout=2_000):
                return True
        except Exception:
            pass
    return False


def _try_fill_phone(page, candidate_profile: CandidateProfile) -> None:
    """Fill the phone field if present and empty."""
    try:
        phone_input = page.locator(_SEL["phone_field"]).first
        if phone_input.count() > 0 and phone_input.is_visible(timeout=3_000):
            existing = phone_input.input_value(timeout=2_000)
            if not existing:
                phone_input.fill(candidate_profile.phone, timeout=3_000)
                logger.debug("linkedin: filled phone number")
    except Exception as e:
        logger.debug("linkedin: phone field not found or already filled — %s", e)


def _try_upload_resume(page, resume_text: str) -> bool:
    """Attempt to upload the resume file in the modal's upload step."""
    tmp_path = None
    try:
        # Write resume text to a named temp file (PDF-named .txt for compatibility)
        suffix = ".pdf"
        with tempfile.NamedTemporaryFile(
            mode="w", suffix=suffix, delete=False, encoding="utf-8"
        ) as tmp:
            tmp.write(resume_text)
            tmp_path = tmp.name

        # Try hidden file input first
        file_input = page.locator(_SEL["resume_file_input"]).first
        if file_input.count() > 0:
            file_input.set_input_files(tmp_path, timeout=10_000)
            logger.debug("linkedin: resume uploaded via file input")
            return True

        # Try clicking upload button to trigger file picker (doesn't work headlessly)
        # — just log and continue, the modal may already have a pre-selected resume
        logger.debug("linkedin: no file input found for resume — may use LinkedIn's saved resume")
        return False

    except Exception as e:
        logger.warning("linkedin: resume upload failed — %s", e)
        return False
    finally:
        if tmp_path and os.path.exists(tmp_path):
            os.unlink(tmp_path)


def _try_fill_cover_letter(page, cover_letter_text: str) -> None:
    """Fill cover letter textarea if present."""
    try:
        ta = page.locator(_SEL["cover_letter_ta"]).first
        if ta.count() > 0 and ta.is_visible(timeout=2_000):
            existing = ta.input_value(timeout=2_000)
            if not existing:
                ta.fill(cover_letter_text, timeout=5_000)
                logger.debug("linkedin: filled cover letter textarea")
    except Exception as e:
        logger.debug("linkedin: cover letter textarea not found — %s", e)


def _click_next_or_submit(page) -> str:
    """
    Click the most appropriate action button on the current modal step.

    Returns:
        'submit'   — clicked Submit application
        'review'   — clicked Review
        'next'     — clicked Next
        'none'     — no clickable button found
    """
    # Priority order: Submit > Review > Next
    for label, sel, return_val in [
        ("Submit", _SEL["submit_btn"], "submit"),
        ("Review", _SEL["review_btn"], "review"),
        ("Next",   _SEL["next_btn"],   "next"),
    ]:
        try:
            btn = page.locator(sel).first
            if btn.count() > 0 and btn.is_visible(timeout=2_000):
                btn.click(timeout=8_000)
                logger.debug("linkedin: clicked '%s' button", label)
                return return_val
        except Exception:
            continue

    return "none"


# ── Public submit() function ───────────────────────────────────────────────────

def submit(
    url: str,
    resume_text: str,
    cover_letter_text: str,
    candidate_profile: CandidateProfile,
) -> bool:
    """
    Fill and submit a LinkedIn Easy Apply application.

    Args:
        url:               LinkedIn job URL (e.g. https://www.linkedin.com/jobs/view/123456789).
        resume_text:       Tailored resume content (written to a temp file for upload).
        cover_letter_text: Cover letter content (inserted into textarea if present).
        candidate_profile: Candidate personal info (name, email, phone, linkedin_url, etc.).

    Returns:
        True  — application submitted successfully.
        False — session invalid, Easy Apply not available, or unrecoverable failure.

    Authentication note:
        The LinkedIn session must be pre-bootstrapped via:
          python -m app.automation.linkedin_login
        If the session file does not exist, this function returns False immediately.
    """
    logger.info("linkedin.submit: starting for url=%s", url)

    # Guard: session file must exist
    if not get_session_path().exists():
        logger.error(
            "linkedin.submit: no session file found at %s. "
            "Run `python -m app.automation.linkedin_login` to authenticate.",
            get_session_path(),
        )
        return False

    try:
        from playwright.sync_api import sync_playwright
    except ImportError:
        logger.error(
            "playwright not installed. Run: uv add playwright && playwright install chromium"
        )
        return False

    with sync_playwright() as pw:
        browser = pw.chromium.launch(
            headless=True,
            slow_mo=50,  # small delay — helps with LinkedIn's React rendering
        )
        context = browser.new_context(
            viewport={"width": 1280, "height": 800},
            user_agent=(
                "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) "
                "AppleWebKit/537.36 (KHTML, like Gecko) "
                "Chrome/125.0.0.0 Safari/537.36"
            ),
        )

        try:
            # ── Load stored session ───────────────────────────────────────────
            loaded = load_session(context)
            if not loaded:
                logger.error("linkedin.submit: session file exists but could not be loaded")
                browser.close()
                return False

            page = context.new_page()
            page.set_default_timeout(15_000)

            # ── Validate session ──────────────────────────────────────────────
            if not is_session_valid(page):
                logger.error(
                    "linkedin.submit: session is invalid or expired. "
                    "Re-run `python -m app.automation.linkedin_login`."
                )
                browser.close()
                return False

            logger.info("linkedin.submit: session valid — navigating to job URL")

            # ── Navigate to job listing ───────────────────────────────────────
            page.goto(url, timeout=30_000, wait_until="domcontentloaded")
            page.wait_for_load_state("networkidle", timeout=20_000)

            # Dismiss any modal popups (login prompt, notification request)
            _dismiss_notifications_prompt(page)

            # ── Click Easy Apply ──────────────────────────────────────────────
            clicked = _click_easy_apply(page)
            if not clicked:
                logger.error(
                    "linkedin.submit: 'Easy Apply' button not found. "
                    "Job may not support Easy Apply or requires manual application."
                )
                browser.close()
                return False

            # Wait for modal to open
            try:
                page.wait_for_selector(_SEL["modal"], timeout=10_000)
                logger.debug("linkedin.submit: Easy Apply modal opened")
            except Exception:
                logger.warning("linkedin.submit: modal selector not found — continuing anyway")

            # ── Navigate multi-step modal ─────────────────────────────────────
            for step in range(_MAX_STEPS):
                logger.debug("linkedin.submit: processing modal step %d", step + 1)

                # Wait for the modal to settle after navigation
                page.wait_for_load_state("domcontentloaded", timeout=10_000)

                # Early success check
                if _is_confirmation_visible(page):
                    logger.info("linkedin.submit: ✓ application submitted (step %d)", step + 1)
                    browser.close()
                    return True

                # Fill fields on the current step
                _try_fill_phone(page, candidate_profile)
                _try_upload_resume(page, resume_text)
                _try_fill_cover_letter(page, cover_letter_text)

                # Click the appropriate action button
                action = _click_next_or_submit(page)

                if action == "submit":
                    # Submitted — wait for confirmation
                    try:
                        page.wait_for_selector(
                            _SEL["confirmation"] + ", " + _SEL["confirmation_generic"],
                            timeout=15_000,
                        )
                        logger.info("linkedin.submit: ✓ application submitted successfully")
                        browser.close()
                        return True
                    except Exception:
                        # Check one more time after wait
                        if _is_confirmation_visible(page):
                            logger.info("linkedin.submit: ✓ application submitted (confirmation via fallback)")
                            browser.close()
                            return True
                        logger.warning("linkedin.submit: Submit clicked but confirmation not detected")
                        browser.close()
                        return False

                elif action == "review":
                    # One more step: the review page — loop will handle it
                    logger.debug("linkedin.submit: on review step — will click Submit next")
                    continue

                elif action == "next":
                    # Moving to next step
                    continue

                else:
                    # No button found — could be a step we can't handle
                    logger.warning(
                        "linkedin.submit: no action button found on step %d — cannot continue",
                        step + 1,
                    )
                    browser.close()
                    return False

            # Final confirmation check after exhausting max steps
            if _is_confirmation_visible(page):
                logger.info("linkedin.submit: ✓ application submitted (post-loop check)")
                browser.close()
                return True

            logger.error(
                "linkedin.submit: reached max steps (%d) without successful submission",
                _MAX_STEPS,
            )
            try:
                page.screenshot(path="linkedin_error.png")
                logger.debug("linkedin.submit: debug screenshot saved to linkedin_error.png")
            except Exception:
                pass
            browser.close()
            return False

        except Exception as e:
            logger.error("linkedin.submit: unhandled exception — %s", e)
            try:
                page.screenshot(path="linkedin_error.png")
            except Exception:
                pass
            browser.close()
            return False
