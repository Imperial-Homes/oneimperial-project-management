"""Progress tracking API endpoints."""

from datetime import datetime
from decimal import Decimal
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy import desc, func
from sqlalchemy.orm import Session

from app.core.deps import get_current_user
from app.database import get_db
from app.models.project import Project
from app.models.task import Task
from app.models.timeline import ProjectProgress, TaskProgress, TimelineMilestone
from app.schemas.timeline import (
    ProgressSummary,
    ProjectProgressCreate,
    ProjectProgressResponse,
    TaskProgressCreate,
    TaskProgressResponse,
    TaskProgressUpdate,
)

router = APIRouter()


# ============================================================================
# Project Progress Endpoints
# ============================================================================


@router.post("/", response_model=ProjectProgressResponse, status_code=status.HTTP_201_CREATED)
def record_project_progress(
    progress_data: ProjectProgressCreate, current_user: dict = Depends(get_current_user), db: Session = Depends(get_db)
):
    """Record project progress."""
    # Verify project exists
    project = db.query(Project).filter(Project.id == progress_data.project_id).first()
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")

    # Calculate performance indices
    earned_value = progress_data.earned_value
    planned_value = progress_data.planned_value
    actual_cost = progress_data.actual_cost

    spi = None
    cpi = None

    if planned_value and planned_value > 0:
        spi = earned_value / planned_value if earned_value else Decimal("0")

    if actual_cost and actual_cost > 0:
        cpi = earned_value / actual_cost if earned_value else Decimal("0")

    progress = ProjectProgress(
        **progress_data.model_dump(),
        schedule_performance_index=spi,
        cost_performance_index=cpi,
        recorded_by=UUID(current_user["sub"]),
    )

    db.add(progress)
    db.commit()
    db.refresh(progress)
    return progress


@router.get("/{progress_id}", response_model=ProjectProgressResponse)
def get_project_progress(
    progress_id: UUID, current_user: dict = Depends(get_current_user), db: Session = Depends(get_db)
):
    """Get project progress by ID."""
    progress = db.query(ProjectProgress).filter(ProjectProgress.id == progress_id).first()
    if not progress:
        raise HTTPException(status_code=404, detail="Progress record not found")
    return progress


