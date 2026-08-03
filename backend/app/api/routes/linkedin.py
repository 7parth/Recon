"""
api/routes/linkedin.py — LinkedIn Easy Apply authentication management endpoints.

Endpoints:
  GET  /api/v1/linkedin/auth/status — Check whether a valid LinkedIn session exists.
  POST /api/v1/linkedin/auth/init   — Trigger one-time interactive login (opens headed browser).

These endpoints are called by the frontend IntegrationsPage to:
  1. Show the current LinkedIn connection status.
  2. Let the user bootstrap a new session without touching the terminal.

Design note:
  - The interactive_login() call blocks a thread and opens a GUI browser on the
    server machine. This is only meaningful on a local dev setup where the user
    is sitting at the same machine as the server.
  - We run it in a BackgroundTask so the HTTP response returns immediately with
    a `browser_opened` status — the user then completes login in the browser window.
  - For remote/cloud deploys the user should run `python -m app.automation.linkedin_login`
    in the terminal directly.
"""

from __future__ import annotations

import logging
import threading

from fastapi import APIRouter, BackgroundTasks
from pydantic import BaseModel

from app.automation.linkedin_auth import (
    get_session_path,
    is_session_valid,
    session_file_exists,
)

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/linkedin", tags=["linkedin"])


# ── Response schemas ──────────────────────────────────────────────────────────

class LinkedInAuthStatus(BaseModel):
    authenticated: bool
    session_file_exists: bool
    session_path: str
    message: str


class LinkedInAuthInitResponse(BaseModel):
    status: str   # "browser_opened" | "already_authenticated" | "error"
    message: str


# ── Status endpoint ───────────────────────────────────────────────────────────

@router.get("/auth/status", response_model=LinkedInAuthStatus)
async def get_linkedin_auth_status():
    """
    Check whether a valid LinkedIn session is stored.

    Returns:
      - `session_file_exists`: True if .linkedin_session.json exists on disk.
      - `authenticated`:       True if the session is also still valid on LinkedIn.
                               Requires a live browser check — may take 3–5 s.
      - `session_path`:        Absolute path to the session file (for reference).
      - `message`:             Human-readable status summary.
    """
    path = get_session_path()
    file_exists = path.exists()

    if not file_exists:
        return LinkedInAuthStatus(
            authenticated=False,
            session_file_exists=False,
            session_path=str(path),
            message="No session file found. Run 'Connect LinkedIn' to authenticate.",
        )

    # Validate the session via a live headless browser check
    try:
        from playwright.sync_api import sync_playwright
        from app.automation.linkedin_auth import load_session

        with sync_playwright() as pw:
            browser = pw.chromium.launch(headless=True)
            context = browser.new_context(
                user_agent=(
                    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) "
                    "AppleWebKit/537.36 (KHTML, like Gecko) "
                    "Chrome/125.0.0.0 Safari/537.36"
                )
            )
            loaded = load_session(context)
            if not loaded:
                browser.close()
                return LinkedInAuthStatus(
                    authenticated=False,
                    session_file_exists=True,
                    session_path=str(path),
                    message="Session file exists but could not be loaded.",
                )

            page = context.new_page()
            valid = is_session_valid(page)
            browser.close()

        if valid:
            return LinkedInAuthStatus(
                authenticated=True,
                session_file_exists=True,
                session_path=str(path),
                message="LinkedIn session is active and authenticated.",
            )
        else:
            return LinkedInAuthStatus(
                authenticated=False,
                session_file_exists=True,
                session_path=str(path),
                message="Session file exists but has expired. Click 'Re-authenticate' to refresh.",
            )

    except Exception as e:
        logger.error("linkedin auth status check failed — %s", e)
        return LinkedInAuthStatus(
            authenticated=False,
            session_file_exists=file_exists,
            session_path=str(path),
            message=f"Session check error: {e}",
        )


# ── Init endpoint ─────────────────────────────────────────────────────────────

def _run_interactive_login_in_thread():
    """
    Run the interactive login in a background thread.
    The headed browser will open on the server's display.
    """
    try:
        from app.automation.linkedin_login import interactive_login
        success = interactive_login()
        if success:
            logger.info("linkedin auth: interactive login completed successfully")
        else:
            logger.error("linkedin auth: interactive login failed or timed out")
    except Exception as e:
        logger.error("linkedin auth: interactive login thread raised — %s", e)


@router.post("/auth/init", response_model=LinkedInAuthInitResponse)
async def init_linkedin_auth(background_tasks: BackgroundTasks):
    """
    Trigger the one-time interactive LinkedIn login.

    Opens a headed (visible) Chromium browser on the server machine.
    The user should complete the LinkedIn login in that browser window.
    The session is saved automatically after a successful login.

    This endpoint returns immediately — the login happens in the background.
    Poll `GET /api/v1/linkedin/auth/status` to check when authentication completes.

    Note: Only useful on local dev machines where the server and browser
    are on the same display. For remote servers, use the CLI:
      `python -m app.automation.linkedin_login`
    """
    # Start the login in a background thread (can't use BackgroundTasks directly
    # because interactive_login() is synchronous and blocks — we use threading)
    thread = threading.Thread(target=_run_interactive_login_in_thread, daemon=True)
    thread.start()

    path = get_session_path()
    return LinkedInAuthInitResponse(
        status="browser_opened",
        message=(
            f"A browser window is opening on the server. "
            f"Please log in to LinkedIn, then return here. "
            f"Session will be saved to: {path}"
        ),
    )
