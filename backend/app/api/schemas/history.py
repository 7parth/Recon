import uuid
from datetime import datetime
from pydantic import BaseModel
from typing import List, Optional

class ApplicationRecordResponse(BaseModel):
    id: uuid.UUID
    thread_id: str
    status: str
    match_score: Optional[float] = None
    resume_storage_url: Optional[str] = None
    tailored_resume_url: Optional[str] = None
    cover_letter_url: Optional[str] = None
    rejection_feedback: Optional[str] = None
    error_message: Optional[str] = None
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True

class HistoryListResponse(BaseModel):
    items: List[ApplicationRecordResponse]
    limit: int
    offset: int
