"""Payment Certificate models."""

import enum
from datetime import datetime
from uuid import uuid4

from sqlalchemy import Column, Date, DateTime, Enum, ForeignKey, Numeric, String, Text
from sqlalchemy.dialects.postgresql import UUID as PostgreSQLUUID
from sqlalchemy.orm import relationship

from app.database import Base


class CertificateStatus(str, enum.Enum):
    """Payment certificate statuses"""

    DRAFT = "draft"
    SUBMITTED = "submitted"
    APPROVED = "approved"
    REJECTED = "rejected"
    PAID = "paid"
    PARTIALLY_PAID = "partially_paid"


class CertificateType(str, enum.Enum):
    """Payment certificate types"""

    INTERIM = "interim"
    ADVANCE = "advance"
    RETENTION = "retention"
    FINAL = "final"
    VARIATION = "variation"


class PaymentCertificate(Base):
    """Payment Certificate model for tracking payment certificates in construction projects."""

    __tablename__ = "payment_certificates"

    id = Column(PostgreSQLUUID(as_uuid=True), primary_key=True, default=uuid4)
    certificate_number = Column(String(50), unique=True, nullable=False, index=True)

    # Project link
    project_id = Column(
        PostgreSQLUUID(as_uuid=True), ForeignKey("projects.id", ondelete="CASCADE"), nullable=False, index=True
    )

    # Certificate details
    certificate_date = Column(Date, nullable=False, index=True)
    certificate_type = Column(
        Enum(CertificateType, values_callable=lambda x: [e.value for e in x]), nullable=False, index=True
    )
    status = Column(
        Enum(CertificateStatus, values_callable=lambda x: [e.value for e in x]),
        nullable=False,
        default=CertificateStatus.DRAFT,
        index=True,
    )

    # Financial details
    gross_amount = Column(Numeric(15, 2), nullable=False)  # Total work value
    previous_amount = Column(Numeric(15, 2), default=0)  # Previous certificates total
    current_amount = Column(Numeric(15, 2), nullable=False)  # This certificate amount
    retention_percentage = Column(Numeric(5, 2), default=5.0)  # Retention %
    retention_amount = Column(Numeric(15, 2), default=0)  # Retention deducted
    net_amount = Column(Numeric(15, 2), nullable=False)  # Amount payable
    currency = Column(String(3), default="GHS")

    # Work period
    period_from = Column(Date)
    period_to = Column(Date)

    # Related entities
    milestone_id = Column(PostgreSQLUUID(as_uuid=True))  # Link to milestone
    variation_id = Column(PostgreSQLUUID(as_uuid=True))  # Link to variation

    # Certificate details
    description = Column(Text)
    work_completed = Column(Text)  # Description of work completed
    notes = Column(Text)

    # Approval workflow
    submitted_date = Column(Date)
    submitted_by = Column(PostgreSQLUUID(as_uuid=True))
    approved_date = Column(Date)
    approved_by = Column(PostgreSQLUUID(as_uuid=True))
    rejected_date = Column(Date)
    rejected_by = Column(PostgreSQLUUID(as_uuid=True))
    rejection_reason = Column(Text)

    # Payment tracking
    payment_date = Column(Date)
    payment_reference = Column(String(100))
    amount_paid = Column(Numeric(15, 2), default=0)

    # Parties
    consultant_name = Column(String(255))  # Certifying consultant
    contractor_name = Column(String(255))  # Contractor
    client_name = Column(String(255))  # Client

    # Documentation
    attachments = Column(Text)  # JSON string of file URLs

    # Metadata
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    created_by = Column(PostgreSQLUUID(as_uuid=True))
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    updated_by = Column(PostgreSQLUUID(as_uuid=True))

    # Relationship
    project = relationship("Project", backref="payment_certificates")
