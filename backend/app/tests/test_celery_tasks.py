"""
app/tests/test_celery_tasks.py — Unit tests for Celery task definitions.

Tests all Celery tasks in isolation using mocked dependencies.
No live Redis, no live DB, no LLM calls.

Coverage:
  1. run_application_pipeline — Celery task registered under correct name.
  2. index_resume_task — registered in Celery app + correct queue.
  3. _run_pipeline_async — success path: returns "applied" status.
  4. _run_pipeline_async — failure path: returns "failed" on exception.
  5. _run_pipeline_async — pending_review path (graph pauses at interrupt).
  6. index_resume_task.run — calls asyncio.run(index_resume(...)).
  7. Celery config — serializer, ack_late, prefetch, queue settings.
"""

from __future__ import annotations

from unittest.mock import AsyncMock, MagicMock, patch, call

import pytest


# ── 1 & 2. Task registration ──────────────────────────────────────────────────

class TestTaskRegistration:
    """Tasks are discoverable in the Celery app by their registered names."""

    def test_pipeline_task_is_registered(self):
        # Force-import the task module so @celery_app.task decorator registers it
        import app.workers.application_tasks  # noqa: F401
        from app.workers.celery_app import celery_app

        assert "app.workers.application_tasks.run_application_pipeline" in celery_app.tasks

    def test_indexing_task_is_registered(self):
        # Force-import the task module so @celery_app.task decorator registers it
        import app.workers.indexing_tasks  # noqa: F401
        from app.workers.celery_app import celery_app

        assert "app.workers.indexing_tasks.index_resume_task" in celery_app.tasks

    def test_indexing_task_queue(self):
        from app.workers.indexing_tasks import index_resume_task

        assert index_resume_task.queue == "indexing"

    def test_pipeline_task_queue(self):
        from app.workers.application_tasks import run_application_pipeline

        assert run_application_pipeline.queue == "pipeline"


# ── 3. _run_pipeline_async — success path ────────────────────────────────────

class TestRunPipelineAsync:
    """Test the async core of run_application_pipeline."""

    def _make_final_state(self, submission_status: str | None = "applied") -> dict:
        job_profile = MagicMock()
        job_profile.job_title = "Software Engineer"
        company_profile = MagicMock()
        company_profile.name = "Acme Corp"
        match_result = MagicMock()
        match_result.overall_score = 0.85
        return {
            "submission_status": submission_status,
            "error": None,
            "job_profile": job_profile,
            "company_profile": company_profile,
            "match_result": match_result,
        }

    @pytest.mark.asyncio
    async def test_success_path_returns_applied(self):
        """On successful graph run → status = 'applied'."""
        import app.workers.application_tasks as module

        final_state = self._make_final_state("applied")
        mock_graph = AsyncMock()
        mock_graph.ainvoke = AsyncMock(return_value=final_state)

        mock_repo = AsyncMock()
        mock_sess = MagicMock()
        mock_sess.__aenter__ = AsyncMock(return_value=mock_sess)
        mock_sess.__aexit__ = AsyncMock(return_value=False)

        mock_cp = MagicMock()
        mock_cp.__aenter__ = AsyncMock(return_value=MagicMock())
        mock_cp.__aexit__ = AsyncMock(return_value=False)

        with (
            patch.object(module, "get_checkpointer", return_value=mock_cp),
            patch.object(module, "build_graph", return_value=mock_graph),
            patch.object(module, "get_async_session", return_value=mock_sess),
            patch.object(module, "ApplicationRepository", return_value=mock_repo),
        ):
            from app.workers.application_tasks import _run_pipeline_async
            result = await _run_pipeline_async(
                thread_id="t1",
                resume_text="Resume text",
                job_url="https://boards.greenhouse.io/jobs/123",
                resume_storage_url=None,
            )

        assert result["thread_id"] == "t1"
        assert result["status"] == "applied"

    @pytest.mark.asyncio
    async def test_failure_path_returns_failed(self):
        """If graph.ainvoke raises, result status is 'failed'."""
        import app.workers.application_tasks as module

        mock_graph = AsyncMock()
        mock_graph.ainvoke = AsyncMock(side_effect=RuntimeError("LLM timeout"))

        mock_repo = AsyncMock()
        mock_sess = MagicMock()
        mock_sess.__aenter__ = AsyncMock(return_value=mock_sess)
        mock_sess.__aexit__ = AsyncMock(return_value=False)

        mock_cp = MagicMock()
        mock_cp.__aenter__ = AsyncMock(return_value=MagicMock())
        mock_cp.__aexit__ = AsyncMock(return_value=False)

        with (
            patch.object(module, "get_checkpointer", return_value=mock_cp),
            patch.object(module, "build_graph", return_value=mock_graph),
            patch.object(module, "get_async_session", return_value=mock_sess),
            patch.object(module, "ApplicationRepository", return_value=mock_repo),
        ):
            from app.workers.application_tasks import _run_pipeline_async
            result = await _run_pipeline_async(
                thread_id="t-fail",
                resume_text="text",
                job_url="https://jobs.lever.co/acme/abc",
                resume_storage_url=None,
            )

        assert result["status"] == "failed"
        assert result["thread_id"] == "t-fail"
    @pytest.mark.asyncio
    async def test_pending_review_when_no_submission_status(self):
        """If graph pauses at interrupt (submission_status=None) → status = pending_review."""
        import app.workers.application_tasks as module

        final_state = {
            "submission_status": None,
            "error": None,
            "job_profile": None,
            "company_profile": None,
            "match_result": None,
        }
        mock_graph = AsyncMock()
        mock_graph.ainvoke = AsyncMock(return_value=final_state)

        mock_repo = AsyncMock()
        mock_sess = MagicMock()
        mock_sess.__aenter__ = AsyncMock(return_value=mock_sess)
        mock_sess.__aexit__ = AsyncMock(return_value=False)

        mock_cp = MagicMock()
        mock_cp.__aenter__ = AsyncMock(return_value=MagicMock())
        mock_cp.__aexit__ = AsyncMock(return_value=False)

        with (
            patch.object(module, "get_checkpointer", return_value=mock_cp),
            patch.object(module, "build_graph", return_value=mock_graph),
            patch.object(module, "get_async_session", return_value=mock_sess),
            patch.object(module, "ApplicationRepository", return_value=mock_repo),
        ):
            from app.workers.application_tasks import _run_pipeline_async
            result = await _run_pipeline_async(
                thread_id="t-review",
                resume_text="text",
                job_url="https://jobs.lever.co/acme/abc",
                resume_storage_url=None,
            )

        assert result["status"] == "pending_review"


