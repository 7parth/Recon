"""
app/tests/test_linkedin_automation.py — Unit tests for LinkedIn Phase 19.

Tests:
  1. URL pattern detection — LinkedIn URLs routed correctly by dispatcher.
  2. Dispatcher routing — linkedin.submit is called for linkedin.com/jobs URLs.
  3. Session path resolution — config env var respected.
  4. linkedin_auth helpers — session file existence checks.
  5. Config — linkedin_session_path setting present in Settings.
"""

from __future__ import annotations

import json
import os
import tempfile
from pathlib import Path
from unittest.mock import MagicMock, patch, mock_open

import pytest


# ── 1. Platform detection ─────────────────────────────────────────────────────

class TestDetectPlatform:
    """dispatcher.detect_platform correctly identifies LinkedIn URLs."""

    @pytest.fixture(autouse=True)
    def _import(self):
        from app.automation.dispatcher import detect_platform
        self.detect = detect_platform

    def test_linkedin_jobs_view_url(self):
        url = "https://www.linkedin.com/jobs/view/4234567890"
        assert self.detect(url) == "linkedin"

    def test_linkedin_jobs_search_url(self):
        url = "https://www.linkedin.com/jobs/search/?keywords=software+engineer"
        assert self.detect(url) == "linkedin"

    def test_linkedin_jobs_collections_url(self):
        url = "https://www.linkedin.com/jobs/collections/recommended/"
        assert self.detect(url) == "linkedin"

    def test_greenhouse_not_linkedin(self):
        assert self.detect("https://boards.greenhouse.io/acme/jobs/123") == "greenhouse"

    def test_lever_not_linkedin(self):
        assert self.detect("https://jobs.lever.co/stripe/abc") == "lever"

    def test_workday_not_linkedin(self):
        assert self.detect("https://mycompany.wd1.myworkdayjobs.com/en-US/job/123") == "workday"

    def test_ashby_not_linkedin(self):
        assert self.detect("https://jobs.ashbyhq.com/acme/abc") == "ashby"

    def test_smartrecruiters_not_linkedin(self):
        assert self.detect("https://jobs.smartrecruiters.com/ACME/123") == "smartrecruiters"

    def test_unknown_url(self):
        assert self.detect("https://careers.example.com/apply/1234") == "unknown"

    def test_linkedin_non_jobs_url_is_unknown(self):
        # linkedin.com/in/ profile pages should NOT match
        assert self.detect("https://www.linkedin.com/in/johndoe") == "unknown"


# ── 2. Dispatcher routing ─────────────────────────────────────────────────────

class TestDispatcherRoutesToLinkedIn:
    """dispatch() calls linkedin.submit for linkedin.com/jobs URLs."""

    def test_dispatch_calls_linkedin_submit(self):
        from app.automation.dispatcher import dispatch
        from app.graph.state import CandidateProfile

        profile = CandidateProfile(
            first_name="Jane",
            last_name="Smith",
            email="jane@example.com",
            phone="+1-555-0100",
            skills=["Python", "FastAPI"],
            experience_years=4.0,
            summary="Backend engineer",
        )

        mock_submit = MagicMock(return_value=True)

        with patch("app.automation.linkedin.submit", mock_submit):
            result = dispatch(
                url="https://www.linkedin.com/jobs/view/9876543210",
                resume_text="Experienced backend engineer…",
                cover_letter_text="Dear Hiring Manager…",
                candidate_profile=profile,
                thread_id="test-thread-li-001",
            )

        # dispatch returns True because mock_submit returns True
        assert result is True
        mock_submit.assert_called_once()
        call_kwargs = mock_submit.call_args.kwargs
        assert "linkedin.com/jobs" in call_kwargs.get("url", "")

    def test_dispatch_unknown_url_returns_false(self):
        from app.automation.dispatcher import dispatch
        from app.graph.state import CandidateProfile

        profile = CandidateProfile(
            first_name="Test", last_name="User", email="t@t.com", phone="1234",
            skills=[], experience_years=0.0, summary="",
        )
        result = dispatch(
            url="https://example.com/jobs/apply",
            resume_text="",
            cover_letter_text="",
            candidate_profile=profile,
            thread_id="test-unknown",
        )
        assert result is False


