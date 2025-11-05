"""Project Payment models."""

from datetime import date, datetime
from decimal import Decimal
from uuid import UUID, uuid4
import enum

from sqlalchemy import Column, Date, DateTime, Enum, ForeignKey, Numeric, String, Text
from sqlalchemy.dialects.postgresql import UUID as PostgreSQLUUID
from sqlalchemy.orm import relationship

from app.database import Base


class PaymentMethod(str, enum.Enum):
    """Payment methods"""
    BANK_TRANSFER = "bank_transfer"
    CHECK = "check"
    CASH = "cash"
    MOBILE_MONEY = "mobile_money"
    WIRE_TRANSFER = "wire_transfer"
    CREDIT_CARD = "credit_card"


class PaymentType(str, enum.Enum):
    """Payment types"""
    ADVANCE = "advance"
    MILESTONE = "milestone"
    PROGRESS = "progress"
    RETENTION = "retention"
    FINAL = "final"
    VARIATION = "variation"


class PaymentStatus(str, enum.Enum):
    """Payment statuses"""
    PENDING = "pending"
    PROCESSING = "processing"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"
    REFUNDED = "refunded"


class ProjectPayment(Base):
    """Project Payment model for tracking payments made or received for projects."""
    
    __tablename__ = "project_payments"
    
    id = Column(PostgreSQLUUID(as_uuid=True), primary_key=True, default=uuid4)
    payment_number = Column(String(50), unique=True, nullable=False, index=True)
    
    # Project link
    project_id = Column(PostgreSQLUUID(as_uuid=True), ForeignKey("projects.id", ondelete="CASCADE"), nullable=False, index=True)
    
    # Payment details
    payment_date = Column(Date, nullable=False, index=True)
    amount = Column(Numeric(15, 2), nullable=False)
    currency = Column(String(3), default="GHS")
    
    # Payment classification
    payment_method = Column(Enum(PaymentMethod), nullable=False)
    payment_type = Column(Enum(PaymentType), nullable=False, index=True)
    status = Column(Enum(PaymentStatus), nullable=False, default=PaymentStatus.PENDING, index=True)
    
    # Related entities
    milestone_id = Column(PostgreSQLUUID(as_uuid=True))  # Link to milestone
    variation_id = Column(PostgreSQLUUID(as_uuid=True))  # Link to variation if variation payment
    invoice_reference = Column(String(100))
    
    # Payment tracking
    reference_number = Column(String(100), index=True)
    transaction_id = Column(String(100))
    description = Column(Text)
    notes = Column(Text)
    
    # Parties involved
    paid_by = Column(PostgreSQLUUID(as_uuid=True))  # Who made the payment
    paid_by_name = Column(String(255))  # Client/contractor name
    received_by = Column(PostgreSQLUUID(as_uuid=True))  # Who received the payment
    received_by_name = Column(String(255))
    
    # Documentation
    receipt_url = Column(String(500))
    attachments = Column(Text)  # JSON string of file URLs
    
    # Bank details (if applicable)
    bank_name = Column(String(255))
    account_number = Column(String(100))
    
    # Reconciliation
    is_reconciled = Column(Boolean, default=False)
    reconciled_date = Column(Date)
    reconciled_by = Column(PostgreSQLUUID(as_uuid=True))
    
    # Metadata
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    created_by = Column(PostgreSQLUUID(as_uuid=True))
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    updated_by = Column(PostgreSQLUUID(as_uuid=True))
    
    # Relationship
    project = relationship("Project", backref="payments")
