"""Project models."""

from datetime import date, datetime
from decimal import Decimal
from uuid import UUID, uuid4

from sqlalchemy import Boolean, Column, Date, DateTime, ForeignKey, Integer, Numeric, String, Text
from sqlalchemy.dialects.postgresql import UUID as PostgreSQLUUID
from sqlalchemy.orm import relationship

from app.database import Base


class Project(Base):
    """Project model."""
    
    __tablename__ = "projects"
    
    id = Column(PostgreSQLUUID(as_uuid=True), primary_key=True, default=uuid4)
    project_code = Column(String(20), unique=True, nullable=False, index=True)
    name = Column(String(255), nullable=False, index=True)
    description = Column(Text)
    project_type = Column(String(100), nullable=False, index=True)  # construction, renovation, development
    client_id = Column(PostgreSQLUUID(as_uuid=True), index=True)  # From CRM
    start_date = Column(Date)
    target_end_date = Column(Date)
    actual_end_date = Column(Date)
    status = Column(String(50), nullable=False, default="planning", index=True)  # planning, active, on_hold, completed, cancelled
    priority = Column(String(20), nullable=False, default="medium")  # low, medium, high, critical
    budget = Column(Numeric(15, 2))
    currency = Column(String(3), default="GHS")
    manager_id = Column(PostgreSQLUUID(as_uuid=True), index=True)
    location = Column(String(255))
    is_active = Column(Boolean, default=True, index=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    created_by = Column(PostgreSQLUUID(as_uuid=True))
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    updated_by = Column(PostgreSQLUUID(as_uuid=True))
    
    # Relationships
    phases = relationship("ProjectPhase", back_populates="project", cascade="all, delete-orphan")
    tasks = relationship("Task", back_populates="project", cascade="all, delete-orphan")
    schedules = relationship("ProjectSchedule", back_populates="project", cascade="all, delete-orphan")
    milestones = relationship("Milestone", back_populates="project", cascade="all, delete-orphan")
    budgets = relationship("ProjectBudget", back_populates="project", cascade="all, delete-orphan")
    costs = relationship("ProjectCost", back_populates="project", cascade="all, delete-orphan")
    resource_assignments = relationship("ResourceAssignment", back_populates="project", cascade="all, delete-orphan")


class ProjectPhase(Base):
    """Project Phase model."""
    
    __tablename__ = "project_phases"
    
    id = Column(PostgreSQLUUID(as_uuid=True), primary_key=True, default=uuid4)
    project_id = Column(PostgreSQLUUID(as_uuid=True), ForeignKey("projects.id", ondelete="CASCADE"), nullable=False)
    name = Column(String(100), nullable=False)
    description = Column(Text)
    sequence_number = Column(Integer, nullable=False)
    start_date = Column(Date)
    end_date = Column(Date)
    status = Column(String(50), nullable=False, default="pending")  # pending, in_progress, completed, cancelled
    completion_percentage = Column(Numeric(5, 2), default=0)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    project = relationship("Project", back_populates="phases")
    tasks = relationship("Task", back_populates="phase")
