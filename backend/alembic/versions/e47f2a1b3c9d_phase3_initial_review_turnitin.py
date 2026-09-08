"""Phase 3: add new enum values and initial review tables

Revision ID: e47f2a1b3c9d
Revises: d335dfe368c0
Create Date: 2026-09-08 12:00:00.000000
"""
from typing import Sequence, Union
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

revision: str = 'e47f2a1b3c9d'
down_revision: Union[str, None] = 'd335dfe368c0'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Add new enum values to researchstatus
    op.execute("ALTER TYPE researchstatus ADD VALUE IF NOT EXISTS 'URO_RECEIVED'")
    op.execute("ALTER TYPE researchstatus ADD VALUE IF NOT EXISTS 'INITIAL_REVIEW'")
    op.execute("ALTER TYPE researchstatus ADD VALUE IF NOT EXISTS 'INITIAL_REVISION_REQUIRED'")
    op.execute("ALTER TYPE researchstatus ADD VALUE IF NOT EXISTS 'INITIAL_REVISION_SUBMITTED'")
    op.execute("ALTER TYPE researchstatus ADD VALUE IF NOT EXISTS 'INITIAL_REVIEW_PASSED'")
    op.execute("ALTER TYPE researchstatus ADD VALUE IF NOT EXISTS 'PROPOSAL_TURNITIN_RESUBMITTED'")
    op.execute("ALTER TYPE researchstatus ADD VALUE IF NOT EXISTS 'READY_FOR_EXTERNAL_EVALUATION'")

    # Create initial_reviews table
    op.create_table(
        'initial_reviews',
        sa.Column('id', sa.UUID(), nullable=False),
        sa.Column('research_id', sa.UUID(), nullable=False),
        sa.Column('reviewer_id', sa.UUID(), nullable=False),
        sa.Column('decision', sa.String(20), nullable=True),
        sa.Column('remarks_researcher', sa.Text(), nullable=True),
        sa.Column('remarks_internal', sa.Text(), nullable=True),
        sa.Column('revision_instructions', sa.Text(), nullable=True),
        sa.Column('started_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('decided_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('round_number', sa.Integer(), nullable=True),
        sa.ForeignKeyConstraint(['research_id'], ['research.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['reviewer_id'], ['users.id']),
        sa.PrimaryKeyConstraint('id'),
    )

    # Create initial_review_items table
    op.create_table(
        'initial_review_items',
        sa.Column('id', sa.UUID(), nullable=False),
        sa.Column('review_id', sa.UUID(), nullable=False),
        sa.Column('checklist_label', sa.String(300), nullable=False),
        sa.Column('status', sa.String(20), nullable=True),
        sa.Column('remarks', sa.Text(), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=True),
        sa.ForeignKeyConstraint(['review_id'], ['initial_reviews.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id'),
    )

    # Add new columns to similarity_check_attempts
    op.add_column('similarity_check_attempts', sa.Column('attempt_number', sa.Integer(), nullable=True))
    op.add_column('similarity_check_attempts', sa.Column('remarks_researcher', sa.Text(), nullable=True))
    op.add_column('similarity_check_attempts', sa.Column('remarks_internal', sa.Text(), nullable=True))

    # Seed default turnitin threshold
    op.execute("""
        INSERT INTO system_settings (id, key, value, description)
        SELECT gen_random_uuid(), 'turnitin_proposal_threshold', '15.0', 'Proposal Turnitin similarity threshold (%)'
        WHERE NOT EXISTS (SELECT 1 FROM system_settings WHERE key = 'turnitin_proposal_threshold')
    """)


def downgrade() -> None:
    op.drop_table('initial_review_items')
    op.drop_table('initial_reviews')
    op.drop_column('similarity_check_attempts', 'remarks_internal')
    op.drop_column('similarity_check_attempts', 'remarks_researcher')
    op.drop_column('similarity_check_attempts', 'attempt_number')
    # Note: PostgreSQL does not support removing enum values
