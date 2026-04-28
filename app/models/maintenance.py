"""Maintenance models — payments, budgets, service fees, rental schedule imports."""

import uuid
from datetime import datetime

from sqlalchemy import Boolean, Column, Date, DateTime, Numeric, String, Text
from sqlalchemy.dialects.postgresql import UUID

from app.database import Base


class MaintenancePayment(Base):
    __tablename__ = "maintenance_payments"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    payment_reference = Column(String(100), unique=True, nullable=False, index=True)
    payment_type = Column(String(50), nullable=False)  # rental | service_fee
    project = Column(String(255), nullable=False)
    block = Column(String(100))
    unit = Column(String(100), nullable=False)
    payer_name = Column(String(255), nullable=False)
    payer_contact = Column(String(255))
    amount = Column(Numeric(15, 2), nullable=False)
    currency = Column(String(10), default="GHS")
    payment_date = Column(Date, nullable=False)
    payment_method = Column(String(50))  # cash | bank_transfer | cheque | mobile_money | card
    bank_name = Column(String(255))
    cheque_number = Column(String(100))
    received_by = Column(String(255))
    description = Column(String(500))
    notes = Column(Text)
    status = Column(String(50), default="completed")  # completed | pending | partial | reversed
    created_by = Column(UUID(as_uuid=True))
    created_at = Column(DateTime(timezone=True), default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime(timezone=True), default=datetime.utcnow, onupdate=datetime.utcnow)


class MaintenanceBudget(Base):
    __tablename__ = "maintenance_budgets"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    budget_reference = Column(String(100), unique=True, nullable=False, index=True)
    title = Column(String(255), nullable=False)
    project_id = Column(UUID(as_uuid=True))   # optional link to a PM project
    project_name = Column(String(255))
    category = Column(String(100))  # Routine | Corrective | Emergency | Preventative
    total_amount = Column(Numeric(15, 2), nullable=False)
    paid_amount = Column(Numeric(15, 2), default=0)
    currency = Column(String(10), default="GHS")
    start_date = Column(Date)
    end_date = Column(Date)
    status = Column(String(50), default="pending_approval")  # pending_approval | approved | rejected | completed
    notes = Column(Text)
    created_by = Column(UUID(as_uuid=True))
    created_by_name = Column(String(255))
    created_at = Column(DateTime(timezone=True), default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime(timezone=True), default=datetime.utcnow, onupdate=datetime.utcnow)


class MaintenanceServiceFee(Base):
    __tablename__ = "maintenance_service_fees"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    project = Column(String(255), nullable=False)
    block = Column(String(100))
    unit = Column(String(100), nullable=False)
    owner_name = Column(String(255), nullable=False)
    owner_contact = Column(String(255))
    fee_type = Column(String(100))
    amount = Column(Numeric(15, 2), nullable=False)
    currency = Column(String(10), default="GHS")
    billing_period = Column(String(100))
    due_date = Column(Date)
    status = Column(String(50), default="pending")  # pending | paid | overdue | waived
    payment_date = Column(Date)
    receipt_number = Column(String(100))
    notes = Column(Text)
    created_by = Column(UUID(as_uuid=True))
    created_at = Column(DateTime(timezone=True), default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime(timezone=True), default=datetime.utcnow, onupdate=datetime.utcnow)


class RentalScheduleEntry(Base):
    """Stores rental schedule data imported from Excel (Palazzo SF Report style)."""

    __tablename__ = "rental_schedule_entries"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    property_name = Column(String(255), nullable=False)   # e.g. "Palazzo", "Imperial Court"
    sheet_year = Column(String(20))                       # e.g. "2026"
    commercial_unit = Column(String(100))                 # Suite1, Block 5, etc.
    square_meters = Column(String(50))
    owner = Column(String(255))
    tenant = Column(String(255))
    start_date = Column(Date)
    expiry_date = Column(Date)
    months = Column(Numeric(5, 1))
    monthly_rent = Column(Numeric(15, 2))
    currency = Column(String(10), default="USD")
    total_amount = Column(Numeric(15, 2))
    amount_paid = Column(Numeric(15, 2))
    balance = Column(Numeric(15, 2))
    tenancy_agreement_status = Column(String(255))
    due_date = Column(Date)
    status_notes = Column(Text)
    is_active = Column(Boolean, default=True)
    imported_by = Column(UUID(as_uuid=True))
    created_at = Column(DateTime(timezone=True), default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime(timezone=True), default=datetime.utcnow, onupdate=datetime.utcnow)
