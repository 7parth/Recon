"""
deduplicator.py — Job URL deduplication and company-exclusion filter.

Used by the discovery orchestrator before handing a batch of raw search
results to the pipeline.  Two filter passes are applied:

  1. URL deduplication — drops URLs already processed in a previous session
     (``existing_urls``) or already queued in the current session
     (``current_queue``).

  2. Company exclusion — drops results whose ``title`` contains any of the
     caller-supplied company names as a case-insensitive substring.

Fail-open policy (R3.4):
  If title inspection raises for a particular result the URL is *retained*
  rather than discarded, so a transient data issue never silently deletes
  a legitimate job.
"""

from __future__ import annotations

import logging
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    # Avoid a hard import cycle at runtime; SearchResult is only used in
    # type hints inside this module.
    from app.graph.tools.search import SearchResult

logger = logging.getLogger(__name__)


class JobDeduplicator:
    """Filter a list of search results, returning only novel, non-excluded URLs.

    Args:
        existing_urls:      Set of job URLs that have already been processed
                            in *any* previous session for this user.  Built
                            from ``ApplicationRepository.list_all_job_urls()``.
        excluded_companies: Company names to suppress.  Matching is a
                            case-insensitive substring check against the
                            search result's ``title`` field.

    Example::

        dedup = JobDeduplicator(
            existing_urls={"https://jobs.lever.co/acme/123"},
            excluded_companies=["Acme Corp", "BigCo"],
        )
        new_urls = dedup.filter(search_results, current_queue=[...])
    """

    def __init__(
        self,
        existing_urls: set[str],
        excluded_companies: list[str],
    ) -> None:
        self._seen: set[str] = set(existing_urls)
        # Lower-case once at construction time — O(n) normalisation upfront.
        self._excluded: list[str] = [name.lower() for name in excluded_companies]

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    def filter(
        self,
        results: list[SearchResult],
        current_queue: list[str],
    ) -> list[str]:
        """Return the subset of result URLs that are new and not excluded.

        Ordering of surviving URLs is preserved (same relative order as
        ``results``).

        Args:
            results:       Raw ``SearchResult`` objects from ``search_jobs()``.
            current_queue: URLs already queued in the *current* session (not
                           yet persisted to the DB) that should also be
                           treated as already-seen.

        Returns:
            List of URL strings that passed both filters, in original order.
        """
        # Merge current-session queue into the seen set for this call.
        seen = self._seen | set(current_queue)

        surviving: list[str] = []
        for result in results:
            url = result.url

            # ── Pass 1: URL deduplication ──────────────────────────────
            if url in seen:
                logger.debug("deduplicator: skip (duplicate) url=%s", url)
                continue

            # ── Pass 2: Company exclusion ──────────────────────────────
            if self._is_excluded(result):
                logger.debug(
                    "deduplicator: skip (excluded company) url=%s title=%r",
                    url,
                    result.title,
                )
                continue

            surviving.append(url)

        return surviving

    # ------------------------------------------------------------------
    # Internal helpers
    # ------------------------------------------------------------------

    def _is_excluded(self, result: SearchResult) -> bool:
        """Return True if the result title matches any excluded company.

        Fail-open: any exception during title inspection returns False so
        the URL is *retained* (R3.4).
        """
        if not self._excluded:
            return False

        try:
            title_lower = result.title.lower()
            return any(company in title_lower for company in self._excluded)
        except Exception:  # noqa: BLE001
            # Defensive: malformed title, unexpected type, etc.  Retain the
            # URL rather than silently dropping a potentially valid listing.
            logger.warning(
                "deduplicator: could not inspect title for url=%s — retaining",
                result.url,
            )
            return False
