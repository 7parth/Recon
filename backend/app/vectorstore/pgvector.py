"""
vectorstore/pgvector.py — Raw async pgvector database operations.

Two public async functions that are the only layer touching the DB directly:

  upsert_embedding(session, thread_id, vector, snippet)
      INSERT the vector for this thread_id, or UPDATE it if it already exists.
      Uses PostgreSQL's ON CONFLICT DO UPDATE so indexing is idempotent.

  search_embeddings(session, query_vector, top_k)
      Return the top-k most similar resumes using cosine distance (``<=>``).
      Returns list of (thread_id, similarity_score) tuples sorted best→worst.

How pgvector cosine distance works:
  ``embedding <=> query``  returns a distance in [0, 2] where 0 = identical.
  We convert to similarity: score = 1 - distance, giving [−1, 1] → clipped [0, 1].
  IVFFlat index (created in migration) makes this sub-linear for large tables.

Dimension: 384 (all-MiniLM-L6-v2 — matches embeddings.py).
"""

from __future__ import annotations

import logging
from typing import Optional

from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession

logger = logging.getLogger(__name__)

_DIM = 384  # must match the model in embeddings.py


async def upsert_embedding(
    session: AsyncSession,
    thread_id: str,
    vector: list[float],
    snippet: Optional[str] = None,
) -> None:
    """
    Insert or update the 384-dim embedding for a resume run.

    Idempotent — calling again with the same thread_id replaces the old vector.
    This is safe to call from Celery tasks which may retry on transient failure.

    Args:
        session:   Async SQLAlchemy session (from get_async_session()).
        thread_id: LangGraph thread ID — unique key for this application run.
        vector:    384-dim float list from get_embeddings([resume_text])[0].
        snippet:   Optional first 500 chars of resume text for display.
    """
    if len(vector) != _DIM:
        raise ValueError(
            f"upsert_embedding: expected {_DIM}-dim vector, got {len(vector)}-dim. "
            "Ensure embeddings come from all-MiniLM-L6-v2."
        )

    # Format the vector as a Postgres literal: '[0.1,0.2,...]'
    vec_literal = "[" + ",".join(str(v) for v in vector) + "]"

    sql = text(
        """
        INSERT INTO resume_embeddings (thread_id, embedding, resume_snippet)
        VALUES (:thread_id, :embedding::vector, :snippet)
        ON CONFLICT (thread_id)
        DO UPDATE SET
            embedding      = EXCLUDED.embedding,
            resume_snippet = EXCLUDED.resume_snippet,
            created_at     = now()
        """
    )

    await session.execute(
        sql,
        {"thread_id": thread_id, "embedding": vec_literal, "snippet": snippet},
    )
    await session.commit()
    logger.info("upsert_embedding: indexed thread_id=%s", thread_id)


async def search_embeddings(
    session: AsyncSession,
    query_vector: list[float],
    top_k: int = 10,
) -> list[tuple[str, float]]:
    """
    Find the top-k most similar resumes using cosine similarity via pgvector.

    The ``<=>`` operator computes cosine distance (0 = identical, 2 = opposite).
    We convert to similarity: score = 1 - distance, so higher = more similar.

    Args:
        session:      Async SQLAlchemy session.
        query_vector: 384-dim query embedding (e.g., from a new JD or resume).
        top_k:        Number of results to return (default 10).

    Returns:
        List of (thread_id, similarity_score) tuples, sorted best→worst.
        Similarity score is in [0.0, 1.0].
    """
    if len(query_vector) != _DIM:
        raise ValueError(
            f"search_embeddings: expected {_DIM}-dim query vector, got {len(query_vector)}-dim."
        )

    vec_literal = "[" + ",".join(str(v) for v in query_vector) + "]"

    sql = text(
        """
        SELECT
            thread_id,
            1 - (embedding <=> :qvec::vector) AS similarity
        FROM resume_embeddings
        ORDER BY embedding <=> :qvec::vector
        LIMIT :top_k
        """
    )

    result = await session.execute(
        sql,
        {"qvec": vec_literal, "top_k": top_k},
    )
    rows = result.fetchall()

    results = [
        (row.thread_id, max(0.0, min(1.0, float(row.similarity))))
        for row in rows
    ]

    logger.info(
        "search_embeddings: top_k=%d, best_score=%.4f",
        top_k,
        results[0][1] if results else 0.0,
    )
    return results
