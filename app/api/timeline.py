"""Timeline and Gantt chart API endpoints."""

from datetime import datetime, timedelta
from typing import List, Optional
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy import and_, func
from sqlalchemy.orm import Session, joinedload

from app.core.auth import get_current_user
from app.database import get_db
from app.models.timeline import ProjectTimeline, TimelineTaskDependency, TimelineMilestone
from app.models.project import Project
from app.models.task import Task
from app.schemas.timeline import (
    ProjectTimelineCreate,
    ProjectTimelineUpdate,
    ProjectTimelineResponse,
    TaskDependencyCreate,
    TaskDependencyUpdate,
    TaskDependencyResponse,
    TimelineMilestoneCreate,
    TimelineMilestoneUpdate,
    TimelineMilestoneResponse,
    GanttChartResponse,
    GanttTaskData,
)

router = APIRouter()


# ============================================================================
# Timeline Endpoints
# ============================================================================

@router.post("/", response_model=ProjectTimelineResponse, status_code=status.HTTP_201_CREATED)
def create_timeline(
    timeline_data: ProjectTimelineCreate,
    current_user: dict = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Create a new project timeline."""
    # Verify project exists
    project = db.query(Project).filter(Project.id == timeline_data.project_id).first()
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")
    
    timeline = ProjectTimeline(
        **timeline_data.model_dump(),
        created_by=UUID(current_user["sub"])
    )
    db.add(timeline)
    db.commit()
    db.refresh(timeline)
    return timeline


@router.get("/{timeline_id}", response_model=ProjectTimelineResponse)
def get_timeline(
    timeline_id: UUID,
    current_user: dict = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get timeline by ID."""
    timeline = db.query(ProjectTimeline).options(
        joinedload(ProjectTimeline.dependencies)
    ).filter(ProjectTimeline.id == timeline_id).first()
    
    if not timeline:
        raise HTTPException(status_code=404, detail="Timeline not found")
    
    return timeline


@router.get("/project/{project_id}", response_model=List[ProjectTimelineResponse])
def get_project_timelines(
    project_id: UUID,
    active_only: bool = Query(True),
    current_user: dict = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get all timelines for a project."""
    query = db.query(ProjectTimeline).filter(ProjectTimeline.project_id == project_id)
    
    if active_only:
        query = query.filter(ProjectTimeline.is_active == True)
    
    timelines = query.options(joinedload(ProjectTimeline.dependencies)).all()
    return timelines


@router.put("/{timeline_id}", response_model=ProjectTimelineResponse)
def update_timeline(
    timeline_id: UUID,
    timeline_data: ProjectTimelineUpdate,
    current_user: dict = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Update timeline."""
    timeline = db.query(ProjectTimeline).filter(ProjectTimeline.id == timeline_id).first()
    if not timeline:
        raise HTTPException(status_code=404, detail="Timeline not found")
    
    update_data = timeline_data.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        setattr(timeline, field, value)
    
    timeline.updated_by = UUID(current_user["sub"])
    db.commit()
    db.refresh(timeline)
    return timeline


@router.delete("/{timeline_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_timeline(
    timeline_id: UUID,
    current_user: dict = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Delete timeline."""
    timeline = db.query(ProjectTimeline).filter(ProjectTimeline.id == timeline_id).first()
    if not timeline:
        raise HTTPException(status_code=404, detail="Timeline not found")
    
    db.delete(timeline)
    db.commit()
    return None


# ============================================================================
# Task Dependency Endpoints
# ============================================================================

@router.post("/dependencies", response_model=TaskDependencyResponse, status_code=status.HTTP_201_CREATED)
def create_task_dependency(
    dependency_data: TaskDependencyCreate,
    current_user: dict = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Create a task dependency."""
    # Verify tasks exist
    predecessor = db.query(Task).filter(Task.id == dependency_data.predecessor_task_id).first()
    successor = db.query(Task).filter(Task.id == dependency_data.successor_task_id).first()
    
    if not predecessor or not successor:
        raise HTTPException(status_code=404, detail="One or both tasks not found")
    
    # Check for circular dependencies
    if dependency_data.predecessor_task_id == dependency_data.successor_task_id:
        raise HTTPException(status_code=400, detail="Task cannot depend on itself")
    
    dependency = TimelineTaskDependency(**dependency_data.model_dump())
    db.add(dependency)
    db.commit()
    db.refresh(dependency)
    return dependency


@router.get("/dependencies/{dependency_id}", response_model=TaskDependencyResponse)
def get_task_dependency(
    dependency_id: UUID,
    current_user: dict = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get task dependency by ID."""
    dependency = db.query(TimelineTaskDependency).filter(TimelineTaskDependency.id == dependency_id).first()
    if not dependency:
        raise HTTPException(status_code=404, detail="Dependency not found")
    return dependency


@router.put("/dependencies/{dependency_id}", response_model=TaskDependencyResponse)
def update_task_dependency(
    dependency_id: UUID,
    dependency_data: TaskDependencyUpdate,
    current_user: dict = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Update task dependency."""
    dependency = db.query(TimelineTaskDependency).filter(TimelineTaskDependency.id == dependency_id).first()
    if not dependency:
        raise HTTPException(status_code=404, detail="Dependency not found")
    
    for key, value in dependency_data.model_dump(exclude_unset=True).items():
        setattr(dependency, key, value)
    
    db.commit()
    db.refresh(dependency)
    return dependency


@router.delete("/dependencies/{dependency_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_task_dependency(
    dependency_id: UUID,
    current_user: dict = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Delete task dependency."""
    dependency = db.query(TimelineTaskDependency).filter(TimelineTaskDependency.id == dependency_id).first()
    if not dependency:
        raise HTTPException(status_code=404, detail="Dependency not found")
    
    db.delete(dependency)
    db.commit()
    return {"message": "Dependency deleted successfully"}


# ============================================================================
# TimelineMilestone Endpoints
# ============================================================================

@router.post("/milestones", response_model=TimelineMilestoneResponse, status_code=status.HTTP_201_CREATED)
def create_milestone(
    milestone_data: TimelineMilestoneCreate,
    current_user: dict = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Create a new milestone."""
    # Verify project exists
    project = db.query(Project).filter(Project.id == milestone_data.project_id).first()
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")
    
    milestone = TimelineMilestone(
        **milestone_data.model_dump(),
        created_by=UUID(current_user["sub"])
    )
    db.add(milestone)
    db.commit()
    db.refresh(milestone)
    return milestone


@router.get("/milestones/{milestone_id}", response_model=TimelineMilestoneResponse)
def get_milestone(
    milestone_id: UUID,
    current_user: dict = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get milestone by ID."""
    milestone = db.query(TimelineMilestone).filter(TimelineMilestone.id == milestone_id).first()
    if not milestone:
        raise HTTPException(status_code=404, detail="TimelineMilestone not found")
    return milestone


@router.get("/milestones/project/{project_id}", response_model=List[TimelineMilestoneResponse])
def get_project_milestones(
    project_id: UUID,
    status: Optional[str] = Query(None),
    current_user: dict = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get all milestones for a project."""
    query = db.query(TimelineMilestone).filter(TimelineMilestone.project_id == project_id)
    
    if status:
        query = query.filter(TimelineMilestone.status == status)
    
    milestones = query.order_by(TimelineMilestone.target_date).all()
    return milestones


@router.put("/milestones/{milestone_id}", response_model=TimelineMilestoneResponse)
def update_milestone(
    milestone_id: UUID,
    milestone_data: TimelineMilestoneUpdate,
    current_user: dict = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Update milestone."""
    milestone = db.query(TimelineMilestone).filter(TimelineMilestone.id == milestone_id).first()
    if not milestone:
        raise HTTPException(status_code=404, detail="TimelineMilestone not found")
    
    update_data = milestone_data.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        setattr(milestone, field, value)
    
    # If marking as achieved, set achieved_by and actual_date
    if update_data.get("status") == "achieved" and not milestone.actual_date:
        milestone.actual_date = datetime.utcnow()
        milestone.achieved_by = UUID(current_user["sub"])
    
    db.commit()
    db.refresh(milestone)
    return milestone


@router.delete("/milestones/{milestone_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_milestone(
    milestone_id: UUID,
    current_user: dict = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Delete milestone."""
    milestone = db.query(TimelineMilestone).filter(TimelineMilestone.id == milestone_id).first()
    if not milestone:
        raise HTTPException(status_code=404, detail="TimelineMilestone not found")
    
    db.delete(milestone)
    db.commit()
    return None


# ============================================================================
# Gantt Chart Data Endpoint
# ============================================================================

@router.get("/gantt/{project_id}", response_model=GanttChartResponse)
def get_gantt_chart_data(
    project_id: UUID,
    current_user: dict = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get Gantt chart data for a project."""
    # Get project
    project = db.query(Project).filter(Project.id == project_id).first()
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")
    
    # Get all tasks for the project
    tasks = db.query(Task).filter(
        Task.project_id == project_id,
        Task.is_active == True
    ).all()
    
    # Get milestones
    milestones = db.query(TimelineMilestone).filter(
        TimelineMilestone.project_id == project_id
    ).order_by(TimelineMilestone.target_date).all()
    
    # Get dependencies
    task_ids = [task.id for task in tasks]
    dependencies = db.query(TimelineTaskDependency).filter(
        TimelineTaskDependency.predecessor_task_id.in_(task_ids)
    ).all()
    
    # Build dependency map
    dependency_map = {}
    for dep in dependencies:
        if dep.successor_task_id not in dependency_map:
            dependency_map[dep.successor_task_id] = []
        dependency_map[dep.successor_task_id].append(dep.predecessor_task_id)
    
    # Calculate critical path (simplified - just mark tasks with dependencies as critical)
    critical_tasks = [dep.is_critical for dep in dependencies if dep.is_critical]
    
    # Build Gantt task data
    gantt_tasks = []
    for task in tasks:
        duration = 0
        if task.start_date and task.due_date:
            duration = (task.due_date - task.start_date).days
        
        gantt_tasks.append(GanttTaskData(
            id=task.id,
            name=task.title,
            start_date=task.start_date or project.start_date or datetime.utcnow().date(),
            end_date=task.due_date or (task.start_date or datetime.utcnow().date()) + timedelta(days=1),
            duration=max(duration, 1),
            progress=task.completion_percentage or 0,
            dependencies=dependency_map.get(task.id, []),
            is_milestone=False,
            is_critical=task.id in [dep.successor_task_id for dep in dependencies if dep.is_critical],
            assigned_resources=[]
        ))
    
    # Calculate project duration
    if tasks:
        min_date = min((t.start_date for t in tasks if t.start_date), default=project.start_date or datetime.utcnow().date())
        max_date = max((t.due_date for t in tasks if t.due_date), default=project.target_end_date or datetime.utcnow().date())
        total_duration = (max_date - min_date).days
    else:
        min_date = project.start_date or datetime.utcnow().date()
        max_date = project.target_end_date or datetime.utcnow().date()
        total_duration = 0
    
    return GanttChartResponse(
        project_id=project.id,
        project_name=project.name,
        start_date=min_date,
        end_date=max_date,
        tasks=gantt_tasks,
        milestones=milestones,
        critical_path=[dep.successor_task_id for dep in dependencies if dep.is_critical],
        total_duration=total_duration
    )
