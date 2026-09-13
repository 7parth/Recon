"""BaseStorage — low-level Supabase Storage operations.

Provides upload, download, delete, and public URL generation against a
named Supabase Storage bucket.  Higher-level wrappers (``ResumeStorage``,
``DocumentStorage``) compose this class with bucket-specific logic.

Rules (code-standards.md):
- This class is only instantiated from ``app/services/storage_service.py``.
- Graph nodes never call storage methods directly.
"""

from __future__ import annotations

import mimetypes
from pathlib import PurePosixPath

from supabase._async.client import AsyncClient


class BaseStorage:
    """Thin async wrapper around a single Supabase Storage bucket.

    Parameters
    ----------
    client
        Authenticated Supabase async client (service role key).
    bucket_name
        Name of the Supabase Storage bucket to operate on.
    """

    def __init__(self, client: AsyncClient, bucket_name: str) -> None:
        self._client = client
        self._bucket = bucket_name

    # ── Upload ────────────────────────────────────────────────────────────

    async def upload(
        self,
        path: str,
        data: bytes,
        content_type: str | None = None,
    ) -> str:
        """Upload ``data`` to ``path`` in the bucket and return the public URL.

        Parameters
        ----------
        path
            Object path inside the bucket, e.g. ``"runs/abc-123/resume.pdf"``.
        data
            Raw file bytes.
        content_type
            MIME type. If omitted, guessed from the file extension in ``path``.

        Returns
        -------
        str
            Public URL of the uploaded object.

        Raises
        ------
        RuntimeError
            If the Supabase Storage upload returns an error.
        """
        if content_type is None:
            suffix = PurePosixPath(path).suffix
            content_type = mimetypes.types_map.get(suffix, "application/octet-stream")

        response = await (
            self._client.storage
            .from_(self._bucket)
            .upload(
                path=path,
                file=data,
                file_options={"content-type": content_type, "upsert": "true"},
            )
        )
        # The Supabase Python client raises on error, but check for safety
        if hasattr(response, "error") and response.error:
            raise RuntimeError(
                f"Supabase Storage upload failed for bucket={self._bucket!r} "
                f"path={path!r}: {response.error}"
            )
        return await self.public_url(path)

    # ── Download ──────────────────────────────────────────────────────────

    async def download(self, path: str) -> bytes:
        """Download the object at ``path`` and return its bytes."""
        response = await (
            self._client.storage
            .from_(self._bucket)
            .download(path)
        )
        return response

    # ── Delete ────────────────────────────────────────────────────────────

    async def delete(self, *paths: str) -> None:
        """Delete one or more objects from the bucket by path."""
        await self._client.storage.from_(self._bucket).remove(list(paths))

    # ── URL ───────────────────────────────────────────────────────────────

    async def public_url(self, path: str) -> str:
        """Return the public URL for an object without making a network call.

        The Supabase SDK computes this deterministically from the project URL
        and bucket name — no round-trip required.

        Note: get_public_url() is synchronous in supabase-py v2 (returns str
        directly). Do NOT await it — that would raise TypeError.
        """
        return (
            self._client.storage
            .from_(self._bucket)
            .get_public_url(path)
        )
