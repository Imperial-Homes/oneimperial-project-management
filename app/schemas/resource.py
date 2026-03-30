"""Resource schemas."""

from datetime import date, datetime
from decimal import Decimal
from uuid import UUID

from pydantic import BaseModel, Field


class ResourceBase(BaseModel):
    """Base resource schema."""

    resource_code: str = Field(..., max_length=20)
    name: str = Field(..., max_length=255)
    description: str | None = None
    resource_type: str = Field(..., max_length=50)
    employee_id: UUID | None = None
    equipment_id: UUID | None = None
    material_id: UUID | None = None
    cost_per_hour: Decimal | None = Field(None, ge=0)
    cost_per_unit: Decimal | None = Field(None, ge=0)
    currency: str = Field(default="GHS", max_length=3)
    availability_status: str = Field(default="available", max_length=50)
    capacity_per_day: Decimal | None = Field(None, ge=0)
    unit_of_measure: str | None = Field(None, max_length=50)


class ResourceCreate(ResourceBase):
    """Create resource schema."""

    pass


class ResourceUpdate(BaseModel):
    """Update resource schema."""

    name: str | None = Field(None, max_length=255)
    description: str | None = None
    cost_per_hour: Decimal | None = Field(None, ge=0)
    cost_per_unit: Decimal | None = Field(None, ge=0)
    availability_status: str | None = Field(None, max_length=50)
    capacity_per_day: Decimal | None = Field(None, ge=0)
    is_active: bool | None = None


class ResourceResponse(ResourceBase):
    """Resource response schema."""

    id: UUID
    is_active: bool
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class ResourceList(BaseModel):
    """Resource list response."""

    items: list[ResourceResponse]
    total: int
    page: int
    page_size: int
    pages: int


class ResourceAssignmentCreate(BaseModel):
    """Create resource assignment schema."""

    resource_id: UUID
    task_id: UUID | None = None
    project_id: UUID
    start_date: date
    end_date: date
    allocation_percentage: Decimal = Field(default=100, ge=0, le=100)
    hours_per_day: Decimal | None = Field(None, ge=0)
    total_hours: Decimal | None = Field(None, ge=0)


class ResourceAssignmentResponse(ResourceAssignmentCreate):
    """Resource assignment response schema."""

    id: UUID
    status: str
    created_at: datetime
    updated_at: datetime
    created_by: UUID | None

    class Config:
        from_attributes = True
