"""Retention Release schemas."""

from datetime import date, datetime
from decimal import Decimal
from uuid import UUID

from pydantic import BaseModel, Field

from app.models.retention import RetentionStatus, RetentionTranche


class RetentionReleaseCreate(BaseModel):
    """Schema for creating a retention release request."""

    project_id: UUID
    tranche: RetentionTranche
    amount_requested: Decimal = Field(..., gt=0)
    currency: str = Field(default="GHS", max_length=10)
    notes: str | None = None
    supporting_docs: str | None = None


class RetentionReleaseUpdate(BaseModel):
    """Schema for updating a draft retention release."""

    tranche: RetentionTranche | None = None
    amount_requested: Decimal | None = Field(None, gt=0)
    currency: str | None = Field(None, max_length=10)
    notes: str | None = None
    supporting_docs: str | None = None


class RetentionReleaseSubmit(BaseModel):
    notes: str | None = None


class RetentionReleaseApprove(BaseModel):
    amount_approved: Decimal = Field(..., gt=0)
    notes: str | None = None


class RetentionReleaseReject(BaseModel):
    rejection_reason: str


class RetentionReleasePayment(BaseModel):
    payment_date: date
    payment_reference: str | None = Field(None, max_length=100)
    notes: str | None = None


class ProjectInfo(BaseModel):
    id: UUID
    name: str

    class Config:
        from_attributes = True


class RetentionReleaseResponse(BaseModel):
    """Full retention release response schema."""

    id: UUID
    release_number: str
    project_id: UUID
    project: ProjectInfo | None = None
    tranche: RetentionTranche
    status: RetentionStatus
    amount_requested: Decimal
    amount_approved: Decimal | None = None
    currency: str
    request_date: date
    approval_date: date | None = None
    payment_date: date | None = None
    requested_by: UUID | None = None
    approved_by: UUID | None = None
    rejected_by: UUID | None = None
    rejection_reason: str | None = None
    notes: str | None = None
    payment_reference: str | None = None
    supporting_docs: str | None = None
    created_at: datetime
    created_by: UUID | None = None
    updated_at: datetime | None = None
    updated_by: UUID | None = None

    class Config:
        from_attributes = True


class RetentionReleaseList(BaseModel):
    items: list[RetentionReleaseResponse]
    total: int
    page: int
    page_size: int
    pages: int


class RetentionSummary(BaseModel):
    """Aggregated retention summary for a project (or all projects)."""

    project_id: UUID | None = None
    total_retention_held: Decimal  # Sum of retention_amount on all paid certs
    total_released: Decimal  # Sum of amount_approved on paid releases
    total_pending: Decimal  # Sum of amount_requested on submitted/approved releases
    balance_retainable: Decimal  # total_held - total_released - total_pending
    practical_completion_released: Decimal
    dlp_end_released: Decimal
    release_count: int
