"""Project Variation models."""

from datetime import date, datetime
from decimal import Decimal
from uuid import UUID, uuid4
import enum

from sqlalchemy import Boolean, Column, Date, DateTime, Enum, ForeignKey, Integer, Numeric, String, Text
from sqlalchemy.dialects.postgresql import UUID as PostgreSQLUUID
from sqlalchemy.orm import relationship

from app.database import Base


class VariationType(str, enum.Enum):
    """Variation types"""
    SCOPE_CHANGE = "scope_change"
    DESIGN_CHANGE = "design_change"
    UNFORESEEN = "unforeseen"
    CLIENT_REQUEST = "client_request"
    COST_SAVING = "cost_saving"
    REGULATORY = "regulatory"


class VariationStatus(str, enum.Enum):
    """Variation statuses"""
    DRAFT = "draft"
    SUBMITTED = "submitted"
    UNDER_REVIEW = "under_review"
    APPROVED = "approved"
    REJECTED = "rejected"
    IMPLEMENTED = "implemented"
    CANCELLED = "cancelled"


class ProjectVariation(Base):
    """Project Variation model for tracking changes to project scope, design, or specifications."""
    
    __tablename__ = "project_variations"
    
    id = Column(PostgreSQLUUID(as_uuid=True), primary_key=True, default=uuid4)
    variation_number = Column(String(50), unique=True, nullable=False, index=True)
    
    # Project link
    project_id = Column(PostgreSQLUUID(as_uuid=True), ForeignKey("projects.id", ondelete="CASCADE"), nullable=False, index=True)
    
    # Variation details
    title = Column(String(255), nullable=False)
    description = Column(Text, nullable=False)
    variation_type = Column(Enum(VariationType, values_callable=lambda x: [e.value for e in x]), nullable=False, index=True)
    status = Column(Enum(VariationStatus, values_callable=lambda x: [e.value for e in x]), nullable=False, default=VariationStatus.DRAFT, index=True)
    
    # Request information
    requested_by = Column(PostgreSQLUUID(as_uuid=True), nullable=False)
    requested_date = Column(Date, nullable=False, default=date.today)
    
    # Financial impact
    original_amount = Column(Numeric(15, 2), default=0)
    variation_amount = Column(Numeric(15, 2), nullable=False)
    new_total_amount = Column(Numeric(15, 2))
    currency = Column(String(3), default="GHS")
    
    # Time impact
    impact_on_timeline = Column(Integer, default=0)  # Days
    original_completion_date = Column(Date)
    new_completion_date = Column(Date)
    
    # Justification and documentation
    justification = Column(Text)
    impact_assessment = Column(Text)
    attachments = Column(Text)  # JSON string of file URLs
    
    # Approval workflow
    approved_by = Column(PostgreSQLUUID(as_uuid=True))
    approved_date = Column(Date)
    rejection_reason = Column(Text)
    
    # Related entities
    phase_id = Column(PostgreSQLUUID(as_uuid=True))  # Optional phase link
    task_id = Column(PostgreSQLUUID(as_uuid=True))  # Optional task link
    
    # Priority
    priority = Column(String(20), default="medium")  # low, medium, high, urgent
    
    # Metadata
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    created_by = Column(PostgreSQLUUID(as_uuid=True))
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    updated_by = Column(PostgreSQLUUID(as_uuid=True))
    
    # Relationship
    project = relationship("Project", backref="variations")
