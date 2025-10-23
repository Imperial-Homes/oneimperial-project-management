"""Task API endpoints."""

from datetime import datetime
from math import ceil
from typing import Optional
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.deps import get_current_user
from app.database import get_db
from app.models import Task, TaskDependency
from app.schemas import TaskCreate, TaskUpdate, TaskResponse, TaskList

router = APIRouter()


def generate_task_code() -> str:
    """Generate task code."""
    return f"TSK-{datetime.now().year}-{datetime.now().strftime('%m%d%H%M%S')}"


@router.get("", response_model=TaskList)
async def list_tasks(
    page: int = Query(1, ge=1),
    page_size: int = Query(50, ge=1, le=100),
    project_id: Optional[UUID] = Query(None),
    phase_id: Optional[UUID] = Query(None),
    assignee_id: Optional[UUID] = Query(None),
    status: Optional[str] = Query(None),
    priority: Optional[str] = Query(None),
    search: Optional[str] = Query(None),
    db: AsyncSession = Depends(get_db),
    current_user: UUID = Depends(get_current_user),
):
    """List tasks with filtering."""
    query = select(Task)
    
    if project_id:
        query = query.where(Task.project_id == project_id)
    
    if phase_id:
        query = query.where(Task.phase_id == phase_id)
    
    if assignee_id:
        query = query.where(Task.assignee_id == assignee_id)
    
    if status:
        query = query.where(Task.status == status)
    
    if priority:
        query = query.where(Task.priority == priority)
    
    if search:
        query = query.where(
            (Task.task_code.ilike(f"%{search}%")) |
            (Task.name.ilike(f"%{search}%"))
        )
    
    count_query = select(func.count()).select_from(query.subquery())
    total = await db.scalar(count_query)
    
    query = query.order_by(Task.created_at.desc()).offset((page - 1) * page_size).limit(page_size)
    result = await db.execute(query)
    tasks = result.scalars().all()
    
    return TaskList(
        items=tasks,
        total=total,
        page=page,
        page_size=page_size,
        pages=ceil(total / page_size) if total > 0 else 0
    )


@router.post("", response_model=TaskResponse, status_code=status.HTTP_201_CREATED)
async def create_task(
    task_data: TaskCreate,
    db: AsyncSession = Depends(get_db),
    current_user: UUID = Depends(get_current_user),
):
    """Create new task with dependencies."""
    # Check if task code exists
    result = await db.execute(
        select(Task).where(Task.task_code == task_data.task_code)
    )
    if result.scalar_one_or_none():
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Task code already exists"
        )
    
    # Create task
    task = Task(
        project_id=task_data.project_id,
        phase_id=task_data.phase_id,
        parent_task_id=task_data.parent_task_id,
        task_code=task_data.task_code,
        name=task_data.name,
        description=task_data.description,
        assignee_id=task_data.assignee_id,
        start_date=task_data.start_date,
        due_date=task_data.due_date,
        estimated_hours=task_data.estimated_hours,
        priority=task_data.priority,
    )
    
    # Create dependencies
    dependencies = []
    for dep_data in task_data.dependencies:
        dependency = TaskDependency(
            dependency_task_id=dep_data.dependency_task_id,
            dependency_type=dep_data.dependency_type,
            lag_days=dep_data.lag_days,
        )
        dependencies.append(dependency)
    
    task.dependencies = dependencies
    
    db.add(task)
    await db.commit()
    await db.refresh(task)
    return task


@router.get("/{task_id}", response_model=TaskResponse)
async def get_task(
    task_id: UUID,
    db: AsyncSession = Depends(get_db),
    current_user: UUID = Depends(get_current_user),
):
    """Get task by ID."""
    result = await db.execute(
        select(Task).where(Task.id == task_id)
    )
    task = result.scalar_one_or_none()
    
    if not task:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Task not found"
        )
    
    return task


@router.put("/{task_id}", response_model=TaskResponse)
async def update_task(
    task_id: UUID,
    task_data: TaskUpdate,
    db: AsyncSession = Depends(get_db),
    current_user: UUID = Depends(get_current_user),
):
    """Update task."""
    result = await db.execute(
        select(Task).where(Task.id == task_id)
    )
    task = result.scalar_one_or_none()
    
    if not task:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Task not found"
        )
    
    for field, value in task_data.dict(exclude_unset=True).items():
        setattr(task, field, value)
    
    if task.status == "done" and not task.completion_date:
        task.completion_date = datetime.now().date()
    
    await db.commit()
    await db.refresh(task)
    return task


@router.delete("/{task_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_task(
    task_id: UUID,
    db: AsyncSession = Depends(get_db),
    current_user: UUID = Depends(get_current_user),
):
    """Delete task."""
    result = await db.execute(
        select(Task).where(Task.id == task_id)
    )
    task = result.scalar_one_or_none()
    
    if not task:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Task not found"
        )
    
    await db.delete(task)
    await db.commit()
