"""Payment Certificates API endpoints."""

from datetime import date, datetime
from math import ceil
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy import func, or_, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.deps import get_current_user
from app.database import get_db
from app.models.payment import CertificateStatus, CertificateType, PaymentCertificate
from app.schemas.payment import (
    PaymentCertificateApprove,
    PaymentCertificateCreate,
    PaymentCertificateList,
    PaymentCertificatePayment,
    PaymentCertificateReject,
    PaymentCertificateResponse,
    PaymentCertificateSubmit,
    PaymentCertificateUpdate,
)

router = APIRouter()


def generate_certificate_number() -> str:
    """Generate certificate number: PC-YYYYMMDD-XXXX"""
    timestamp = datetime.utcnow().strftime("%Y%m%d%H%M%S")
    return f"PC-{timestamp}"


@router.get("", response_model=PaymentCertificateList)
async def list_certificates(
    page: int = Query(1, ge=1),
    page_size: int = Query(50, ge=1, le=100),
    project_id: UUID | None = Query(None),
    certificate_type: CertificateType | None = Query(None),
    status: CertificateStatus | None = Query(None),
    search: str | None = Query(None),
    db: AsyncSession = Depends(get_db),
    current_user: UUID = Depends(get_current_user),
):
    """List payment certificates with filtering."""
    from sqlalchemy.orm import selectinload

    query = select(PaymentCertificate).options(selectinload(PaymentCertificate.project))

    if project_id:
        query = query.where(PaymentCertificate.project_id == project_id)

    if certificate_type:
        query = query.where(PaymentCertificate.certificate_type == certificate_type)

    if status:
        query = query.where(PaymentCertificate.status == status)

    if search:
        query = query.where(
            or_(
                PaymentCertificate.certificate_number.ilike(f"%{search}%"),
                PaymentCertificate.description.ilike(f"%{search}%"),
                PaymentCertificate.contractor_name.ilike(f"%{search}%"),
            )
        )

    count_query = select(func.count()).select_from(query.subquery())
    total = await db.scalar(count_query)

    query = query.order_by(PaymentCertificate.certificate_date.desc())
    query = query.offset((page - 1) * page_size).limit(page_size)
    result = await db.execute(query)
    certificates = result.scalars().all()

    return PaymentCertificateList(
        items=certificates,
        total=total,
        page=page,
        page_size=page_size,
        pages=ceil(total / page_size) if total > 0 else 0,
    )


@router.post("", response_model=PaymentCertificateResponse, status_code=status.HTTP_201_CREATED)
async def create_certificate(
    certificate_data: PaymentCertificateCreate,
    db: AsyncSession = Depends(get_db),
    current_user: UUID = Depends(get_current_user),
):
    """Create new payment certificate."""
    certificate = PaymentCertificate(
        certificate_number=generate_certificate_number(), **certificate_data.dict(), created_by=current_user
    )
    db.add(certificate)
    await db.commit()
    await db.refresh(certificate)
    return certificate


@router.get("/{certificate_id}", response_model=PaymentCertificateResponse)
async def get_certificate(
    certificate_id: UUID,
    db: AsyncSession = Depends(get_db),
    current_user: UUID = Depends(get_current_user),
):
    """Get payment certificate by ID."""
    result = await db.execute(select(PaymentCertificate).where(PaymentCertificate.id == certificate_id))
    certificate = result.scalar_one_or_none()

    if not certificate:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Payment certificate not found")

    return certificate


@router.put("/{certificate_id}", response_model=PaymentCertificateResponse)
async def update_certificate(
    certificate_id: UUID,
    certificate_data: PaymentCertificateUpdate,
    db: AsyncSession = Depends(get_db),
    current_user: UUID = Depends(get_current_user),
):
    """Update payment certificate."""
    result = await db.execute(select(PaymentCertificate).where(PaymentCertificate.id == certificate_id))
    certificate = result.scalar_one_or_none()

    if not certificate:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Payment certificate not found")

    for field, value in certificate_data.dict(exclude_unset=True).items():
        setattr(certificate, field, value)

    certificate.updated_by = current_user
    await db.commit()
    await db.refresh(certificate)
    return certificate


