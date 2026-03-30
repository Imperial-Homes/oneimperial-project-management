"""Timeline and Progress schemas."""

from datetime import date, datetime
from decimal import Decimal
from uuid import UUID

from pydantic import BaseModel, Field

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

    dependency_type: str | None = Field(None, pattern="^(FS|SS|FF|SF)$")
    lag_days: int | None = None
    is_critical: bool | None = None


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
    description: str | None = None
    timeline_type: str = Field(default="master", pattern="^(master|phase|detailed)$")


class ProjectTimelineCreate(ProjectTimelineBase):
    """Create project timeline schema."""

    project_id: UUID


class ProjectTimelineUpdate(BaseModel):
    """Update project timeline schema."""

    name: str | None = Field(None, min_length=1, max_length=255)
    description: str | None = None
    is_active: bool | None = None


class ProjectTimelineResponse(ProjectTimelineBase):
    """Project timeline response schema."""

    id: UUID
    project_id: UUID
    version: int
    is_active: bool
    created_at: datetime
    updated_at: datetime
    dependencies: list[TaskDependencyResponse] = []

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
    earned_value: Decimal | None = None
    planned_value: Decimal | None = None
    actual_cost: Decimal | None = None
    notes: str | None = None


class ProjectProgressCreate(ProjectProgressBase):
    """Create project progress schema."""

    project_id: UUID
    recorded_date: datetime | None = None


class ProjectProgressResponse(ProjectProgressBase):
    """Project progress response schema."""

    id: UUID
    project_id: UUID
    recorded_date: datetime
    schedule_performance_index: Decimal | None = None
    cost_performance_index: Decimal | None = None
    recorded_by: UUID | None = None
    created_at: datetime

    class Config:
        from_attributes = True


class TaskProgressBase(BaseModel):
    """Base task progress schema."""

    completion_percentage: Decimal = Field(..., ge=0, le=100)
    hours_worked: Decimal = Field(default=Decimal("0"), ge=0)
    hours_remaining: Decimal | None = Field(None, ge=0)
    status: str = Field(..., pattern="^(not_started|in_progress|completed|blocked)$")
    blockers: str | None = None
    notes: str | None = None


class TaskProgressCreate(TaskProgressBase):
    """Create task progress schema."""

    task_id: UUID
    recorded_date: datetime | None = None


class TaskProgressUpdate(BaseModel):
    """Update task progress schema."""

    completion_percentage: Decimal | None = Field(None, ge=0, le=100)
    hours_worked: Decimal | None = Field(None, ge=0)
    hours_remaining: Decimal | None = Field(None, ge=0)
    status: str | None = Field(None, pattern="^(not_started|in_progress|completed|blocked)$")
    blockers: str | None = None
    notes: str | None = None


class TaskProgressResponse(TaskProgressBase):
    """Task progress response schema."""

    id: UUID
    task_id: UUID
    recorded_date: datetime
    recorded_by: UUID | None = None
    created_at: datetime

    class Config:
        from_attributes = True


# ============================================================================
# Milestone Schemas
# ============================================================================


class MilestoneBase(BaseModel):
    """Base milestone schema."""

    name: str = Field(..., min_length=1, max_length=255)
    description: str | None = None
    target_date: datetime
    priority: str = Field(default="medium", pattern="^(low|medium|high|critical)$")
    completion_criteria: str | None = None
    deliverables: list[dict] | None = None
    is_critical: bool = False


class MilestoneCreate(MilestoneBase):
    """Create milestone schema."""

    project_id: UUID


class MilestoneUpdate(BaseModel):
    """Update milestone schema."""

    name: str | None = Field(None, min_length=1, max_length=255)
    description: str | None = None
    target_date: datetime | None = None
    actual_date: datetime | None = None
    status: str | None = Field(None, pattern="^(pending|achieved|missed|cancelled)$")
    priority: str | None = Field(None, pattern="^(low|medium|high|critical)$")
    completion_criteria: str | None = None
    deliverables: list[dict] | None = None
    is_critical: bool | None = None


class MilestoneResponse(MilestoneBase):
    """Milestone response schema."""

    id: UUID
    project_id: UUID
    actual_date: datetime | None = None
    status: str
    achieved_by: UUID | None = None
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
    utilization_rate: Decimal | None = None
    efficiency_rate: Decimal | None = None
    idle_hours: Decimal | None = None
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
    dependencies: list[UUID] = []
    is_milestone: bool = False
    is_critical: bool = False
    assigned_resources: list[dict] = []


class GanttChartResponse(BaseModel):
    """Gantt chart response schema."""

    project_id: UUID
    project_name: str
    start_date: date
    end_date: date
    tasks: list[GanttTaskData]
    milestones: list[MilestoneResponse]
    critical_path: list[UUID]
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
