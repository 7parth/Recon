from pydantic import BaseModel
from typing import List, Optional

class JobSearchResult(BaseModel):
    title: str
    url: str
    snippet: str
    company: Optional[str] = None    # extracted from title heuristic; may be None
    location: Optional[str] = None   # not returned by DDGS; reserved for future enrichment

class JobSearchResponse(BaseModel):
    query: str
    results: List[JobSearchResult]
