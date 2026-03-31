"""Project schemas."""

from datetime import date, datetime
from decimal import Decimal
from uuid import UUID

from pydantic import BaseModel, Field


class ProjectPhaseCreate(BaseModel):
    """Create project phase schema."""

    name: str = Field(..., max_length=100)
    description: str | None = None
    sequence_number: int = Field(..., ge=1)
    start_date: date | None = None
    end_date: date | None = None


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
    description: str | None = None
    project_type: str = Field(..., max_length=100)
    client_id: UUID | None = None
    start_date: date | None = None
    target_end_date: date | None = None
    priority: str = Field(default="medium", max_length=20)
    budget: Decimal | None = Field(None, ge=0)
    currency: str = Field(default="GHS", max_length=10)
    manager_id: UUID | None = None
    location: str | None = Field(None, max_length=255)


class ProjectCreate(ProjectBase):
    """Create project schema."""

    phases: list[ProjectPhaseCreate] = []


class ProjectUpdate(BaseModel):
    """Update project schema."""

    name: str | None = Field(None, max_length=255)
    description: str | None = None
    project_type: str | None = Field(None, max_length=100)
    target_end_date: date | None = None
    status: str | None = Field(None, max_length=50)
    priority: str | None = Field(None, max_length=20)
    budget: Decimal | None = Field(None, ge=0)
    manager_id: UUID | None = None
    location: str | None = Field(None, max_length=255)
    is_active: bool | None = None


class ProjectResponse(ProjectBase):
    """Project response schema."""

    id: UUID
    status: str
    actual_end_date: date | None
    is_active: bool
    phases: list[ProjectPhaseResponse]
    created_at: datetime
    created_by: UUID | None
    updated_at: datetime
    updated_by: UUID | None

    class Config:
        from_attributes = True


class ProjectList(BaseModel):
    """Project list response."""

    items: list[ProjectResponse]
    total: int
    page: int
    page_size: int
    pages: int
