"""
api/schemas/application.py — Request and response schemas for application runs.

Why separate schemas from state.py models?
  state.py models are LangGraph-internal: they define what agents read/write.
  API schemas define the HTTP contract: what the client sends and receives.
  They're deliberately different:
    - The API hides internal state details (no raw embeddings, no error strings)
    - The API adds fields the graph doesn't care about (thread_id, timestamps)
    - The client sends flat data (form fields); the graph works with structured objects
  Keeping them separate means either side can evolve independently.
"""

from pydantic import BaseModel, Field, HttpUrl
from typing import Optional
from datetime import datetime


# ── Request schemas (client → API) ────────────────────────────────────────────

class RunRequest(BaseModel):
    """
    Start a new application run.

    The client provides the two required inputs; the graph does the rest.
    resume_text can come from a prior parse or be sent directly.
    """
    resume_text: str = Field(
        ...,
        description="Plain text of the candidate's resume (parse via /resume/parse first)",
        min_length=100,
    )
    resume_storage_url: Optional[str] = Field(
        None,
        description="Public URL to the uploaded resume file in Supabase Storage",
    )
    job_url: str = Field(
        ...,
        description="Job listing URL (e.g. https://boards.greenhouse.io/acme/jobs/123) "
                    "or raw job description text",
        min_length=10,
    )


class ApproveRequest(BaseModel):
    """Resume the graph with an approval decision after the human-review interrupt."""
    approved: bool = Field(..., description="True = approve and submit, False = reject")
    feedback: Optional[str] = Field(
        None,
        description="Required when approved=False. Specific notes for the re-tailor.",
    )


# ── Response schemas (API → client) ──────────────────────────────────────────

class RunStarted(BaseModel):
    """Returned immediately when a run is launched (non-blocking)."""
    thread_id: str = Field(..., description="Unique ID for this run — use to poll status and review")
    status: str = "started"
    message: str = "Application run started. Poll /runs/{thread_id}/status for progress."


class MatchSummary(BaseModel):
    """Compact match result for the review endpoint — client doesn't need full state."""
    overall_score: float
    strengths: list[str]
    weaknesses: list[str]
    gap_areas: list[str]


class ReviewPayload(BaseModel):
    """
    Surfaced to the user when the graph pauses at the HUMAN_REVIEW interrupt.
    Contains everything the user needs to make an informed decision.
    """
    thread_id: str
    company_name: Optional[str] = None
    job_url: str
    match_score: float
    ats_keyword_coverage: float
    tailored_resume: str         # full text for the user to read/edit
    cover_letter: str
    match_summary: MatchSummary
    ats_recommendations: str


class RunStatus(BaseModel):
    """Current status of a run — for polling."""
    thread_id: str
    status: str   # "running" | "awaiting_review" | "completed" | "failed" | "skipped"
    submission_status: Optional[str] = None   # "applied" | "failed" | "skipped" | None
    error: Optional[str] = None
    completed_at: Optional[datetime] = None


class ResumeParseResponse(BaseModel):
    """Result of parsing an uploaded resume file."""
    resume_text: str
    resume_storage_url: Optional[str] = None
    char_count: int
    message: str = "Resume parsed successfully. Use resume_text in /runs/start."
