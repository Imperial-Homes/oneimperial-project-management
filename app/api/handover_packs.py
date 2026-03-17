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
