"""Add dean routing: dean_id to school_colleges, school_college_id + assigned_dean_id to research

Revision ID: f1a2b3c4d5e6
Revises: e47f2a1b3c9d
Create Date: 2026-09-09 12:00:00.000000

"""
from typing import Sequence, Union
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects.postgresql import UUID


# revision identifiers
revision: str = 'f1a2b3c4d5e6'
down_revision: Union[str, None] = 'e47f2a1b3c9d'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Add dean_user_id to school_colleges
    op.add_column('school_colleges', sa.Column('dean_user_id', sa.dialects.postgresql.UUID(as_uuid=True), sa.ForeignKey('users.id'), nullable=True))

    # Add school_college_id and assigned_dean_id to research
    op.add_column('research', sa.Column('school_college_id', sa.dialects.postgresql.UUID(as_uuid=True), sa.ForeignKey('school_colleges.id'), nullable=True))
    op.add_column('research', sa.Column('assigned_dean_id', sa.dialects.postgresql.UUID(as_uuid=True), sa.ForeignKey('users.id'), nullable=True))


def downgrade() -> None:
    op.drop_column('research', 'assigned_dean_id')
    op.drop_column('research', 'school_college_id')
    op.drop_column('school_colleges', 'dean_user_id')
