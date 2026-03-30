"""Timeline and Progress Tracking models."""

from datetime import datetime
from uuid import uuid4

from sqlalchemy import JSON, Boolean, Column, DateTime, ForeignKey, Integer, Numeric, String, Text
from sqlalchemy.dialects.postgresql import UUID as PostgreSQLUUID
from sqlalchemy.orm import relationship

from app.database import Base


class ProjectTimeline(Base):
    """Project Timeline model for Gantt chart data."""

    __tablename__ = "project_timelines"

    id = Column(PostgreSQLUUID(as_uuid=True), primary_key=True, default=uuid4)
    project_id = Column(
        PostgreSQLUUID(as_uuid=True), ForeignKey("projects.id", ondelete="CASCADE"), nullable=False, index=True
    )
    name = Column(String(255), nullable=False)
    description = Column(Text)
    timeline_type = Column(String(50), nullable=False, default="master")  # master, phase, detailed
    version = Column(Integer, default=1)
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    created_by = Column(PostgreSQLUUID(as_uuid=True))
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    updated_by = Column(PostgreSQLUUID(as_uuid=True))

    # Relationships
    project = relationship("Project", backref="timelines")
    dependencies = relationship("TimelineTaskDependency", back_populates="timeline", cascade="all, delete-orphan")
    milestones = relationship("TimelineMilestone", back_populates="timeline", cascade="all, delete-orphan")


class TimelineTaskDependency(Base):
    """Task dependency model for critical path calculation."""

    __tablename__ = "timeline_task_dependencies"

    id = Column(PostgreSQLUUID(as_uuid=True), primary_key=True, default=uuid4)
    timeline_id = Column(
        PostgreSQLUUID(as_uuid=True), ForeignKey("project_timelines.id", ondelete="CASCADE"), nullable=False
    )
    predecessor_task_id = Column(
        PostgreSQLUUID(as_uuid=True), ForeignKey("tasks.id", ondelete="CASCADE"), nullable=False
    )
    successor_task_id = Column(PostgreSQLUUID(as_uuid=True), ForeignKey("tasks.id", ondelete="CASCADE"), nullable=False)
    dependency_type = Column(
        String(20), nullable=False, default="FS"
    )  # FS (Finish-to-Start), SS (Start-to-Start), FF (Finish-to-Finish), SF (Start-to-Finish)
    lag_days = Column(Integer, default=0)  # Positive for delay, negative for lead time
    is_critical = Column(Boolean, default=False)  # Part of critical path
    created_at = Column(DateTime, default=datetime.utcnow)

    # Relationships
    timeline = relationship("ProjectTimeline", back_populates="dependencies")
    predecessor = relationship("Task", foreign_keys=[predecessor_task_id], backref="successor_dependencies")
    successor = relationship("Task", foreign_keys=[successor_task_id], backref="predecessor_dependencies")


class ProjectProgress(Base):
    """Project progress tracking model."""

    __tablename__ = "project_progress"

    id = Column(PostgreSQLUUID(as_uuid=True), primary_key=True, default=uuid4)
    project_id = Column(
        PostgreSQLUUID(as_uuid=True), ForeignKey("projects.id", ondelete="CASCADE"), nullable=False, index=True
    )
    recorded_date = Column(DateTime, nullable=False, default=datetime.utcnow, index=True)
    overall_progress = Column(Numeric(5, 2), nullable=False, default=0)  # 0-100%
    physical_progress = Column(Numeric(5, 2), default=0)  # Actual work completed
    financial_progress = Column(Numeric(5, 2), default=0)  # Budget spent
    schedule_variance = Column(Numeric(10, 2), default=0)  # Days ahead/behind schedule
    cost_variance = Column(Numeric(15, 2), default=0)  # Amount over/under budget
    earned_value = Column(Numeric(15, 2))  # EV = % Complete × Budget
    planned_value = Column(Numeric(15, 2))  # PV = Planned % × Budget
    actual_cost = Column(Numeric(15, 2))  # AC = Actual spending
    schedule_performance_index = Column(Numeric(5, 2))  # SPI = EV / PV
    cost_performance_index = Column(Numeric(5, 2))  # CPI = EV / AC
    notes = Column(Text)
    recorded_by = Column(PostgreSQLUUID(as_uuid=True))
    created_at = Column(DateTime, default=datetime.utcnow)

    # Relationships
    project = relationship("Project", backref="progress_history")


