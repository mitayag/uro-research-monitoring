"""Add description and updated_at to SchoolCollege and DepartmentUnit

Revision ID: b3c4d5e6f7a8
Revises: a2b3c4d5e6f7
Create Date: 2026-09-10
"""
from alembic import op
import sqlalchemy as sa

revision = "b3c4d5e6f7a8"
down_revision = "a2b3c4d5e6f7"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column("school_colleges", sa.Column("description", sa.Text(), nullable=True))
    op.add_column("school_colleges", sa.Column("updated_at", sa.DateTime(timezone=True), nullable=True))
    op.add_column("department_units", sa.Column("description", sa.Text(), nullable=True))
    op.add_column("department_units", sa.Column("updated_at", sa.DateTime(timezone=True), nullable=True))


def downgrade() -> None:
    op.drop_column("department_units", "updated_at")
    op.drop_column("department_units", "description")
    op.drop_column("school_colleges", "updated_at")
    op.drop_column("school_colleges", "description")
