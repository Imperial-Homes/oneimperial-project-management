"""Retention Release API endpoints."""

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
from app.models.payment import PaymentCertificate
from app.models.retention import RetentionRelease, RetentionStatus, RetentionTranche
from app.schemas.retention import (
    RetentionReleaseApprove,
    RetentionReleaseCreate,
    RetentionReleaseList,
    RetentionReleasePayment,
    RetentionReleaseReject,
    RetentionReleaseResponse,
    RetentionReleaseSubmit,
    RetentionReleaseUpdate,
    RetentionSummary,
)

router = APIRouter()
logger = logging.getLogger(__name__)


def _generate_release_number() -> str:
    """Generate release number: RR-YYYYMMDDHHMMSS"""
    return f"RR-{datetime.utcnow().strftime('%Y%m%d%H%M%S')}"


def _post_retention_gl(
    *,
    release_number: str,
    project_name: str,
    amount: float,
    pay_date: str,
    auth_token: Optional[str] = None,
) -> None:
    """Background task: post retention payment as GL journal to finance.

    DR  Retention Liability (liability account holding withheld retention)
    CR  Bank / Cash (money leaving the company to contractor)
    """
    breaker = get_breaker("finance-accounting")
    if not breaker.is_available():
        logger.warning("finance-accounting circuit open — skipping retention GL post")
        return

    headers = {"Content-Type": "application/json"}
    if auth_token:
        headers["Authorization"] = f"Bearer {auth_token}"

    finance_url = settings.FINANCE_SERVICE_URL

    try:
        with httpx.Client(timeout=10.0) as client:
            # Find Retention Liability account
            retention_account_id = None
            for search_term in ("Retention", "Contractor Retention", "Retention Payable"):
                resp = client.get(
                    f"{finance_url}/accounts",
                    params={"search": search_term, "page_size": 1},
                    headers=headers,
                )
                if resp.status_code == 200:
                    items = resp.json().get("items", [])
                    if items:
                        retention_account_id = items[0]["id"]
                        break

            # Find Bank / Cash account
            bank_account_id = None
            for search_term in ("Bank", "Cash", "GCB"):
                resp = client.get(
                    f"{finance_url}/accounts",
                    params={"search": search_term, "page_size": 1},
                    headers=headers,
                )
                if resp.status_code == 200:
                    items = resp.json().get("items", [])
                    if items:
                        bank_account_id = items[0]["id"]
                        break

            if not retention_account_id or not bank_account_id:
                logger.warning(
                    "GL accounts not found for retention release — skipping journal",
                    extra={"release": release_number},
                )
                breaker.record_success()
                return

            je_resp = client.post(
                f"{finance_url}/journal-entries",
                json={
                    "entry_number": f"JE-RET-{release_number}",
                    "entry_date": pay_date,
                    "description": f"Retention release: {project_name} — {release_number}",
                    "reference": release_number,
                    "status": "posted",
                    "lines": [
                        {
                            "account_id": retention_account_id,
                            "description": f"Retention released: {release_number}",
                            "debit": amount,
                            "credit": 0,
                        },
                        {
                            "account_id": bank_account_id,
                            "description": f"Bank payment: {release_number}",
                            "debit": 0,
                            "credit": amount,
                        },
                    ],
                },
                headers=headers,
            )

            if je_resp.status_code in (200, 201):
                logger.info("Posted retention GL journal", extra={"release": release_number})
                breaker.record_success()
            else:
                logger.warning("Finance GL post failed", extra={"status": je_resp.status_code})
                breaker.record_failure()

    except Exception as exc:
        logger.warning(f"Finance retention GL post error: {exc}")
        breaker.record_failure()


# ── List ──────────────────────────────────────────────────────────────────────

