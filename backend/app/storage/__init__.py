"""Storage module — Supabase Storage wrappers.

Graph nodes must never import from this module directly.
All uploads go through ``app/services/storage_service.py``.
"""

from app.storage.storage import BaseStorage
from app.storage.resume_storage import ResumeStorage
from app.storage.document_storage import DocumentStorage

__all__ = ["BaseStorage", "ResumeStorage", "DocumentStorage"]
