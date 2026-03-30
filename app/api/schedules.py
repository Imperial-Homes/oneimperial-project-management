"""Schedule and Milestone API endpoints."""

from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.deps import get_current_user
from app.database import get_db
from app.models import Milestone, ProjectSchedule
from app.schemas import (
    MilestoneCreate,
    MilestoneResponse,
    MilestoneUpdate,
    ProjectScheduleCreate,
    ProjectScheduleResponse,
)

router = APIRouter()


@router.get("/{project_id}", response_model=list[ProjectScheduleResponse])
async def get_project_schedules(
    project_id: UUID,
    db: AsyncSession = Depends(get_db),
    current_user: UUID = Depends(get_current_user),
):
    """Get all schedules for a project."""
    result = await db.execute(
        select(ProjectSchedule).where(ProjectSchedule.project_id == project_id).order_by(ProjectSchedule.version.desc())
    )
    schedules = result.scalars().all()
    return schedules


@router.post("", response_model=ProjectScheduleResponse, status_code=status.HTTP_201_CREATED)
async def create_schedule(
    schedule_data: ProjectScheduleCreate,
    db: AsyncSession = Depends(get_db),
    current_user: UUID = Depends(get_current_user),
):
    """Create project schedule."""
    schedule = ProjectSchedule(**schedule_data.dict(), created_by=current_user)
    db.add(schedule)
    await db.commit()
    await db.refresh(schedule)
    return schedule


@router.get("/milestones/{project_id}", response_model=list[MilestoneResponse])
async def get_project_milestones(
    project_id: UUID,
    status: str | None = Query(None),
    db: AsyncSession = Depends(get_db),
    current_user: UUID = Depends(get_current_user),
):
    """Get project milestones."""
    query = select(Milestone).where(Milestone.project_id == project_id)

    if status:
        query = query.where(Milestone.status == status)

    query = query.order_by(Milestone.due_date)
    result = await db.execute(query)
    milestones = result.scalars().all()
    return milestones


@router.post("/milestones", response_model=MilestoneResponse, status_code=status.HTTP_201_CREATED)
async def create_milestone(
    milestone_data: MilestoneCreate,
    db: AsyncSession = Depends(get_db),
    current_user: UUID = Depends(get_current_user),
):
    """Create milestone."""
    milestone = Milestone(**milestone_data.dict())
    db.add(milestone)
    await db.commit()
    await db.refresh(milestone)
    return milestone


@router.put("/milestones/{milestone_id}", response_model=MilestoneResponse)
async def update_milestone(
    milestone_id: UUID,
    milestone_data: MilestoneUpdate,
    db: AsyncSession = Depends(get_db),
    current_user: UUID = Depends(get_current_user),
):
    """Update milestone."""
    result = await db.execute(select(Milestone).where(Milestone.id == milestone_id))
    milestone = result.scalar_one_or_none()

    if not milestone:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Milestone not found")

    for field, value in milestone_data.dict(exclude_unset=True).items():
        setattr(milestone, field, value)

    await db.commit()
    await db.refresh(milestone)
    return milestone
