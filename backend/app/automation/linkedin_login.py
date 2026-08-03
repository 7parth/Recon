"""
linkedin_login.py — One-time interactive LinkedIn login to bootstrap the session.

Run this script ONCE to create the stored session file used by all subsequent
automation runs. It opens a HEADED (visible) browser so you can log in manually.

Usage:
    cd backend
    python -m app.automation.linkedin_login

What it does:
  1. Opens a visible Chromium browser at linkedin.com/login.
  2. Waits for you to log in (up to 3 minutes).
  3. Detects the /feed redirect → confirms you're logged in.
  4. Saves the session to .linkedin_session.json (git-ignored).
  5. Closes the browser and exits.

After this, the linkedin.py automation module will reuse the saved session for
headless automated applications.

Re-run this script if:
  - You see "Session expired" or "Authentication required" in automation logs.
  - It's been 30+ days since last login (LinkedIn sessions typically last 30–90 days).
"""

from __future__ import annotations

import logging
import sys
import time

from app.automation.linkedin_auth import get_session_path, save_session

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s | %(levelname)-8s | %(message)s",
    datefmt="%H:%M:%S",
)
logger = logging.getLogger(__name__)

# Maximum time to wait for the user to log in (seconds)
_LOGIN_TIMEOUT_SECONDS = 180


def interactive_login() -> bool:
    """
    Open a headed browser and wait for the user to log in manually.

    Returns True on success, False on timeout or error.
    """
    try:
        from playwright.sync_api import sync_playwright
    except ImportError:
        logger.error(
            "playwright not found. Install with: uv add playwright && playwright install chromium"
        )
        return False

    session_path = get_session_path()
    logger.info("Session will be saved to: %s", session_path)
    logger.info("=" * 60)
    logger.info("A browser window will open. Please log in to LinkedIn.")
    logger.info("The script will continue automatically after login.")
    logger.info("=" * 60)

    with sync_playwright() as pw:
        # HEADED browser — user needs to see and interact with the page
        browser = pw.chromium.launch(headless=False, slow_mo=50)
        context = browser.new_context(
            viewport={"width": 1280, "height": 800},
            user_agent=(
                "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) "
                "AppleWebKit/537.36 (KHTML, like Gecko) "
                "Chrome/125.0.0.0 Safari/537.36"
            ),
        )
        page = context.new_page()

        try:
            logger.info("Navigating to linkedin.com/login ...")
            page.goto("https://www.linkedin.com/login", timeout=30_000)

            # Poll until we detect the feed URL (login success) or timeout
            deadline = time.time() + _LOGIN_TIMEOUT_SECONDS
            while time.time() < deadline:
                url = page.url
                if "/feed" in url or "/mynetwork" in url or "/jobs" in url:
                    logger.info("Login detected! (URL: %s)", url)
                    break
                # Small poll interval — don't hammer CPU
                time.sleep(1.5)
            else:
                logger.error(
                    "Timeout: login not detected within %d seconds. "
                    "Please re-run this script and complete login faster.",
                    _LOGIN_TIMEOUT_SECONDS,
                )
                browser.close()
                return False

            # Give the page a moment for all cookies/storage to settle
            time.sleep(2)

            # Save the session
            ok = save_session(context)
            if ok:
                logger.info("✓ Session saved successfully to: %s", session_path)
                logger.info("You can now close this terminal. Automation will use the saved session.")
            else:
                logger.error("✗ Failed to save session. Check permissions on %s", session_path.parent)
                browser.close()
                return False

            browser.close()
            return True

        except Exception as e:
            logger.error("interactive_login: unexpected error — %s", e)
            try:
                browser.close()
            except Exception:
                pass
            return False


if __name__ == "__main__":
    success = interactive_login()
    sys.exit(0 if success else 1)
