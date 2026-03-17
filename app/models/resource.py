"""Resource models."""

from datetime import datetime
from uuid import uuid4

from sqlalchemy import Boolean, Column, Date, DateTime, ForeignKey, Numeric, String, Text
from sqlalchemy.dialects.postgresql import UUID as PostgreSQLUUID
from sqlalchemy.orm import relationship

from app.database import Base


class Resource(Base):
    """Resource model - human, equipment, or materials."""

    __tablename__ = "resources"

    id = Column(PostgreSQLUUID(as_uuid=True), primary_key=True, default=uuid4)
    resource_code = Column(String(20), unique=True, nullable=False, index=True)
    name = Column(String(255), nullable=False, index=True)
    description = Column(Text)
    resource_type = Column(String(50), nullable=False, index=True)  # human, equipment, material
    employee_id = Column(PostgreSQLUUID(as_uuid=True), index=True)  # Link to HR service
    equipment_id = Column(PostgreSQLUUID(as_uuid=True))  # Link to equipment inventory
    material_id = Column(PostgreSQLUUID(as_uuid=True))  # Link to material inventory
    cost_per_hour = Column(Numeric(10, 2))
    cost_per_unit = Column(Numeric(10, 2))
    currency = Column(String(3), default="GHS")
    availability_status = Column(
        String(50), nullable=False, default="available", index=True
    )  # available, assigned, unavailable
    capacity_per_day = Column(Numeric(10, 2))  # hours per day or units per day
    unit_of_measure = Column(String(50))
    is_active = Column(Boolean, default=True, index=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relationships
    assignments = relationship("ResourceAssignment", back_populates="resource", cascade="all, delete-orphan")


class ResourceAssignment(Base):
    """Resource Assignment model - assigns resources to tasks/projects."""

    __tablename__ = "resource_assignments"

    id = Column(PostgreSQLUUID(as_uuid=True), primary_key=True, default=uuid4)
    resource_id = Column(
        PostgreSQLUUID(as_uuid=True), ForeignKey("resources.id", ondelete="CASCADE"), nullable=False, index=True
    )
    task_id = Column(PostgreSQLUUID(as_uuid=True), ForeignKey("tasks.id", ondelete="CASCADE"), index=True)
    project_id = Column(
        PostgreSQLUUID(as_uuid=True), ForeignKey("projects.id", ondelete="CASCADE"), nullable=False, index=True
    )
    start_date = Column(Date, nullable=False)
    end_date = Column(Date, nullable=False)
    allocation_percentage = Column(Numeric(5, 2), nullable=False, default=100)  # % of capacity allocated
    hours_per_day = Column(Numeric(5, 2))
    total_hours = Column(Numeric(10, 2))
    status = Column(String(50), nullable=False, default="planned", index=True)  # planned, active, completed, cancelled
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    created_by = Column(PostgreSQLUUID(as_uuid=True))

    # Relationships
    resource = relationship("Resource", back_populates="assignments")
    task = relationship("Task", back_populates="resource_assignments")
    project = relationship("Project", back_populates="resource_assignments")
