"""Site Visit API endpoints for project site inspections."""

import logging
from datetime import datetime
from math import ceil
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.deps import get_current_user
from app.database import get_db
from app.models.site_visit import SiteVisit
from app.schemas.site_visit import (
    SiteVisitCreate,
    SiteVisitList,
    SiteVisitResponse,
    SiteVisitStats,
    SiteVisitUpdate,
)

router = APIRouter()
logger = logging.getLogger(__name__)


async def generate_visit_id(db: AsyncSession) -> str:
    """Generate a unique visit ID like SV-2026-0001."""
    year = datetime.utcnow().year
    prefix = f"SV-{year}-"

    query = (
        select(SiteVisit.visit_id)
        .where(SiteVisit.visit_id.like(f"{prefix}%"))
        .order_by(SiteVisit.visit_id.desc())
        .limit(1)
    )

    result = await db.execute(query)
    last_id = result.scalar_one_or_none()

    if last_id:
        try:
            last_num = int(last_id.split("-")[-1])
            next_num = last_num + 1
        except (ValueError, IndexError):
            next_num = 1
    else:
        next_num = 1

    return f"{prefix}{next_num:04d}"


@router.get("/stats", response_model=SiteVisitStats)
async def get_site_visit_stats(
    db: AsyncSession = Depends(get_db),
    current_user: dict = Depends(get_current_user),
):
    """Get site visit statistics."""
    total = await db.scalar(select(func.count(SiteVisit.id)))
    completed = await db.scalar(select(func.count(SiteVisit.id)).where(SiteVisit.status == "completed"))
    scheduled = await db.scalar(select(func.count(SiteVisit.id)).where(SiteVisit.status == "scheduled"))
    follow_up_required = await db.scalar(select(func.count(SiteVisit.id)).where(SiteVisit.follow_up_required == "yes"))

    return SiteVisitStats(
        total=total or 0,
        completed=completed or 0,
        scheduled=scheduled or 0,
        follow_up_required=follow_up_required or 0,
    )


@router.get("", response_model=SiteVisitList)
async def list_site_visits(
    page: int = Query(1, ge=1),
    page_size: int = Query(50, ge=1, le=100),
    search: str | None = Query(None),
    status_filter: str | None = Query(None, alias="status"),
    db: AsyncSession = Depends(get_db),
    current_user: dict = Depends(get_current_user),
):
    """List site visits with pagination and filtering."""
    query = select(SiteVisit)

    if search:
        query = query.where(
            (SiteVisit.project_name.ilike(f"%{search}%"))
            | (SiteVisit.visit_id.ilike(f"%{search}%"))
            | (SiteVisit.site_location.ilike(f"%{search}%"))
        )

    if status_filter:
        query = query.where(SiteVisit.status == status_filter)

    count_query = select(func.count()).select_from(query.subquery())
    total = await db.scalar(count_query)

    query = query.order_by(SiteVisit.visit_date.desc()).offset((page - 1) * page_size).limit(page_size)
    result = await db.execute(query)
    visits = result.scalars().all()

    return SiteVisitList(
        items=visits,
        total=total or 0,
        page=page,
        page_size=page_size,
        pages=ceil(total / page_size) if total and total > 0 else 0,
    )


@router.get("/{visit_id}", response_model=SiteVisitResponse)
async def get_site_visit(
    visit_id: UUID,
    db: AsyncSession = Depends(get_db),
    current_user: dict = Depends(get_current_user),
):
    """Get a single site visit by ID."""
    result = await db.execute(select(SiteVisit).where(SiteVisit.id == visit_id))
    visit = result.scalar_one_or_none()

    if not visit:
        raise HTTPException(status_code=404, detail="Site visit not found")

    return visit


@router.post("", response_model=SiteVisitResponse, status_code=status.HTTP_201_CREATED)
async def create_site_visit(
    data: SiteVisitCreate,
    db: AsyncSession = Depends(get_db),
    current_user: dict = Depends(get_current_user),
):
    """Create a new site visit entry."""
    visit_id = await generate_visit_id(db)

    visit = SiteVisit(
        visit_id=visit_id,
        project_name=data.project_name,
        project_id=data.project_id,
        site_location=data.site_location,
        visit_date=data.visit_date,
        visit_time=data.visit_time,
        visitors=data.visitors,
        site_contact=data.site_contact,
        site_contact_phone=data.site_contact_phone,
        visit_purpose=data.visit_purpose,
        observations=data.observations,
        issues_identified=data.issues_identified,
        recommendations=data.recommendations,
        follow_up_required=data.follow_up_required or "no",
        follow_up_notes=data.follow_up_notes,
        next_visit_date=data.next_visit_date,
        photos_url=data.photos_url,
        report_url=data.report_url,
        status=data.status or "completed",
        logged_by=data.logged_by or current_user.get("name", ""),
        logged_by_id=data.logged_by_id or (UUID(current_user["sub"]) if current_user.get("sub") else None),
    )

    db.add(visit)
    await db.commit()
    await db.refresh(visit)

    logger.info(f"Site visit created: {visit_id}")

    return visit


@router.put("/{visit_id}", response_model=SiteVisitResponse)
async def update_site_visit(
    visit_id: UUID,
    data: SiteVisitUpdate,
    db: AsyncSession = Depends(get_db),
    current_user: dict = Depends(get_current_user),
):
    """Update a site visit."""
    result = await db.execute(select(SiteVisit).where(SiteVisit.id == visit_id))
    visit = result.scalar_one_or_none()

    if not visit:
        raise HTTPException(status_code=404, detail="Site visit not found")

    update_data = data.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        setattr(visit, field, value)

    visit.updated_at = datetime.utcnow()
    await db.commit()
    await db.refresh(visit)

    logger.info(f"Site visit updated: {visit.visit_id}")

    return visit


@router.delete("/{visit_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_site_visit(
    visit_id: UUID,
    db: AsyncSession = Depends(get_db),
    current_user: dict = Depends(get_current_user),
):
    """Delete a site visit."""
    result = await db.execute(select(SiteVisit).where(SiteVisit.id == visit_id))
    visit = result.scalar_one_or_none()

    if not visit:
        raise HTTPException(status_code=404, detail="Site visit not found")

    await db.delete(visit)
    await db.commit()

    logger.info(f"Site visit deleted: {visit.visit_id}")
