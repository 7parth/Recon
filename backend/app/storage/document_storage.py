"""DocumentStorage — Supabase Storage wrapper for generated documents.

Stores the LLM-generated tailored resume and cover letter produced during
an application run.  Each document is scoped to a run_id folder.

Bucket path conventions:
- Tailored resume:  ``{run_id}/tailored_resume.pdf``
- Cover letter:     ``{run_id}/cover_letter.pdf``

The bucket name is the same as the resumes bucket (``SUPABASE_STORAGE_BUCKET``)
unless you prefer separate buckets per document type — adjust here.
"""

from __future__ import annotations

from supabase._async.client import AsyncClient

from app.config import get_settings
from app.storage.storage import BaseStorage


class DocumentStorage(BaseStorage):
    """Supabase Storage operations for generated application documents.

    Usage (via ``StorageService`` — never instantiate directly in routes)::

        storage = DocumentStorage(supabase_client)
        tr_url = await storage.upload_tailored_resume(run_id="abc", data=pdf_bytes)
        cl_url = await storage.upload_cover_letter(run_id="abc", data=pdf_bytes)
    """

    def __init__(self, client: AsyncClient) -> None:
        # Re-use the same bucket as resumes; sub-folder per run keeps them separate.
        bucket = get_settings().supabase_storage_bucket
        super().__init__(client, bucket)

    async def upload_tailored_resume(self, run_id: str, data: bytes) -> str:
        """Upload a tailored resume PDF and return its public URL.

        Parameters
        ----------
        run_id
            LangGraph thread ID used as the folder scope.
        data
            PDF bytes of the tailored resume.
        """
        path = f"{run_id}/tailored_resume.pdf"
        return await self.upload(path, data, content_type="application/pdf")

    async def upload_cover_letter(self, run_id: str, data: bytes) -> str:
        """Upload a cover letter PDF and return its public URL.

        Parameters
        ----------
        run_id
            LangGraph thread ID used as the folder scope.
        data
            PDF bytes of the cover letter.
        """
        path = f"{run_id}/cover_letter.pdf"
        return await self.upload(path, data, content_type="application/pdf")