@router.get("", response_model=RetentionReleaseList)
async def list_retention_releases(
    page: int = Query(1, ge=1),
    page_size: int = Query(50, ge=1, le=500),
    project_id: UUID | None = Query(None),
    status: RetentionStatus | None = Query(None),
    tranche: RetentionTranche | None = Query(None),
    search: str | None = Query(None),
    db: AsyncSession = Depends(get_db),
    current_user: UUID = Depends(get_current_user),
):
    """List retention releases with filtering."""
    from sqlalchemy.orm import selectinload

    query = select(RetentionRelease).options(selectinload(RetentionRelease.project))

    if project_id:
        query = query.where(RetentionRelease.project_id == project_id)
    if status:
        query = query.where(RetentionRelease.status == status)
    if tranche:
        query = query.where(RetentionRelease.tranche == tranche)
    if search:
        query = query.where(
            or_(
                RetentionRelease.release_number.ilike(f"%{search}%"),
                RetentionRelease.notes.ilike(f"%{search}%"),
            )
        )

    count_query = select(func.count()).select_from(query.subquery())
    total = await db.scalar(count_query)

    query = query.order_by(RetentionRelease.created_at.desc())
    query = query.offset((page - 1) * page_size).limit(page_size)
    result = await db.execute(query)
    releases = result.scalars().all()

    return RetentionReleaseList(
        items=releases,
        total=total,
        page=page,
        page_size=page_size,
        pages=ceil(total / page_size) if total > 0 else 0,
    )


# ── Summary ────────────────────────────────────────────────────────────────────

@router.get("/summary", response_model=RetentionSummary)
async def get_retention_summary(
    project_id: UUID | None = Query(None),
    db: AsyncSession = Depends(get_db),
    current_user: UUID = Depends(get_current_user),
):
    """
    Aggregated retention summary.

    total_retention_held = sum of retention_amount on all paid payment certificates
    total_released       = sum of amount_approved on paid retention releases
    total_pending        = sum of amount_requested on submitted/approved (not yet paid) releases
    balance_retainable   = held - released - pending
    """
    from decimal import Decimal

    # --- Retention held: sum retention_amount on PAID payment certificates ---
    cert_query = select(func.coalesce(func.sum(PaymentCertificate.retention_amount), 0))
    if project_id:
        cert_query = cert_query.where(PaymentCertificate.project_id == project_id)
    cert_query = cert_query.where(PaymentCertificate.status == "paid")
    total_held = Decimal(str(await db.scalar(cert_query) or 0))

    # --- Released: sum amount_approved on PAID retention releases ---
    rel_base = select(RetentionRelease)
    if project_id:
        rel_base = rel_base.where(RetentionRelease.project_id == project_id)

    paid_q = select(func.coalesce(func.sum(RetentionRelease.amount_approved), 0))
    if project_id:
        paid_q = paid_q.where(RetentionRelease.project_id == project_id)
    paid_q = paid_q.where(RetentionRelease.status == RetentionStatus.PAID)
    total_released = Decimal(str(await db.scalar(paid_q) or 0))

    # --- Pending: sum amount_requested on submitted/approved not yet paid ---
    pending_q = select(func.coalesce(func.sum(RetentionRelease.amount_requested), 0))
    if project_id:
        pending_q = pending_q.where(RetentionRelease.project_id == project_id)
    pending_q = pending_q.where(
        RetentionRelease.status.in_([RetentionStatus.SUBMITTED, RetentionStatus.APPROVED])
    )
    total_pending = Decimal(str(await db.scalar(pending_q) or 0))

    # --- Per-tranche released ---
    pc_q = select(func.coalesce(func.sum(RetentionRelease.amount_approved), 0)).where(
        RetentionRelease.status == RetentionStatus.PAID,
        RetentionRelease.tranche == RetentionTranche.PRACTICAL_COMPLETION,
    )
    if project_id:
        pc_q = pc_q.where(RetentionRelease.project_id == project_id)
    pc_released = Decimal(str(await db.scalar(pc_q) or 0))

    dlp_q = select(func.coalesce(func.sum(RetentionRelease.amount_approved), 0)).where(
        RetentionRelease.status == RetentionStatus.PAID,
        RetentionRelease.tranche == RetentionTranche.DLP_END,
    )
    if project_id:
        dlp_q = dlp_q.where(RetentionRelease.project_id == project_id)
    dlp_released = Decimal(str(await db.scalar(dlp_q) or 0))

    # --- Count ---
    count_q = select(func.count(RetentionRelease.id))
    if project_id:
        count_q = count_q.where(RetentionRelease.project_id == project_id)
    release_count = await db.scalar(count_q) or 0

    return RetentionSummary(
        project_id=project_id,
        total_retention_held=total_held,
        total_released=total_released,
        total_pending=total_pending,
        balance_retainable=max(total_held - total_released - total_pending, Decimal(0)),
        practical_completion_released=pc_released,
        dlp_end_released=dlp_released,
        release_count=release_count,
    )


