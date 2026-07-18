"""
jd_parser.py — Fetch a job description URL and return clean plain text.

Single public function:
  fetch_jd(url: str) -> str

The agents (job_agent, company_agent) call this first, then pass the text
to the LLM for structured extraction.  Keeping fetch separate from extraction
means we can cache the raw fetch result and re-use it for both agents.
"""

import logging
import re

logger = logging.getLogger(__name__)

# ── Constants ─────────────────────────────────────────────────────────────────

# Many ATS platforms (Greenhouse, Lever, Workday) block requests from
# the default Python user-agent string ("python-httpx/...").
# Spoofing a real browser UA is enough to get through.
_USER_AGENT = (
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) "
    "AppleWebKit/537.36 (KHTML, like Gecko) "
    "Chrome/125.0.0.0 Safari/537.36"
)

_REQUEST_TIMEOUT = 15  # seconds — ATS sites can be slow


# ── Main fetch function ───────────────────────────────────────────────────────

def fetch_jd(url: str) -> str:
    """
    Fetch a job listing URL and return its clean plain text.

    Strategy:
      1. GET the page with httpx (sync) using a browser-like User-Agent.
      2. Parse HTML with BeautifulSoup.
      3. Find the <main> or largest <article>/<section> tag — this is
         almost always the JD content block on ATS pages.
      4. Fall back to <body> if no semantic landmark is found.
      5. Strip scripts, styles, and nav elements.
      6. Collapse whitespace and return.

    Args:
        url: Full job listing URL (e.g. "https://boards.greenhouse.io/acme/jobs/123")

    Returns:
        Plain text of the job description.

    Raises:
        ValueError:   If the URL is empty or the page returns no usable text.
        RuntimeError: On network errors or non-200 HTTP responses.
    """
    if not url or not url.startswith("http"):
        raise ValueError(f"Invalid URL: '{url}'. Must start with http/https.")

    # ── Step 1: Fetch the page ────────────────────────────────────────────────
    # Why httpx over requests?
    #   httpx has a nearly identical API but is async-native — when we later
    #   move to async agents we can swap `httpx.get` → `await httpx.AsyncClient().get`
    #   with minimal changes.
    try:
        import httpx
    except ImportError as e:
        raise RuntimeError("httpx is not installed. Run: uv add httpx") from e

    logger.info("fetch_jd: GET %s", url)
    try:
        response = httpx.get(
            url,
            headers={"User-Agent": _USER_AGENT},
            timeout=_REQUEST_TIMEOUT,
            follow_redirects=True,     # ATS platforms often redirect canonical URLs
        )
        response.raise_for_status()    # raises httpx.HTTPStatusError on 4xx/5xx
    except httpx.HTTPStatusError as e:
        raise RuntimeError(
            f"HTTP {e.response.status_code} fetching job listing: {url}"
        ) from e
    except httpx.RequestError as e:
        raise RuntimeError(f"Network error fetching {url}: {e}") from e

    # ── Step 2: Parse HTML ────────────────────────────────────────────────────
    try:
        from bs4 import BeautifulSoup
    except ImportError as e:
        raise RuntimeError("beautifulsoup4 is not installed. Run: uv add beautifulsoup4") from e

    # "html.parser" is Python's built-in — no extra install needed.
    # "lxml" is faster but requires a C extension.
    soup = BeautifulSoup(response.text, "html.parser")

    # ── Step 3: Remove noise elements ────────────────────────────────────────
    # Scripts, styles, nav bars, and footers add tokens that confuse the LLM.
    # Decompose() removes the tag AND its contents from the parse tree.
    for tag in soup(["script", "style", "nav", "footer", "header", "aside"]):
        tag.decompose()

    # ── Step 4: Find the content block ───────────────────────────────────────
    # Prefer semantic landmarks in this priority order:
    #   <main>     — HTML5 standard landmark for primary content
    #   <article>  — common on Lever / Greenhouse job pages
    #   <section>  — fallback semantic block
    #   <body>     — last resort
    content_tag = (
        soup.find("main")
        or soup.find("article")
        or soup.find("section")
        or soup.find("body")
    )

    if content_tag is None:
        raise ValueError(f"Could not find any content in page: {url}")

    # ── Step 5: Extract and clean text ───────────────────────────────────────
    raw_text = content_tag.get_text(separator="\n")

    # Collapse runs of 3+ newlines → 2 newlines (preserves paragraph breaks)
    # and strip leading/trailing whitespace on each line.
    lines = [line.strip() for line in raw_text.splitlines()]
    cleaned = re.sub(r"\n{3,}", "\n\n", "\n".join(lines)).strip()

    if not cleaned:
        raise ValueError(f"Page fetched but contained no usable text: {url}")

    logger.info("fetch_jd: extracted %d chars from %s", len(cleaned), url)
    return cleaned


# ── Optional: parse raw JD text passed directly (no URL) ─────────────────────

def normalize_jd(raw_text: str) -> str:
    """
    Clean up a raw job description string pasted directly by the user
    (instead of fetched from a URL).

    Just collapses whitespace — no HTML parsing needed.
    """
    lines = [line.strip() for line in raw_text.splitlines()]
    return re.sub(r"\n{3,}", "\n\n", "\n".join(lines)).strip()
