"""Project Payment schemas."""

from datetime import date, datetime
from decimal import Decimal
from typing import Optional
from uuid import UUID

from pydantic import BaseModel, Field

from app.models.payment import PaymentMethod, PaymentType, PaymentStatus


class PaymentBase(BaseModel):
    """Base payment schema."""
    payment_date: date
    amount: Decimal = Field(..., gt=0)
    currency: str = Field(default="GHS", max_length=3)
    payment_method: PaymentMethod
    payment_type: PaymentType
    milestone_id: Optional[UUID] = None
    variation_id: Optional[UUID] = None
    invoice_reference: Optional[str] = Field(None, max_length=100)
    reference_number: Optional[str] = Field(None, max_length=100)
    transaction_id: Optional[str] = Field(None, max_length=100)
    description: Optional[str] = None
    notes: Optional[str] = None
    paid_by: Optional[UUID] = None
    paid_by_name: Optional[str] = Field(None, max_length=255)
    received_by: Optional[UUID] = None
    received_by_name: Optional[str] = Field(None, max_length=255)
    receipt_url: Optional[str] = Field(None, max_length=500)
    attachments: Optional[str] = None
    bank_name: Optional[str] = Field(None, max_length=255)
    account_number: Optional[str] = Field(None, max_length=100)


class PaymentCreate(PaymentBase):
    """Schema for creating a payment."""
    project_id: UUID


class PaymentUpdate(BaseModel):
    """Schema for updating a payment."""
    payment_date: Optional[date] = None
    amount: Optional[Decimal] = Field(None, gt=0)
    currency: Optional[str] = Field(None, max_length=3)
    payment_method: Optional[PaymentMethod] = None
    payment_type: Optional[PaymentType] = None
    status: Optional[PaymentStatus] = None
    milestone_id: Optional[UUID] = None
    variation_id: Optional[UUID] = None
    invoice_reference: Optional[str] = Field(None, max_length=100)
    reference_number: Optional[str] = Field(None, max_length=100)
    transaction_id: Optional[str] = Field(None, max_length=100)
    description: Optional[str] = None
    notes: Optional[str] = None
    paid_by_name: Optional[str] = Field(None, max_length=255)
    received_by_name: Optional[str] = Field(None, max_length=255)
    receipt_url: Optional[str] = Field(None, max_length=500)
    attachments: Optional[str] = None
    bank_name: Optional[str] = Field(None, max_length=255)
    account_number: Optional[str] = Field(None, max_length=100)


class PaymentResponse(PaymentBase):
    """Schema for payment response."""
    id: UUID
    payment_number: str
    project_id: UUID
    status: PaymentStatus
    is_reconciled: bool
    reconciled_date: Optional[date] = None
    reconciled_by: Optional[UUID] = None
    created_at: datetime
    created_by: Optional[UUID] = None
    updated_at: datetime
    updated_by: Optional[UUID] = None
    
    class Config:
        from_attributes = True


class PaymentList(BaseModel):
    """Schema for paginated payment list."""
    items: list[PaymentResponse]
    total: int
    page: int
    page_size: int
    pages: int


class PaymentReconcile(BaseModel):
    """Schema for reconciling payment."""
    notes: Optional[str] = None
