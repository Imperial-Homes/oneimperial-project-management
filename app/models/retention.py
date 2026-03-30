"""Retention Release models."""

import enum
from datetime import datetime
from uuid import uuid4

from sqlalchemy import Column, Date, DateTime, Enum, ForeignKey, Numeric, String, Text
from sqlalchemy.dialects.postgresql import UUID as PostgreSQLUUID
from sqlalchemy.orm import relationship

from app.database import Base


class RetentionTranche(str, enum.Enum):
    """Retention release tranches — matches Ghana construction SOPs."""

    PRACTICAL_COMPLETION = "practical_completion"  # 2.5% on handover
    DLP_END = "dlp_end"  # 2.5% after Defects Liability Period
    FULL = "full"  # full retention in one release (non-standard)


class RetentionStatus(str, enum.Enum):
    """Retention release workflow statuses."""

    DRAFT = "draft"
    SUBMITTED = "submitted"
    APPROVED = "approved"
    REJECTED = "rejected"
    PAID = "paid"


class RetentionRelease(Base):
    """Retention Release — tracks contractor retention release requests per project."""

    __tablename__ = "retention_releases"

    id = Column(PostgreSQLUUID(as_uuid=True), primary_key=True, default=uuid4)
    release_number = Column(String(50), unique=True, nullable=False, index=True)

    # Project link
    project_id = Column(
        PostgreSQLUUID(as_uuid=True),
        ForeignKey("projects.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )

    # Tranche & status
    tranche = Column(
        Enum(RetentionTranche, values_callable=lambda x: [e.value for e in x]),
        nullable=False,
        index=True,
    )
    status = Column(
        Enum(RetentionStatus, values_callable=lambda x: [e.value for e in x]),
        nullable=False,
        default=RetentionStatus.DRAFT,
        index=True,
    )

    # Financial
    amount_requested = Column(Numeric(15, 2), nullable=False)
    amount_approved = Column(Numeric(15, 2))  # Set on approval
    currency = Column(String(3), default="GHS")

    # Dates
    request_date = Column(Date, nullable=False)
    approval_date = Column(Date)
    payment_date = Column(Date)

    # Workflow actors
    requested_by = Column(PostgreSQLUUID(as_uuid=True))
    approved_by = Column(PostgreSQLUUID(as_uuid=True))
    rejected_by = Column(PostgreSQLUUID(as_uuid=True))

    # Narrative
    notes = Column(Text)
    rejection_reason = Column(Text)
    payment_reference = Column(String(100))
    supporting_docs = Column(Text)  # JSON string of doc references

    # Metadata
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    created_by = Column(PostgreSQLUUID(as_uuid=True))
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    updated_by = Column(PostgreSQLUUID(as_uuid=True))

    # Relationships
    project = relationship("Project", backref="retention_releases")
