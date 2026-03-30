"""Resource Assignment API endpoints."""

from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.deps import get_current_user
from app.database import get_db
from app.models import ResourceAssignment
from app.schemas import ResourceAssignmentCreate, ResourceAssignmentResponse

router = APIRouter()


@router.get("", response_model=list[ResourceAssignmentResponse])
async def list_assignments(
    project_id: UUID | None = Query(None),
    resource_id: UUID | None = Query(None),
    task_id: UUID | None = Query(None),
    db: AsyncSession = Depends(get_db),
    current_user: UUID = Depends(get_current_user),
):
    """List resource assignments with filtering."""
    query = select(ResourceAssignment)

    if project_id:
        query = query.where(ResourceAssignment.project_id == project_id)

    if resource_id:
        query = query.where(ResourceAssignment.resource_id == resource_id)

    if task_id:
        query = query.where(ResourceAssignment.task_id == task_id)

    result = await db.execute(query)
    assignments = result.scalars().all()
    return assignments


@router.post("", response_model=ResourceAssignmentResponse, status_code=status.HTTP_201_CREATED)
async def create_assignment(
    assignment_data: ResourceAssignmentCreate,
    db: AsyncSession = Depends(get_db),
    current_user: UUID = Depends(get_current_user),
):
    """Create resource assignment."""
    # Check for conflicts
    result = await db.execute(
        select(ResourceAssignment).where(
            ResourceAssignment.resource_id == assignment_data.resource_id,
            ResourceAssignment.start_date <= assignment_data.end_date,
            ResourceAssignment.end_date >= assignment_data.start_date,
            ResourceAssignment.status.in_(["planned", "active"]),
        )
    )
    existing = result.scalars().all()

    if existing:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, detail="Resource has conflicting assignments in this period"
        )

    assignment = ResourceAssignment(**assignment_data.dict(), created_by=current_user)
    db.add(assignment)
    await db.commit()
    await db.refresh(assignment)
    return assignment


@router.delete("/{assignment_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_assignment(
    assignment_id: UUID,
    db: AsyncSession = Depends(get_db),
    current_user: UUID = Depends(get_current_user),
):
    """Delete resource assignment."""
    result = await db.execute(select(ResourceAssignment).where(ResourceAssignment.id == assignment_id))
    assignment = result.scalar_one_or_none()

    if not assignment:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Assignment not found")

    await db.delete(assignment)
    await db.commit()
