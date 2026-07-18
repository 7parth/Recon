"""
browser.py — Shared Playwright browser utilities for automation modules.

Provides:
  BrowserSession        — context manager that owns the Playwright lifecycle
  get_page_text(page)   — extract clean text from an already-open page
  safe_fill(page, sel, value)   — fill a form field, skip if not found
  safe_click(page, sel)         — click an element, skip if not found
  upload_file(page, sel, path)  — attach a file to a file-input element

The automation modules (greenhouse.py, lever.py, etc.) import from here.
They never call playwright.sync_api directly — this file owns the Playwright
lifecycle so there is always exactly one browser process per graph run.

Sync vs Async Playwright:
  Playwright ships two APIs: playwright.sync_api and playwright.async_api.
  We use SYNC here because LangGraph nodes are synchronous by default.
  The sync API wraps the async internals with threading — it's safe to call
  from a normal Python function.  If we later move to async agents (using
  LangGraph's async runner), the swap is: `from playwright.async_api import ...`
  and add `await` before page calls — the structure stays identical.

Context manager pattern:
  with BrowserSession(headless=True) as session:
      page = session.new_page()
      page.goto("https://boards.greenhouse.io/acme/jobs/123")
      ...
  # Browser is automatically closed when the `with` block exits,
  # even if an exception is raised inside.
"""

import logging
import tempfile
import os
from contextlib import contextmanager
from pathlib import Path
from typing import Generator

logger = logging.getLogger(__name__)

# Default timeout for all Playwright waits (milliseconds)
DEFAULT_TIMEOUT_MS = 15_000


class BrowserSession:
    """
    Context manager that owns a single Playwright browser instance.

    Usage:
        with BrowserSession(headless=True) as session:
            page = session.new_page()
            page.goto(url)
            ...
        # Browser closes here — always, even on exception

    Args:
        headless: Run browser without a visible UI window.
                  Set to False for debugging automation locally.
        slow_mo:  Milliseconds to wait between each Playwright action.
                  Useful for watching automation in slow motion (debug mode).
    """

    def __init__(self, headless: bool = True, slow_mo: int = 0):
        self.headless = headless
        self.slow_mo = slow_mo
        self._playwright = None
        self._browser = None

    def __enter__(self):
        try:
            from playwright.sync_api import sync_playwright
        except ImportError as e:
            raise RuntimeError(
                "playwright is not installed. Run: uv add playwright && playwright install chromium"
            ) from e

        # ── Start Playwright ──────────────────────────────────────────────────
        # sync_playwright() is a context manager itself, but we manage its
        # lifecycle manually here so BrowserSession can be the single owner.
        self._pw = sync_playwright().start()

        # We use Chromium. It's the most widely supported and matches what
        # most ATS platforms are tested against.  Firefox and WebKit are
        # available via self._pw.firefox / self._pw.webkit if needed.
        self._browser = self._pw.chromium.launch(
            headless=self.headless,
            slow_mo=self.slow_mo,
        )

        logger.debug(
            "BrowserSession: browser started (headless=%s, slow_mo=%dms)",
            self.headless,
            self.slow_mo,
        )
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        # Always close browser and stop Playwright, even on exception.
        # This prevents zombie browser processes accumulating over time.
        if self._browser:
            self._browser.close()
        if self._pw:
            self._pw.stop()
        logger.debug("BrowserSession: browser closed")
        return False  # don't suppress exceptions

    def new_page(self):
        """
        Open a new browser tab (Playwright calls these 'pages').

        Returns a Playwright Page object with our default timeout pre-set.
        The automation module drives this page — navigates, fills forms, clicks.
        """
        if self._browser is None:
            raise RuntimeError("BrowserSession not started — use it as a context manager")

        page = self._browser.new_page()

        # Set a default timeout for ALL operations on this page.
        # Without this, Playwright waits forever by default on slow ATS pages.
        page.set_default_timeout(DEFAULT_TIMEOUT_MS)

        # Mimic a real browser — some ATS platforms check the user agent and
        # show CAPTCHAs or block headless browsers with the default Playwright UA.
        page.set_extra_http_headers({
            "User-Agent": (
                "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) "
                "AppleWebKit/537.36 (KHTML, like Gecko) "
                "Chrome/125.0.0.0 Safari/537.36"
            )
        })

        return page


# ── Shared helper functions used by automation modules ────────────────────────

def safe_fill(page, selector: str, value: str) -> bool:
    """
    Fill a form field by CSS/XPath selector.  No-ops if the field is not found.

    Why 'safe'?
      Different ATS instances may customise their forms (extra fields, renamed
      fields, A/B tests).  Crashing on a missing optional field would abort the
      whole application.  safe_fill logs a warning and continues instead.

    Args:
        page:     Playwright Page object.
        selector: CSS or XPath selector for the input field.
        value:    Text to type into the field.

    Returns:
        True if the field was found and filled, False if skipped.
    """
    try:
        page.locator(selector).fill(value, timeout=5_000)
        logger.debug("safe_fill: filled selector='%s'", selector)
        return True
    except Exception as e:
        logger.warning("safe_fill: skipped selector='%s' — %s", selector, e)
        return False


def safe_click(page, selector: str) -> bool:
    """
    Click an element by selector.  No-ops if not found.

    Args:
        page:     Playwright Page object.
        selector: CSS selector or XPath for the element to click.

    Returns:
        True if clicked, False if skipped.
    """
    try:
        page.locator(selector).click(timeout=5_000)
        logger.debug("safe_click: clicked selector='%s'", selector)
        return True
    except Exception as e:
        logger.warning("safe_click: skipped selector='%s' — %s", selector, e)
        return False


def upload_file(page, selector: str, content: str, filename: str = "resume.pdf") -> bool:
    """
    Write content to a temp file and attach it to a file-input element.

    ATS platforms expect a real file upload — they use <input type="file">.
    Playwright's set_input_files() handles this by injecting the file path
    into the input element, triggering the same event as a real user upload.

    Why a temp file?
      We have the resume as a string in memory (tailored_resume.content).
      Playwright's set_input_files() requires a file path on disk, not bytes.
      We write to a NamedTemporaryFile, upload, then clean it up.

    Args:
        page:      Playwright Page object.
        selector:  CSS selector for the <input type="file"> element.
        content:   Text content to write to the temp file.
        filename:  Desired filename (affects what the ATS sees on upload).

    Returns:
        True if uploaded, False if skipped.
    """
    tmp_path = None
    try:
        # NamedTemporaryFile with delete=False so we can pass the path to Playwright
        # before the file is garbage-collected.  We manually delete after upload.
        suffix = Path(filename).suffix or ".txt"
        with tempfile.NamedTemporaryFile(
            mode="w", suffix=suffix, delete=False, encoding="utf-8"
        ) as tmp:
            tmp.write(content)
            tmp_path = tmp.name

        page.locator(selector).set_input_files(tmp_path, timeout=10_000)
        logger.debug("upload_file: uploaded '%s' via selector='%s'", filename, selector)
        return True

    except Exception as e:
        logger.warning("upload_file: skipped selector='%s' — %s", selector, e)
        return False
    finally:
        # Always clean up the temp file, even on failure
        if tmp_path and os.path.exists(tmp_path):
            os.unlink(tmp_path)


def get_page_text(page) -> str:
    """
    Extract clean plain text from the current page (for validation/logging).

    Useful to confirm you're on the right page after navigation,
    or to scrape a JD if jd_parser's httpx approach fails.
    """
    return page.inner_text("body").strip()
