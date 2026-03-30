"""Schemas for Handover Pack."""

import uuid
from datetime import datetime
from decimal import Decimal

from pydantic import BaseModel


class HandoverPackBase(BaseModel):
    property_name: str
    property_id: uuid.UUID | None = None
    apartment_number: str | None = None
    site_location: str | None = None
    client_name: str
    client_id: uuid.UUID | None = None
    client_email: str | None = None
    client_phone: str | None = None
    sinking_fund_invoiced: bool | None = False
    sinking_fund_amount: Decimal | None = None
    transfer_document_invoiced: bool | None = False
    transfer_document_amount: Decimal | None = None
    hoa_forms_completed: bool | None = False
    facility_manager_info_provided: bool | None = False
    all_payments_made: bool | None = False
    payments_date: datetime | None = None
    handover_pack_drafted: bool | None = False
    handover_pack_url: str | None = None
    doa_approved: bool | None = False
    doa_approved_date: datetime | None = None
    client_signed: bool | None = False
    client_signed_date: datetime | None = None
    keys_handed_over: bool | None = False
    handover_date: datetime | None = None
    letter_to_client: str | None = None
    notes: str | None = None
    issues_noted: str | None = None
    status: str | None = "initiated"
    handled_by: str | None = None
    handled_by_id: uuid.UUID | None = None


class HandoverPackCreate(HandoverPackBase):
    pass


class HandoverPackUpdate(BaseModel):
    property_name: str | None = None
    apartment_number: str | None = None
    site_location: str | None = None
    client_name: str | None = None
    client_email: str | None = None
    client_phone: str | None = None
    sinking_fund_invoiced: bool | None = None
    sinking_fund_amount: Decimal | None = None
    transfer_document_invoiced: bool | None = None
    transfer_document_amount: Decimal | None = None
    hoa_forms_completed: bool | None = None
    facility_manager_info_provided: bool | None = None
    all_payments_made: bool | None = None
    payments_date: datetime | None = None
    handover_pack_drafted: bool | None = None
    handover_pack_url: str | None = None
    doa_approved: bool | None = None
    doa_approved_date: datetime | None = None
    client_signed: bool | None = None
    client_signed_date: datetime | None = None
    keys_handed_over: bool | None = None
    handover_date: datetime | None = None
    letter_to_client: str | None = None
    notes: str | None = None
    issues_noted: str | None = None
    status: str | None = None


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
