"""Add client_name to projects

Revision ID: 012
Revises: 011
Create Date: 2026-06-24 00:00:00.000000

"""
from alembic import op
import sqlalchemy as sa

revision = '012'
down_revision = '011'
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column('projects', sa.Column('client_name', sa.String(length=255), nullable=True))


def downgrade() -> None:
    op.drop_column('projects', 'client_name')
