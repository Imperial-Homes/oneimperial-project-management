"""Project schemas."""

from datetime import date, datetime
from decimal import Decimal
from typing import Optional
from uuid import UUID

from pydantic import BaseModel, Field


class ProjectPhaseCreate(BaseModel):
    """Create project phase schema."""
    name: str = Field(..., max_length=100)
    description: Optional[str] = None
    sequence_number: int = Field(..., ge=1)
    start_date: Optional[date] = None
    end_date: Optional[date] = None


class ProjectPhaseResponse(ProjectPhaseCreate):
    """Project phase response schema."""
    id: UUID
    project_id: UUID
    status: str
    completion_percentage: Decimal
    created_at: datetime
    updated_at: datetime
    
    class Config:
        from_attributes = True


class ProjectBase(BaseModel):
    """Base project schema."""
    project_code: str = Field(..., max_length=20)
    name: str = Field(..., max_length=255)
    description: Optional[str] = None
    project_type: str = Field(..., max_length=100)
    client_id: Optional[UUID] = None
    start_date: Optional[date] = None
    target_end_date: Optional[date] = None
    priority: str = Field(default="medium", max_length=20)
    budget: Optional[Decimal] = Field(None, ge=0)
    currency: str = Field(default="GHS", max_length=3)
    manager_id: Optional[UUID] = None
    location: Optional[str] = Field(None, max_length=255)


class ProjectCreate(ProjectBase):
    """Create project schema."""
    phases: list[ProjectPhaseCreate] = []


class ProjectUpdate(BaseModel):
    """Update project schema."""
    name: Optional[str] = Field(None, max_length=255)
    description: Optional[str] = None
    project_type: Optional[str] = Field(None, max_length=100)
    target_end_date: Optional[date] = None
    status: Optional[str] = Field(None, max_length=50)
    priority: Optional[str] = Field(None, max_length=20)
    budget: Optional[Decimal] = Field(None, ge=0)
    manager_id: Optional[UUID] = None
    location: Optional[str] = Field(None, max_length=255)
    is_active: Optional[bool] = None


class ProjectResponse(ProjectBase):
    """Project response schema."""
    id: UUID
    status: str
    actual_end_date: Optional[date]
    is_active: bool
    phases: list[ProjectPhaseResponse]
    created_at: datetime
    created_by: Optional[UUID]
    updated_at: datetime
    updated_by: Optional[UUID]
    
    class Config:
        from_attributes = True


class ProjectList(BaseModel):
    """Project list response."""
    items: list[ProjectResponse]
    total: int
    page: int
    page_size: int
    pages: int
