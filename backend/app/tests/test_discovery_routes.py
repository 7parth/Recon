"""app/tests/test_discovery_routes.py — Unit tests for discovery API routes.

Tests the following endpoints using FastAPI TestClient with mocked DB
repositories, so no live database is required:

  GET  /api/v1/discovery/preferences          — returns defaults (R8.1)
  PUT  /api/v1/discovery/preferences          — partial update (R8.2)
  POST /api/v1/discovery/sessions             — 409 (running), 422 (no role / no resume), 202 (ok)
  POST /api/v1/discovery/sessions/{id}/cancel — 409 (not running), 200 (running)

Requirements: 2.1, 2.2, 2.3, 6.1, 6.2, 8.1, 8.2
"""

from __future__ import annotations

import uuid
from datetime import datetime, timezone
from types import SimpleNamespace
from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from fastapi.testclient import TestClient


# ── Helpers ────────────────────────────────────────────────────────────────────


def _make_prefs(**overrides):
    """Return a fake DiscoveryPreferencesRecord-like object."""
    defaults = dict(
        id=uuid.uuid4(),
        user_id="default_user",
        target_role="Software Engineer",
        preferred_locations=["San Francisco"],
        excluded_companies=[],
        max_jobs_per_session=10,
        updated_at=datetime.now(timezone.utc),
    )
    defaults.update(overrides)
    return SimpleNamespace(**defaults)


def _make_session(**overrides):
    """Return a fake DiscoverySessionRecord-like object."""
    defaults = dict(
        id=uuid.uuid4(),
        user_id="default_user",
        session_status="running",
        jobs_found=0,
        jobs_processed=0,
        error_message=None,
        started_at=datetime.now(timezone.utc),
        completed_at=None,
    )
    defaults.update(overrides)
    return SimpleNamespace(**defaults)


def _make_resume(**overrides):
    """Return a fake ResumeRecord-like object."""
    defaults = dict(
        id=uuid.uuid4(),
        parsed_text="Alice Smith\nSoftware Engineer\nPython, FastAPI",
        storage_url="https://example.com/resume.pdf",
    )
    defaults.update(overrides)
    return SimpleNamespace(**defaults)


def _make_counters():
    """Return a fake SessionCounters-like object."""
    return SimpleNamespace(
        jobs_pending_review=0,
        jobs_applied=0,
        jobs_skipped=0,
        jobs_failed=0,
    )


# ── Fixtures ───────────────────────────────────────────────────────────────────


@pytest.fixture(scope="module")
def client():
    """TestClient for the FastAPI app.

    The lifespan tries to connect to Postgres/Supabase which is unavailable in
    CI.  We patch the graph-builder and scheduler so startup completes cleanly
    with an in-memory MemorySaver, then set ``app.state.graph`` to a sentinel.
    """
    # Prevent real DB / external connections during startup
    with (
        patch(
            "app.services.checkpoint_service.get_checkpointer",
            side_effect=Exception("no db in tests"),
        ),
        patch("app.graph.builder.build_graph", return_value=MagicMock()),
        patch("app.discovery.scheduler.init_scheduler", return_value=MagicMock(running=False)),
    ):
        from app.main import app as _app  # noqa: PLC0415 — deferred to apply patches first

        with TestClient(_app, raise_server_exceptions=False) as c:
            # Ensure app.state.graph exists for the start_session endpoint
            _app.state.graph = MagicMock()
            yield c


# ── GET /discovery/preferences ─────────────────────────────────────────────────


