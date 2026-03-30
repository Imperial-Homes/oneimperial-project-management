"""Add retention_releases table.

Revision ID: 008_add_retention_releases
Revises: merge_project_heads_001
Create Date: 2026-03-23 00:00:00.000000
"""

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects.postgresql import UUID

revision = '008'
down_revision = '007'
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "retention_releases",
        sa.Column("id", UUID(as_uuid=True), primary_key=True),
        sa.Column("release_number", sa.String(50), nullable=False, unique=True),
        sa.Column("project_id", UUID(as_uuid=True), sa.ForeignKey("projects.id", ondelete="CASCADE"), nullable=False),
        sa.Column(
            "tranche",
            sa.Enum("practical_completion", "dlp_end", "full", name="retentiontranche"),
            nullable=False,
        ),
        sa.Column(
            "status",
            sa.Enum("draft", "submitted", "approved", "rejected", "paid", name="retentionstatus"),
            nullable=False,
            server_default="draft",
        ),
        sa.Column("amount_requested", sa.Numeric(15, 2), nullable=False),
        sa.Column("amount_approved", sa.Numeric(15, 2), nullable=True),
        sa.Column("currency", sa.String(3), server_default="GHS"),
        sa.Column("request_date", sa.Date, nullable=False),
        sa.Column("approval_date", sa.Date, nullable=True),
        sa.Column("payment_date", sa.Date, nullable=True),
        sa.Column("requested_by", UUID(as_uuid=True), nullable=True),
        sa.Column("approved_by", UUID(as_uuid=True), nullable=True),
        sa.Column("rejected_by", UUID(as_uuid=True), nullable=True),
        sa.Column("notes", sa.Text, nullable=True),
        sa.Column("rejection_reason", sa.Text, nullable=True),
        sa.Column("payment_reference", sa.String(100), nullable=True),
        sa.Column("supporting_docs", sa.Text, nullable=True),
        sa.Column("created_at", sa.DateTime, server_default=sa.func.now(), nullable=False),
        sa.Column("created_by", UUID(as_uuid=True), nullable=True),
        sa.Column("updated_at", sa.DateTime, server_default=sa.func.now(), onupdate=sa.func.now(), nullable=True),
        sa.Column("updated_by", UUID(as_uuid=True), nullable=True),
    )
    op.create_index("ix_retention_releases_project_id", "retention_releases", ["project_id"])
    op.create_index("ix_retention_releases_status", "retention_releases", ["status"])
    op.create_index("ix_retention_releases_tranche", "retention_releases", ["tranche"])
    op.create_index("ix_retention_releases_release_number", "retention_releases", ["release_number"])


def downgrade() -> None:
    op.drop_index("ix_retention_releases_release_number", table_name="retention_releases")
    op.drop_index("ix_retention_releases_tranche", table_name="retention_releases")
    op.drop_index("ix_retention_releases_status", table_name="retention_releases")
    op.drop_index("ix_retention_releases_project_id", table_name="retention_releases")
    op.drop_table("retention_releases")
    op.execute("DROP TYPE IF EXISTS retentiontranche")
    op.execute("DROP TYPE IF EXISTS retentionstatus")
