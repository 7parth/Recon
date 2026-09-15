"""api/schemas/discovery.py — Pydantic schemas for the discovery API.

Covers discovery preferences (read/write) and session lifecycle (read-only
responses + the start-session confirmation).  Counter fields on
``DiscoverySessionResponse`` are populated by merging ``DiscoverySessionRecord``
data with a live ``SessionCounters`` query before serialisation.
"""

from __future__ import annotations

import uuid
from datetime import datetime
from typing import List, Optional

from pydantic import BaseModel, ConfigDict, Field


# ── Preferences ───────────────────────────────────────────────────────────────


class DiscoveryPreferencesResponse(BaseModel):
    """Full preferences object returned by GET /discovery/preferences."""

    model_config = ConfigDict(from_attributes=True)

    target_role: str = ""
    preferred_locations: List[str] = Field(default_factory=list)
    excluded_companies: List[str] = Field(default_factory=list)
    max_jobs_per_session: int = 10
    updated_at: Optional[datetime] = None


class DiscoveryPreferencesUpdate(BaseModel):
    """Body accepted by PUT /discovery/preferences.

    All fields are optional — only the fields supplied are written.
    ``max_jobs_per_session`` is range-validated here (ge=1, le=50) per R1.4
    and R8.3; the DB also has a CHECK constraint as a safety net.
    """

    target_role: Optional[str] = None
    preferred_locations: Optional[List[str]] = None
    excluded_companies: Optional[List[str]] = None
    max_jobs_per_session: Optional[int] = Field(None, ge=1, le=50)


# ── Session counters ──────────────────────────────────────────────────────────


class SessionCounters(BaseModel):
    """Per-status application counts for a single discovery session.

    This is the Pydantic counterpart of the ``SessionCounters`` dataclass in
    ``discovery_repo.py``.  It is embedded directly into
    ``DiscoverySessionResponse`` rather than being nested, so the API surface
    is flat and easy to consume from the frontend.
    """

    model_config = ConfigDict(from_attributes=True)

    jobs_pending_review: int = 0
    jobs_applied: int = 0
    jobs_skipped: int = 0
    jobs_failed: int = 0


# ── Session responses ─────────────────────────────────────────────────────────


class DiscoverySessionResponse(BaseModel):
    """Full session object returned by GET /discovery/sessions/{session_id}.

    The four ``jobs_*`` counter fields come from a live GROUP BY query (via
    ``DiscoveryRepository.get_session_counters``) and are merged in at the
    route layer before returning this model.

    Requirements: 5.1, 5.3
    """

    model_config = ConfigDict(from_attributes=True)

    session_id: uuid.UUID
    session_status: str
    jobs_found: int = 0
    jobs_processed: int = 0

    # Live counters — populated from SessionCounters query
    jobs_pending_review: int = 0
    jobs_applied: int = 0
    jobs_skipped: int = 0
    jobs_failed: int = 0

    started_at: datetime
    completed_at: Optional[datetime] = None


class StartSessionResponse(BaseModel):
    """Returned with HTTP 202 when a discovery session is successfully queued.

    Requirements: 2.1
    """

    model_config = ConfigDict(from_attributes=True)

    session_id: uuid.UUID
    session_status: str = "running"
    message: str
