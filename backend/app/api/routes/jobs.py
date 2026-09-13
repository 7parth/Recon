"""
api/routes/jobs.py — Job search endpoints.
"""

import logging
import re
from fastapi import APIRouter, Query, HTTPException
from typing import Optional

from app.api.schemas.jobs import JobSearchResponse, JobSearchResult
from app.graph.tools.search import search_jobs

logger = logging.getLogger(__name__)
router = APIRouter(tags=["jobs"])


def _extract_company_from_title(title: str) -> Optional[str]:
    """Best-effort company extraction from a job listing title string.

    DDGS job titles often follow patterns like:
      "Senior Engineer — Acme Corp"
      "Backend Engineer at Stripe | LinkedIn"
      "Python Developer - Remote | Greenhouse"
    Returns the company token when detected, otherwise None.
    """
    # Pattern: "Role — Company" or "Role - Company" (em dash or hyphen)
    match = re.search(r'[—–\-]\s*([^|–—\-]+?)(?:\s*\|.*)?$', title)
    if match:
        candidate = match.group(1).strip()
        # Reject generic suffixes that are not company names
        if candidate.lower() not in {"remote", "full time", "part time", "contract", ""}:
            return candidate
    # Pattern: "Role at Company"
    match = re.search(r'\bat\s+([A-Z][^|–—\-]+?)(?:\s*\|.*)?$', title)
    if match:
        return match.group(1).strip()
    return None

@router.get("/jobs/search", response_model=JobSearchResponse)
async def search_for_jobs(
    role: str = Query(..., description="Job title or role description"),
    location: Optional[str] = Query(None, description="Optional location filter (e.g. 'remote', 'San Francisco')"),
    max_results: int = Query(10, description="Maximum number of results to return")
):
    """
    Search for job listings matching a role and location.
    Returns a list of URLs and titles found via DuckDuckGo.
    """
    logger.info("GET /jobs/search: role='%s' location='%s'", role, location)
    
    try:
        # search_jobs is a synchronous function that does network IO via DDGS
        # In a high-throughput async app, we would run it in a threadpool.
        # For this scale, running it directly is acceptable.
        results = search_jobs(role=role, location=location or "", max_results=max_results)
    except Exception as e:
        logger.error("Job search failed: %s", e)
        raise HTTPException(status_code=500, detail=f"Job search failed: {e}")

    job_results = [
        JobSearchResult(
            title=res.title,
            url=res.url,
            snippet=res.snippet,
            company=_extract_company_from_title(res.title),
            location=location or None,   # echo user's location filter; None if unspecified
        )
        for res in results
    ]
    
    query_str = role
    if location:
        query_str += f" in {location}"

    return JobSearchResponse(
        query=query_str,
        results=job_results
    )
