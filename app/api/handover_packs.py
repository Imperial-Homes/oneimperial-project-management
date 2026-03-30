"""Handover Pack API endpoints - SOP 5.0."""

import math
from datetime import datetime

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy import and_, func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.models.handover_pack import HandoverPack
from app.schemas.handover_pack import (
    HandoverPackCreate,
    HandoverPackList,
    HandoverPackResponse,
    HandoverPackStats,
    HandoverPackUpdate,
)

router = APIRouter()


async def get_next_handover_id(db: AsyncSession) -> str:
    year = datetime.now().year
    result = await db.execute(
        select(HandoverPack)
        .where(HandoverPack.handover_id.like(f"HP-{year}-%"))
        .order_by(HandoverPack.handover_id.desc())
        .limit(1)
    )
    last = result.scalar_one_or_none()
    seq = int(last.handover_id.split("-")[-1]) + 1 if last else 1
    return f"HP-{year}-{seq:04d}"


@router.post("/", response_model=HandoverPackResponse, status_code=201)
async def create_handover(data: HandoverPackCreate, db: AsyncSession = Depends(get_db)):
    handover_id = await get_next_handover_id(db)
    obj = HandoverPack(handover_id=handover_id, **data.model_dump())
    db.add(obj)
    await db.commit()
    await db.refresh(obj)
    return obj


@router.get("/", response_model=HandoverPackList)
@router.get("", response_model=HandoverPackList)
async def get_handovers(
    page: int = Query(1, ge=1),
    page_size: int = Query(10, ge=1, le=100),
    search: str | None = None,
    status: str | None = None,
    db: AsyncSession = Depends(get_db),
):
    filters = []
    if search:
        s = f"%{search}%"
        filters.append(
            HandoverPack.property_name.ilike(s) | HandoverPack.client_name.ilike(s) | HandoverPack.handover_id.ilike(s)
        )
    if status:
        filters.append(HandoverPack.status == status)

    query = select(HandoverPack)
    if filters:
        query = query.where(and_(*filters))

    count_q = select(func.count()).select_from(HandoverPack)
    if filters:
        count_q = count_q.where(and_(*filters))
    total = (await db.execute(count_q)).scalar()

    query = query.order_by(HandoverPack.created_at.desc()).offset((page - 1) * page_size).limit(page_size)
    items = (await db.execute(query)).scalars().all()

    return HandoverPackList(
        items=items, total=total, page=page, page_size=page_size, pages=math.ceil(total / page_size) if total > 0 else 0
    )


@router.get("/stats", response_model=HandoverPackStats)
async def get_handover_stats(db: AsyncSession = Depends(get_db)):
    async def count(where=None):
        q = select(func.count()).select_from(HandoverPack)
        if where is not None:
            q = q.where(where)
        return (await db.execute(q)).scalar()

    return HandoverPackStats(
        total=await count(),
        initiated=await count(HandoverPack.status == "initiated"),
        obligations_pending=await count(HandoverPack.status == "obligations_pending"),
        pack_drafted=await count(HandoverPack.status == "pack_drafted"),
        doa_review=await count(HandoverPack.status == "doa_review"),
        client_signoff=await count(HandoverPack.status == "client_signoff"),
        completed=await count(HandoverPack.status == "completed"),
    )


@router.get("/{item_id}", response_model=HandoverPackResponse)
async def get_handover(item_id: str, db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(HandoverPack).where(HandoverPack.id == item_id))
    obj = result.scalar_one_or_none()
    if not obj:
        raise HTTPException(status_code=404, detail="Handover pack not found")
    return obj


@router.put("/{item_id}", response_model=HandoverPackResponse)
async def update_handover(item_id: str, data: HandoverPackUpdate, db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(HandoverPack).where(HandoverPack.id == item_id))
    obj = result.scalar_one_or_none()
    if not obj:
        raise HTTPException(status_code=404, detail="Handover pack not found")
    for k, v in data.model_dump(exclude_unset=True).items():
        setattr(obj, k, v)
    await db.commit()
    await db.refresh(obj)
    return obj


@router.delete("/{item_id}", status_code=204)
async def delete_handover(item_id: str, db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(HandoverPack).where(HandoverPack.id == item_id))
    obj = result.scalar_one_or_none()
    if not obj:
        raise HTTPException(status_code=404, detail="Handover pack not found")
    await db.delete(obj)
    await db.commit()


@router.get("/{item_id}/pdf")
async def download_handover_certificate_pdf(
    item_id: str,
    db: AsyncSession = Depends(get_db),
):
    """Generate and download a branded Handover Certificate PDF (SOP 5.0)."""
    from fastapi.responses import Response
    from app.utils.pdf_handover import generate_handover_certificate_pdf

    result = await db.execute(select(HandoverPack).where(HandoverPack.id == item_id))
    hp = result.scalar_one_or_none()
    if not hp:
        raise HTTPException(status_code=404, detail="Handover pack not found")

    pdf_bytes = generate_handover_certificate_pdf(
        handover_id=hp.handover_id,
        status=hp.status,
        property_name=hp.property_name,
        apartment_number=hp.apartment_number or "",
        site_location=hp.site_location or "",
        client_name=hp.client_name,
        client_email=hp.client_email or "",
        client_phone=hp.client_phone or "",
        sinking_fund_invoiced=bool(hp.sinking_fund_invoiced),
        sinking_fund_amount=float(hp.sinking_fund_amount) if hp.sinking_fund_amount else None,
        transfer_document_invoiced=bool(hp.transfer_document_invoiced),
        transfer_document_amount=float(hp.transfer_document_amount) if hp.transfer_document_amount else None,
        hoa_forms_completed=bool(hp.hoa_forms_completed),
        facility_manager_info_provided=bool(hp.facility_manager_info_provided),
        all_payments_made=bool(hp.all_payments_made),
        payments_date=hp.payments_date,
        handover_pack_drafted=bool(hp.handover_pack_drafted),
        doa_approved=bool(hp.doa_approved),
        doa_approved_date=hp.doa_approved_date,
        client_signed=bool(hp.client_signed),
        client_signed_date=hp.client_signed_date,
        keys_handed_over=bool(hp.keys_handed_over),
        handover_date=hp.handover_date,
        letter_to_client=hp.letter_to_client or "",
        notes=hp.notes or "",
        issues_noted=hp.issues_noted or "",
        handled_by=hp.handled_by or "",
    )

    if not pdf_bytes:
        raise HTTPException(status_code=500, detail="PDF generation failed")

    return Response(
        content=pdf_bytes,
        media_type="application/pdf",
        headers={"Content-Disposition": f'attachment; filename="handover_{hp.handover_id}.pdf"'},
    )
