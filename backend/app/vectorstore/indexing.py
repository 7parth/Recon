"""
vectorstore/indexing.py — High-level resume indexing helpers.

Public async API:

  index_resume(thread_id, resume_text)
      Embed the resume text and upsert into pgvector. Call this after a run
      completes and the resume has been parsed (i.e., after resume_agent).

  search_similar_resumes(query_text, top_k)
      Embed the query text and return the top-k most similar indexed resumes.
      Useful for finding past applications similar to a new job posting.

Both functions open their own DB session — safe to call from Celery tasks,
background tasks, or any async context with a running event loop.

Why separate from pgvector.py?
  pgvector.py owns only the SQL operations.
  indexing.py owns the embedding → DB round-trip.
  This keeps the embedding model dependency out of the raw DB layer
  (easier to test each layer in isolation with mocks).
"""

from __future__ import annotations

import logging
from typing import Optional

logger = logging.getLogger(__name__)


async def index_resume(
    thread_id: str,
    resume_text: str,
    snippet_chars: int = 500,
) -> None:
    """
    Embed ``resume_text`` and upsert the vector into the pgvector store.

    Call this after the resume is parsed and the run thread_id is known.
    The operation is idempotent — safe to retry.

    Args:
        thread_id:    LangGraph thread ID for this application run.
        resume_text:  Full resume text (or tailored resume text).
        snippet_chars: Number of leading chars to store as a display snippet.
    """
    from app.graph.tools.embeddings import get_embeddings
    from app.db.database import get_async_session
    from app.vectorstore.pgvector import upsert_embedding

    # Embed — get_embeddings returns a list of vectors; we only have one text.
    vectors = get_embeddings([resume_text])
    if not vectors:
        logger.warning("index_resume: get_embeddings returned empty for thread_id=%s", thread_id)
        return

    vector = vectors[0]
    snippet: Optional[str] = resume_text[:snippet_chars].strip() if resume_text else None

    async with get_async_session() as session:
        await upsert_embedding(
            session=session,
            thread_id=thread_id,
            vector=vector,
            snippet=snippet,
        )

    logger.info("index_resume: completed for thread_id=%s (dim=%d)", thread_id, len(vector))


async def search_similar_resumes(
    query_text: str,
    top_k: int = 10,
) -> list[tuple[str, float]]:
    """
    Embed ``query_text`` and return the top-k most similar indexed resumes.

    Useful for:
      - Surfacing past applications similar to a new job posting.
      - Deduplication — checking if a very similar resume was already submitted.

    Args:
        query_text: Free text to search against (e.g., job description, new resume).
        top_k:      Number of results (default 10).

    Returns:
        List of (thread_id, similarity_score) tuples, sorted best→worst.
        Similarity is in [0.0, 1.0]. Returns [] if the index is empty.
    """
    from app.graph.tools.embeddings import get_embeddings
    from app.db.database import get_async_session
    from app.vectorstore.pgvector import search_embeddings

    vectors = get_embeddings([query_text])
    if not vectors:
        logger.warning("search_similar_resumes: get_embeddings returned empty for query")
        return []

    query_vector = vectors[0]

    async with get_async_session() as session:
        results = await search_embeddings(
            session=session,
            query_vector=query_vector,
            top_k=top_k,
        )

    logger.info(
        "search_similar_resumes: top_k=%d, results=%d",
        top_k,
        len(results),
    )
    return results
