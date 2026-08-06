"""
app/tests/test_vectorstore.py — Unit tests for the pgvector vectorstore layer.

Tests the vectorstore and indexing layers in isolation using mocked DB sessions
and mocked embeddings — no live Supabase connection or model download required.

Coverage:
  1. upsert_embedding — SQL upsert executes with correct params.
  2. search_embeddings — SQL search executes and returns ranked results.
  3. upsert_embedding — raises ValueError for wrong vector dimension.
  4. search_embeddings — raises ValueError for wrong query dimension.
  5. index_resume — calls get_embeddings + upsert_embedding.
  6. search_similar_resumes — calls get_embeddings + search_embeddings.
  7. index_resume — handles empty embedding gracefully (no DB call).
"""

from __future__ import annotations

from unittest.mock import AsyncMock, MagicMock, patch

import pytest


# ── 1. upsert_embedding ───────────────────────────────────────────────────────

class TestUpsertEmbedding:
    """upsert_embedding calls session.execute with correct SQL and commits."""

    @pytest.mark.asyncio
    async def test_upsert_executes_and_commits(self):
        from app.vectorstore.pgvector import upsert_embedding

        mock_session = AsyncMock()
        mock_session.execute = AsyncMock()
        mock_session.commit = AsyncMock()

        vector = [0.1] * 384
        await upsert_embedding(mock_session, "thread-1", vector, snippet="Hello")

        assert mock_session.execute.called
        assert mock_session.commit.called

    @pytest.mark.asyncio
    async def test_upsert_includes_thread_id_in_params(self):
        from app.vectorstore.pgvector import upsert_embedding

        mock_session = AsyncMock()
        mock_session.execute = AsyncMock()
        mock_session.commit = AsyncMock()

        vector = [0.5] * 384
        await upsert_embedding(mock_session, "my-thread-xyz", vector)

        call_args = mock_session.execute.call_args
        params = call_args[0][1]  # positional second arg = params dict
        assert params["thread_id"] == "my-thread-xyz"
        assert "embedding" in params

    @pytest.mark.asyncio
    async def test_upsert_wrong_dimension_raises(self):
        from app.vectorstore.pgvector import upsert_embedding

        mock_session = AsyncMock()
        with pytest.raises(ValueError, match="384-dim"):
            await upsert_embedding(mock_session, "t1", [0.1] * 128)


# ── 2. search_embeddings ──────────────────────────────────────────────────────

class TestSearchEmbeddings:
    """search_embeddings returns clipped similarity scores from DB rows."""

    @pytest.mark.asyncio
    async def test_search_returns_sorted_results(self):
        from app.vectorstore.pgvector import search_embeddings

        mock_row_1 = MagicMock()
        mock_row_1.thread_id = "thread-A"
        mock_row_1.similarity = 0.95

        mock_row_2 = MagicMock()
        mock_row_2.thread_id = "thread-B"
        mock_row_2.similarity = 0.72

        mock_result = MagicMock()
        mock_result.fetchall.return_value = [mock_row_1, mock_row_2]

        mock_session = AsyncMock()
        mock_session.execute = AsyncMock(return_value=mock_result)

        results = await search_embeddings(mock_session, [0.1] * 384, top_k=5)

        assert len(results) == 2
        assert results[0] == ("thread-A", 0.95)
        assert results[1] == ("thread-B", 0.72)

    @pytest.mark.asyncio
    async def test_search_clips_score_to_01(self):
        from app.vectorstore.pgvector import search_embeddings

        mock_row = MagicMock()
        mock_row.thread_id = "t1"
        mock_row.similarity = -0.05  # can happen with cosine on extreme vectors

        mock_result = MagicMock()
        mock_result.fetchall.return_value = [mock_row]

        mock_session = AsyncMock()
        mock_session.execute = AsyncMock(return_value=mock_result)

        results = await search_embeddings(mock_session, [0.1] * 384)
        assert results[0][1] == 0.0  # clipped to 0

    @pytest.mark.asyncio
    async def test_search_empty_table_returns_empty(self):
        from app.vectorstore.pgvector import search_embeddings

        mock_result = MagicMock()
        mock_result.fetchall.return_value = []

        mock_session = AsyncMock()
        mock_session.execute = AsyncMock(return_value=mock_result)

        results = await search_embeddings(mock_session, [0.1] * 384)
        assert results == []

    @pytest.mark.asyncio
    async def test_search_wrong_dimension_raises(self):
        from app.vectorstore.pgvector import search_embeddings

        mock_session = AsyncMock()
        with pytest.raises(ValueError, match="384-dim"):
            await search_embeddings(mock_session, [0.1] * 100)