# ── Create ────────────────────────────────────────────────────────────────────

@router.post("", response_model=RetentionReleaseResponse, status_code=status.HTTP_201_CREATED)
async def create_retention_release(
    release_data: RetentionReleaseCreate,
    db: AsyncSession = Depends(get_db),
    current_user: UUID = Depends(get_current_user),
):
    """Create a new retention release request (starts as DRAFT)."""
    release = RetentionRelease(
        release_number=_generate_release_number(),
        request_date=date.today(),
        requested_by=current_user,
        created_by=current_user,
        **release_data.dict(),
    )
    db.add(release)
    await db.commit()
    await db.refresh(release)
    return release


# ── Get by ID ─────────────────────────────────────────────────────────────────

@router.get("/{release_id}", response_model=RetentionReleaseResponse)
async def get_retention_release(
    release_id: UUID,
    db: AsyncSession = Depends(get_db),
    current_user: UUID = Depends(get_current_user),
):
    """Get a single retention release by ID."""
    from sqlalchemy.orm import selectinload

    result = await db.execute(
        select(RetentionRelease)
        .options(selectinload(RetentionRelease.project))
        .where(RetentionRelease.id == release_id)
    )
    release = result.scalar_one_or_none()
    if not release:
        raise HTTPException(status_code=404, detail="Retention release not found")
    return release


# ── Update ────────────────────────────────────────────────────────────────────

@router.put("/{release_id}", response_model=RetentionReleaseResponse)
async def update_retention_release(
    release_id: UUID,
    release_data: RetentionReleaseUpdate,
    db: AsyncSession = Depends(get_db),
    current_user: UUID = Depends(get_current_user),
):
    """Update a DRAFT retention release."""
    result = await db.execute(
        select(RetentionRelease).where(RetentionRelease.id == release_id)
    )
    release = result.scalar_one_or_none()
    if not release:
        raise HTTPException(status_code=404, detail="Retention release not found")
    if release.status != RetentionStatus.DRAFT:
        raise HTTPException(status_code=400, detail="Only DRAFT releases can be updated")

    for field, value in release_data.dict(exclude_unset=True).items():
        setattr(release, field, value)
    release.updated_by = current_user
    await db.commit()
    await db.refresh(release)
    return release


# ── Delete (draft only) ───────────────────────────────────────────────────────

@router.delete("/{release_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_retention_release(
    release_id: UUID,
    db: AsyncSession = Depends(get_db),
    current_user: UUID = Depends(get_current_user),
):
    """Delete a DRAFT retention release."""
    result = await db.execute(
        select(RetentionRelease).where(RetentionRelease.id == release_id)
    )
    release = result.scalar_one_or_none()
    if not release:
        raise HTTPException(status_code=404, detail="Retention release not found")
    if release.status != RetentionStatus.DRAFT:
        raise HTTPException(status_code=400, detail="Only DRAFT releases can be deleted")
    await db.delete(release)
    await db.commit()


# ── Submit ────────────────────────────────────────────────────────────────────

