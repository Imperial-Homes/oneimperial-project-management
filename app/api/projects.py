"""Project API endpoints."""

from datetime import datetime
from math import ceil
from uuid import UUID

from fastapi import APIRouter, BackgroundTasks, Depends, HTTPException, Query, status
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.deps import get_current_user
from app.database import get_db
from app.models import Project, ProjectPhase
from app.schemas import ProjectCreate, ProjectList, ProjectResponse, ProjectUpdate
from app.utils.notification_service import notification_service

router = APIRouter()


def generate_project_code() -> str:
    """Generate project code."""
    return f"PRJ-{datetime.now().year}-{datetime.now().strftime('%m%d%H%M%S')}"


@router.get("", response_model=ProjectList)
async def list_projects(
    page: int = Query(1, ge=1),
    page_size: int = Query(50, ge=1, le=500),
    status: str | None = Query(None),
    project_type: str | None = Query(None),
    manager_id: UUID | None = Query(None),
    client_id: UUID | None = Query(None),
    is_active: bool | None = Query(None),
    search: str | None = Query(None),
    db: AsyncSession = Depends(get_db),
    current_user: UUID = Depends(get_current_user),
):
    """List projects with filtering."""
    from sqlalchemy.orm import selectinload

    query = select(Project).options(selectinload(Project.phases))

    if status:
        query = query.where(Project.status == status)

    if project_type:
        query = query.where(Project.project_type == project_type)

    if manager_id:
        query = query.where(Project.manager_id == manager_id)

    if client_id:
        query = query.where(Project.client_id == client_id)

    if is_active is not None:
        query = query.where(Project.is_active == is_active)

    if search:
        query = query.where((Project.project_code.ilike(f"%{search}%")) | (Project.name.ilike(f"%{search}%")))

    count_query = select(func.count()).select_from(query.subquery())
    total = await db.scalar(count_query)

    query = query.order_by(Project.created_at.desc()).offset((page - 1) * page_size).limit(page_size)
    result = await db.execute(query)
    projects = result.scalars().all()

    return ProjectList(
        items=projects, total=total, page=page, page_size=page_size, pages=ceil(total / page_size) if total > 0 else 0
    )


@router.post("", response_model=ProjectResponse, status_code=status.HTTP_201_CREATED)
async def create_project(
    project_data: ProjectCreate,
    background_tasks: BackgroundTasks,
    db: AsyncSession = Depends(get_db),
    current_user: UUID = Depends(get_current_user),
):
    """Create new project with phases."""

    # Check if project code exists
    result = await db.execute(select(Project).where(Project.project_code == project_data.project_code))
    if result.scalar_one_or_none():
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Project code already exists")

    # Create project
    project = Project(
        project_code=project_data.project_code,
        name=project_data.name,
        description=project_data.description,
        project_type=project_data.project_type,
        client_id=project_data.client_id,
        start_date=project_data.start_date,
        target_end_date=project_data.target_end_date,
        priority=project_data.priority,
        budget=project_data.budget,
        currency=project_data.currency,
        manager_id=project_data.manager_id,
        location=project_data.location,
        created_by=current_user,
    )

    # Create phases
    phases = []
    for phase_data in project_data.phases:
        phase = ProjectPhase(
            name=phase_data.name,
            description=phase_data.description,
            sequence_number=phase_data.sequence_number,
            start_date=phase_data.start_date,
            end_date=phase_data.end_date,
        )
        phases.append(phase)

    project.phases = phases

    db.add(project)
    await db.commit()
    await db.refresh(project, ["phases"])

    # Notify manager if assigned
    if project.manager_id:
        background_tasks.add_task(
            notification_service.send_notification,
            user_id=project.manager_id,
            title="New Project Assigned",
            message=f"You have been assigned as manager for project: '{project.name}'",
            type="info",
            link="/project-management/projects",
        )

    return project


@router.get("/dropdown", response_model=list[dict])
async def projects_dropdown(
    project_type: str | None = Query(None),
    db: AsyncSession = Depends(get_db),
    current_user: UUID = Depends(get_current_user),
):
    """Lightweight list for dropdown selects — returns id, name, project_type."""
    query = select(Project.id, Project.name, Project.project_type).where(Project.is_active == True)  # noqa: E712
    if project_type:
        query = query.where(Project.project_type == project_type)
    query = query.order_by(Project.name)
    result = await db.execute(query)
    rows = result.all()
    return [{"id": str(r.id), "name": r.name, "project_type": r.project_type} for r in rows]


@router.get("/{project_id}", response_model=ProjectResponse)
async def get_project(
    project_id: UUID,
    db: AsyncSession = Depends(get_db),
    current_user: UUID = Depends(get_current_user),
):
    """Get project by ID."""
    from sqlalchemy.orm import selectinload

    result = await db.execute(select(Project).options(selectinload(Project.phases)).where(Project.id == project_id))
    project = result.scalar_one_or_none()

    if not project:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Project not found")

    return project


@router.put("/{project_id}", response_model=ProjectResponse)
async def update_project(
    project_id: UUID,
    project_data: ProjectUpdate,
    background_tasks: BackgroundTasks,
    db: AsyncSession = Depends(get_db),
    current_user: UUID = Depends(get_current_user),
):
    """Update project."""
    from sqlalchemy.orm import selectinload

    result = await db.execute(select(Project).options(selectinload(Project.phases)).where(Project.id == project_id))
    project = result.scalar_one_or_none()

    if not project:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Project not found")

    old_manager_id = project.manager_id

    for field, value in project_data.dict(exclude_unset=True).items():
        setattr(project, field, value)

    project.updated_by = current_user
    await db.commit()
    await db.refresh(project, ["phases"])

    # Notify new manager if reassigned
    if project.manager_id and project.manager_id != old_manager_id:
        background_tasks.add_task(
            notification_service.send_notification,
            user_id=project.manager_id,
            title="Project Reassigned",
            message=f"You have been assigned as manager for project: '{project.name}'",
            type="info",
            link="/project-management/projects",
        )

    return project


@router.delete("/{project_id}", status_code=status.HTTP_204_NO_CONTENT)
async def archive_project(
    project_id: UUID,
    db: AsyncSession = Depends(get_db),
    current_user: UUID = Depends(get_current_user),
):
    """Archive project."""
    result = await db.execute(select(Project).where(Project.id == project_id))
    project = result.scalar_one_or_none()

    if not project:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Project not found")

    project.is_active = False
    project.updated_by = current_user
    await db.commit()


@router.put("/{project_id}/status", response_model=ProjectResponse)
async def update_project_status(
    project_id: UUID,
    new_status: str,
    background_tasks: BackgroundTasks,
    db: AsyncSession = Depends(get_db),
    current_user: UUID = Depends(get_current_user),
):
    """Update project status."""
    from sqlalchemy.orm import selectinload

    result = await db.execute(select(Project).options(selectinload(Project.phases)).where(Project.id == project_id))
    project = result.scalar_one_or_none()

    if not project:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Project not found")

    project.status = new_status
    if new_status == "completed":
        project.actual_end_date = datetime.now().date()

    project.updated_by = current_user
    await db.commit()
    await db.refresh(project, ["phases"])

    # Notify manager of status change
    if project.manager_id:
        background_tasks.add_task(
            notification_service.send_notification,
            user_id=project.manager_id,
            title="Project Status Updated",
            message=f"Status of project '{project.name}' changed to {new_status}",
            type="success" if new_status == "completed" else "info",
            link="/project-management/projects",
        )

    return project
