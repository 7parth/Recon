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


from app.graph.state import CandidateProfile

def submit(url: str, resume_text: str, cover_letter_text: str, candidate_profile: CandidateProfile) -> bool:
    """
    Fill and submit a Greenhouse job application form.

    Args:
        url:               Greenhouse job listing URL.
        resume_text:       Tailored resume content (plain text).
        cover_letter_text: Cover letter content (plain text).
        candidate_profile: Candidate's personal and professional info.

    Returns:
        True on successful submission, False on failure.
    """
    logger.info("greenhouse.submit: starting for url=%s", url)

    # Use the context manager to spin up a browser
    with BrowserSession(headless=True) as session:
        page = session.new_page()
        try:
            page.goto(url)
            
            # 1. Fill basic personal information
            safe_fill(page, "input#first_name", candidate_profile.first_name)
            safe_fill(page, "input#last_name", candidate_profile.last_name)
            safe_fill(page, "input#email", candidate_profile.email)
            safe_fill(page, "input#phone", candidate_profile.phone)

            # 2. Upload resume
            # Greenhouse usually has an <input type="file" id="s3_upload_for_resume"> 
            # or name="resume" or similar.
            upload_file(page, "input[type='file']", resume_text, filename="resume.pdf")

            # 3. Fill Cover Letter
            # Sometimes cover letter is a file upload, sometimes a textarea.
            # If there's a textarea for cover letter:
            if page.locator("textarea#cover_letter_text").count() > 0:
                safe_fill(page, "textarea#cover_letter_text", cover_letter_text)
            
            # 4. Fill custom fields (LinkedIn, LeetCode)
            if candidate_profile.linkedin_url:
                # Playwright pseudo-classes: locate input inside a div that contains label with 'linkedin'
                safe_fill(page, "xpath=//label[contains(translate(., 'LINKEDIN', 'linkedin'), 'linkedin')]/following-sibling::*//input", candidate_profile.linkedin_url)
            
            if candidate_profile.leetcode_url:
                safe_fill(page, "xpath=//label[contains(translate(., 'LEETCODE', 'leetcode'), 'leetcode')]/following-sibling::*//input", candidate_profile.leetcode_url)

            # 5. Submit
            submit_button = page.locator("input[type='submit'], button#submit_app")
            if submit_button.count() > 0:
                submit_button.first.click()
                # Wait for confirmation page
                page.wait_for_url("**/application_submitted", timeout=15000)
                logger.info("greenhouse.submit: successfully reached confirmation page")
                return True
            else:
                logger.error("greenhouse.submit: Could not find submit button.")
                return False

        except Exception as e:
            logger.error("greenhouse.submit: failed during automation: %s", e)
            # Optional: take a screenshot for debugging
            try:
                page.screenshot(path="greenhouse_error.png")
            except:
                pass
            return False
