"""Project Variation schemas."""

from datetime import date, datetime
from decimal import Decimal
from uuid import UUID

from pydantic import BaseModel, Field

from app.models.variation import VariationStatus, VariationType


class VariationBase(BaseModel):
    """Base variation schema."""

    title: str = Field(..., min_length=1, max_length=255)
    description: str = Field(..., min_length=1)
    variation_type: VariationType
    requested_by: UUID
    requested_date: date = Field(default_factory=date.today)
    variation_amount: Decimal = Field(..., ge=0)
    original_amount: Decimal = Field(default=0, ge=0)
    new_total_amount: Decimal | None = Field(None, ge=0)
    currency: str = Field(default="GHS", max_length=10)
    impact_on_timeline: int = Field(default=0)
    original_completion_date: date | None = None
    new_completion_date: date | None = None
    justification: str | None = None
    impact_assessment: str | None = None
    attachments: str | None = None
    phase_id: UUID | None = None
    task_id: UUID | None = None
    priority: str = Field(default="medium", max_length=20)


class VariationCreate(VariationBase):
    """Schema for creating a variation."""

    project_id: UUID


class VariationUpdate(BaseModel):
    """Schema for updating a variation."""

    title: str | None = Field(None, min_length=1, max_length=255)
    description: str | None = Field(None, min_length=1)
    variation_type: VariationType | None = None
    status: VariationStatus | None = None
    requested_date: date | None = None
    variation_amount: Decimal | None = Field(None, ge=0)
    original_amount: Decimal | None = Field(None, ge=0)
    new_total_amount: Decimal | None = Field(None, ge=0)
    currency: str | None = Field(None, max_length=10)
    impact_on_timeline: int | None = None
    original_completion_date: date | None = None
    new_completion_date: date | None = None
    justification: str | None = None
    impact_assessment: str | None = None
    attachments: str | None = None
    priority: str | None = Field(None, max_length=20)


class VariationResponse(VariationBase):
    """Schema for variation response."""

    id: UUID
    variation_number: str
    project_id: UUID
    status: VariationStatus
    approved_by: UUID | None = None
    approved_date: date | None = None
    rejection_reason: str | None = None
    is_active: bool
    created_at: datetime
    created_by: UUID | None = None
    updated_at: datetime
    updated_by: UUID | None = None

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
    notes: str | None = None
