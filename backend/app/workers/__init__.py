"""workers package — Celery task workers for Recon.

Usage:
    Start the worker (from backend/ directory):

        # Both queues on one worker (dev)
        celery -A app.workers.celery_app worker --loglevel=info

        # Separate queues (production — scale independently)
        celery -A app.workers.celery_app worker -Q pipeline --concurrency=2
        celery -A app.workers.celery_app worker -Q indexing --concurrency=4

    Monitor:
        celery -A app.workers.celery_app flower  # Web UI at http://localhost:5555

Task registry:
    app.workers.application_tasks.run_application_pipeline  (queue: pipeline)
    app.workers.indexing_tasks.index_resume_task             (queue: indexing)
"""
