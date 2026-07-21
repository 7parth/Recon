"""
api/routes/jobs.py — Job search endpoints.
"""

import logging
from fastapi import APIRouter, Query, HTTPException
from typing import Optional

from app.api.schemas.jobs import JobSearchResponse, JobSearchResult
from app.graph.tools.search import search_jobs

logger = logging.getLogger(__name__)
router = APIRouter(tags=["jobs"])

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
            snippet=res.snippet
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
