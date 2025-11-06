"""Timeline and Progress schemas."""

from datetime import datetime, date
from decimal import Decimal
from typing import List, Optional
from uuid import UUID

from pydantic import BaseModel, Field, field_validator


# ============================================================================
# Timeline Schemas
# ============================================================================

class TaskDependencyBase(BaseModel):
    """Base task dependency schema."""
    predecessor_task_id: UUID
    successor_task_id: UUID
    dependency_type: str = Field(default="FS", pattern="^(FS|SS|FF|SF)$")
    lag_days: int = 0


class TaskDependencyCreate(TaskDependencyBase):
    """Create task dependency schema."""
    timeline_id: UUID


class TaskDependencyUpdate(BaseModel):
    """Update task dependency schema."""
    dependency_type: Optional[str] = Field(None, pattern="^(FS|SS|FF|SF)$")
    lag_days: Optional[int] = None
    is_critical: Optional[bool] = None


class TaskDependencyResponse(TaskDependencyBase):
    """Task dependency response schema."""
    id: UUID
    timeline_id: UUID
    is_critical: bool
    created_at: datetime

    class Config:
        from_attributes = True


class ProjectTimelineBase(BaseModel):
    """Base project timeline schema."""
    name: str = Field(..., min_length=1, max_length=255)
    description: Optional[str] = None
    timeline_type: str = Field(default="master", pattern="^(master|phase|detailed)$")


class ProjectTimelineCreate(ProjectTimelineBase):
    """Create project timeline schema."""
    project_id: UUID


class ProjectTimelineUpdate(BaseModel):
    """Update project timeline schema."""
    name: Optional[str] = Field(None, min_length=1, max_length=255)
    description: Optional[str] = None
    is_active: Optional[bool] = None


class ProjectTimelineResponse(ProjectTimelineBase):
    """Project timeline response schema."""
    id: UUID
    project_id: UUID
    version: int
    is_active: bool
    created_at: datetime
    updated_at: datetime
    dependencies: List[TaskDependencyResponse] = []

    class Config:
        from_attributes = True


# ============================================================================
# Progress Tracking Schemas
# ============================================================================

class ProjectProgressBase(BaseModel):
    """Base project progress schema."""
    overall_progress: Decimal = Field(..., ge=0, le=100)
    physical_progress: Decimal = Field(default=Decimal("0"), ge=0, le=100)
    financial_progress: Decimal = Field(default=Decimal("0"), ge=0, le=100)
    schedule_variance: Decimal = Decimal("0")
    cost_variance: Decimal = Decimal("0")
    earned_value: Optional[Decimal] = None
    planned_value: Optional[Decimal] = None
    actual_cost: Optional[Decimal] = None
    notes: Optional[str] = None


class ProjectProgressCreate(ProjectProgressBase):
    """Create project progress schema."""
    project_id: UUID
    recorded_date: Optional[datetime] = None


class ProjectProgressResponse(ProjectProgressBase):
    """Project progress response schema."""
    id: UUID
    project_id: UUID
    recorded_date: datetime
    schedule_performance_index: Optional[Decimal] = None
    cost_performance_index: Optional[Decimal] = None
    recorded_by: Optional[UUID] = None
    created_at: datetime

    class Config:
        from_attributes = True


class TaskProgressBase(BaseModel):
    """Base task progress schema."""
    completion_percentage: Decimal = Field(..., ge=0, le=100)
    hours_worked: Decimal = Field(default=Decimal("0"), ge=0)
    hours_remaining: Optional[Decimal] = Field(None, ge=0)
    status: str = Field(..., pattern="^(not_started|in_progress|completed|blocked)$")
    blockers: Optional[str] = None
    notes: Optional[str] = None


class TaskProgressCreate(TaskProgressBase):
    """Create task progress schema."""
    task_id: UUID
    recorded_date: Optional[datetime] = None


class TaskProgressUpdate(BaseModel):
    """Update task progress schema."""
    completion_percentage: Optional[Decimal] = Field(None, ge=0, le=100)
    hours_worked: Optional[Decimal] = Field(None, ge=0)
    hours_remaining: Optional[Decimal] = Field(None, ge=0)
    status: Optional[str] = Field(None, pattern="^(not_started|in_progress|completed|blocked)$")
    blockers: Optional[str] = None
    notes: Optional[str] = None


