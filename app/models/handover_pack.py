"""Handover Pack model - SOP 5.0 Site Visitation / Client Handover."""

import uuid
from datetime import datetime
from sqlalchemy import Boolean, Column, DateTime, Numeric, String, Text
from sqlalchemy.dialects.postgresql import UUID

from app.database import Base


class HandoverPack(Base):
    """Handover Pack model - tracks property handover process per SOP 5.0."""

    __tablename__ = "handover_packs"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    handover_id = Column(String(50), unique=True, nullable=False, index=True)  # HP-2026-0001

    # Property info
    property_name = Column(String(255), nullable=False)
    property_id = Column(UUID(as_uuid=True), nullable=True)
    apartment_number = Column(String(100), nullable=True)
    site_location = Column(String(500), nullable=True)

    # Client info
    client_name = Column(String(255), nullable=False)
    client_id = Column(UUID(as_uuid=True), nullable=True)
    client_email = Column(String(255), nullable=True)
    client_phone = Column(String(50), nullable=True)

    # Handover checklist
    sinking_fund_invoiced = Column(Boolean, default=False)
    sinking_fund_amount = Column(Numeric(15, 2), nullable=True)
    transfer_document_invoiced = Column(Boolean, default=False)
    transfer_document_amount = Column(Numeric(15, 2), nullable=True)
    hoa_forms_completed = Column(Boolean, default=False)
    facility_manager_info_provided = Column(Boolean, default=False)

    # Obligations
    all_payments_made = Column(Boolean, default=False)
    payments_date = Column(DateTime(timezone=True), nullable=True)

    # Pack details
    handover_pack_drafted = Column(Boolean, default=False)
    handover_pack_url = Column(String(500), nullable=True)
    doa_approved = Column(Boolean, default=False)
    doa_approved_date = Column(DateTime(timezone=True), nullable=True)

    # Sign-off
    client_signed = Column(Boolean, default=False)
    client_signed_date = Column(DateTime(timezone=True), nullable=True)
    keys_handed_over = Column(Boolean, default=False)
    handover_date = Column(DateTime(timezone=True), nullable=True)

    # Notes
    letter_to_client = Column(Text, nullable=True)  # Steps communicated to client
    notes = Column(Text, nullable=True)
    issues_noted = Column(Text, nullable=True)

    # Status
    status = Column(String(50), nullable=False, default="initiated")
    # initiated, obligations_pending, pack_drafted, doa_review, client_signoff, completed

    # Audit
    is_active = Column(Boolean, default=True, nullable=False)
    handled_by = Column(String(255), nullable=True)
    handled_by_id = Column(UUID(as_uuid=True), nullable=True)
    created_at = Column(DateTime(timezone=True), default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime(timezone=True), default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)