@router.post("/{release_id}/submit", response_model=RetentionReleaseResponse)
async def submit_retention_release(
    release_id: UUID,
    submit_data: RetentionReleaseSubmit,
    db: AsyncSession = Depends(get_db),
    current_user: UUID = Depends(get_current_user),
):
    """Submit a retention release for approval."""
    result = await db.execute(
        select(RetentionRelease).where(RetentionRelease.id == release_id)
    )
    release = result.scalar_one_or_none()
    if not release:
        raise HTTPException(status_code=404, detail="Retention release not found")
    if release.status != RetentionStatus.DRAFT:
        raise HTTPException(status_code=400, detail="Only DRAFT releases can be submitted")

    release.status = RetentionStatus.SUBMITTED
    if submit_data.notes:
        release.notes = submit_data.notes
    release.updated_by = current_user
    await db.commit()
    await db.refresh(release)
    return release


# ── Approve ───────────────────────────────────────────────────────────────────

@router.post("/{release_id}/approve", response_model=RetentionReleaseResponse)
async def approve_retention_release(
    release_id: UUID,
    approve_data: RetentionReleaseApprove,
    db: AsyncSession = Depends(get_db),
    current_user: UUID = Depends(get_current_user),
):
    """Approve a submitted retention release."""
    result = await db.execute(
        select(RetentionRelease).where(RetentionRelease.id == release_id)
    )
    release = result.scalar_one_or_none()
    if not release:
        raise HTTPException(status_code=404, detail="Retention release not found")
    if release.status != RetentionStatus.SUBMITTED:
        raise HTTPException(status_code=400, detail="Only SUBMITTED releases can be approved")

    release.status = RetentionStatus.APPROVED
    release.amount_approved = approve_data.amount_approved
    release.approval_date = date.today()
    release.approved_by = current_user
    if approve_data.notes:
        release.notes = approve_data.notes
    release.updated_by = current_user
    await db.commit()
    await db.refresh(release)
    return release


# ── Reject ────────────────────────────────────────────────────────────────────

@router.post("/{release_id}/reject", response_model=RetentionReleaseResponse)
async def reject_retention_release(
    release_id: UUID,
    reject_data: RetentionReleaseReject,
    db: AsyncSession = Depends(get_db),
    current_user: UUID = Depends(get_current_user),
):
    """Reject a submitted retention release."""
    result = await db.execute(
        select(RetentionRelease).where(RetentionRelease.id == release_id)
    )
    release = result.scalar_one_or_none()
    if not release:
        raise HTTPException(status_code=404, detail="Retention release not found")
    if release.status != RetentionStatus.SUBMITTED:
        raise HTTPException(status_code=400, detail="Only SUBMITTED releases can be rejected")

    release.status = RetentionStatus.REJECTED
    release.rejection_reason = reject_data.rejection_reason
    release.rejected_by = current_user
    release.updated_by = current_user
    await db.commit()
    await db.refresh(release)
    return release


# ── Record Payment ────────────────────────────────────────────────────────────

@router.post("/{release_id}/payment", response_model=RetentionReleaseResponse)
async def record_retention_payment(
    release_id: UUID,
    payment_data: RetentionReleasePayment,
    background_tasks: BackgroundTasks,
    db: AsyncSession = Depends(get_db),
    current_user: UUID = Depends(get_current_user),
):
    """Record payment for an approved retention release. Posts GL to Finance."""
    from sqlalchemy.orm import selectinload

    result = await db.execute(
        select(RetentionRelease)
        .options(selectinload(RetentionRelease.project))
        .where(RetentionRelease.id == release_id)
    )
    release = result.scalar_one_or_none()
    if not release:
        raise HTTPException(status_code=404, detail="Retention release not found")
    if release.status != RetentionStatus.APPROVED:
        raise HTTPException(status_code=400, detail="Only APPROVED releases can be marked paid")

    release.status = RetentionStatus.PAID
    release.payment_date = payment_data.payment_date
    release.payment_reference = payment_data.payment_reference
    if payment_data.notes:
        release.notes = payment_data.notes
    release.updated_by = current_user
    await db.commit()
    await db.refresh(release)

    # Post GL journal to Finance (fire-and-forget)
    project = release.project
    background_tasks.add_task(
        _post_retention_gl,
        release_number=release.release_number,
        project_name=project.name if project else "Unknown Project",
        amount=float(release.amount_approved or release.amount_requested),
        pay_date=payment_data.payment_date.isoformat(),
    )

    return release
