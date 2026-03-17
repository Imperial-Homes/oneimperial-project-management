"""Project Incidents API endpoints."""

from datetime import datetime
from math import ceil
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy import func, or_, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.core.deps import get_current_user
from app.database import get_db
from app.models.incident import IncidentSeverity, IncidentStatus, IncidentType, ProjectIncident
from app.schemas.incident import IncidentCreate, IncidentList, IncidentResolve, IncidentResponse, IncidentUpdate

router = APIRouter()


def generate_incident_number() -> str:
    """Generate incident number: INC-YYYYMMDD-XXXX"""
    timestamp = datetime.utcnow().strftime("%Y%m%d%H%M%S")
    return f"INC-{timestamp}"


@router.get("", response_model=IncidentList)
async def list_incidents(
    page: int = Query(1, ge=1),
    page_size: int = Query(50, ge=1, le=100),
    project_id: UUID | None = Query(None),
    incident_type: IncidentType | None = Query(None),
    severity: IncidentSeverity | None = Query(None),
    status: IncidentStatus | None = Query(None),
    search: str | None = Query(None),
    db: AsyncSession = Depends(get_db),
    current_user: UUID = Depends(get_current_user),
):
    """List incidents with filtering."""
    query = select(ProjectIncident).options(selectinload(ProjectIncident.project))

    if project_id:
        query = query.where(ProjectIncident.project_id == project_id)

    if incident_type:
        query = query.where(ProjectIncident.incident_type == incident_type)

    if severity:
        query = query.where(ProjectIncident.severity == severity)

    if status:
        query = query.where(ProjectIncident.status == status)

    if search:
        query = query.where(
            or_(
                ProjectIncident.incident_number.ilike(f"%{search}%"),
                ProjectIncident.title.ilike(f"%{search}%"),
                ProjectIncident.description.ilike(f"%{search}%"),
            )
        )

    count_query = select(func.count()).select_from(query.subquery())
    total = await db.scalar(count_query)

    query = query.order_by(ProjectIncident.incident_date.desc())
    query = query.offset((page - 1) * page_size).limit(page_size)
    result = await db.execute(query)
    incidents = result.scalars().all()

    return IncidentList(
        items=incidents, total=total, page=page, page_size=page_size, pages=ceil(total / page_size) if total > 0 else 0
    )


@router.post("", response_model=IncidentResponse, status_code=status.HTTP_201_CREATED)
async def create_incident(
    incident_data: IncidentCreate,
    db: AsyncSession = Depends(get_db),
    current_user: UUID = Depends(get_current_user),
):
    """Create new incident."""
    incident = ProjectIncident(
        incident_number=generate_incident_number(),
        **incident_data.dict(),
        reported_by=current_user,
        created_by=current_user,
    )
    db.add(incident)
    await db.commit()
    await db.refresh(incident)
    return incident


@router.get("/{incident_id}", response_model=IncidentResponse)
async def get_incident(
    incident_id: UUID,
    db: AsyncSession = Depends(get_db),
    current_user: UUID = Depends(get_current_user),
):
    """Get incident by ID."""
    result = await db.execute(select(ProjectIncident).where(ProjectIncident.id == incident_id))
    incident = result.scalar_one_or_none()

    if not incident:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Incident not found")

    return incident


@router.put("/{incident_id}", response_model=IncidentResponse)
async def update_incident(
    incident_id: UUID,
    incident_data: IncidentUpdate,
    db: AsyncSession = Depends(get_db),
    current_user: UUID = Depends(get_current_user),
):
    """Update incident."""
    result = await db.execute(select(ProjectIncident).where(ProjectIncident.id == incident_id))
    incident = result.scalar_one_or_none()

    if not incident:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Incident not found")

    for field, value in incident_data.dict(exclude_unset=True).items():
        setattr(incident, field, value)

    incident.updated_by = current_user
    await db.commit()
    await db.refresh(incident)
    return incident


@router.delete("/{incident_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_incident(
    incident_id: UUID,
    db: AsyncSession = Depends(get_db),
    current_user: UUID = Depends(get_current_user),
):
    """Delete incident."""
    result = await db.execute(select(ProjectIncident).where(ProjectIncident.id == incident_id))
    incident = result.scalar_one_or_none()

    if not incident:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Incident not found")

    await db.delete(incident)
    await db.commit()


@router.post("/{incident_id}/resolve", response_model=IncidentResponse)
async def resolve_incident(
    incident_id: UUID,
    resolve_data: IncidentResolve,
    db: AsyncSession = Depends(get_db),
    current_user: UUID = Depends(get_current_user),
):
    """Mark incident as resolved."""
    result = await db.execute(select(ProjectIncident).where(ProjectIncident.id == incident_id))
    incident = result.scalar_one_or_none()

    if not incident:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Incident not found")

    incident.status = IncidentStatus.RESOLVED
    incident.root_cause = resolve_data.root_cause
    incident.corrective_actions = resolve_data.corrective_actions
    incident.preventive_measures = resolve_data.preventive_measures
    incident.resolved_date = resolve_data.resolved_date
    incident.resolved_by = current_user
    if resolve_data.notes:
        incident.notes = resolve_data.notes

    await db.commit()
    await db.refresh(incident)
    return incident


@router.patch("/{incident_id}/status", response_model=IncidentResponse)
async def update_incident_status(
    incident_id: UUID,
    new_status: IncidentStatus,
    db: AsyncSession = Depends(get_db),
    current_user: UUID = Depends(get_current_user),
):
    """Update incident status."""
    result = await db.execute(select(ProjectIncident).where(ProjectIncident.id == incident_id))
    incident = result.scalar_one_or_none()

    if not incident:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Incident not found")

    incident.status = new_status
    incident.updated_by = current_user
    await db.commit()
    await db.refresh(incident)
    return incident
