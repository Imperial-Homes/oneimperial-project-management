"""Payment Certificate schemas."""

from datetime import date, datetime
from decimal import Decimal
from typing import Optional
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
    period_from: Optional[date] = None
    period_to: Optional[date] = None
    milestone_id: Optional[UUID] = None
    variation_id: Optional[UUID] = None
    description: Optional[str] = None
    work_completed: Optional[str] = None
    notes: Optional[str] = None
    consultant_name: Optional[str] = Field(None, max_length=255)
    contractor_name: Optional[str] = Field(None, max_length=255)
    client_name: Optional[str] = Field(None, max_length=255)
    attachments: Optional[str] = None


class PaymentCertificateCreate(PaymentCertificateBase):
    """Schema for creating a payment certificate."""
    project_id: UUID


class PaymentCertificateUpdate(BaseModel):
    """Schema for updating a payment certificate."""
    certificate_date: Optional[date] = None
    certificate_type: Optional[CertificateType] = None
    status: Optional[CertificateStatus] = None
    gross_amount: Optional[Decimal] = Field(None, gt=0)
    previous_amount: Optional[Decimal] = Field(None, ge=0)
    current_amount: Optional[Decimal] = Field(None, gt=0)
    retention_percentage: Optional[Decimal] = Field(None, ge=0, le=100)
    retention_amount: Optional[Decimal] = Field(None, ge=0)
    net_amount: Optional[Decimal] = Field(None, gt=0)
    currency: Optional[str] = Field(None, max_length=3)
    period_from: Optional[date] = None
    period_to: Optional[date] = None
    milestone_id: Optional[UUID] = None
    variation_id: Optional[UUID] = None
    description: Optional[str] = None
    work_completed: Optional[str] = None
    notes: Optional[str] = None
    consultant_name: Optional[str] = Field(None, max_length=255)
    contractor_name: Optional[str] = Field(None, max_length=255)
    client_name: Optional[str] = Field(None, max_length=255)
    attachments: Optional[str] = None


class PaymentCertificateResponse(PaymentCertificateBase):
    """Schema for payment certificate response."""
    id: UUID
    certificate_number: str
    project_id: UUID
    status: CertificateStatus
    submitted_date: Optional[date] = None
    submitted_by: Optional[UUID] = None
    approved_date: Optional[date] = None
    approved_by: Optional[UUID] = None
    rejected_date: Optional[date] = None
    rejected_by: Optional[UUID] = None
    rejection_reason: Optional[str] = None
    payment_date: Optional[date] = None
    payment_reference: Optional[str] = None
    amount_paid: Decimal
    created_at: datetime
    created_by: Optional[UUID] = None
    updated_at: datetime
    updated_by: Optional[UUID] = None
    
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
    notes: Optional[str] = None


class PaymentCertificateApprove(BaseModel):
    """Schema for approving certificate."""
    notes: Optional[str] = None


class PaymentCertificateReject(BaseModel):
    """Schema for rejecting certificate."""
    rejection_reason: str


class PaymentCertificatePayment(BaseModel):
    """Schema for recording payment."""
    payment_date: date
    payment_reference: Optional[str] = Field(None, max_length=100)
    amount_paid: Decimal = Field(..., gt=0)
    notes: Optional[str] = None