@router.get("/project/{project_id}/history", response_model=list[ProjectProgressResponse])
def get_project_progress_history(
    project_id: UUID,
    start_date: datetime | None = Query(None),
    end_date: datetime | None = Query(None),
    limit: int = Query(100, le=1000),
    current_user: dict = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Get project progress history."""
    query = db.query(ProjectProgress).filter(ProjectProgress.project_id == project_id)

    if start_date:
        query = query.filter(ProjectProgress.recorded_date >= start_date)
    if end_date:
        query = query.filter(ProjectProgress.recorded_date <= end_date)

    progress_history = query.order_by(desc(ProjectProgress.recorded_date)).limit(limit).all()
    return progress_history


@router.get("/project/{project_id}/latest", response_model=ProjectProgressResponse)
def get_latest_project_progress(
    project_id: UUID, current_user: dict = Depends(get_current_user), db: Session = Depends(get_db)
):
    """Get latest project progress."""
    progress = (
        db.query(ProjectProgress)
        .filter(ProjectProgress.project_id == project_id)
        .order_by(desc(ProjectProgress.recorded_date))
        .first()
    )

    if not progress:
        raise HTTPException(status_code=404, detail="No progress records found for this project")

    return progress


@router.get("/project/{project_id}/summary", response_model=ProgressSummary)
def get_project_progress_summary(
    project_id: UUID, current_user: dict = Depends(get_current_user), db: Session = Depends(get_db)
):
    """Get comprehensive project progress summary."""
    # Get project
    project = db.query(Project).filter(Project.id == project_id).first()
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")

    # Get latest progress
    latest_progress = (
        db.query(ProjectProgress)
        .filter(ProjectProgress.project_id == project_id)
        .order_by(desc(ProjectProgress.recorded_date))
        .first()
    )

    # Get milestone counts
    milestones = (
        db.query(TimelineMilestone.status, func.count(TimelineMilestone.id).label("count"))
        .filter(TimelineMilestone.project_id == project_id)
        .group_by(TimelineMilestone.status)
        .all()
    )

    milestone_counts = {status: count for status, count in milestones}

    # Get task counts
    tasks = (
        db.query(Task.status, func.count(Task.id).label("count"))
        .filter(Task.project_id == project_id, Task.is_active == True)
        .group_by(Task.status)
        .all()
    )

    task_counts = {status: count for status, count in tasks}

    # Determine schedule and cost status
    schedule_status = "on_track"
    if latest_progress:
        if latest_progress.schedule_variance < -5:
            schedule_status = "behind"
        elif latest_progress.schedule_variance > 5:
            schedule_status = "ahead"

    cost_status = "on_budget"
    if latest_progress:
        if latest_progress.cost_variance < -1000:
            cost_status = "over_budget"
        elif latest_progress.cost_variance > 1000:
            cost_status = "under_budget"

    return ProgressSummary(
        project_id=project.id,
        project_name=project.name,
        overall_progress=latest_progress.overall_progress if latest_progress else Decimal("0"),
        physical_progress=latest_progress.physical_progress if latest_progress else Decimal("0"),
        financial_progress=latest_progress.financial_progress if latest_progress else Decimal("0"),
        schedule_status=schedule_status,
        cost_status=cost_status,
        days_ahead_behind=int(latest_progress.schedule_variance) if latest_progress else 0,
        amount_over_under=latest_progress.cost_variance if latest_progress else Decimal("0"),
        milestones_achieved=milestone_counts.get("achieved", 0),
        milestones_pending=milestone_counts.get("pending", 0),
        milestones_missed=milestone_counts.get("missed", 0),
        tasks_completed=task_counts.get("completed", 0),
        tasks_in_progress=task_counts.get("in_progress", 0),
        tasks_not_started=task_counts.get("not_started", 0) + task_counts.get("pending", 0),
        last_updated=latest_progress.recorded_date if latest_progress else datetime.utcnow(),
    )


# ============================================================================
# Task Progress Endpoints
# ============================================================================


@router.post("/tasks", response_model=TaskProgressResponse, status_code=status.HTTP_201_CREATED)
def record_task_progress(
    progress_data: TaskProgressCreate, current_user: dict = Depends(get_current_user), db: Session = Depends(get_db)
):
    """Record task progress."""
    # Verify task exists
    task = db.query(Task).filter(Task.id == progress_data.task_id).first()
    if not task:
        raise HTTPException(status_code=404, detail="Task not found")

    progress = TaskProgress(**progress_data.model_dump(), recorded_by=UUID(current_user["sub"]))

    # Update task completion percentage
    task.completion_percentage = progress_data.completion_percentage
    task.status = progress_data.status

    db.add(progress)
    db.commit()
    db.refresh(progress)
    return progress


@router.get("/tasks/{progress_id}", response_model=TaskProgressResponse)
def get_task_progress(progress_id: UUID, current_user: dict = Depends(get_current_user), db: Session = Depends(get_db)):
    """Get task progress by ID."""
    progress = db.query(TaskProgress).filter(TaskProgress.id == progress_id).first()
    if not progress:
        raise HTTPException(status_code=404, detail="Progress record not found")
    return progress


@router.get("/tasks/task/{task_id}/history", response_model=list[TaskProgressResponse])
def get_task_progress_history(
    task_id: UUID,
    limit: int = Query(50, le=500),
    current_user: dict = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Get task progress history."""
    progress_history = (
        db.query(TaskProgress)
        .filter(TaskProgress.task_id == task_id)
        .order_by(desc(TaskProgress.recorded_date))
        .limit(limit)
        .all()
    )

    return progress_history


@router.put("/tasks/{progress_id}", response_model=TaskProgressResponse)
def update_task_progress(
    progress_id: UUID,
    progress_data: TaskProgressUpdate,
    current_user: dict = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Update task progress."""
    progress = db.query(TaskProgress).filter(TaskProgress.id == progress_id).first()
    if not progress:
        raise HTTPException(status_code=404, detail="Progress record not found")

    update_data = progress_data.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        setattr(progress, field, value)

    # Update associated task if completion percentage or status changed
    if "completion_percentage" in update_data or "status" in update_data:
        task = db.query(Task).filter(Task.id == progress.task_id).first()
        if task:
            if "completion_percentage" in update_data:
                task.completion_percentage = update_data["completion_percentage"]
            if "status" in update_data:
                task.status = update_data["status"]

    db.commit()
    db.refresh(progress)
    return progress


@router.delete("/tasks/{progress_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_task_progress(
    progress_id: UUID, current_user: dict = Depends(get_current_user), db: Session = Depends(get_db)
):
    """Delete task progress record."""
    progress = db.query(TaskProgress).filter(TaskProgress.id == progress_id).first()
    if not progress:
        raise HTTPException(status_code=404, detail="Progress record not found")

    db.delete(progress)
    db.commit()
    return None


# ============================================================================
# Bulk Progress Update
# ============================================================================


@router.post("/tasks/bulk", response_model=list[TaskProgressResponse])
def bulk_update_task_progress(
    progress_data_list: list[TaskProgressCreate],
    current_user: dict = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Bulk update task progress for multiple tasks."""
    created_progress = []

    for progress_data in progress_data_list:
        # Verify task exists
        task = db.query(Task).filter(Task.id == progress_data.task_id).first()
        if not task:
            continue  # Skip invalid tasks

        progress = TaskProgress(**progress_data.model_dump(), recorded_by=UUID(current_user["sub"]))

        # Update task
        task.completion_percentage = progress_data.completion_percentage
        task.status = progress_data.status

        db.add(progress)
        created_progress.append(progress)

    db.commit()

    # Refresh all created progress records
    for progress in created_progress:
        db.refresh(progress)

    return created_progress