# ── 4. index_resume_task ──────────────────────────────────────────────────────

class TestIndexResumeTask:
    """index_resume_task calls asyncio.run(index_resume(...))."""

    def test_index_resume_task_calls_asyncio_run(self):
        """Task body must call asyncio.run with index_resume coroutine."""
        import app.workers.indexing_tasks as module

        with (
            patch.object(module, "index_resume") as mock_index,
            patch("asyncio.run") as mock_run,
        ):
            from app.workers.indexing_tasks import index_resume_task
            index_resume_task.run(thread_id="t1", resume_text="My resume")

            mock_run.assert_called_once()
            # Verify index_resume was called with the right args
            mock_index.assert_called_once_with(thread_id="t1", resume_text="My resume")

    def test_index_resume_task_returns_correct_dict(self):
        """Task must return {status: 'indexed', thread_id: ...}."""
        import app.workers.indexing_tasks as module

        with (
            patch.object(module, "index_resume"),
            patch("asyncio.run"),
        ):
            from app.workers.indexing_tasks import index_resume_task
            result = index_resume_task.run(thread_id="t42", resume_text="text")

        assert result == {"status": "indexed", "thread_id": "t42"}


# ── 5. Celery configuration ───────────────────────────────────────────────────

class TestCeleryConfig:
    """Celery app is configured with production-safe defaults."""

    def test_task_serializer_is_json(self):
        from app.workers.celery_app import celery_app
        assert celery_app.conf.task_serializer == "json"

    def test_task_track_started(self):
        from app.workers.celery_app import celery_app
        assert celery_app.conf.task_track_started is True

    def test_worker_prefetch_multiplier(self):
        from app.workers.celery_app import celery_app
        assert celery_app.conf.worker_prefetch_multiplier == 1

    def test_task_acks_late(self):
        from app.workers.celery_app import celery_app
        assert celery_app.conf.task_acks_late is True

    def test_default_queue(self):
        from app.workers.celery_app import celery_app
        assert celery_app.conf.task_default_queue == "pipeline"

    def test_result_expires(self):
        from app.workers.celery_app import celery_app
        assert celery_app.conf.result_expires == 86_400
