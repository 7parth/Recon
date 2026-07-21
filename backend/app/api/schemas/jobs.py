from pydantic import BaseModel
from typing import List

class JobSearchResult(BaseModel):
    title: str
    url: str
    snippet: str

class JobSearchResponse(BaseModel):
    query: str
    results: List[JobSearchResult]
