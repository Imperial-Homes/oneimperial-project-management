"""Site Visit model for project site inspections."""

import uuid
from datetime import datetime
from sqlalchemy import Column, DateTime, String, Text, Numeric
from sqlalchemy.dialects.postgresql import UUID

from app.database import Base


class SiteVisit(Base):
    """Site Visit model - tracks site visits logged by Admin Officer."""

    __tablename__ = "site_visits"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    visit_id = Column(String(50), unique=True, nullable=False, index=True)  # e.g., SV-2026-0001

    # Visit details
    project_name = Column(String(255), nullable=False)
    project_id = Column(UUID(as_uuid=True))  # Link to project if available
    site_location = Column(String(500), nullable=False)
    visit_date = Column(DateTime(timezone=True), nullable=False)
    visit_time = Column(String(20))

    # Participants
    visitors = Column(Text)  # Names of people who visited
    site_contact = Column(String(255))  # On-site contact person
    site_contact_phone = Column(String(50))

    # Purpose and findings
    visit_purpose = Column(String(255), nullable=False)
    observations = Column(Text)
    issues_identified = Column(Text)
    recommendations = Column(Text)

    # Follow-up
    follow_up_required = Column(String(20), default="no")  # yes, no, pending
    follow_up_notes = Column(Text)
    next_visit_date = Column(DateTime(timezone=True))

    # Attachments
    photos_url = Column(String(500))  # URL to photos/documents
    report_url = Column(String(500))  # URL to visit report

    # Status
    status = Column(String(50), nullable=False, default="completed")  # scheduled, completed, cancelled

    # Audit
    logged_by = Column(String(255))
    logged_by_id = Column(UUID(as_uuid=True))
    created_at = Column(DateTime(timezone=True), default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime(timezone=True), default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)
