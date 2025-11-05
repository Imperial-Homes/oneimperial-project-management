"""Project Payments API endpoints."""

from datetime import date, datetime
from math import ceil
from typing import Optional
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy import func, or_, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.deps import get_current_user
from app.database import get_db
from app.models.payment import ProjectPayment, PaymentStatus, PaymentType
from app.schemas.payment import (
    PaymentCreate, PaymentUpdate, PaymentResponse,
    PaymentList, PaymentReconcile
)

router = APIRouter()


def generate_payment_number() -> str:
    """Generate payment number: PAY-YYYYMMDD-XXXX"""
    timestamp = datetime.utcnow().strftime("%Y%m%d%H%M%S")
    return f"PAY-{timestamp}"


@router.get("", response_model=PaymentList)
async def list_payments(
    page: int = Query(1, ge=1),
    page_size: int = Query(50, ge=1, le=100),
    project_id: Optional[UUID] = Query(None),
    payment_type: Optional[PaymentType] = Query(None),
    status: Optional[PaymentStatus] = Query(None),
    search: Optional[str] = Query(None),
    db: AsyncSession = Depends(get_db),
    current_user: UUID = Depends(get_current_user),
):
    """List payments with filtering."""
    query = select(ProjectPayment)
    
    if project_id:
        query = query.where(ProjectPayment.project_id == project_id)
    
    if payment_type:
        query = query.where(ProjectPayment.payment_type == payment_type)
    
    if status:
        query = query.where(ProjectPayment.status == status)
    
    if search:
        query = query.where(
            or_(
                ProjectPayment.payment_number.ilike(f"%{search}%"),
                ProjectPayment.reference_number.ilike(f"%{search}%"),
                ProjectPayment.paid_by_name.ilike(f"%{search}%"),
                ProjectPayment.received_by_name.ilike(f"%{search}%")
            )
        )
    
    count_query = select(func.count()).select_from(query.subquery())
    total = await db.scalar(count_query)
    
    query = query.order_by(ProjectPayment.payment_date.desc())
    query = query.offset((page - 1) * page_size).limit(page_size)
    result = await db.execute(query)
    payments = result.scalars().all()
    
    return PaymentList(
        items=payments,
        total=total,
        page=page,
        page_size=page_size,
        pages=ceil(total / page_size) if total > 0 else 0
    )


@router.post("", response_model=PaymentResponse, status_code=status.HTTP_201_CREATED)
async def create_payment(
    payment_data: PaymentCreate,
    db: AsyncSession = Depends(get_db),
    current_user: UUID = Depends(get_current_user),
):
    """Create new project payment."""
    payment = ProjectPayment(
        payment_number=generate_payment_number(),
        **payment_data.dict(),
        created_by=current_user
    )
    db.add(payment)
    await db.commit()
    await db.refresh(payment)
    return payment


@router.get("/{payment_id}", response_model=PaymentResponse)
async def get_payment(
    payment_id: UUID,
    db: AsyncSession = Depends(get_db),
    current_user: UUID = Depends(get_current_user),
):
    """Get payment by ID."""
    result = await db.execute(
        select(ProjectPayment).where(ProjectPayment.id == payment_id)
    )
    payment = result.scalar_one_or_none()
    
    if not payment:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Payment not found"
        )
    
    return payment


@router.put("/{payment_id}", response_model=PaymentResponse)
async def update_payment(
    payment_id: UUID,
    payment_data: PaymentUpdate,
    db: AsyncSession = Depends(get_db),
    current_user: UUID = Depends(get_current_user),
):
    """Update payment."""
    result = await db.execute(
        select(ProjectPayment).where(ProjectPayment.id == payment_id)
    )
    payment = result.scalar_one_or_none()
    
    if not payment:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Payment not found"
        )
    
    for field, value in payment_data.dict(exclude_unset=True).items():
        setattr(payment, field, value)
    
    payment.updated_by = current_user
    await db.commit()
    await db.refresh(payment)
    return payment


@router.delete("/{payment_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_payment(
    payment_id: UUID,
    db: AsyncSession = Depends(get_db),
    current_user: UUID = Depends(get_current_user),
):
    """Delete payment."""
    result = await db.execute(
        select(ProjectPayment).where(ProjectPayment.id == payment_id)
    )
    payment = result.scalar_one_or_none()
    
    if not payment:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Payment not found"
        )
    
    await db.delete(payment)
    await db.commit()


@router.post("/{payment_id}/reconcile", response_model=PaymentResponse)
async def reconcile_payment(
    payment_id: UUID,
    reconcile_data: PaymentReconcile,
    db: AsyncSession = Depends(get_db),
    current_user: UUID = Depends(get_current_user),
):
    """Mark payment as reconciled."""
    result = await db.execute(
        select(ProjectPayment).where(ProjectPayment.id == payment_id)
    )
    payment = result.scalar_one_or_none()
    
    if not payment:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Payment not found"
        )
    
    payment.is_reconciled = True
    payment.reconciled_date = date.today()
    payment.reconciled_by = current_user
    if reconcile_data.notes:
        payment.notes = reconcile_data.notes
    
    await db.commit()
    await db.refresh(payment)
    return payment


@router.patch("/{payment_id}/status", response_model=PaymentResponse)
async def update_payment_status(
    payment_id: UUID,
    new_status: PaymentStatus,
    db: AsyncSession = Depends(get_db),
    current_user: UUID = Depends(get_current_user),
):
    """Update payment status."""
    result = await db.execute(
        select(ProjectPayment).where(ProjectPayment.id == payment_id)
    )
    payment = result.scalar_one_or_none()
    
    if not payment:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Payment not found"
        )
    
    payment.status = new_status
    payment.updated_by = current_user
    await db.commit()
    await db.refresh(payment)
    return payment
