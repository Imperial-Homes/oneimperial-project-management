"""Add assigned_to_name and assigned_by_name to tasks table."""

revision = "010"
down_revision = "009_add_maintenance_tables"
branch_labels = None
depends_on = None

from alembic import op
import sqlalchemy as sa


def upgrade() -> None:
    op.add_column("tasks", sa.Column("assigned_to_name", sa.String(255), nullable=True))
    op.add_column("tasks", sa.Column("assigned_by_name", sa.String(255), nullable=True))


def downgrade() -> None:
    op.drop_column("tasks", "assigned_by_name")
    op.drop_column("tasks", "assigned_to_name")