class TestGetPreferences:
    """R8.1 — GET /discovery/preferences returns current (or default) prefs."""

    def test_returns_defaults_when_no_row(self, client: TestClient):
        """If no prefs row exists the endpoint returns default values."""
        default_prefs = _make_prefs(target_role="", preferred_locations=[], excluded_companies=[])

        with patch(
            "app.api.routes.discovery.DiscoveryRepository.get_preferences",
            new_callable=AsyncMock,
            return_value=default_prefs,
        ):
            resp = client.get("/api/v1/discovery/preferences")

        assert resp.status_code == 200
        data = resp.json()
        assert data["target_role"] == ""
        assert data["preferred_locations"] == []
        assert data["excluded_companies"] == []
        assert data["max_jobs_per_session"] == 10

    def test_returns_stored_prefs(self, client: TestClient):
        """Returns stored values when a preferences row exists."""
        stored = _make_prefs(
            target_role="ML Engineer",
            preferred_locations=["Remote", "New York"],
            excluded_companies=["MegaCorp"],
            max_jobs_per_session=20,
        )

        with patch(
            "app.api.routes.discovery.DiscoveryRepository.get_preferences",
            new_callable=AsyncMock,
            return_value=stored,
        ):
            resp = client.get("/api/v1/discovery/preferences")

        assert resp.status_code == 200
        data = resp.json()
        assert data["target_role"] == "ML Engineer"
        assert data["preferred_locations"] == ["Remote", "New York"]
        assert data["excluded_companies"] == ["MegaCorp"]
        assert data["max_jobs_per_session"] == 20


# ── PUT /discovery/preferences ─────────────────────────────────────────────────


class TestUpdatePreferences:
    """R8.2 — PUT /discovery/preferences updates fields and returns full object."""

    def test_partial_update_returns_full_object(self, client: TestClient):
        """Updating only target_role returns the full preferences object."""
        updated = _make_prefs(target_role="Backend Engineer")

        with patch(
            "app.api.routes.discovery.DiscoveryRepository.upsert_preferences",
            new_callable=AsyncMock,
            return_value=updated,
        ):
            resp = client.put(
                "/api/v1/discovery/preferences",
                json={"target_role": "Backend Engineer"},
            )

        assert resp.status_code == 200
        data = resp.json()
        assert data["target_role"] == "Backend Engineer"
        # Full object fields are present
        assert "preferred_locations" in data
        assert "excluded_companies" in data
        assert "max_jobs_per_session" in data

    def test_update_all_fields(self, client: TestClient):
        """All preference fields can be updated in a single request."""
        updated = _make_prefs(
            target_role="DevOps Engineer",
            preferred_locations=["Austin", "Remote"],
            excluded_companies=["BadCorp"],
            max_jobs_per_session=25,
        )

        with patch(
            "app.api.routes.discovery.DiscoveryRepository.upsert_preferences",
            new_callable=AsyncMock,
            return_value=updated,
        ):
            resp = client.put(
                "/api/v1/discovery/preferences",
                json={
                    "target_role": "DevOps Engineer",
                    "preferred_locations": ["Austin", "Remote"],
                    "excluded_companies": ["BadCorp"],
                    "max_jobs_per_session": 25,
                },
            )

        assert resp.status_code == 200
        data = resp.json()
        assert data["target_role"] == "DevOps Engineer"
        assert data["max_jobs_per_session"] == 25

    def test_422_when_max_jobs_out_of_range_low(self, client: TestClient):
        """max_jobs_per_session = 0 is rejected with 422 (R8.3)."""
        resp = client.put(
            "/api/v1/discovery/preferences",
            json={"max_jobs_per_session": 0},
        )
        assert resp.status_code == 422

    def test_422_when_max_jobs_out_of_range_high(self, client: TestClient):
        """max_jobs_per_session = 51 is rejected with 422 (R8.3)."""
        resp = client.put(
            "/api/v1/discovery/preferences",
            json={"max_jobs_per_session": 51},
        )
        assert resp.status_code == 422

    def test_422_when_preferred_locations_exceeds_five(self, client: TestClient):
        """More than 5 preferred_locations is rejected with 422 (R8.4)."""
        resp = client.put(
            "/api/v1/discovery/preferences",
            json={"preferred_locations": ["A", "B", "C", "D", "E", "F"]},
        )
        assert resp.status_code == 422


# ── POST /discovery/sessions ──────────────────────────────────────────────────


