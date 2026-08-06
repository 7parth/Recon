"""add_resume_embeddings_pgvector

Enables the pgvector extension in Supabase Postgres and creates the
``resume_embeddings`` table for storing 384-dim candidate embedding vectors.

An IVFFlat index on the embedding column enables fast approximate cosine
similarity search via the ``<=>`` operator.

Revision ID: 646c34ea53a5
Revises: f92a101b4567
Create Date: 2026-08-06 21:39:54.472696
"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from pgvector.sqlalchemy import Vector


# revision identifiers, used by Alembic.
revision: str = '646c34ea53a5'
down_revision: Union[str, Sequence[str], None] = 'f92a101b4567'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    # Enable pgvector extension (idempotent — safe to run multiple times).
    # Supabase has pgvector pre-installed; this just activates it for the schema.
    op.execute("CREATE EXTENSION IF NOT EXISTS vector")

    op.create_table(
        'resume_embeddings',
        sa.Column(
            'id',
            sa.UUID(),
            server_default=sa.text('gen_random_uuid()'),
            nullable=False,
        ),
        sa.Column(
            'thread_id',
            sa.String(length=255),
            nullable=False,
            comment='LangGraph thread_id — one embedding per run',
        ),
        sa.Column(
            'embedding',
            Vector(384),
            nullable=False,
            comment='384-dim float32 embedding from all-MiniLM-L6-v2',
        ),
        sa.Column(
            'resume_snippet',
            sa.Text(),
            nullable=True,
            comment='First 500 chars of resume text — for display in similarity results',
        ),
        sa.Column(
            'created_at',
            sa.DateTime(timezone=True),
            server_default=sa.text('now()'),
            nullable=False,
        ),
        sa.PrimaryKeyConstraint('id'),
    )

    # Unique B-tree index on thread_id for fast upsert lookups.
    op.create_index(
        op.f('ix_resume_embeddings_thread_id'),
        'resume_embeddings',
        ['thread_id'],
        unique=True,
    )

    # IVFFlat index for approximate cosine similarity search.
    # lists=100 is a reasonable default for up to ~1M rows.
    # Adjust at runtime with: SET ivfflat.probes = 10;
    op.execute(
        "CREATE INDEX ON resume_embeddings "
        "USING ivfflat (embedding vector_cosine_ops) WITH (lists = 100)"
    )


def downgrade() -> None:
    """Downgrade schema."""
    op.drop_index(op.f('ix_resume_embeddings_thread_id'), table_name='resume_embeddings')
    op.drop_table('resume_embeddings')
    # Note: we intentionally do NOT drop the vector extension on downgrade,
    # as other tables or extensions may depend on it.
