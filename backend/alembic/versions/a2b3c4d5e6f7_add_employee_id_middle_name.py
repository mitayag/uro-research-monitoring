"""Add employee_id and middle_name to users

Revision ID: a2b3c4d5e6f7
Revises: f1a2b3c4d5e6
Create Date: 2026-09-10 12:00:00.000000

"""
from typing import Sequence, Union
from alembic import op
import sqlalchemy as sa


revision: str = 'a2b3c4d5e6f7'
down_revision: Union[str, None] = 'f1a2b3c4d5e6'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column('users', sa.Column('employee_id', sa.String(50), nullable=True))
    op.add_column('users', sa.Column('middle_name', sa.String(100), nullable=True))
    op.create_index('ix_users_employee_id', 'users', ['employee_id'], unique=True)


def downgrade() -> None:
    op.drop_index('ix_users_employee_id', table_name='users')
    op.drop_column('users', 'middle_name')
    op.drop_column('users', 'employee_id')
