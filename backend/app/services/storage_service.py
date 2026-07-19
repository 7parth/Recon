"""StorageService — orchestrates file uploads to Supabase Storage.

This is the only service layer that interacts with ``ResumeStorage``
and ``DocumentStorage``.  Graph nodes receive URLs as part of state;
they never call upload methods directly.

Concept: **Upload-then-persist** pattern
1. Upload the file to Supabase Storage → get back a public URL.
2. Persist the URL in the DB via the relevant repository.
3. Return the URL so it can be added to ``ApplicationState``.

Usage (from API routes or background workers)::

    async with get_async_session() as session:
        svc = StorageService(supabase_client, session)
        resume_url = await svc.upload_resume(
            run_id="abc-123",
            file_bytes=pdf_bytes,
            file_ext=".pdf",
        )
"""

from __future__ import annotations

from supabase._async.client import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession

from app.storage.resume_storage import ResumeStorage
from app.storage.document_storage import DocumentStorage
from app.db.repositories.application_repo import ApplicationRepository


class StorageService:
    """Uploads documents to Supabase Storage and returns public URLs.

    Parameters
    ----------
    client
        Authenticated Supabase async client (service role key).
    session
        Active ``AsyncSession`` for persisting URLs in the DB.
    """

    def __init__(self, client: AsyncClient, session: AsyncSession) -> None:
        self._resume_storage = ResumeStorage(client)
        self._document_storage = DocumentStorage(client)
        self._app_repo = ApplicationRepository(session)

    async def upload_resume(
        self,
        run_id: str,
        file_bytes: bytes,
        file_ext: str = ".pdf",
    ) -> str:
        """Upload an original resume and return its public URL.

        The URL is **not** persisted here — it is passed back to the caller
        which stores it when creating the ApplicationRecord.

        Parameters
        ----------
        run_id
            LangGraph thread ID (used as the folder scope in Storage).
        file_bytes
            Raw bytes of the uploaded resume file.
        file_ext
            File extension — ``".pdf"`` or ``".docx"``.

        Returns
        -------
        str
            Public Supabase Storage URL for the uploaded file.
        """
        return await self._resume_storage.upload_resume(
            run_id=run_id,
            data=file_bytes,
            ext=file_ext,
        )

    async def upload_tailored_resume(self, run_id: str, data: bytes) -> str:
        """Upload a tailored resume PDF, persist the URL, and return it.

        Persists the URL to ``applications.tailored_resume_url`` via the repo.
        """
        url = await self._document_storage.upload_tailored_resume(run_id, data)
        await self._app_repo.set_document_urls(run_id, tailored_resume_url=url)
        return url

    async def upload_cover_letter(self, run_id: str, data: bytes) -> str:
        """Upload a cover letter PDF, persist the URL, and return it.

        Persists the URL to ``applications.cover_letter_url`` via the repo.
        """
        url = await self._document_storage.upload_cover_letter(run_id, data)
        await self._app_repo.set_document_urls(run_id, cover_letter_url=url)
        return url
