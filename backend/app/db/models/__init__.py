"""ORM models package.

Import all models here so that Alembic's ``env.py`` can discover them
through ``Base.metadata`` with a single ``from app.db.models import *``.
"""

# Discovery models must be imported before ApplicationRecord so that the
# DiscoverySessionRecord relationship target is already registered when
# ApplicationRecord's TYPE_CHECKING import is resolved at runtime.
from app.db.models.discovery import DiscoveryPreferencesRecord, DiscoverySessionRecord  # noqa: F401
from app.db.models.application import ApplicationRecord  # noqa: F401
from app.db.models.company import CompanyRecord  # noqa: F401
from app.db.models.job import JobRecord  # noqa: F401
from app.db.models.log import AutomationLogRecord  # noqa: F401
from app.db.models.resume import ResumeRecord  # noqa: F401
from app.db.models.review import ReviewRecord  # noqa: F401
from app.db.models.user import UserProfileRecord, UserSettingsRecord  # noqa: F401
from app.db.models.embedding import ResumeEmbeddingRecord  # noqa: F401

__all__ = [
    "DiscoveryPreferencesRecord",
    "DiscoverySessionRecord",
    "ApplicationRecord",
    "CompanyRecord",
    "JobRecord",
    "AutomationLogRecord",
    "ResumeRecord",
    "ReviewRecord",
    "UserProfileRecord",
    "UserSettingsRecord",
    "ResumeEmbeddingRecord",
]