class TaskProgress(Base):
    """Task-level progress tracking."""

    __tablename__ = "task_progress"

    id = Column(PostgreSQLUUID(as_uuid=True), primary_key=True, default=uuid4)
    task_id = Column(
        PostgreSQLUUID(as_uuid=True), ForeignKey("tasks.id", ondelete="CASCADE"), nullable=False, index=True
    )
    recorded_date = Column(DateTime, nullable=False, default=datetime.utcnow, index=True)
    completion_percentage = Column(Numeric(5, 2), nullable=False, default=0)  # 0-100%
    hours_worked = Column(Numeric(10, 2), default=0)
    hours_remaining = Column(Numeric(10, 2))
    status = Column(String(50), nullable=False)  # not_started, in_progress, completed, blocked
    blockers = Column(Text)  # Description of any blockers
    notes = Column(Text)
    recorded_by = Column(PostgreSQLUUID(as_uuid=True))
    created_at = Column(DateTime, default=datetime.utcnow)

    # Relationships
    task = relationship("Task", backref="progress_history")


class TimelineMilestone(Base):
    """Project milestone model."""

    __tablename__ = "timeline_milestones"

    id = Column(PostgreSQLUUID(as_uuid=True), primary_key=True, default=uuid4)
    timeline_id = Column(
        PostgreSQLUUID(as_uuid=True), ForeignKey("project_timelines.id", ondelete="CASCADE"), nullable=True, index=True
    )
    project_id = Column(
        PostgreSQLUUID(as_uuid=True), ForeignKey("projects.id", ondelete="CASCADE"), nullable=False, index=True
    )
    name = Column(String(255), nullable=False)
    description = Column(Text)
    target_date = Column(DateTime, nullable=False, index=True)
    actual_date = Column(DateTime)
    status = Column(String(50), nullable=False, default="pending")  # pending, achieved, missed, cancelled
    priority = Column(String(20), default="medium")  # low, medium, high, critical
    completion_criteria = Column(Text)
    deliverables = Column(JSON)  # List of deliverables
    is_critical = Column(Boolean, default=False)
    achieved_by = Column(PostgreSQLUUID(as_uuid=True))
    created_at = Column(DateTime, default=datetime.utcnow)
    created_by = Column(PostgreSQLUUID(as_uuid=True))
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relationships
    timeline = relationship("ProjectTimeline", back_populates="milestones")
    project = relationship("Project", backref="timeline_milestones")


class ResourceUtilization(Base):
    """Resource utilization tracking model."""

    __tablename__ = "resource_utilization"

    id = Column(PostgreSQLUUID(as_uuid=True), primary_key=True, default=uuid4)
    resource_id = Column(
        PostgreSQLUUID(as_uuid=True), ForeignKey("resources.id", ondelete="CASCADE"), nullable=False, index=True
    )
    period_start = Column(DateTime, nullable=False, index=True)
    period_end = Column(DateTime, nullable=False, index=True)
    total_available_hours = Column(Numeric(10, 2), nullable=False)
    allocated_hours = Column(Numeric(10, 2), default=0)
    actual_hours_worked = Column(Numeric(10, 2), default=0)
    utilization_rate = Column(Numeric(5, 2))  # (allocated_hours / available_hours) * 100
    efficiency_rate = Column(Numeric(5, 2))  # (actual_hours / allocated_hours) * 100
    overtime_hours = Column(Numeric(10, 2), default=0)
    idle_hours = Column(Numeric(10, 2))  # available - allocated
    projects_count = Column(Integer, default=0)
    tasks_completed = Column(Integer, default=0)
    calculated_at = Column(DateTime, default=datetime.utcnow)

    # Relationships
    resource = relationship("Resource", backref="utilization_history")
