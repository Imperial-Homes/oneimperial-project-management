"""Project Variations API endpoints."""

from datetime import date, datetime
from math import ceil
from typing import Optional
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy import func, or_, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.deps import get_current_user
from app.database import get_db
from app.models.variation import ProjectVariation, VariationStatus
from app.schemas.variation import (
    VariationCreate, VariationUpdate, VariationResponse,
    VariationList, VariationApproval
)

router = APIRouter()


def generate_variation_number() -> str:
    """Generate variation number: VAR-YYYYMMDD-XXXX"""
    timestamp = datetime.utcnow().strftime("%Y%m%d%H%M%S")
    return f"VAR-{timestamp}"


@router.get("", response_model=VariationList)
async def list_variations(
    page: int = Query(1, ge=1),
    page_size: int = Query(50, ge=1, le=100),
    project_id: Optional[UUID] = Query(None),
    status: Optional[VariationStatus] = Query(None),
    search: Optional[str] = Query(None),
    db: AsyncSession = Depends(get_db),
    current_user: UUID = Depends(get_current_user),
):
    """List variations with filtering."""
    query = select(ProjectVariation)
    
    if project_id:
        query = query.where(ProjectVariation.project_id == project_id)
    
    if status:
        query = query.where(ProjectVariation.status == status)
    
    if search:
        query = query.where(
            or_(
                ProjectVariation.title.ilike(f"%{search}%"),
                ProjectVariation.variation_number.ilike(f"%{search}%"),
                ProjectVariation.description.ilike(f"%{search}%")
            )
        )
    
    count_query = select(func.count()).select_from(query.subquery())
    total = await db.scalar(count_query)
    
    query = query.order_by(ProjectVariation.requested_date.desc())
    query = query.offset((page - 1) * page_size).limit(page_size)
    result = await db.execute(query)
    variations = result.scalars().all()
    
    return VariationList(
        items=variations,
        total=total,
        page=page,
        page_size=page_size,
        pages=ceil(total / page_size) if total > 0 else 0
    )


@router.post("", response_model=VariationResponse, status_code=status.HTTP_201_CREATED)
async def create_variation(
    variation_data: VariationCreate,
    db: AsyncSession = Depends(get_db),
    current_user: UUID = Depends(get_current_user),
):
    """Create new project variation."""
    variation = ProjectVariation(
        variation_number=generate_variation_number(),
        **variation_data.dict(),
        created_by=current_user
    )
    db.add(variation)
    await db.commit()
    await db.refresh(variation)
    return variation


@router.get("/{variation_id}", response_model=VariationResponse)
async def get_variation(
    variation_id: UUID,
    db: AsyncSession = Depends(get_db),
    current_user: UUID = Depends(get_current_user),
):
    """Get variation by ID."""
    result = await db.execute(
        select(ProjectVariation).where(ProjectVariation.id == variation_id)
    )
    variation = result.scalar_one_or_none()
    
    if not variation:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Variation not found"
        )
    
    return variation


@router.put("/{variation_id}", response_model=VariationResponse)
async def update_variation(
    variation_id: UUID,
    variation_data: VariationUpdate,
    db: AsyncSession = Depends(get_db),
    current_user: UUID = Depends(get_current_user),
):
    """Update variation."""
    result = await db.execute(
        select(ProjectVariation).where(ProjectVariation.id == variation_id)
    )
    variation = result.scalar_one_or_none()
    
    if not variation:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Variation not found"
        )
    
    for field, value in variation_data.dict(exclude_unset=True).items():
        setattr(variation, field, value)
    
    variation.updated_by = current_user
    await db.commit()
    await db.refresh(variation)
    return variation


@router.delete("/{variation_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_variation(
    variation_id: UUID,
    db: AsyncSession = Depends(get_db),
    current_user: UUID = Depends(get_current_user),
):
    """Delete variation (soft delete)."""
    result = await db.execute(
        select(ProjectVariation).where(ProjectVariation.id == variation_id)
    )
    variation = result.scalar_one_or_none()
    
    if not variation:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Variation not found"
        )
    
    variation.is_active = False
    await db.commit()


@router.post("/{variation_id}/approve", response_model=VariationResponse)
async def approve_variation(
    variation_id: UUID,
    approval_data: VariationApproval,
    db: AsyncSession = Depends(get_db),
    current_user: UUID = Depends(get_current_user),
):
    """Approve or reject variation."""
    result = await db.execute(
        select(ProjectVariation).where(ProjectVariation.id == variation_id)
    )
    variation = result.scalar_one_or_none()
    
    if not variation:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Variation not found"
        )
    
    if approval_data.approved:
        variation.status = VariationStatus.APPROVED
        variation.approved_by = current_user
        variation.approved_date = date.today()
    else:
        variation.status = VariationStatus.REJECTED
        variation.rejection_reason = approval_data.notes
    
    variation.updated_by = current_user
    await db.commit()
    await db.refresh(variation)
    return variation


@router.patch("/{variation_id}/status", response_model=VariationResponse)
async def update_variation_status(
    variation_id: UUID,
    new_status: VariationStatus,
    db: AsyncSession = Depends(get_db),
    current_user: UUID = Depends(get_current_user),
):
    """Update variation status."""
    result = await db.execute(
        select(ProjectVariation).where(ProjectVariation.id == variation_id)
    )
    variation = result.scalar_one_or_none()
    
    if not variation:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Variation not found"
        )
    
    variation.status = new_status
    variation.updated_by = current_user
    await db.commit()
    await db.refresh(variation)
    return variation
