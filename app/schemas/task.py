"""Task schemas."""

from datetime import date, datetime
from decimal import Decimal
from typing import Optional
from uuid import UUID

from pydantic import BaseModel, Field


class TaskDependencyCreate(BaseModel):
    """Create task dependency schema."""
    dependency_task_id: UUID
    dependency_type: str = Field(default="finish_to_start", max_length=50)
    lag_days: Decimal = Field(default=0, ge=0)


class TaskDependencyResponse(TaskDependencyCreate):
    """Task dependency response schema."""
    id: UUID
    task_id: UUID
    created_at: datetime
    
    class Config:
        from_attributes = True


class TaskBase(BaseModel):
    """Base task schema."""
    project_id: UUID
    phase_id: Optional[UUID] = None
    parent_task_id: Optional[UUID] = None
    task_code: str = Field(..., max_length=20)
    name: str = Field(..., max_length=255)
    description: Optional[str] = None
    assignee_id: Optional[UUID] = None
    start_date: Optional[date] = None
    due_date: Optional[date] = None
    estimated_hours: Optional[Decimal] = Field(None, ge=0)
    priority: str = Field(default="medium", max_length=20)


class TaskCreate(TaskBase):
    """Create task schema."""
    dependencies: list[TaskDependencyCreate] = []


class TaskUpdate(BaseModel):
    """Update task schema."""
    name: Optional[str] = Field(None, max_length=255)
    description: Optional[str] = None
    assignee_id: Optional[UUID] = None
    start_date: Optional[date] = None
    due_date: Optional[date] = None
    estimated_hours: Optional[Decimal] = Field(None, ge=0)
    actual_hours: Optional[Decimal] = Field(None, ge=0)
    status: Optional[str] = Field(None, max_length=50)
    priority: Optional[str] = Field(None, max_length=20)
    completion_percentage: Optional[Decimal] = Field(None, ge=0, le=100)


class TaskResponse(TaskBase):
    """Task response schema."""
    id: UUID
    status: str
    completion_date: Optional[date]
    actual_hours: Decimal
    completion_percentage: Decimal
    dependencies: list[TaskDependencyResponse]
    created_at: datetime
    updated_at: datetime
    
    class Config:
        from_attributes = True


class TaskList(BaseModel):
    """Task list response."""
    items: list[TaskResponse]
    total: int
    page: int
    page_size: int
    pages: int
