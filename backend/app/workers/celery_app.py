"""
workers/celery_app.py — Celery application factory.

Creates the shared Celery app used by all task modules.

Configuration is read from app.config.Settings (pydantic-settings), which
picks up CELERY_BROKER_URL and CELERY_RESULT_BACKEND from the .env file.

Default values (for local dev):
  broker:  redis://localhost:6379/0
  backend: redis://localhost:6379/0

Run the worker:
  cd backend
  celery -A app.workers.celery_app worker --loglevel=info --concurrency=2

Run with dedicated queues:
  celery -A app.workers.celery_app worker -Q pipeline,indexing --loglevel=info

Inspect tasks:
  celery -A app.workers.celery_app inspect active
  celery -A app.workers.celery_app inspect reserved
"""

from __future__ import annotations

from celery import Celery


def _make_celery() -> Celery:
    """
    Build and configure the Celery app.

    We defer the Settings import to this factory so that importing celery_app
    at the module level doesn't trigger pydantic-settings env parsing in
    contexts where .env is not present (e.g. unit tests that mock the module).
    """
    from app.config import get_settings

    settings = get_settings()

    app = Celery(
        "recon",
        broker=settings.celery_broker_url,
        backend=settings.celery_result_backend,
        include=[
            "app.workers.application_tasks",
            "app.workers.indexing_tasks",
        ],
    )

    app.conf.update(
        # ── Serialization ────────────────────────────────────────────────────
        # JSON is safer than pickle and human-readable in Redis.
        task_serializer="json",
        result_serializer="json",
        accept_content=["json"],

        # ── Task behaviour ───────────────────────────────────────────────────
        # Report task as STARTED (not just PENDING) once the worker picks it up.
        # Critical for the frontend polling GET /runs/{id}/status correctly.
        task_track_started=True,

        # Keep results for 24 hours — long enough for any reasonable review queue.
        result_expires=86_400,

        # Acknowledge tasks only after completion, not on receipt.
        # Prevents task loss if the worker crashes mid-execution.
        task_acks_late=True,

        # Prefetch one task at a time — graph execution is long-running, so
        # we don't want one worker hoarding a full prefetch buffer.
        worker_prefetch_multiplier=1,

        # ── Queues ───────────────────────────────────────────────────────────
        # Default queue for graph pipeline runs.
        task_default_queue="pipeline",

        # Timezone ─────────────────────────────────────────────────────────
        timezone="UTC",
        enable_utc=True,
    )

    return app


# Module-level singleton — imported by tasks and the CLI worker command.
celery_app = _make_celery()
