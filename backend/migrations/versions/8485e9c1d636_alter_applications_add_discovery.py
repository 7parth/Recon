"""alter applications add discovery

Adds ``job_url`` and ``discovery_session_id`` columns to the ``applications``
table so that applications created by the discovery orchestrator can be
linked back to their parent ``discovery_sessions`` row and carry the raw
job URL that was discovered.

Revision ID: 8485e9c1d636
Revises: b882a2a660e7
Create Date: 2026-08-10 00:10:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql


# revision identifiers, used by Alembic.
revision: str = '8485e9c1d636'
down_revision: Union[str, None] = 'b882a2a660e7'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Add job_url and discovery_session_id columns to applications."""
    # Raw job URL discovered by the orchestrator.
    # Stored directly on ApplicationRecord (denormalised) because the jobs
    # table row may not exist yet at record-creation time — it is written
    # asynchronously by job_agent during the pipeline run.
    op.add_column(
        'applications',
        sa.Column(
            'job_url',
            sa.Text(),
            nullable=True,
            comment='Raw job URL from discovery search — denormalised for dedup queries',
        ),
    )

    # FK back to discovery_sessions.  SET NULL on delete so that cancelling
    # or purging a session record does not orphan the application rows.
    op.add_column(
        'applications',
        sa.Column(
            'discovery_session_id',
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey('discovery_sessions.id', ondelete='SET NULL'),
            nullable=True,
            comment='Parent discovery session — NULL for ad-hoc (manual) runs',
        ),
    )

    op.create_index(
        op.f('ix_applications_discovery_session_id'),
        'applications',
        ['discovery_session_id'],
        unique=False,
    )


def downgrade() -> None:
    """Remove job_url and discovery_session_id columns from applications."""
    op.drop_index(
        op.f('ix_applications_discovery_session_id'),
        table_name='applications',
    )
    op.drop_column('applications', 'discovery_session_id')
    op.drop_column('applications', 'job_url')