# ── 3. index_resume (indexing.py) ─────────────────────────────────────────────

class TestIndexResume:
    """index_resume embeds text and calls upsert_embedding."""

    @pytest.mark.asyncio
    async def test_index_resume_calls_upsert(self):
        """index_resume embeds text and upserts into DB."""
        fake_vector = [0.1] * 384

        mock_session = AsyncMock()
        mock_ctx = MagicMock()
        mock_ctx.__aenter__ = AsyncMock(return_value=mock_session)
        mock_ctx.__aexit__ = AsyncMock(return_value=False)

        # Patch at source — indexing.py uses lazy imports inside the function
        with (
            patch("app.graph.tools.embeddings.get_embeddings", return_value=[fake_vector]),
            patch("app.db.database.get_async_session", return_value=mock_ctx),
            patch("app.vectorstore.pgvector.upsert_embedding", new_callable=AsyncMock) as mock_upsert,
        ):
            from app.vectorstore.indexing import index_resume
            await index_resume("thread-42", "Resume text here")

            mock_upsert.assert_called_once()
            call_kwargs = mock_upsert.call_args[1]
            assert call_kwargs["thread_id"] == "thread-42"
            assert call_kwargs["vector"] == fake_vector

    @pytest.mark.asyncio
    async def test_index_resume_snippet_truncated(self):
        """Snippet stored is truncated to snippet_chars characters."""
        fake_vector = [0.1] * 384
        long_text = "A" * 1000

        mock_session = AsyncMock()
        mock_ctx = MagicMock()
        mock_ctx.__aenter__ = AsyncMock(return_value=mock_session)
        mock_ctx.__aexit__ = AsyncMock(return_value=False)

        with (
            patch("app.graph.tools.embeddings.get_embeddings", return_value=[fake_vector]),
            patch("app.db.database.get_async_session", return_value=mock_ctx),
            patch("app.vectorstore.pgvector.upsert_embedding", new_callable=AsyncMock) as mock_upsert,
        ):
            from app.vectorstore.indexing import index_resume
            await index_resume("t1", long_text, snippet_chars=500)

            call_kwargs = mock_upsert.call_args[1]
            assert len(call_kwargs["snippet"]) == 500

    @pytest.mark.asyncio
    async def test_index_resume_empty_embeddings_skips_upsert(self):
        """If get_embeddings returns [] (e.g. model not available), no DB call."""
        with (
            patch("app.graph.tools.embeddings.get_embeddings", return_value=[]),
            patch("app.vectorstore.pgvector.upsert_embedding", new_callable=AsyncMock) as mock_upsert,
        ):
            from app.vectorstore.indexing import index_resume
            await index_resume("t1", "some text")
            mock_upsert.assert_not_called()


# ── 4. search_similar_resumes (indexing.py) ───────────────────────────────────

class TestSearchSimilarResumes:
    """search_similar_resumes embeds query and delegates to search_embeddings."""

    @pytest.mark.asyncio
    async def test_returns_results_from_db(self):
        fake_vector = [0.2] * 384
        db_results = [("thread-X", 0.91), ("thread-Y", 0.83)]

        mock_session = AsyncMock()
        mock_ctx = MagicMock()
        mock_ctx.__aenter__ = AsyncMock(return_value=mock_session)
        mock_ctx.__aexit__ = AsyncMock(return_value=False)

        with (
            patch("app.graph.tools.embeddings.get_embeddings", return_value=[fake_vector]),
            patch("app.db.database.get_async_session", return_value=mock_ctx),
            patch(
                "app.vectorstore.pgvector.search_embeddings",
                new_callable=AsyncMock,
                return_value=db_results,
            ),
        ):
            from app.vectorstore.indexing import search_similar_resumes
            results = await search_similar_resumes("Software engineer JD", top_k=5)

            assert results == db_results

    @pytest.mark.asyncio
    async def test_returns_empty_on_empty_embeddings(self):
        with patch("app.graph.tools.embeddings.get_embeddings", return_value=[]):
            from app.vectorstore.indexing import search_similar_resumes
            results = await search_similar_resumes("query text")
            assert results == []
