"""Merge project management branch heads

Revision ID: merge_project_heads_001
Revises: add_project_incidents, add_site_visits_001
Create Date: 2026-03-18 00:00:00.000000
"""

from alembic import op
import sqlalchemy as sa

revision = 'merge_project_heads_001'
down_revision = ('add_project_incidents', 'add_site_visits_001')
branch_labels = None
depends_on = None


def upgrade() -> None:
    pass


def downgrade() -> None:
    pass
