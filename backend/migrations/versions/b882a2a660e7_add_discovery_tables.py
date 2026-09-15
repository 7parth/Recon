"""add discovery tables

Adds ``discovery_preferences`` and ``discovery_sessions`` tables required
by the Automated Job Discovery feature.

Revision ID: b882a2a660e7
Revises: 646c34ea53a5
Create Date: 2026-08-10 00:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql


# revision identifiers, used by Alembic.
revision: str = 'b882a2a660e7'
down_revision: Union[str, None] = '646c34ea53a5'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # 1. discovery_preferences table
    op.create_table(
        'discovery_preferences',
        sa.Column(
            'id',
            sa.UUID(),
            server_default=sa.text('gen_random_uuid()'),
            nullable=False,
        ),
        sa.Column('user_id', sa.String(length=255), nullable=False),
        sa.Column(
            'target_role',
            sa.String(length=200),
            nullable=False,
            server_default=sa.text("''"),
        ),
        sa.Column(
            'preferred_locations',
            postgresql.ARRAY(sa.Text()),
            nullable=False,
            server_default=sa.text("'{}'"),
        ),
        sa.Column(
            'excluded_companies',
            postgresql.ARRAY(sa.Text()),
            nullable=False,
            server_default=sa.text("'{}'"),
        ),
        sa.Column(
            'max_jobs_per_session',
            sa.Integer(),
            nullable=False,
            server_default=sa.text('10'),
        ),
        sa.Column(
            'updated_at',
            sa.DateTime(timezone=True),
            nullable=False,
            server_default=sa.text('now()'),
        ),
        sa.CheckConstraint(
            'max_jobs_per_session BETWEEN 1 AND 50',
            name='ck_discovery_preferences_max_jobs_per_session',
        ),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('user_id'),
    )
    op.create_index(
        op.f('ix_discovery_preferences_user_id'),
        'discovery_preferences',
        ['user_id'],
        unique=True,
    )

    # 2. discovery_sessions table
    op.create_table(
        'discovery_sessions',
        sa.Column(
            'id',
            sa.UUID(),
            server_default=sa.text('gen_random_uuid()'),
            nullable=False,
        ),
        sa.Column('user_id', sa.String(length=255), nullable=False),
        sa.Column(
            'session_status',
            sa.String(length=50),
            nullable=False,
            server_default=sa.text("'running'"),
        ),
        sa.Column(
            'jobs_found',
            sa.Integer(),
            nullable=False,
            server_default=sa.text('0'),
        ),
        sa.Column(
            'jobs_processed',
            sa.Integer(),
            nullable=False,
            server_default=sa.text('0'),
        ),
        sa.Column('error_message', sa.Text(), nullable=True),
        sa.Column(
            'started_at',
            sa.DateTime(timezone=True),
            nullable=False,
            server_default=sa.text('now()'),
        ),
        sa.Column('completed_at', sa.DateTime(timezone=True), nullable=True),
        sa.PrimaryKeyConstraint('id'),
    )
    op.create_index(
        op.f('ix_discovery_sessions_user_id'),
        'discovery_sessions',
        ['user_id'],
        unique=False,
    )
    op.create_index(
        op.f('ix_discovery_sessions_session_status'),
        'discovery_sessions',
        ['session_status'],
        unique=False,
    )


def downgrade() -> None:
    op.drop_index(op.f('ix_discovery_sessions_session_status'), table_name='discovery_sessions')
    op.drop_index(op.f('ix_discovery_sessions_user_id'), table_name='discovery_sessions')
    op.drop_table('discovery_sessions')

    op.drop_index(op.f('ix_discovery_preferences_user_id'), table_name='discovery_preferences')
    op.drop_table('discovery_preferences')
