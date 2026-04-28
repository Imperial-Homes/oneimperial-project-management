"""add maintenance tables

Revision ID: 009_add_maintenance_tables
Revises: 008_add_retention_releases
Create Date: 2026-04-28
"""

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects.postgresql import UUID

revision = "009_add_maintenance_tables"
down_revision = "008_add_retention_releases"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "maintenance_payments",
        sa.Column("id", UUID(as_uuid=True), primary_key=True),
        sa.Column("payment_reference", sa.String(100), nullable=False, unique=True, index=True),
        sa.Column("payment_type", sa.String(50), nullable=False),
        sa.Column("project", sa.String(255), nullable=False),
        sa.Column("block", sa.String(100)),
        sa.Column("unit", sa.String(100), nullable=False),
        sa.Column("payer_name", sa.String(255), nullable=False),
        sa.Column("payer_contact", sa.String(255)),
        sa.Column("amount", sa.Numeric(15, 2), nullable=False),
        sa.Column("currency", sa.String(10), server_default="GHS"),
        sa.Column("payment_date", sa.Date, nullable=False),
        sa.Column("payment_method", sa.String(50)),
        sa.Column("bank_name", sa.String(255)),
        sa.Column("cheque_number", sa.String(100)),
        sa.Column("received_by", sa.String(255)),
        sa.Column("description", sa.String(500)),
        sa.Column("notes", sa.Text),
        sa.Column("status", sa.String(50), server_default="completed"),
        sa.Column("created_by", UUID(as_uuid=True)),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
    )

    op.create_table(
        "maintenance_budgets",
        sa.Column("id", UUID(as_uuid=True), primary_key=True),
        sa.Column("budget_reference", sa.String(100), nullable=False, unique=True, index=True),
        sa.Column("title", sa.String(255), nullable=False),
        sa.Column("project_id", UUID(as_uuid=True)),
        sa.Column("project_name", sa.String(255)),
        sa.Column("category", sa.String(100)),
        sa.Column("total_amount", sa.Numeric(15, 2), nullable=False),
        sa.Column("paid_amount", sa.Numeric(15, 2), server_default="0"),
        sa.Column("currency", sa.String(10), server_default="GHS"),
        sa.Column("start_date", sa.Date),
        sa.Column("end_date", sa.Date),
        sa.Column("status", sa.String(50), server_default="pending_approval"),
        sa.Column("notes", sa.Text),
        sa.Column("created_by", UUID(as_uuid=True)),
        sa.Column("created_by_name", sa.String(255)),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
    )

    op.create_table(
        "maintenance_service_fees",
        sa.Column("id", UUID(as_uuid=True), primary_key=True),
        sa.Column("project", sa.String(255), nullable=False),
        sa.Column("block", sa.String(100)),
        sa.Column("unit", sa.String(100), nullable=False),
        sa.Column("owner_name", sa.String(255), nullable=False),
        sa.Column("owner_contact", sa.String(255)),
        sa.Column("fee_type", sa.String(100)),
        sa.Column("amount", sa.Numeric(15, 2), nullable=False),
        sa.Column("currency", sa.String(10), server_default="GHS"),
        sa.Column("billing_period", sa.String(100)),
        sa.Column("due_date", sa.Date),
        sa.Column("status", sa.String(50), server_default="pending"),
        sa.Column("payment_date", sa.Date),
        sa.Column("receipt_number", sa.String(100)),
        sa.Column("notes", sa.Text),
        sa.Column("created_by", UUID(as_uuid=True)),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
    )

    op.create_table(
        "rental_schedule_entries",
        sa.Column("id", UUID(as_uuid=True), primary_key=True),
        sa.Column("property_name", sa.String(255), nullable=False),
        sa.Column("sheet_year", sa.String(20)),
        sa.Column("commercial_unit", sa.String(100)),
        sa.Column("square_meters", sa.String(50)),
        sa.Column("owner", sa.String(255)),
        sa.Column("tenant", sa.String(255)),
        sa.Column("start_date", sa.Date),
        sa.Column("expiry_date", sa.Date),
        sa.Column("months", sa.Numeric(5, 1)),
        sa.Column("monthly_rent", sa.Numeric(15, 2)),
        sa.Column("currency", sa.String(10), server_default="USD"),
        sa.Column("total_amount", sa.Numeric(15, 2)),
        sa.Column("amount_paid", sa.Numeric(15, 2)),
        sa.Column("balance", sa.Numeric(15, 2)),
        sa.Column("tenancy_agreement_status", sa.String(255)),
        sa.Column("due_date", sa.Date),
        sa.Column("status_notes", sa.Text),
        sa.Column("is_active", sa.Boolean, server_default="true"),
        sa.Column("imported_by", UUID(as_uuid=True)),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
    )


def downgrade() -> None:
    op.drop_table("rental_schedule_entries")
    op.drop_table("maintenance_service_fees")
    op.drop_table("maintenance_budgets")
    op.drop_table("maintenance_payments")
