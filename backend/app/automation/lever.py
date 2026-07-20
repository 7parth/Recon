"""
lever.py — Playwright automation for Lever ATS.

Lever job board URLs follow this pattern:
  https://jobs.lever.co/<company>/<job_id>

Implementation status: STUB — full Playwright flow in next sprint.
"""

import logging

logger = logging.getLogger(__name__)


from app.graph.state import CandidateProfile

def submit(url: str, resume_text: str, cover_letter_text: str, candidate_profile: CandidateProfile) -> bool:
    """
    Fill and submit a Lever job application.
    
    Args:
        url:               Lever job listing URL.
        resume_text:       Tailored resume content (plain text).
        cover_letter_text: Cover letter content (plain text).
        candidate_profile: Candidate's personal and professional info.
    """
    logger.info("lever.submit: starting for url=%s", url)

    # Ensure URL points to the application form
    if not url.endswith("/apply"):
        url = url.rstrip("/") + "/apply"

    from app.graph.tools.browser import BrowserSession, safe_fill, safe_click, upload_file

    with BrowserSession(headless=True) as session:
        page = session.new_page()
        try:
            page.goto(url)
            
            # Lever uses a single "Full name" field often, or first/last.
            # We'll try "name" first, then "first_name"/"last_name"
            full_name = f"{candidate_profile.first_name} {candidate_profile.last_name}"
            safe_fill(page, "input[name='name']", full_name)
            
            safe_fill(page, "input[name='email']", candidate_profile.email)
            safe_fill(page, "input[name='phone']", candidate_profile.phone)

            # Upload resume
            upload_file(page, "input[type='file'][name='resume']", resume_text, filename="resume.pdf")

            # LinkedIn / Leetcode (Lever uses name="urls[LinkedIn]" etc)
            if candidate_profile.linkedin_url:
                safe_fill(page, "input[name*='LinkedIn' i]", candidate_profile.linkedin_url)
                
            if candidate_profile.leetcode_url:
                # Custom question or other URL
                safe_fill(page, "xpath=//label[contains(translate(., 'LEETCODE', 'leetcode'), 'leetcode')]/following-sibling::*//input", candidate_profile.leetcode_url)

            # Cover letter
            if cover_letter_text:
                safe_fill(page, "textarea[name='comments']", cover_letter_text)

            # Submit button
            submit_button = page.locator("button.template-btn-submit")
            if submit_button.count() > 0:
                submit_button.first.click()
                # Wait for confirmation page
                page.wait_for_url("**/thanks", timeout=15000)
                logger.info("lever.submit: successfully reached confirmation page")
                return True
            else:
                logger.error("lever.submit: Could not find submit button.")
                return False

        except Exception as e:
            logger.error("lever.submit: failed during automation: %s", e)
            try:
                page.screenshot(path="lever_error.png")
            except:
                pass
            return False
