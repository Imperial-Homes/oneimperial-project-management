"""Project Variation schemas."""

from datetime import date, datetime
from decimal import Decimal
from typing import Optional
from uuid import UUID

from pydantic import BaseModel, Field

from app.models.variation import VariationType, VariationStatus


class VariationBase(BaseModel):
    """Base variation schema."""
    title: str = Field(..., min_length=1, max_length=255)
    description: str = Field(..., min_length=1)
    variation_type: VariationType
    requested_by: UUID
    requested_date: date = Field(default_factory=date.today)
    variation_amount: Decimal = Field(..., ge=0)
    original_amount: Decimal = Field(default=0, ge=0)
    new_total_amount: Optional[Decimal] = Field(None, ge=0)
    currency: str = Field(default="GHS", max_length=3)
    impact_on_timeline: int = Field(default=0)
    original_completion_date: Optional[date] = None
    new_completion_date: Optional[date] = None
    justification: Optional[str] = None
    impact_assessment: Optional[str] = None
    attachments: Optional[str] = None
    phase_id: Optional[UUID] = None
    task_id: Optional[UUID] = None
    priority: str = Field(default="medium", max_length=20)


class VariationCreate(VariationBase):
    """Schema for creating a variation."""
    project_id: UUID


class VariationUpdate(BaseModel):
    """Schema for updating a variation."""
    title: Optional[str] = Field(None, min_length=1, max_length=255)
    description: Optional[str] = Field(None, min_length=1)
    variation_type: Optional[VariationType] = None
    status: Optional[VariationStatus] = None
    requested_date: Optional[date] = None
    variation_amount: Optional[Decimal] = Field(None, ge=0)
    original_amount: Optional[Decimal] = Field(None, ge=0)
    new_total_amount: Optional[Decimal] = Field(None, ge=0)
    currency: Optional[str] = Field(None, max_length=3)
    impact_on_timeline: Optional[int] = None
    original_completion_date: Optional[date] = None
    new_completion_date: Optional[date] = None
    justification: Optional[str] = None
    impact_assessment: Optional[str] = None
    attachments: Optional[str] = None
    priority: Optional[str] = Field(None, max_length=20)


class VariationResponse(VariationBase):
    """Schema for variation response."""
    id: UUID
    variation_number: str
    project_id: UUID
    status: VariationStatus
    approved_by: Optional[UUID] = None
    approved_date: Optional[date] = None
    rejection_reason: Optional[str] = None
    is_active: bool
    created_at: datetime
    created_by: Optional[UUID] = None
    updated_at: datetime
    updated_by: Optional[UUID] = None
    
    class Config:
        from_attributes = True


class VariationList(BaseModel):
    """Schema for paginated variation list."""
    items: list[VariationResponse]
    total: int
    page: int
    page_size: int
    pages: int


class VariationApproval(BaseModel):
    """Schema for approving/rejecting variation."""
    approved: bool
    notes: Optional[str] = None