class TaskProgressResponse(TaskProgressBase):
    """Task progress response schema."""
    id: UUID
    task_id: UUID
    recorded_date: datetime
    recorded_by: Optional[UUID] = None
    created_at: datetime

    class Config:
        from_attributes = True


# ============================================================================
# Milestone Schemas
# ============================================================================

class MilestoneBase(BaseModel):
    """Base milestone schema."""
    name: str = Field(..., min_length=1, max_length=255)
    description: Optional[str] = None
    target_date: datetime
    priority: str = Field(default="medium", pattern="^(low|medium|high|critical)$")
    completion_criteria: Optional[str] = None
    deliverables: Optional[List[dict]] = None
    is_critical: bool = False


class MilestoneCreate(MilestoneBase):
    """Create milestone schema."""
    project_id: UUID


class MilestoneUpdate(BaseModel):
    """Update milestone schema."""
    name: Optional[str] = Field(None, min_length=1, max_length=255)
    description: Optional[str] = None
    target_date: Optional[datetime] = None
    actual_date: Optional[datetime] = None
    status: Optional[str] = Field(None, pattern="^(pending|achieved|missed|cancelled)$")
    priority: Optional[str] = Field(None, pattern="^(low|medium|high|critical)$")
    completion_criteria: Optional[str] = None
    deliverables: Optional[List[dict]] = None
    is_critical: Optional[bool] = None


class MilestoneResponse(MilestoneBase):
    """Milestone response schema."""
    id: UUID
    project_id: UUID
    actual_date: Optional[datetime] = None
    status: str
    achieved_by: Optional[UUID] = None
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


# ============================================================================
# Resource Utilization Schemas
# ============================================================================

class ResourceUtilizationBase(BaseModel):
    """Base resource utilization schema."""
    period_start: datetime
    period_end: datetime
    total_available_hours: Decimal = Field(..., gt=0)
    allocated_hours: Decimal = Field(default=Decimal("0"), ge=0)
    actual_hours_worked: Decimal = Field(default=Decimal("0"), ge=0)
    overtime_hours: Decimal = Field(default=Decimal("0"), ge=0)
    projects_count: int = Field(default=0, ge=0)
    tasks_completed: int = Field(default=0, ge=0)


class ResourceUtilizationCreate(ResourceUtilizationBase):
    """Create resource utilization schema."""
    resource_id: UUID


class ResourceUtilizationResponse(ResourceUtilizationBase):
    """Resource utilization response schema."""
    id: UUID
    resource_id: UUID
    utilization_rate: Optional[Decimal] = None
    efficiency_rate: Optional[Decimal] = None
    idle_hours: Optional[Decimal] = None
    calculated_at: datetime

    class Config:
        from_attributes = True


# ============================================================================
# Gantt Chart Data Schemas
# ============================================================================

class GanttTaskData(BaseModel):
    """Gantt chart task data."""
    id: UUID
    name: str
    start_date: date
    end_date: date
    duration: int  # days
    progress: Decimal  # 0-100
    dependencies: List[UUID] = []
    is_milestone: bool = False
    is_critical: bool = False
    assigned_resources: List[dict] = []


class GanttChartResponse(BaseModel):
    """Gantt chart response schema."""
    project_id: UUID
    project_name: str
    start_date: date
    end_date: date
    tasks: List[GanttTaskData]
    milestones: List[MilestoneResponse]
    critical_path: List[UUID]
    total_duration: int  # days


# ============================================================================
# Progress Summary Schemas
# ============================================================================

class ProgressSummary(BaseModel):
    """Project progress summary."""
    project_id: UUID
    project_name: str
    overall_progress: Decimal
    physical_progress: Decimal
    financial_progress: Decimal
    schedule_status: str  # on_track, ahead, behind
    cost_status: str  # on_budget, under_budget, over_budget
    days_ahead_behind: int
    amount_over_under: Decimal
    milestones_achieved: int
    milestones_pending: int
    milestones_missed: int
    tasks_completed: int
    tasks_in_progress: int
    tasks_not_started: int
    last_updated: datetime


class ResourceUtilizationSummary(BaseModel):
    """Resource utilization summary."""
    resource_id: UUID
    resource_name: str
    resource_type: str
    current_utilization_rate: Decimal
    average_utilization_rate: Decimal
    allocated_hours: Decimal
    available_hours: Decimal
    overtime_hours: Decimal
    active_projects: int
    tasks_assigned: int
    tasks_completed: int
    efficiency_rate: Decimal
