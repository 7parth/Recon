"""Repository package.

Repositories are the only place that touches SQLAlchemy directly.
Graph nodes and API routes must go through these classes — never
query the DB directly from agent functions or route handlers.
"""

from app.db.repositories.application_repo import ApplicationRepository
from app.db.repositories.discovery_repo import DiscoveryRepository
from app.db.repositories.job_repo import JobRepository
from app.db.repositories.resume_repo import ResumeRepository

__all__ = ["ApplicationRepository", "DiscoveryRepository", "JobRepository", "ResumeRepository"]
