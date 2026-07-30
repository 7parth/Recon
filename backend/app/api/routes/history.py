"""
api/routes/history.py — Application history endpoints.
"""

import logging
from fastapi import APIRouter, Query, HTTPException
from typing import Optional

from app.api.schemas.history import (
    ApplicationRecordResponse,
    ApplicationRecordDB,
    HistoryListResponse,
)
from app.db.database import get_async_session
from app.db.repositories.application_repo import ApplicationRepository

logger = logging.getLogger(__name__)
router = APIRouter(tags=["history"])


@router.get("/history", response_model=HistoryListResponse)
async def list_history(
    limit: int = Query(50, ge=1, le=100),
    offset: int = Query(0, ge=0),
    status: Optional[str] = Query(None, description="Filter by status (e.g. 'applied', 'pending_review')"),
):
    """
    List application history, paginated and optionally filtered by status.
    Returns items with computed submission_status, approval_status, job_title, and company.
    """
    async with get_async_session() as session:
        repo = ApplicationRepository(session)
        records = await repo.list_all(limit=limit, offset=offset, status=status)

        items = [ApplicationRecordDB.model_validate(r).to_response() for r in records]

        return HistoryListResponse(
            items=items,
            limit=limit,
            offset=offset,
        )


@router.get("/history/{thread_id}", response_model=ApplicationRecordResponse)
async def get_history_detail(thread_id: str):
    """
    Get detailed history for a specific application run by thread_id.
    """
    async with get_async_session() as session:
        repo = ApplicationRepository(session)
        record = await repo.get_by_thread_id(thread_id)

        if not record:
            raise HTTPException(
                status_code=404,
                detail=f"Application run with thread_id {thread_id} not found",
            )

        return ApplicationRecordDB.model_validate(record).to_response()
