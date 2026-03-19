"""Add site_visits, progress_reports and handover_packs tables

Moved from crm service — these are project domain models and belong here.

Revision ID: add_site_visits_001
Revises: rename_to_payment_certificates
Create Date: 2026-03-17 00:00:00.000000
"""

from typing import Union

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

revision: str = "006"
down_revision: Union[str, None] = "004"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "site_visits",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True,
                  server_default=sa.text("gen_random_uuid()")),
        sa.Column("visit_id", sa.String(50), nullable=False, unique=True),
        sa.Column("project_name", sa.String(255), nullable=False),
        sa.Column("project_id", postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column("site_location", sa.String(500), nullable=False),
        sa.Column("visit_date", sa.DateTime(timezone=True), nullable=False),
        sa.Column("visit_time", sa.String(20), nullable=True),
        sa.Column("visitors", sa.Text, nullable=True),
        sa.Column("site_contact", sa.String(255), nullable=True),
        sa.Column("site_contact_phone", sa.String(50), nullable=True),
        sa.Column("visit_purpose", sa.String(255), nullable=False),
        sa.Column("observations", sa.Text, nullable=True),
        sa.Column("issues_identified", sa.Text, nullable=True),
        sa.Column("recommendations", sa.Text, nullable=True),
        sa.Column("follow_up_required", sa.String(20), nullable=True, server_default="no"),
        sa.Column("follow_up_notes", sa.Text, nullable=True),
        sa.Column("next_visit_date", sa.DateTime(timezone=True), nullable=True),
        sa.Column("photos_url", sa.String(500), nullable=True),
        sa.Column("report_url", sa.String(500), nullable=True),
        sa.Column("status", sa.String(50), nullable=False, server_default="completed"),
        sa.Column("logged_by", sa.String(255), nullable=True),
        sa.Column("logged_by_id", postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False,
                  server_default=sa.text("now()")),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False,
                  server_default=sa.text("now()")),
    )
    op.create_index("ix_site_visits_visit_id", "site_visits", ["visit_id"])

    op.create_table(
        "progress_reports",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True,
                  server_default=sa.text("gen_random_uuid()")),
        sa.Column("report_id", sa.String(50), nullable=False, unique=True),
        sa.Column("report_title", sa.String(500), nullable=False),
        sa.Column("project_name", sa.String(255), nullable=True),
        sa.Column("project_id", postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column("reporting_period", sa.String(100), nullable=True),
        sa.Column("period_start_date", sa.DateTime(timezone=True), nullable=True),
        sa.Column("period_end_date", sa.DateTime(timezone=True), nullable=True),
        sa.Column("report_date", sa.DateTime(timezone=True), nullable=False),
        sa.Column("executive_summary", sa.Text, nullable=True),
        sa.Column("achievements", sa.Text, nullable=True),
        sa.Column("challenges", sa.Text, nullable=True),
        sa.Column("next_steps", sa.Text, nullable=True),
        sa.Column("budget_status", sa.Text, nullable=True),
        sa.Column("timeline_status", sa.Text, nullable=True),
        sa.Column("completion_percentage", sa.Integer, nullable=True),
        sa.Column("submitted_to", sa.String(255), nullable=True),
        sa.Column("submitted_to_id", postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column("status", sa.String(50), nullable=False, server_default="draft"),
        sa.Column("attachment_url", sa.String(500), nullable=True),
        sa.Column("compiled_by", sa.String(255), nullable=True),
        sa.Column("compiled_by_id", postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False,
                  server_default=sa.text("now()")),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False,
                  server_default=sa.text("now()")),
    )
    op.create_index("ix_progress_reports_report_id", "progress_reports", ["report_id"])

    op.create_table(
        "handover_packs",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True,
                  server_default=sa.text("gen_random_uuid()")),
        sa.Column("handover_id", sa.String(50), nullable=False, unique=True),
        sa.Column("property_name", sa.String(255), nullable=False),
        sa.Column("property_id", postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column("apartment_number", sa.String(100), nullable=True),
        sa.Column("site_location", sa.String(500), nullable=True),
        sa.Column("client_name", sa.String(255), nullable=False),
        sa.Column("client_id", postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column("client_email", sa.String(255), nullable=True),
        sa.Column("client_phone", sa.String(50), nullable=True),
        sa.Column("sinking_fund_invoiced", sa.Boolean, nullable=True, server_default="false"),
        sa.Column("sinking_fund_amount", sa.Numeric(15, 2), nullable=True),
        sa.Column("transfer_document_invoiced", sa.Boolean, nullable=True, server_default="false"),
        sa.Column("transfer_document_amount", sa.Numeric(15, 2), nullable=True),
        sa.Column("hoa_forms_completed", sa.Boolean, nullable=True, server_default="false"),
        sa.Column("facility_manager_info_provided", sa.Boolean, nullable=True, server_default="false"),
        sa.Column("all_payments_made", sa.Boolean, nullable=True, server_default="false"),
        sa.Column("payments_date", sa.DateTime(timezone=True), nullable=True),
        sa.Column("handover_pack_drafted", sa.Boolean, nullable=True, server_default="false"),
        sa.Column("handover_pack_url", sa.String(500), nullable=True),
        sa.Column("doa_approved", sa.Boolean, nullable=True, server_default="false"),
        sa.Column("doa_approved_date", sa.DateTime(timezone=True), nullable=True),
        sa.Column("client_signed", sa.Boolean, nullable=True, server_default="false"),
        sa.Column("client_signed_date", sa.DateTime(timezone=True), nullable=True),
        sa.Column("keys_handed_over", sa.Boolean, nullable=True, server_default="false"),
        sa.Column("handover_date", sa.DateTime(timezone=True), nullable=True),
        sa.Column("letter_to_client", sa.Text, nullable=True),
        sa.Column("notes", sa.Text, nullable=True),
        sa.Column("issues_noted", sa.Text, nullable=True),
        sa.Column("status", sa.String(50), nullable=False, server_default="initiated"),
        sa.Column("is_active", sa.Boolean, nullable=False, server_default="true"),
        sa.Column("handled_by", sa.String(255), nullable=True),
        sa.Column("handled_by_id", postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False,
                  server_default=sa.text("now()")),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False,
                  server_default=sa.text("now()")),
    )
    op.create_index("ix_handover_packs_handover_id", "handover_packs", ["handover_id"])


def downgrade() -> None:
    op.drop_index("ix_handover_packs_handover_id", table_name="handover_packs")
    op.drop_table("handover_packs")
    op.drop_index("ix_progress_reports_report_id", table_name="progress_reports")
    op.drop_table("progress_reports")
    op.drop_index("ix_site_visits_visit_id", table_name="site_visits")
    op.drop_table("site_visits")
