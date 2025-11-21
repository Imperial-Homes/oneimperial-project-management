"""Project Incident models."""

from datetime import date, datetime
from uuid import UUID, uuid4
import enum

from sqlalchemy import Boolean, Column, Date, DateTime, Enum, ForeignKey, String, Text
from sqlalchemy.dialects.postgresql import UUID as PostgreSQLUUID
from sqlalchemy.orm import relationship

from app.database import Base


class IncidentSeverity(str, enum.Enum):
    """Incident severity levels"""
    MINOR = "minor"
    MODERATE = "moderate"
    MAJOR = "major"
    CRITICAL = "critical"


class IncidentStatus(str, enum.Enum):
    """Incident status"""
    INVESTIGATING = "investigating"
    IN_RECOVERY = "in_recovery"
    RESOLVED = "resolved"
    CLOSED = "closed"


class IncidentType(str, enum.Enum):
    """Types of incidents"""
    SAFETY = "safety"
    QUALITY = "quality"
    SECURITY = "security"
    ENVIRONMENTAL = "environmental"
    EQUIPMENT = "equipment"
    DELAY = "delay"
    ACCIDENT = "accident"
    OTHER = "other"


class ProjectIncident(Base):
    """Project Incident model for tracking safety and project incidents."""
    
    __tablename__ = "project_incidents"
    
    id = Column(PostgreSQLUUID(as_uuid=True), primary_key=True, default=uuid4)
    incident_number = Column(String(50), unique=True, nullable=False, index=True)
    
    # Project link
    project_id = Column(PostgreSQLUUID(as_uuid=True), ForeignKey("projects.id", ondelete="CASCADE"), nullable=False, index=True)
    
    # Incident details
    incident_type = Column(Enum(IncidentType, values_callable=lambda x: [e.value for e in x]), nullable=False, index=True)
    severity = Column(Enum(IncidentSeverity, values_callable=lambda x: [e.value for e in x]), nullable=False, index=True)
    status = Column(Enum(IncidentStatus, values_callable=lambda x: [e.value for e in x]), nullable=False, default=IncidentStatus.INVESTIGATING, index=True)
    
    # Incident information
    title = Column(String(255), nullable=False)
    description = Column(Text, nullable=False)
    location = Column(String(255))
    incident_date = Column(Date, nullable=False, index=True)
    reported_date = Column(Date, nullable=False)
    
    # People involved
    reported_by = Column(PostgreSQLUUID(as_uuid=True))
    reported_by_name = Column(String(255))
    assigned_to = Column(PostgreSQLUUID(as_uuid=True))
    assigned_to_name = Column(String(255))
    
    # Impact assessment
    injuries_count = Column(String(50))  # e.g., "0", "1", "2+"
    property_damage = Column(String(255))
    work_stoppage_hours = Column(String(50))
    estimated_cost = Column(String(100))
    
    # Resolution
    root_cause = Column(Text)
    corrective_actions = Column(Text)
    preventive_measures = Column(Text)
    resolved_date = Column(Date)
    resolved_by = Column(PostgreSQLUUID(as_uuid=True))
    
    # Documentation
    attachments = Column(Text)  # JSON string of file URLs
    notes = Column(Text)
    
    # Follow-up
    requires_investigation = Column(Boolean, default=True)
    investigation_completed = Column(Boolean, default=False)
    follow_up_required = Column(Boolean, default=False)
    follow_up_date = Column(Date)
    
    # Metadata
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    created_by = Column(PostgreSQLUUID(as_uuid=True))
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    updated_by = Column(PostgreSQLUUID(as_uuid=True))
    
    # Relationship
    project = relationship("Project", backref="incidents")
