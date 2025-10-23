"""Schedule and Milestone models."""

from datetime import date, datetime
from uuid import UUID, uuid4

from sqlalchemy import Boolean, Column, Date, DateTime, ForeignKey, Integer, String, Text
from sqlalchemy.dialects.postgresql import UUID as PostgreSQLUUID
from sqlalchemy.orm import relationship

from app.database import Base


class ProjectSchedule(Base):
    """Project Schedule model - versions of project schedules."""
    
    __tablename__ = "project_schedules"
    
    id = Column(PostgreSQLUUID(as_uuid=True), primary_key=True, default=uuid4)
    project_id = Column(PostgreSQLUUID(as_uuid=True), ForeignKey("projects.id", ondelete="CASCADE"), nullable=False, index=True)
    version = Column(Integer, nullable=False, default=1)
    is_baseline = Column(Boolean, default=False, index=True)
    start_date = Column(Date, nullable=False)
    end_date = Column(Date, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)
    created_by = Column(PostgreSQLUUID(as_uuid=True))
    notes = Column(Text)
    
    # Relationships
    project = relationship("Project", back_populates="schedules")


class Milestone(Base):
    """Milestone model - key project milestones."""
    
    __tablename__ = "milestones"
    
    id = Column(PostgreSQLUUID(as_uuid=True), primary_key=True, default=uuid4)
    project_id = Column(PostgreSQLUUID(as_uuid=True), ForeignKey("projects.id", ondelete="CASCADE"), nullable=False, index=True)
    name = Column(String(255), nullable=False)
    description = Column(Text)
    due_date = Column(Date, nullable=False)
    completion_date = Column(Date)
    status = Column(String(50), nullable=False, default="pending", index=True)  # pending, at_risk, completed, missed
    priority = Column(String(20), nullable=False, default="medium")  # low, medium, high, critical
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    project = relationship("Project", back_populates="milestones")
