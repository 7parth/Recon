"""
api/schemas/history.py — Response schemas for the history endpoint.

ApplicationRecordResponse includes computed submission_status and approval_status
derived from the single underlying ``status`` DB column, so the frontend
ApplicationRecord type can remain unchanged.

Status semantics:
  DB status          submission_status   approval_status
  ─────────────────  ─────────────────   ───────────────
  running            None                pending
  pending_review     None                pending
  approved           None                approved
  rejected           None                rejected
  applied            applied             approved
  skipped            skipped             approved
  failed             failed              approved (or pending — ambiguous, treat as pending)
"""

import uuid
from datetime import datetime
from pydantic import BaseModel, model_validator
from typing import List, Optional


class ApplicationRecordResponse(BaseModel):
    # ── Primary fields ────────────────────────────────────────────────────────
    id: uuid.UUID
    thread_id: str
    status: str

    # ── Display fields (denormalised from job/company agents) ─────────────────
    job_title: Optional[str] = None
    company: Optional[str] = None          # maps from company_name column

    # ── Computed split status fields (for frontend compatibility) ─────────────
    submission_status: Optional[str] = None   # "applied" | "skipped" | "failed" | None
    approval_status: Optional[str] = None     # "approved" | "rejected" | "pending"

    # ── Scores & documents ────────────────────────────────────────────────────
    match_score: Optional[float] = None
    resume_storage_url: Optional[str] = None
    resume_url: Optional[str] = None          # alias for resume_storage_url
    tailored_resume_url: Optional[str] = None
    cover_letter_url: Optional[str] = None

    # ── Review ────────────────────────────────────────────────────────────────
    rejection_feedback: Optional[str] = None
    error_message: Optional[str] = None

    # ── Timestamps ────────────────────────────────────────────────────────────
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True

    @model_validator(mode="after")
    def compute_split_status(self) -> "ApplicationRecordResponse":
        """Compute submission_status and approval_status from the single DB status column."""
        s = self.status

        # submission_status — terminal state from apply_agent
        if s in ("applied", "skipped", "failed"):
            self.submission_status = s
        else:
            self.submission_status = None

        # approval_status — human review decision
        if s in ("approved", "applied", "skipped"):
            self.approval_status = "approved"
        elif s == "rejected":
            self.approval_status = "rejected"
        else:
            # running, pending_review, failed (pre-review failure)
            self.approval_status = "pending"

        # resume_url alias
        if self.resume_url is None and self.resume_storage_url:
            self.resume_url = self.resume_storage_url

        return self


class ApplicationRecordDB(BaseModel):
    """Internal model for reading from ORM — maps company_name → company."""
    id: uuid.UUID
    thread_id: str
    status: str
    job_title: Optional[str] = None
    company_name: Optional[str] = None   # ORM column name
    match_score: Optional[float] = None
    resume_storage_url: Optional[str] = None
    tailored_resume_url: Optional[str] = None
    cover_letter_url: Optional[str] = None
    rejection_feedback: Optional[str] = None
    error_message: Optional[str] = None
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True

    def to_response(self) -> ApplicationRecordResponse:
        return ApplicationRecordResponse(
            id=self.id,
            thread_id=self.thread_id,
            status=self.status,
            job_title=self.job_title,
            company=self.company_name,
            match_score=self.match_score,
            resume_storage_url=self.resume_storage_url,
            resume_url=self.resume_storage_url,
            tailored_resume_url=self.tailored_resume_url,
            cover_letter_url=self.cover_letter_url,
            rejection_feedback=self.rejection_feedback,
            error_message=self.error_message,
            created_at=self.created_at,
            updated_at=self.updated_at,
        )


class HistoryListResponse(BaseModel):
    items: List[ApplicationRecordResponse]
    limit: int
    offset: int