class TestStartSession:
    """R2.1–2.3 — POST /discovery/sessions lifecycle checks."""

    def _patch_start(
        self,
        *,
        active_session=None,
        prefs=None,
        resume=None,
        new_session=None,
    ):
        """Return a context manager that patches the three repo methods used by start_session."""
        if prefs is None:
            prefs = _make_prefs()
        if new_session is None:
            new_session = _make_session()

        return patch.multiple(
            "app.api.routes.discovery",
            **{
                "DiscoveryRepository.get_active_session": AsyncMock(return_value=active_session),
                "DiscoveryRepository.get_preferences": AsyncMock(return_value=prefs),
                "ResumeRepository.get_latest": AsyncMock(return_value=resume),
                "DiscoveryRepository.create_session": AsyncMock(return_value=new_session),
            },
        )

    def test_409_when_session_already_running(self, client: TestClient):
        """409 with active_session_id when a running session exists (R2.2)."""
        running = _make_session(session_status="running")

        with (
            patch(
                "app.api.routes.discovery.DiscoveryRepository.get_active_session",
                new_callable=AsyncMock,
                return_value=running,
            ),
        ):
            resp = client.post("/api/v1/discovery/sessions")

        assert resp.status_code == 409
        detail = resp.json()["detail"]
        assert "active_session_id" in detail
        assert detail["active_session_id"] == str(running.id)

    def test_422_when_target_role_empty(self, client: TestClient):
        """422 when target_role is empty (R2.3)."""
        empty_prefs = _make_prefs(target_role="")

        with (
            patch(
                "app.api.routes.discovery.DiscoveryRepository.get_active_session",
                new_callable=AsyncMock,
                return_value=None,
            ),
            patch(
                "app.api.routes.discovery.DiscoveryRepository.get_preferences",
                new_callable=AsyncMock,
                return_value=empty_prefs,
            ),
        ):
            resp = client.post("/api/v1/discovery/sessions")

        assert resp.status_code == 422
        assert "target_role" in resp.json()["detail"].lower()

    def test_422_when_target_role_whitespace_only(self, client: TestClient):
        """422 when target_role is whitespace only (R2.3)."""
        whitespace_prefs = _make_prefs(target_role="   ")

        with (
            patch(
                "app.api.routes.discovery.DiscoveryRepository.get_active_session",
                new_callable=AsyncMock,
                return_value=None,
            ),
            patch(
                "app.api.routes.discovery.DiscoveryRepository.get_preferences",
                new_callable=AsyncMock,
                return_value=whitespace_prefs,
            ),
        ):
            resp = client.post("/api/v1/discovery/sessions")

        assert resp.status_code == 422
        assert "target_role" in resp.json()["detail"].lower()

    def test_422_when_no_resume(self, client: TestClient):
        """422 when no parsed resume is stored (R2.4)."""
        with (
            patch(
                "app.api.routes.discovery.DiscoveryRepository.get_active_session",
                new_callable=AsyncMock,
                return_value=None,
            ),
            patch(
                "app.api.routes.discovery.DiscoveryRepository.get_preferences",
                new_callable=AsyncMock,
                return_value=_make_prefs(),
            ),
            patch(
                "app.api.routes.discovery.ResumeRepository.get_latest",
                new_callable=AsyncMock,
                return_value=None,
            ),
        ):
            resp = client.post("/api/v1/discovery/sessions")

        assert resp.status_code == 422
        assert "resume" in resp.json()["detail"].lower()

    def test_422_when_resume_has_no_parsed_text(self, client: TestClient):
        """422 when resume exists but parsed_text is absent (R2.4)."""
        empty_resume = _make_resume(parsed_text=None)

        with (
            patch(
                "app.api.routes.discovery.DiscoveryRepository.get_active_session",
                new_callable=AsyncMock,
                return_value=None,
            ),
            patch(
                "app.api.routes.discovery.DiscoveryRepository.get_preferences",
                new_callable=AsyncMock,
                return_value=_make_prefs(),
            ),
            patch(
                "app.api.routes.discovery.ResumeRepository.get_latest",
                new_callable=AsyncMock,
                return_value=empty_resume,
            ),
        ):
            resp = client.post("/api/v1/discovery/sessions")

        assert resp.status_code == 422

    def test_202_on_valid_start(self, client: TestClient):
        """202 with session_id and session_status='running' on success (R2.1)."""
        new_session = _make_session()

        with (
            patch(
                "app.api.routes.discovery.DiscoveryRepository.get_active_session",
                new_callable=AsyncMock,
                return_value=None,
            ),
            patch(
                "app.api.routes.discovery.DiscoveryRepository.get_preferences",
                new_callable=AsyncMock,
                return_value=_make_prefs(),
            ),
            patch(
                "app.api.routes.discovery.ResumeRepository.get_latest",
                new_callable=AsyncMock,
                return_value=_make_resume(),
            ),
            patch(
                "app.api.routes.discovery.DiscoveryRepository.create_session",
                new_callable=AsyncMock,
                return_value=new_session,
            ),
            # Prevent the actual orchestrator from running
            patch("app.discovery.orchestrator.run_discovery_session", new_callable=AsyncMock),
        ):
            resp = client.post("/api/v1/discovery/sessions")

        assert resp.status_code == 202
        data = resp.json()
        assert data["session_id"] == str(new_session.id)
        assert data["session_status"] == "running"
        assert "message" in data


