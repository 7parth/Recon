"""
search.py — Web search utilities for the Recon agent pipeline.

Provides:
  search_web(query, max_results)   → list[SearchResult]
  search_company(company_name)     → list[SearchResult]  (convenience wrapper)
  fetch_first_result(query)        → str  (text of the top result page)

Why DuckDuckGo?
  - No API key required — works out of the box
  - No rate-limit registration needed for moderate usage
  - The `duckduckgo_search` Python package wraps the HTML interface cleanly
  
  If you later want more results or better quality, drop in:
    - SerpAPI (Google results, paid)
    - Tavily (built for LLM agents, has a free tier)
  The SearchResult dataclass stays the same — only this file changes.

Where is search.py used in the pipeline?
  Currently: not called by any agent — it's a tool available for:
    1. Enriching company_profile when JD has minimal company info
    2. Future: proactive job discovery ("find React roles at Series B startups")
  The company_agent could call search_company() if company_profile.name is found
  but industry/culture_notes are still None after JD extraction.
"""

import logging
from dataclasses import dataclass, field

logger = logging.getLogger(__name__)

# ── Result schema ─────────────────────────────────────────────────────────────

@dataclass
class SearchResult:
    """
    A single web search result.

    Using a dataclass (not Pydantic) because search results are internal tool
    data — they don't cross the LangGraph state boundary and don't need
    JSON serialisation.  Dataclasses are simpler and faster to construct.
    """
    title:   str
    url:     str
    snippet: str = ""  # short description from the search engine
    body:    str = ""  # full page text (only populated by fetch_first_result)


# ── Core search function ──────────────────────────────────────────────────────

def search_web(query: str, max_results: int = 5) -> list[SearchResult]:
    """
    Search the web and return a list of results.

    Uses DuckDuckGo via the `duckduckgo-search` package.

    How DuckDuckGo search works here:
      DDGS().text(query) returns an iterator of dicts with keys:
        { "title", "href", "body" }
      We wrap each dict in our SearchResult dataclass for a clean interface.

    Args:
        query:       Search query string.
        max_results: Maximum number of results to return (default 5).

    Returns:
        List of SearchResult objects ordered by relevance.
        Empty list if search fails (network error, no results).
    """
    if not query.strip():
        logger.warning("search_web: empty query — returning no results")
        return []

    try:
        from duckduckgo_search import DDGS
    except ImportError as e:
        raise RuntimeError(
            "duckduckgo-search is not installed. Run: uv add duckduckgo-search"
        ) from e

    logger.info("search_web: query='%s' (max=%d)", query, max_results)

    results = []
    try:
        # DDGS().text() returns a generator — we wrap in list() with a limit.
        # `region="wt-wt"` = worldwide (no region bias).
        # `safesearch="off"` = don't filter results (we want all job listings).
        with DDGS() as ddgs:
            raw_results = ddgs.text(
                query,
                region="wt-wt",
                safesearch="off",
                max_results=max_results,
            )
            for item in raw_results:
                results.append(SearchResult(
                    title=item.get("title", ""),
                    url=item.get("href", ""),
                    snippet=item.get("body", ""),
                ))
    except Exception as e:
        logger.error("search_web: DuckDuckGo search failed: %s", e)
        return []   # Graceful degradation — caller handles empty list

    logger.info("search_web: returned %d results for '%s'", len(results), query)
    return results


# ── Convenience wrappers ──────────────────────────────────────────────────────

def search_company(company_name: str, max_results: int = 3) -> list[SearchResult]:
    """
    Search for company info — used to enrich a sparse CompanyProfile.

    Constructs a targeted query: "<name> company culture size industry"
    This surfaces LinkedIn, Glassdoor, Crunchbase, and the company's own
    About page — all good sources of industry, size, and culture signals.

    Args:
        company_name: Name of the company (from company_profile.name).
        max_results:  How many results to return.

    Returns:
        List of SearchResult with company information pages.

    Example use in company_agent (future enrichment):
        if not profile.industry:
            results = search_company(profile.name)
            # Pass results to LLM to extract industry from snippets
    """
    query = f"{company_name} company culture size industry about"
    return search_web(query, max_results=max_results)


def search_jobs(role: str, location: str = "", max_results: int = 10) -> list[SearchResult]:
    """
    Proactively search for job listings matching a role and location.

    Future use: planner could call this to discover jobs automatically
    instead of requiring a URL from the user each time.

    Args:
        role:     Job title or role description (e.g. "backend engineer Python").
        location: Optional location filter (e.g. "remote", "San Francisco").

    Returns:
        List of SearchResult where each URL is a job listing page.
    """
    query = f"{role} job site:greenhouse.io OR site:lever.co OR site:ashbyhq.com"
    if location:
        query += f" {location}"
    return search_web(query, max_results=max_results)


def fetch_first_result(query: str) -> str:
    """
    Search and return the full page text of the top result.

    This is a convenience for the common pattern:
      "search for X, fetch the most relevant page, return its text"

    Useful when search_web() snippets are too short and you need the
    full page content (e.g. to extract detailed company info from About page).

    Args:
        query: Search query.

    Returns:
        Full plain text of the top result page, or "" if nothing found.
    """
    from app.graph.tools.jd_parser import fetch_jd  # avoid circular import at module level

    results = search_web(query, max_results=1)
    if not results:
        logger.warning("fetch_first_result: no results for query='%s'", query)
        return ""

    top_url = results[0].url
    logger.info("fetch_first_result: fetching top result url=%s", top_url)

    try:
        return fetch_jd(top_url)   # reuse our existing clean text extractor
    except Exception as e:
        logger.error("fetch_first_result: failed to fetch %s — %s", top_url, e)
        return results[0].snippet  # fall back to the short snippet
