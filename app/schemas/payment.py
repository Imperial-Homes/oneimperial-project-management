"""Payment Certificate schemas."""

from datetime import date, datetime
from decimal import Decimal
from uuid import UUID

from pydantic import BaseModel, Field

from app.models.payment import CertificateStatus, CertificateType


class PaymentCertificateBase(BaseModel):
    """Base payment certificate schema."""

    certificate_date: date
    certificate_type: CertificateType
    gross_amount: Decimal = Field(..., gt=0)
    previous_amount: Decimal = Field(default=Decimal(0), ge=0)
    current_amount: Decimal = Field(..., gt=0)
    retention_percentage: Decimal = Field(default=Decimal(5.0), ge=0, le=100)
    retention_amount: Decimal = Field(default=Decimal(0), ge=0)
    net_amount: Decimal = Field(..., gt=0)
    currency: str = Field(default="GHS", max_length=3)
    period_from: date | None = None
    period_to: date | None = None
    milestone_id: UUID | None = None
    variation_id: UUID | None = None
    description: str | None = None
    work_completed: str | None = None
    notes: str | None = None
    consultant_name: str | None = Field(None, max_length=255)
    contractor_name: str | None = Field(None, max_length=255)
    client_name: str | None = Field(None, max_length=255)
    attachments: str | None = None


class PaymentCertificateCreate(PaymentCertificateBase):
    """Schema for creating a payment certificate."""

    project_id: UUID


class PaymentCertificateUpdate(BaseModel):
    """Schema for updating a payment certificate."""

    certificate_date: date | None = None
    certificate_type: CertificateType | None = None
    status: CertificateStatus | None = None
    gross_amount: Decimal | None = Field(None, gt=0)
    previous_amount: Decimal | None = Field(None, ge=0)
    current_amount: Decimal | None = Field(None, gt=0)
    retention_percentage: Decimal | None = Field(None, ge=0, le=100)
    retention_amount: Decimal | None = Field(None, ge=0)
    net_amount: Decimal | None = Field(None, gt=0)
    currency: str | None = Field(None, max_length=3)
    period_from: date | None = None
    period_to: date | None = None
    milestone_id: UUID | None = None
    variation_id: UUID | None = None
    description: str | None = None
    work_completed: str | None = None
    notes: str | None = None
    consultant_name: str | None = Field(None, max_length=255)
    contractor_name: str | None = Field(None, max_length=255)
    client_name: str | None = Field(None, max_length=255)
    attachments: str | None = None


class ProjectInfo(BaseModel):
    """Basic project info for certificate response."""

    id: UUID
    name: str

    class Config:
        from_attributes = True


class PaymentCertificateResponse(PaymentCertificateBase):
    """Schema for payment certificate response."""

    id: UUID
    certificate_number: str
    project_id: UUID
    project: ProjectInfo | None = None
    status: CertificateStatus
    submitted_date: date | None = None
    submitted_by: UUID | None = None
    approved_date: date | None = None
    approved_by: UUID | None = None
    rejected_date: date | None = None
    rejected_by: UUID | None = None
    rejection_reason: str | None = None
    payment_date: date | None = None
    payment_reference: str | None = None
    amount_paid: Decimal
    created_at: datetime
    created_by: UUID | None = None
    updated_at: datetime
    updated_by: UUID | None = None

    class Config:
        from_attributes = True


class PaymentCertificateList(BaseModel):
    """Schema for paginated payment certificate list."""

    items: list[PaymentCertificateResponse]
    total: int
    page: int
    page_size: int
    pages: int


class PaymentCertificateSubmit(BaseModel):
    """Schema for submitting certificate for approval."""

    notes: str | None = None


class PaymentCertificateApprove(BaseModel):
    """Schema for approving certificate."""

    notes: str | None = None


class PaymentCertificateReject(BaseModel):
    """Schema for rejecting certificate."""

    rejection_reason: str


class PaymentCertificatePayment(BaseModel):
    """Schema for recording payment."""

    payment_date: date
    payment_reference: str | None = Field(None, max_length=100)
    amount_paid: Decimal = Field(..., gt=0)
    notes: str | None = None
