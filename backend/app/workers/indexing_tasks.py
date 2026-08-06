"""
workers/indexing_tasks.py — Celery task for FAISS/pgvector resume indexing.

Task:
  index_resume_task(thread_id, resume_text)
      Embeds resume_text and upserts the vector into Supabase pgvector.
      Typically chained after run_application_pipeline completes.

This task is intentionally tiny — all logic lives in vectorstore/indexing.py.
The Celery task layer only provides retry/queue routing/observability.

Queue: "indexing"  (separate from the heavier "pipeline" queue)
"""

from __future__ import annotations

import asyncio
import logging

from app.workers.celery_app import celery_app
from app.vectorstore.indexing import index_resume

logger = logging.getLogger(__name__)



@celery_app.task(
    name="app.workers.indexing_tasks.index_resume_task",
    queue="indexing",
    bind=True,
    max_retries=3,
    default_retry_delay=30,  # seconds
    autoretry_for=(Exception,),
    retry_backoff=True,
)
def index_resume_task(self, thread_id: str, resume_text: str) -> dict:
    """
    Celery task: embed and upsert a resume into the pgvector store.

    Args:
        thread_id:   LangGraph thread ID for this application run.
        resume_text: Full parsed resume text to embed and index.

    Returns:
        {"status": "indexed", "thread_id": <thread_id>}

    Retries automatically on any exception (up to max_retries=3)
    with exponential backoff starting at 30 s.
    """
    logger.info("index_resume_task: starting thread_id=%s", thread_id)

    # index_resume is async; Celery workers are sync by default.
    # asyncio.run() starts a fresh event loop for this task.
    asyncio.run(index_resume(thread_id=thread_id, resume_text=resume_text))

    logger.info("index_resume_task: done thread_id=%s", thread_id)
    return {"status": "indexed", "thread_id": thread_id}