# ── 3. Session path resolution ────────────────────────────────────────────────

class TestSessionPath:
    """linkedin_auth.get_session_path() respects env var override."""

    def test_default_path_is_inside_backend(self):
        from app.automation.linkedin_auth import get_session_path

        with patch.dict(os.environ, {}, clear=False):
            # Remove override if present
            os.environ.pop("LINKEDIN_SESSION_PATH", None)
            path = get_session_path()

        assert path.name == ".linkedin_session.json"
        # Should be inside the backend directory
        assert "backend" in str(path)

    def test_env_var_overrides_path(self, tmp_path):
        from app.automation.linkedin_auth import get_session_path

        custom = str(tmp_path / "custom_session.json")
        with patch.dict(os.environ, {"LINKEDIN_SESSION_PATH": custom}):
            path = get_session_path()

        assert str(path) == custom

    def test_path_is_absolute(self):
        from app.automation.linkedin_auth import get_session_path

        os.environ.pop("LINKEDIN_SESSION_PATH", None)
        path = get_session_path()
        assert path.is_absolute()


# ── 4. linkedin_auth helpers ──────────────────────────────────────────────────

class TestLinkedInAuthHelpers:
    """Unit tests for load_session, save_session, session_file_exists."""

    def test_session_file_exists_false_when_no_file(self, tmp_path):
        from app.automation.linkedin_auth import session_file_exists, get_session_path

        custom = str(tmp_path / "nonexistent.json")
        with patch.dict(os.environ, {"LINKEDIN_SESSION_PATH": custom}):
            assert session_file_exists() is False

    def test_session_file_exists_true_when_file_present(self, tmp_path):
        from app.automation.linkedin_auth import session_file_exists

        session_file = tmp_path / ".linkedin_session.json"
        session_file.write_text("{}")

        with patch.dict(os.environ, {"LINKEDIN_SESSION_PATH": str(session_file)}):
            assert session_file_exists() is True

    def test_load_session_returns_false_when_no_file(self, tmp_path):
        from app.automation.linkedin_auth import load_session

        mock_context = MagicMock()
        with patch.dict(os.environ, {"LINKEDIN_SESSION_PATH": str(tmp_path / "nope.json")}):
            result = load_session(mock_context)

        assert result is False
        mock_context.add_cookies.assert_not_called()

    def test_load_session_loads_cookies(self, tmp_path):
        from app.automation.linkedin_auth import load_session

        session_data = {
            "cookies": [{"name": "li_at", "value": "test_token", "domain": ".linkedin.com"}],
            "origins": [],
        }
        session_file = tmp_path / ".linkedin_session.json"
        session_file.write_text(json.dumps(session_data))

        mock_context = MagicMock()
        with patch.dict(os.environ, {"LINKEDIN_SESSION_PATH": str(session_file)}):
            result = load_session(mock_context)

        assert result is True
        mock_context.add_cookies.assert_called_once_with(session_data["cookies"])

    def test_save_session_writes_file(self, tmp_path):
        from app.automation.linkedin_auth import save_session

        session_file = tmp_path / ".linkedin_session.json"
        fake_state = {"cookies": [{"name": "li_at", "value": "abc"}], "origins": []}

        mock_context = MagicMock()
        mock_context.storage_state.return_value = fake_state

        with patch.dict(os.environ, {"LINKEDIN_SESSION_PATH": str(session_file)}):
            result = save_session(mock_context)

        assert result is True
        assert session_file.exists()
        saved = json.loads(session_file.read_text())
        assert saved["cookies"][0]["name"] == "li_at"


# ── 5. Config ─────────────────────────────────────────────────────────────────

class TestLinkedInConfig:
    """Settings object includes the linkedin_session_path field."""

    def test_linkedin_session_path_in_settings(self):
        from app.config import Settings

        s = Settings()
        assert hasattr(s, "linkedin_session_path")
        assert ".linkedin_session.json" in s.linkedin_session_path

    def test_linkedin_session_path_env_override(self):
        from app.config import Settings

        with patch.dict(os.environ, {"LINKEDIN_SESSION_PATH": "/custom/path/session.json"}):
            s = Settings()
            assert s.linkedin_session_path == "/custom/path/session.json"
