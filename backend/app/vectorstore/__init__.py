"""vectorstore package — pgvector-backed candidate embedding search.

Public API:

    from app.vectorstore.indexing import index_resume, search_similar_resumes
    from app.vectorstore.pgvector import upsert_embedding, search_embeddings

``faiss.py`` is retained as an empty placeholder for backwards compatibility
with the original scaffold; all logic lives in ``pgvector.py``.
"""

from app.vectorstore.indexing import index_resume, search_similar_resumes
from app.vectorstore.pgvector import upsert_embedding, search_embeddings

__all__ = [
    "index_resume",
    "search_similar_resumes",
    "upsert_embedding",
    "search_embeddings",
]