# ── POST /discovery/sessions/{id}/cancel ─────────────────────────────────────


class TestCancelSession:
    """R6.1, R6.2 — POST /discovery/sessions/{id}/cancel."""

    def test_409_when_session_not_running(self, client: TestClient):
        """409 with current_status when session is not running (R6.2)."""
        completed_session = _make_session(session_status="completed")
        session_id = completed_session.id

        with patch(
            "app.api.routes.discovery.DiscoveryRepository.get_session",
            new_callable=AsyncMock,
            return_value=completed_session,
        ):
            resp = client.post(f"/api/v1/discovery/sessions/{session_id}/cancel")

        assert resp.status_code == 409
        detail = resp.json()["detail"]
        assert detail["current_status"] == "completed"

    def test_409_when_session_failed(self, client: TestClient):
        """409 when session is in failed state (R6.2)."""
        failed_session = _make_session(session_status="failed")
        session_id = failed_session.id

        with patch(
            "app.api.routes.discovery.DiscoveryRepository.get_session",
            new_callable=AsyncMock,
            return_value=failed_session,
        ):
            resp = client.post(f"/api/v1/discovery/sessions/{session_id}/cancel")

        assert resp.status_code == 409
        assert resp.json()["detail"]["current_status"] == "failed"

    def test_409_when_session_already_cancelled(self, client: TestClient):
        """409 when session was previously cancelled (R6.2)."""
        cancelled_session = _make_session(session_status="cancelled")
        session_id = cancelled_session.id

        with patch(
            "app.api.routes.discovery.DiscoveryRepository.get_session",
            new_callable=AsyncMock,
            return_value=cancelled_session,
        ):
            resp = client.post(f"/api/v1/discovery/sessions/{session_id}/cancel")

        assert resp.status_code == 409

    def test_200_cancel_running_session(self, client: TestClient):
        """200 with cancelled status when cancelling a running session (R6.1)."""
        running_session = _make_session(session_status="running")
        session_id = running_session.id

        with (
            patch(
                "app.api.routes.discovery.DiscoveryRepository.get_session",
                new_callable=AsyncMock,
                return_value=running_session,
            ),
            patch(
                "app.api.routes.discovery.DiscoveryRepository.update_session_status",
                new_callable=AsyncMock,
                return_value=None,
            ),
        ):
            resp = client.post(f"/api/v1/discovery/sessions/{session_id}/cancel")

        assert resp.status_code == 200
        data = resp.json()
        assert data["session_id"] == str(session_id)
        assert data["session_status"] == "cancelled"

    def test_404_when_session_not_found(self, client: TestClient):
        """404 when the session does not exist."""
        nonexistent_id = uuid.uuid4()

        with patch(
            "app.api.routes.discovery.DiscoveryRepository.get_session",
            new_callable=AsyncMock,
            return_value=None,
        ):
            resp = client.post(f"/api/v1/discovery/sessions/{nonexistent_id}/cancel")

        assert resp.status_code == 404
