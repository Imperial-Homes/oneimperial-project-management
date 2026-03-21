"""Payment Certificates API endpoints."""

import logging
from datetime import date, datetime
from math import ceil
from typing import Optional
from uuid import UUID

import httpx
from fastapi import APIRouter, BackgroundTasks, Depends, HTTPException, Query, status
from sqlalchemy import func, or_, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.config import settings
from app.core.deps import get_current_user
from app.core.resilience import get_breaker
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
logger = logging.getLogger(__name__)


def _post_project_cost_journal(
    *,
    certificate_number: str,
    project_name: str,
    contractor_name: str,
    amount: float,
    pay_date: str,
    certificate_type: str,
    auth_token: Optional[str] = None,
) -> None:
    """Background task: post project payment certificate as a GL journal to finance.

    DR  Project Cost / Construction Expense
    CR  Accounts Payable (contractor payable)
    """
    breaker = get_breaker("finance-accounting")
    if not breaker.is_available():
        logger.warning("finance-accounting circuit open — skipping project cost GL post")
        return

    headers = {"Content-Type": "application/json"}
    if auth_token:
        headers["Authorization"] = f"Bearer {auth_token}"

    finance_url = settings.FINANCE_SERVICE_URL

    try:
        with httpx.Client(timeout=10.0) as client:
            # Find expense account (Project Cost or Construction)
            expense_account_id = None
            for search_term in ("Project Cost", "Construction", "Contract Expense"):
                resp = client.get(
                    f"{finance_url}/accounts",
                    params={"search": search_term, "page_size": 1},
                    headers=headers,
                )
                if resp.status_code == 200:
                    items = resp.json().get("items", [])
                    if items:
                        expense_account_id = items[0]["id"]
                        break

            # Find Accounts Payable account
            ap_account_id = None
            resp = client.get(
                f"{finance_url}/accounts",
                params={"search": "Accounts Payable", "page_size": 1},
                headers=headers,
            )
            if resp.status_code == 200:
                items = resp.json().get("items", [])
                if items:
                    ap_account_id = items[0]["id"]

            if not expense_account_id or not ap_account_id:
                logger.warning(
                    "GL accounts not found for project cost — skipping journal",
                    extra={"certificate": certificate_number},
                )
                breaker.record_success()
                return

            je_resp = client.post(
                f"{finance_url}/journal-entries",
                json={
                    "entry_number": f"JE-PM-{certificate_number}",
                    "entry_date": pay_date,
                    "description": f"Project cost: {project_name} — {certificate_number}",
                    "reference": certificate_number,
                    "status": "posted",
                    "lines": [
                        {
                            "account_id": expense_account_id,
                            "description": f"{certificate_type}: {certificate_number}",
                            "debit": amount,
                            "credit": 0,
                        },
                        {
                            "account_id": ap_account_id,
                            "description": f"Payable: {contractor_name}",
                            "debit": 0,
                            "credit": amount,
                        },
                    ],
                },
                headers=headers,
            )

            if je_resp.status_code in (200, 201):
                logger.info("Posted project cost GL journal", extra={"certificate": certificate_number})
                breaker.record_success()
            else:
                logger.warning("Finance GL post failed", extra={"status": je_resp.status_code})
                breaker.record_failure()

    except Exception as exc:
        logger.warning(f"Finance GL post error: {exc}")
        breaker.record_failure()


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
    background_tasks: BackgroundTasks,
    db: AsyncSession = Depends(get_db),
    current_user: UUID = Depends(get_current_user),
):
    """Record payment for certificate and post GL journal to finance."""
    from sqlalchemy.orm import selectinload

    result = await db.execute(
        select(PaymentCertificate)
        .options(selectinload(PaymentCertificate.project))
        .where(PaymentCertificate.id == certificate_id)
    )
    certificate = result.scalar_one_or_none()

    if not certificate:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Payment certificate not found")

    certificate.payment_date = payment_data.payment_date
    certificate.payment_reference = payment_data.payment_reference
    certificate.amount_paid = payment_data.amount_paid

    if certificate.amount_paid >= certificate.net_amount:
        certificate.status = CertificateStatus.PAID
    else:
        certificate.status = CertificateStatus.PARTIALLY_PAID

    if payment_data.notes:
        certificate.notes = payment_data.notes

    await db.commit()
    await db.refresh(certificate)

    # Post project cost as GL journal to finance (fire-and-forget)
    project = certificate.project
    background_tasks.add_task(
        _post_project_cost_journal,
        certificate_number=certificate.certificate_number,
        project_name=project.name if project else "Unknown Project",
        contractor_name=certificate.contractor_name or "",
        amount=float(certificate.current_amount),
        pay_date=payment_data.payment_date.isoformat(),
        certificate_type=certificate.certificate_type.value
        if hasattr(certificate.certificate_type, "value")
        else str(certificate.certificate_type),
    )

    return certificate


@router.get("/{certificate_id}/pdf")
async def download_certificate_pdf(
    certificate_id: UUID,
    db: AsyncSession = Depends(get_db),
    current_user: UUID = Depends(get_current_user),
):
    """Generate and download a Payment Certificate PDF."""
    from fastapi.responses import Response
    from sqlalchemy.orm import selectinload

    from app.utils.pdf_certificate import generate_payment_certificate_pdf

    result = await db.execute(
        select(PaymentCertificate)
        .options(selectinload(PaymentCertificate.project))
        .where(PaymentCertificate.id == certificate_id)
    )
    cert = result.scalar_one_or_none()
    if not cert:
        raise HTTPException(status_code=404, detail="Payment certificate not found")

    project = cert.project

    pdf_bytes = generate_payment_certificate_pdf(
        certificate_number=cert.certificate_number,
        certificate_type=cert.certificate_type.value
        if hasattr(cert.certificate_type, "value")
        else str(cert.certificate_type),
        certificate_date=cert.certificate_date,
        status=cert.status.value if hasattr(cert.status, "value") else str(cert.status),
        currency=cert.currency or "GHS",
        # Project
        project_name=project.name if project else "",
        project_code=project.project_code if project else "",
        project_location=project.location or "" if project else "",
        project_type=project.project_type or "" if project else "",
        # Parties
        client_name=cert.client_name or "",
        contractor_name=cert.contractor_name or "",
        consultant_name=cert.consultant_name or "",
        # Period
        period_from=cert.period_from,
        period_to=cert.period_to,
        # Financials
        gross_amount=float(cert.gross_amount or 0),
        previous_amount=float(cert.previous_amount or 0),
        current_amount=float(cert.current_amount or 0),
        retention_percentage=float(cert.retention_percentage or 5),
        retention_amount=float(cert.retention_amount or 0),
        net_amount=float(cert.net_amount or 0),
        amount_paid=float(cert.amount_paid or 0),
        # Narrative
        work_completed=cert.work_completed or "",
        description=cert.description or "",
        notes=cert.notes or "",
        # Timeline
        submitted_date=cert.submitted_date,
        approved_date=cert.approved_date,
        payment_date=cert.payment_date,
        payment_reference=cert.payment_reference or "",
    )

    if not pdf_bytes:
        raise HTTPException(status_code=500, detail="PDF generation failed")

    filename = f"payment_certificate_{cert.certificate_number}.pdf"
    return Response(
        content=pdf_bytes,
        media_type="application/pdf",
        headers={"Content-Disposition": f'attachment; filename="{filename}"'},
    )
