"""Resource schemas."""

from datetime import date, datetime
from decimal import Decimal
from typing import Optional
from uuid import UUID

from pydantic import BaseModel, Field


class ResourceBase(BaseModel):
    """Base resource schema."""
    resource_code: str = Field(..., max_length=20)
    name: str = Field(..., max_length=255)
    description: Optional[str] = None
    resource_type: str = Field(..., max_length=50)
    employee_id: Optional[UUID] = None
    equipment_id: Optional[UUID] = None
    material_id: Optional[UUID] = None
    cost_per_hour: Optional[Decimal] = Field(None, ge=0)
    cost_per_unit: Optional[Decimal] = Field(None, ge=0)
    currency: str = Field(default="GHS", max_length=3)
    availability_status: str = Field(default="available", max_length=50)
    capacity_per_day: Optional[Decimal] = Field(None, ge=0)
    unit_of_measure: Optional[str] = Field(None, max_length=50)


class ResourceCreate(ResourceBase):
    """Create resource schema."""
    pass


class ResourceUpdate(BaseModel):
    """Update resource schema."""
    name: Optional[str] = Field(None, max_length=255)
    description: Optional[str] = None
    cost_per_hour: Optional[Decimal] = Field(None, ge=0)
    cost_per_unit: Optional[Decimal] = Field(None, ge=0)
    availability_status: Optional[str] = Field(None, max_length=50)
    capacity_per_day: Optional[Decimal] = Field(None, ge=0)
    is_active: Optional[bool] = None


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
    task_id: Optional[UUID] = None
    project_id: UUID
    start_date: date
    end_date: date
    allocation_percentage: Decimal = Field(default=100, ge=0, le=100)
    hours_per_day: Optional[Decimal] = Field(None, ge=0)
    total_hours: Optional[Decimal] = Field(None, ge=0)


class ResourceAssignmentResponse(ResourceAssignmentCreate):
    """Resource assignment response schema."""
    id: UUID
    status: str
    created_at: datetime
    updated_at: datetime
    created_by: Optional[UUID]
    
    class Config:
        from_attributes = True
