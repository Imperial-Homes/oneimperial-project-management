"""Schemas for Handover Pack."""

from pydantic import BaseModel
from typing import Optional
from datetime import datetime
from decimal import Decimal
import uuid


class HandoverPackBase(BaseModel):
    property_name: str
    property_id: Optional[uuid.UUID] = None
    apartment_number: Optional[str] = None
    site_location: Optional[str] = None
    client_name: str
    client_id: Optional[uuid.UUID] = None
    client_email: Optional[str] = None
    client_phone: Optional[str] = None
    sinking_fund_invoiced: Optional[bool] = False
    sinking_fund_amount: Optional[Decimal] = None
    transfer_document_invoiced: Optional[bool] = False
    transfer_document_amount: Optional[Decimal] = None
    hoa_forms_completed: Optional[bool] = False
    facility_manager_info_provided: Optional[bool] = False
    all_payments_made: Optional[bool] = False
    payments_date: Optional[datetime] = None
    handover_pack_drafted: Optional[bool] = False
    handover_pack_url: Optional[str] = None
    doa_approved: Optional[bool] = False
    doa_approved_date: Optional[datetime] = None
    client_signed: Optional[bool] = False
    client_signed_date: Optional[datetime] = None
    keys_handed_over: Optional[bool] = False
    handover_date: Optional[datetime] = None
    letter_to_client: Optional[str] = None
    notes: Optional[str] = None
    issues_noted: Optional[str] = None
    status: Optional[str] = "initiated"
    handled_by: Optional[str] = None
    handled_by_id: Optional[uuid.UUID] = None


class HandoverPackCreate(HandoverPackBase):
    pass


class HandoverPackUpdate(BaseModel):
    property_name: Optional[str] = None
    apartment_number: Optional[str] = None
    site_location: Optional[str] = None
    client_name: Optional[str] = None
    client_email: Optional[str] = None
    client_phone: Optional[str] = None
    sinking_fund_invoiced: Optional[bool] = None
    sinking_fund_amount: Optional[Decimal] = None
    transfer_document_invoiced: Optional[bool] = None
    transfer_document_amount: Optional[Decimal] = None
    hoa_forms_completed: Optional[bool] = None
    facility_manager_info_provided: Optional[bool] = None
    all_payments_made: Optional[bool] = None
    payments_date: Optional[datetime] = None
    handover_pack_drafted: Optional[bool] = None
    handover_pack_url: Optional[str] = None
    doa_approved: Optional[bool] = None
    doa_approved_date: Optional[datetime] = None
    client_signed: Optional[bool] = None
    client_signed_date: Optional[datetime] = None
    keys_handed_over: Optional[bool] = None
    handover_date: Optional[datetime] = None
    letter_to_client: Optional[str] = None
    notes: Optional[str] = None
    issues_noted: Optional[str] = None
    status: Optional[str] = None


class HandoverPackResponse(HandoverPackBase):
    id: uuid.UUID
    handover_id: str
    is_active: bool
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}


class HandoverPackList(BaseModel):
    items: list[HandoverPackResponse]
    total: int
    page: int
    page_size: int
    pages: int


class HandoverPackStats(BaseModel):
    total: int
    initiated: int
    obligations_pending: int
    pack_drafted: int
    doa_review: int
    client_signoff: int
    completed: int
