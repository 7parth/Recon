"""Initial schema

Revision ID: ecca31836228
Revises: 
Create Date: 2026-07-19 14:34:05.123456

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'ecca31836228'
down_revision: Union[str, None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # 1. resumes table
    op.create_table(
        'resumes',
        sa.Column('id', sa.UUID(), server_default=sa.text('gen_random_uuid()'), nullable=False),
        sa.Column('storage_url', sa.Text(), nullable=True, comment='Supabase Storage public URL for the original resume file'),
        sa.Column('parsed_text', sa.Text(), nullable=True, comment='Plain-text extracted from the resume — used for re-parsing without re-upload'),
        sa.Column('candidate_name', sa.String(length=255), nullable=True),
        sa.Column('candidate_email', sa.String(length=255), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.PrimaryKeyConstraint('id')
    )

    # 2. jobs table
    op.create_table(
        'jobs',
        sa.Column('id', sa.UUID(), server_default=sa.text('gen_random_uuid()'), nullable=False),
        sa.Column('job_url', sa.Text(), nullable=True),
        sa.Column('company_name', sa.String(length=255), nullable=True),
        sa.Column('job_title', sa.String(length=255), nullable=True),
        sa.Column('jd_text', sa.Text(), nullable=True, comment='Normalised JD text — stored for re-use without re-fetching the URL'),
        sa.Column('match_score', sa.Float(), nullable=True, comment='Blended match score (0.0–1.0) from match_agent'),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.PrimaryKeyConstraint('id')
    )

    # 3. companies table
    op.create_table(
        'companies',
        sa.Column('id', sa.UUID(), server_default=sa.text('gen_random_uuid()'), nullable=False),
        sa.Column('name', sa.String(length=255), nullable=False),
        sa.Column('website', sa.Text(), nullable=True),
        sa.Column('industry', sa.String(length=255), nullable=True),
        sa.Column('summary', sa.Text(), nullable=True),
        sa.Column('culture_notes', sa.Text(), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_companies_name'), 'companies', ['name'], unique=False)

    # 4. applications table
    op.create_table(
        'applications',
        sa.Column('id', sa.UUID(), server_default=sa.text('gen_random_uuid()'), nullable=False),
        sa.Column('thread_id', sa.String(length=255), nullable=False, comment='LangGraph checkpoint thread_id — used to resume interrupted runs'),
        sa.Column('resume_id', sa.UUID(), nullable=True),
        sa.Column('job_id', sa.UUID(), nullable=True),
        sa.Column('company_id', sa.UUID(), nullable=True),
        sa.Column('status', sa.String(length=50), server_default=sa.text("'pending_review'"), nullable=False, comment='pending_review | approved | rejected | applied | failed | skipped'),
        sa.Column('match_score', sa.Float(), nullable=True, comment='Blended match score (0.0–1.0) from match_agent'),
        sa.Column('resume_storage_url', sa.Text(), nullable=True, comment='Supabase Storage URL for the original resume file'),
        sa.Column('tailored_resume_url', sa.Text(), nullable=True, comment='Supabase Storage URL for the tailored resume generated for this run'),
        sa.Column('cover_letter_url', sa.Text(), nullable=True, comment='Supabase Storage URL for the cover letter generated for this run'),
        sa.Column('rejection_feedback', sa.Text(), nullable=True, comment="User's rejection note — triggers re-tailor loop when set"),
        sa.Column('error_message', sa.Text(), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.ForeignKeyConstraint(['company_id'], ['companies.id'], ondelete='SET NULL'),
        sa.ForeignKeyConstraint(['job_id'], ['jobs.id'], ondelete='SET NULL'),
        sa.ForeignKeyConstraint(['resume_id'], ['resumes.id'], ondelete='SET NULL'),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_applications_job_id'), 'applications', ['job_id'], unique=False)
    op.create_index(op.f('ix_applications_resume_id'), 'applications', ['resume_id'], unique=False)
    op.create_index(op.f('ix_applications_status'), 'applications', ['status'], unique=False)
    op.create_index(op.f('ix_applications_thread_id'), 'applications', ['thread_id'], unique=True)

    # 5. reviews table
    op.create_table(
        'reviews',
        sa.Column('id', sa.UUID(), server_default=sa.text('gen_random_uuid()'), nullable=False),
        sa.Column('application_id', sa.UUID(), nullable=False),
        sa.Column('decision', sa.String(length=20), nullable=False, comment='approved | rejected'),
        sa.Column('feedback', sa.Text(), nullable=True, comment='Rejection feedback forwarded to tailoring_agent for re-tailor'),
        sa.Column('reviewed_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.ForeignKeyConstraint(['application_id'], ['applications.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_reviews_application_id'), 'reviews', ['application_id'], unique=False)


def downgrade() -> None:
    op.drop_index(op.f('ix_reviews_application_id'), table_name='reviews')
    op.drop_table('reviews')
    op.drop_index(op.f('ix_applications_thread_id'), table_name='applications')
    op.drop_index(op.f('ix_applications_status'), table_name='applications')
    op.drop_index(op.f('ix_applications_resume_id'), table_name='applications')
    op.drop_index(op.f('ix_applications_job_id'), table_name='applications')
    op.drop_table('applications')
    op.drop_index(op.f('ix_companies_name'), table_name='companies')
    op.drop_table('companies')
    op.drop_table('jobs')
    op.drop_table('resumes')