@router.delete("/{certificate_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_certificate(
    certificate_id: UUID,
    db: AsyncSession = Depends(get_db),
    current_user: UUID = Depends(get_current_user),
):
    """Delete payment certificate."""
    result = await db.execute(select(PaymentCertificate).where(PaymentCertificate.id == certificate_id))
    certificate = result.scalar_one_or_none()

    if not certificate:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Payment certificate not found")

    await db.delete(certificate)
    await db.commit()


@router.post("/{certificate_id}/submit", response_model=PaymentCertificateResponse)
async def submit_certificate(
    certificate_id: UUID,
    submit_data: PaymentCertificateSubmit,
    db: AsyncSession = Depends(get_db),
    current_user: UUID = Depends(get_current_user),
):
    """Submit certificate for approval."""
    result = await db.execute(select(PaymentCertificate).where(PaymentCertificate.id == certificate_id))
    certificate = result.scalar_one_or_none()

    if not certificate:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Payment certificate not found")

    certificate.status = CertificateStatus.SUBMITTED
    certificate.submitted_date = date.today()
    certificate.submitted_by = current_user
    if submit_data.notes:
        certificate.notes = submit_data.notes

    await db.commit()
    await db.refresh(certificate)
    return certificate


@router.post("/{certificate_id}/approve", response_model=PaymentCertificateResponse)
async def approve_certificate(
    certificate_id: UUID,
    approve_data: PaymentCertificateApprove,
    db: AsyncSession = Depends(get_db),
    current_user: UUID = Depends(get_current_user),
):
    """Approve certificate."""
    result = await db.execute(select(PaymentCertificate).where(PaymentCertificate.id == certificate_id))
    certificate = result.scalar_one_or_none()

    if not certificate:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Payment certificate not found")

    certificate.status = CertificateStatus.APPROVED
    certificate.approved_date = date.today()
    certificate.approved_by = current_user
    if approve_data.notes:
        certificate.notes = approve_data.notes

    await db.commit()
    await db.refresh(certificate)
    return certificate


@router.post("/{certificate_id}/reject", response_model=PaymentCertificateResponse)
async def reject_certificate(
    certificate_id: UUID,
    reject_data: PaymentCertificateReject,
    db: AsyncSession = Depends(get_db),
    current_user: UUID = Depends(get_current_user),
):
    """Reject certificate."""
    result = await db.execute(select(PaymentCertificate).where(PaymentCertificate.id == certificate_id))
    certificate = result.scalar_one_or_none()

    if not certificate:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Payment certificate not found")

    certificate.status = CertificateStatus.REJECTED
    certificate.rejected_date = date.today()
    certificate.rejected_by = current_user
    certificate.rejection_reason = reject_data.rejection_reason

    await db.commit()
    await db.refresh(certificate)
    return certificate


@router.post("/{certificate_id}/payment", response_model=PaymentCertificateResponse)
async def record_payment(
    certificate_id: UUID,
    payment_data: PaymentCertificatePayment,
    db: AsyncSession = Depends(get_db),
    current_user: UUID = Depends(get_current_user),
):
    """Record payment for certificate."""
    result = await db.execute(select(PaymentCertificate).where(PaymentCertificate.id == certificate_id))
    certificate = result.scalar_one_or_none()

    if not certificate:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Payment certificate not found")

    certificate.payment_date = payment_data.payment_date
    certificate.payment_reference = payment_data.payment_reference
    certificate.amount_paid = payment_data.amount_paid

    # Update status based on payment
    if certificate.amount_paid >= certificate.net_amount:
        certificate.status = CertificateStatus.PAID
    else:
        certificate.status = CertificateStatus.PARTIALLY_PAID

    if payment_data.notes:
        certificate.notes = payment_data.notes

    await db.commit()
    await db.refresh(certificate)
    return certificate
