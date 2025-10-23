"""Task models."""

from datetime import date, datetime
from decimal import Decimal
from uuid import UUID, uuid4

from sqlalchemy import Column, Date, DateTime, ForeignKey, Numeric, String, Text, UniqueConstraint
from sqlalchemy.dialects.postgresql import UUID as PostgreSQLUUID
from sqlalchemy.orm import relationship

from app.database import Base


class Task(Base):
    """Task model."""
    
    __tablename__ = "tasks"
    
    id = Column(PostgreSQLUUID(as_uuid=True), primary_key=True, default=uuid4)
    project_id = Column(PostgreSQLUUID(as_uuid=True), ForeignKey("projects.id", ondelete="CASCADE"), nullable=False, index=True)
    phase_id = Column(PostgreSQLUUID(as_uuid=True), ForeignKey("project_phases.id", ondelete="SET NULL"), index=True)
    parent_task_id = Column(PostgreSQLUUID(as_uuid=True), ForeignKey("tasks.id", ondelete="SET NULL"), index=True)
    task_code = Column(String(20), unique=True, nullable=False, index=True)
    name = Column(String(255), nullable=False)
    description = Column(Text)
    assignee_id = Column(PostgreSQLUUID(as_uuid=True), index=True)
    start_date = Column(Date)
    due_date = Column(Date)
    completion_date = Column(Date)
    estimated_hours = Column(Numeric(10, 2))
    actual_hours = Column(Numeric(10, 2), default=0)
    status = Column(String(50), nullable=False, default="todo", index=True)  # todo, in_progress, review, done, blocked
    priority = Column(String(20), nullable=False, default="medium")  # low, medium, high, critical
    completion_percentage = Column(Numeric(5, 2), default=0)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    project = relationship("Project", back_populates="tasks")
    phase = relationship("ProjectPhase", back_populates="tasks")
    parent_task = relationship("Task", remote_side=[id], backref="subtasks")
    dependencies = relationship(
        "TaskDependency",
        foreign_keys="TaskDependency.task_id",
        back_populates="task",
        cascade="all, delete-orphan"
    )
    dependent_on = relationship(
        "TaskDependency",
        foreign_keys="TaskDependency.dependency_task_id",
        back_populates="dependency_task"
    )
    resource_assignments = relationship("ResourceAssignment", back_populates="task")
    costs = relationship("ProjectCost", back_populates="task")


class TaskDependency(Base):
    """Task Dependency model."""
    
    __tablename__ = "task_dependencies"
    
    id = Column(PostgreSQLUUID(as_uuid=True), primary_key=True, default=uuid4)
    task_id = Column(PostgreSQLUUID(as_uuid=True), ForeignKey("tasks.id", ondelete="CASCADE"), nullable=False)
    dependency_task_id = Column(PostgreSQLUUID(as_uuid=True), ForeignKey("tasks.id", ondelete="CASCADE"), nullable=False)
    dependency_type = Column(String(50), nullable=False, default="finish_to_start")  # finish_to_start, start_to_start, finish_to_finish, start_to_finish
    lag_days = Column(Numeric(5, 2), default=0)
    created_at = Column(DateTime, default=datetime.utcnow)
    
    __table_args__ = (
        UniqueConstraint('task_id', 'dependency_task_id', name='uq_task_dependency'),
    )
    
    # Relationships
    task = relationship("Task", foreign_keys=[task_id], back_populates="dependencies")
    dependency_task = relationship("Task", foreign_keys=[dependency_task_id], back_populates="dependent_on")
