"""
linkedin_auth.py — LinkedIn session management for Playwright automation.

LinkedIn does not provide a public OAuth API for automation. Instead we use
Playwright's storage_state() to persist the browser session (cookies + local
storage) after a manual one-time login.

Workflow:
  1. First run: python -m app.automation.linkedin_login
       → A headed browser opens → user logs in manually → session saved.
  2. Subsequent automation runs:
       → load_session() restores cookies/storage → LinkedIn treats it as logged in.

Session storage:
  Default: backend/.linkedin_session.json (git-ignored).
  Override via env var: LINKEDIN_SESSION_PATH.

Notes:
  - The session file contains auth cookies and localStorage tokens — treat it as
    a secret. It is added to .gitignore automatically by Phase 19 setup.
  - Sessions expire. LinkedIn typically keeps sessions alive for 30–90 days if
    used regularly. Re-run linkedin_login.py to refresh.
  - If LinkedIn detects automation and invalidates the session, re-login.
"""

from __future__ import annotations

import json
import logging
import os
from pathlib import Path
from typing import Optional

logger = logging.getLogger(__name__)

# ── Session path resolution ────────────────────────────────────────────────────

_DEFAULT_SESSION_FILENAME = ".linkedin_session.json"


def get_session_path() -> Path:
    """
    Return the absolute path to the LinkedIn session state file.

    Resolution order:
      1. LINKEDIN_SESSION_PATH env var (absolute or relative to cwd).
      2. Default: backend/.linkedin_session.json
         (i.e. two dirs up from this file — the repo's backend/ directory).

    The file does NOT need to exist yet; this function only returns the path.
    """
    env_path = os.environ.get("LINKEDIN_SESSION_PATH", "").strip()
    if env_path:
        return Path(env_path).expanduser().resolve()

    # Default: <repo>/backend/.linkedin_session.json
    # This file is __file__ = backend/app/automation/linkedin_auth.py
    # So two levels up from this file's dir = backend/
    backend_dir = Path(__file__).parent.parent.parent  # backend/
    return backend_dir / _DEFAULT_SESSION_FILENAME


# ── Session load / save ────────────────────────────────────────────────────────

def load_session(context) -> bool:
    """
    Load a persisted Playwright browser storage state into `context`.

    Args:
        context: Playwright BrowserContext object.

    Returns:
        True  — session file found and loaded successfully.
        False — no session file exists (first-run, or session was deleted).

    Note:
        This does NOT guarantee the session is still valid (LinkedIn may have
        expired or invalidated it). Call is_session_valid() after loading to
        confirm.
    """
    path = get_session_path()

    if not path.exists():
        logger.info(
            "linkedin_auth.load_session: no session file at %s — user must login first",
            path,
        )
        return False

    try:
        with open(path, "r", encoding="utf-8") as f:
            state = json.load(f)
        context.add_cookies(state.get("cookies", []))
        logger.info(
            "linkedin_auth.load_session: loaded %d cookies from %s",
            len(state.get("cookies", [])),
            path,
        )
        return True
    except Exception as e:
        logger.error("linkedin_auth.load_session: failed to load session — %s", e)
        return False


def save_session(context) -> bool:
    """
    Save the current Playwright browser context state (cookies + localStorage)
    to the session file.

    Args:
        context: Playwright BrowserContext object (after successful login).

    Returns:
        True on success, False on failure.
    """
    path = get_session_path()

    try:
        state = context.storage_state()
        path.parent.mkdir(parents=True, exist_ok=True)
        with open(path, "w", encoding="utf-8") as f:
            json.dump(state, f, indent=2)
        logger.info(
            "linkedin_auth.save_session: session saved to %s (%d cookies)",
            path,
            len(state.get("cookies", [])),
        )
        return True
    except Exception as e:
        logger.error("linkedin_auth.save_session: failed to save session — %s", e)
        return False


# ── Session validity check ─────────────────────────────────────────────────────

def is_session_valid(page) -> bool:
    """
    Verify that the currently loaded session is still authenticated on LinkedIn.

    Strategy:
      Navigate to linkedin.com/feed and check for DOM indicators that appear
      only when logged in (e.g. the global nav or profile avatar element).

    Args:
        page: Playwright Page object (context must have the session loaded).

    Returns:
        True  — session is valid and user appears to be logged in.
        False — not authenticated (session expired or never loaded).

    Side effect:
        The page navigates to linkedin.com/feed. The caller should not rely on
        the page staying at its previous URL after this call.
    """
    try:
        page.goto("https://www.linkedin.com/feed", timeout=20_000, wait_until="domcontentloaded")
        # LinkedIn redirects to /login when unauthenticated
        if "linkedin.com/login" in page.url or "linkedin.com/uas/login" in page.url:
            logger.info("linkedin_auth.is_session_valid: redirected to login — session expired")
            return False
        # Check for presence of the global nav (only rendered when logged in)
        nav = page.locator("[data-test-global-nav], .global-nav, #global-nav")
        if nav.count() > 0:
            logger.info("linkedin_auth.is_session_valid: session is valid")
            return True
        # Fallback: if we didn't get redirected to /login, assume logged in
        if "/feed" in page.url or "/in/" in page.url:
            logger.info("linkedin_auth.is_session_valid: session appears valid (URL check)")
            return True
        logger.warning(
            "linkedin_auth.is_session_valid: unexpected page url=%s — treating as invalid",
            page.url,
        )
        return False
    except Exception as e:
        logger.error("linkedin_auth.is_session_valid: error during check — %s", e)
        return False


def session_file_exists() -> bool:
    """Return True if the session file exists on disk (does not validate it)."""
    return get_session_path().exists()
