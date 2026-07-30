"""ORM models package.

Import all models here so that Alembic's ``env.py`` can discover them
through ``Base.metadata`` with a single ``from app.db.models import *``.
"""

from app.db.models.application import ApplicationRecord  # noqa: F401
from app.db.models.company import CompanyRecord  # noqa: F401
from app.db.models.job import JobRecord  # noqa: F401
from app.db.models.log import AutomationLogRecord  # noqa: F401
from app.db.models.resume import ResumeRecord  # noqa: F401
from app.db.models.review import ReviewRecord  # noqa: F401

__all__ = [
    "ApplicationRecord",
    "CompanyRecord",
    "JobRecord",
    "AutomationLogRecord",
    "ResumeRecord",
    "ReviewRecord",
]
