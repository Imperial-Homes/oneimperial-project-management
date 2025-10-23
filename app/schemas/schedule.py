"""Schedule and Milestone schemas."""

from datetime import date, datetime
from typing import Optional
from uuid import UUID

from pydantic import BaseModel, Field


class ProjectScheduleCreate(BaseModel):
    """Create project schedule schema."""
    project_id: UUID
    version: int = Field(default=1, ge=1)
    is_baseline: bool = False
    start_date: date
    end_date: date
    notes: Optional[str] = None


class ProjectScheduleResponse(ProjectScheduleCreate):
    """Project schedule response schema."""
    id: UUID
    created_at: datetime
    created_by: Optional[UUID]
    
    class Config:
        from_attributes = True


class MilestoneBase(BaseModel):
    """Base milestone schema."""
    name: str = Field(..., max_length=255)
    description: Optional[str] = None
    due_date: date
    priority: str = Field(default="medium", max_length=20)


class MilestoneCreate(MilestoneBase):
    """Create milestone schema."""
    project_id: UUID


class MilestoneUpdate(BaseModel):
    """Update milestone schema."""
    name: Optional[str] = Field(None, max_length=255)
    description: Optional[str] = None
    due_date: Optional[date] = None
    completion_date: Optional[date] = None
    status: Optional[str] = Field(None, max_length=50)
    priority: Optional[str] = Field(None, max_length=20)


class MilestoneResponse(MilestoneBase):
    """Milestone response schema."""
    id: UUID
    project_id: UUID
    completion_date: Optional[date]
    status: str
    created_at: datetime
    updated_at: datetime
    
    class Config:
        from_attributes = True
