"""ResumeStorage — Supabase Storage wrapper for original resume uploads.

Bucket: configured via ``SUPABASE_STORAGE_BUCKET`` (default: ``"resumes"``).
Path convention: ``{run_id}/resume{ext}`` — one object per run.
"""

from __future__ import annotations

from supabase._async.client import AsyncClient

from app.config import get_settings
from app.storage.storage import BaseStorage


class ResumeStorage(BaseStorage):
    """Supabase Storage operations scoped to the resumes bucket.

    Usage (via ``StorageService`` — never instantiate directly in routes)::

        storage = ResumeStorage(supabase_client)
        url = await storage.upload_resume(run_id="abc-123", data=pdf_bytes, ext=".pdf")
    """

    def __init__(self, client: AsyncClient) -> None:
        bucket = get_settings().supabase_storage_bucket
        super().__init__(client, bucket)

    async def upload_resume(
        self,
        run_id: str,
        data: bytes,
        ext: str = ".pdf",
    ) -> str:
        """Upload an original resume file and return its public URL.

        Parameters
        ----------
        run_id
            LangGraph thread ID — used as the folder name to scope files per run.
        data
            Raw bytes of the resume file.
        ext
            File extension (``".pdf"`` or ``".docx"``).

        Returns
        -------
        str
            Public Supabase Storage URL.
        """
        path = f"{run_id}/resume{ext}"
        content_type = (
            "application/pdf"
            if ext == ".pdf"
            else "application/vnd.openxmlformats-officedocument.wordprocessingml.document"
        )
        return await self.upload(path, data, content_type=content_type)
