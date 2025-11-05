"""Dashboard API endpoints for Project Management."""

from datetime import datetime
from uuid import UUID

from fastapi import APIRouter, Depends
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.deps import get_current_user
from app.database import get_db
from app.models import Project, Task, Resource, ProjectBudget, ProjectCost, ProjectSchedule

router = APIRouter()


@router.get("/stats")
async def get_dashboard_stats(
    db: AsyncSession = Depends(get_db),
    current_user: UUID = Depends(get_current_user),
):
    """Get dashboard statistics for project management."""
    
    # Project stats
    total_projects = await db.scalar(
        select(func.count()).select_from(Project).where(Project.is_active == True)
    )
    
    active_projects = await db.scalar(
        select(func.count()).select_from(Project)
        .where(Project.status == "active", Project.is_active == True)
    )
    
    projects_by_status = {}
    result = await db.execute(
        select(Project.status, func.count(Project.id))
        .where(Project.is_active == True)
        .group_by(Project.status)
    )
    for status, count in result:
        projects_by_status[status] = count
    
    # Task stats
    total_tasks = await db.scalar(
        select(func.count()).select_from(Task)
    )
    
    tasks_by_status = {}
    result = await db.execute(
        select(Task.status, func.count(Task.id))
        .group_by(Task.status)
    )
    for status, count in result:
        tasks_by_status[status] = count
    
    # Resource stats
    total_resources = await db.scalar(
        select(func.count()).select_from(Resource)
    )
    
    available_resources = await db.scalar(
        select(func.count()).select_from(Resource)
        .where(Resource.availability_status == "available")
    )
    
    # Budget stats
    result = await db.execute(
        select(
            func.sum(ProjectBudget.total_budget),
            func.sum(ProjectBudget.total_spent)
        )
    )
    total_budget, total_spent = result.one()
    
    return {
        "projects": {
            "total": total_projects or 0,
            "active": active_projects or 0,
            "by_status": projects_by_status,
        },
        "tasks": {
            "total": total_tasks or 0,
            "by_status": tasks_by_status,
        },
        "resources": {
            "total": total_resources or 0,
            "available": available_resources or 0,
        },
        "budget": {
            "total_budget": float(total_budget) if total_budget else 0,
            "total_spent": float(total_spent) if total_spent else 0,
            "budget_utilization": float((total_spent / total_budget * 100) if total_budget else 0),
        },
    }


@router.get("/recent-activity")
async def get_recent_activity(
    limit: int = 10,
    db: AsyncSession = Depends(get_db),
    current_user: UUID = Depends(get_current_user),
):
    """Get recent activity in project management."""
    
    # Recent projects
    result = await db.execute(
        select(Project)
        .where(Project.is_active == True)
        .order_by(Project.created_at.desc())
        .limit(limit)
    )
    recent_projects = result.scalars().all()
    
    # Recent tasks
    result = await db.execute(
        select(Task)
        .order_by(Task.created_at.desc())
        .limit(limit)
    )
    recent_tasks = result.scalars().all()
    
    return {
        "recent_projects": [
            {
                "id": str(project.id),
                "name": project.name,
                "status": project.status,
                "priority": project.priority,
                "start_date": project.start_date.isoformat() if project.start_date else None,
                "created_at": project.created_at.isoformat(),
            }
            for project in recent_projects
        ],
        "recent_tasks": [
            {
                "id": str(task.id),
                "title": task.title,
                "status": task.status,
                "priority": task.priority,
                "project_id": str(task.project_id),
                "created_at": task.created_at.isoformat(),
            }
            for task in recent_tasks
        ],
    }


@router.get("/alerts")
async def get_alerts(
    db: AsyncSession = Depends(get_db),
    current_user: UUID = Depends(get_current_user),
):
    """Get important alerts for dashboard."""
    
    alerts = []
    
    # Overdue tasks
    result = await db.execute(
        select(Task)
        .where(
            Task.due_date < datetime.now().date(),
            Task.status.in_(["todo", "in_progress"])
        )
    )
    overdue_tasks = result.scalars().all()
    
    if overdue_tasks:
        alerts.append({
            "type": "overdue_tasks",
            "severity": "high",
            "title": "Overdue Tasks",
            "message": f"{len(overdue_tasks)} task(s) are overdue",
            "count": len(overdue_tasks),
        })
    
    # Projects over budget - calculate actual spending from ProjectCost
    result = await db.execute(
        select(
            ProjectBudget.project_id,
            ProjectBudget.total_budget,
            func.coalesce(func.sum(ProjectCost.amount), 0).label('total_spent')
        )
        .outerjoin(ProjectCost, ProjectBudget.project_id == ProjectCost.project_id)
        .where(ProjectBudget.is_approved == True)
        .group_by(ProjectBudget.project_id, ProjectBudget.total_budget)
        .having(func.coalesce(func.sum(ProjectCost.amount), 0) > ProjectBudget.total_budget)
    )
    over_budget = result.all()
    
    if over_budget:
        alerts.append({
            "type": "over_budget",
            "severity": "high",
            "title": "Projects Over Budget",
            "message": f"{len(over_budget)} project(s) are over budget",
            "count": len(over_budget),
        })
    
    # Projects nearing budget limit (>90%)
    result = await db.execute(
        select(
            ProjectBudget.project_id,
            ProjectBudget.total_budget,
            func.coalesce(func.sum(ProjectCost.amount), 0).label('total_spent')
        )
        .outerjoin(ProjectCost, ProjectBudget.project_id == ProjectCost.project_id)
        .where(ProjectBudget.is_approved == True)
        .group_by(ProjectBudget.project_id, ProjectBudget.total_budget)
        .having(
            func.coalesce(func.sum(ProjectCost.amount), 0) > (ProjectBudget.total_budget * 0.9),
            func.coalesce(func.sum(ProjectCost.amount), 0) <= ProjectBudget.total_budget
        )
    )
    near_budget = result.scalars().all()
    
    if near_budget:
        alerts.append({
            "type": "budget_warning",
            "severity": "medium",
            "title": "Budget Warning",
            "message": f"{len(near_budget)} project(s) nearing budget limit",
            "count": len(near_budget),
        })
    
    return {
        "alerts": alerts,
        "total_count": len(alerts),
    }
