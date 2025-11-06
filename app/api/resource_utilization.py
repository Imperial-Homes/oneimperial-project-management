"""Resource utilization API endpoints."""

from datetime import datetime, timedelta
from decimal import Decimal
from typing import List, Optional
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy import and_, func, desc
from sqlalchemy.orm import Session

from app.core.auth import get_current_user
from app.database import get_db
from app.models.timeline import ResourceUtilization
from app.models.resource import Resource, ResourceAssignment
from app.models.task import Task
from app.schemas.timeline import (
    ResourceUtilizationCreate,
    ResourceUtilizationResponse,
    ResourceUtilizationSummary,
)

router = APIRouter()


# ============================================================================
# Resource Utilization Endpoints
# ============================================================================

@router.post("/", response_model=ResourceUtilizationResponse, status_code=status.HTTP_201_CREATED)
def record_resource_utilization(
    utilization_data: ResourceUtilizationCreate,
    current_user: dict = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Record resource utilization."""
    # Verify resource exists
    resource = db.query(Resource).filter(Resource.id == utilization_data.resource_id).first()
    if not resource:
        raise HTTPException(status_code=404, detail="Resource not found")
    
    # Calculate rates
    utilization_rate = None
    efficiency_rate = None
    idle_hours = None
    
    if utilization_data.total_available_hours > 0:
        utilization_rate = (utilization_data.allocated_hours / utilization_data.total_available_hours) * 100
        idle_hours = utilization_data.total_available_hours - utilization_data.allocated_hours
    
    if utilization_data.allocated_hours > 0:
        efficiency_rate = (utilization_data.actual_hours_worked / utilization_data.allocated_hours) * 100
    
    utilization = ResourceUtilization(
        **utilization_data.model_dump(),
        utilization_rate=utilization_rate,
        efficiency_rate=efficiency_rate,
        idle_hours=idle_hours
    )
    
    db.add(utilization)
    db.commit()
    db.refresh(utilization)
    return utilization


@router.get("/{utilization_id}", response_model=ResourceUtilizationResponse)
def get_resource_utilization(
    utilization_id: UUID,
    current_user: dict = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get resource utilization by ID."""
    utilization = db.query(ResourceUtilization).filter(
        ResourceUtilization.id == utilization_id
    ).first()
    
    if not utilization:
        raise HTTPException(status_code=404, detail="Utilization record not found")
    
    return utilization


@router.get("/resource/{resource_id}/history", response_model=List[ResourceUtilizationResponse])
def get_resource_utilization_history(
    resource_id: UUID,
    start_date: Optional[datetime] = Query(None),
    end_date: Optional[datetime] = Query(None),
    limit: int = Query(100, le=1000),
    current_user: dict = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get resource utilization history."""
    query = db.query(ResourceUtilization).filter(
        ResourceUtilization.resource_id == resource_id
    )
    
    if start_date:
        query = query.filter(ResourceUtilization.period_start >= start_date)
    if end_date:
        query = query.filter(ResourceUtilization.period_end <= end_date)
    
    utilization_history = query.order_by(desc(ResourceUtilization.period_start)).limit(limit).all()
    return utilization_history


@router.get("/resource/{resource_id}/current", response_model=ResourceUtilizationResponse)
def get_current_resource_utilization(
    resource_id: UUID,
    current_user: dict = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get current period resource utilization."""
    now = datetime.utcnow()
    
    utilization = db.query(ResourceUtilization).filter(
        ResourceUtilization.resource_id == resource_id,
        ResourceUtilization.period_start <= now,
        ResourceUtilization.period_end >= now
    ).first()
    
    if not utilization:
        raise HTTPException(
            status_code=404,
            detail="No utilization record found for current period"
        )
    
    return utilization


@router.get("/resource/{resource_id}/summary", response_model=ResourceUtilizationSummary)
def get_resource_utilization_summary(
    resource_id: UUID,
    period_days: int = Query(30, ge=1, le=365),
    current_user: dict = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get comprehensive resource utilization summary."""
    # Get resource
    resource = db.query(Resource).filter(Resource.id == resource_id).first()
    if not resource:
        raise HTTPException(status_code=404, detail="Resource not found")
    
    # Calculate date range
    end_date = datetime.utcnow()
    start_date = end_date - timedelta(days=period_days)
    
    # Get utilization records for the period
    utilization_records = db.query(ResourceUtilization).filter(
        ResourceUtilization.resource_id == resource_id,
        ResourceUtilization.period_start >= start_date,
        ResourceUtilization.period_end <= end_date
    ).all()
    
    # Calculate averages
    if utilization_records:
        avg_utilization = sum(r.utilization_rate or 0 for r in utilization_records) / len(utilization_records)
        avg_efficiency = sum(r.efficiency_rate or 0 for r in utilization_records) / len(utilization_records)
        total_allocated = sum(r.allocated_hours or 0 for r in utilization_records)
        total_available = sum(r.total_available_hours or 0 for r in utilization_records)
        total_overtime = sum(r.overtime_hours or 0 for r in utilization_records)
        total_tasks_completed = sum(r.tasks_completed or 0 for r in utilization_records)
    else:
        avg_utilization = Decimal("0")
        avg_efficiency = Decimal("0")
        total_allocated = Decimal("0")
        total_available = Decimal("0")
        total_overtime = Decimal("0")
        total_tasks_completed = 0
    
    # Get current utilization
    current_utilization = db.query(ResourceUtilization).filter(
        ResourceUtilization.resource_id == resource_id
    ).order_by(desc(ResourceUtilization.period_start)).first()
    
    # Count active projects
    active_projects = db.query(func.count(func.distinct(ResourceAssignment.project_id))).filter(
        ResourceAssignment.resource_id == resource_id,
        ResourceAssignment.is_active == True
    ).scalar() or 0
    
    # Count assigned tasks
    assigned_tasks = db.query(func.count(Task.id)).join(
        ResourceAssignment,
        Task.id == ResourceAssignment.task_id
    ).filter(
        ResourceAssignment.resource_id == resource_id,
        Task.is_active == True,
        Task.status.in_(["pending", "in_progress"])
    ).scalar() or 0
    
    return ResourceUtilizationSummary(
        resource_id=resource.id,
        resource_name=resource.name,
        resource_type=resource.resource_type,
        current_utilization_rate=current_utilization.utilization_rate if current_utilization else Decimal("0"),
        average_utilization_rate=avg_utilization,
        allocated_hours=total_allocated,
        available_hours=total_available,
        overtime_hours=total_overtime,
        active_projects=active_projects,
        tasks_assigned=assigned_tasks,
        tasks_completed=total_tasks_completed,
        efficiency_rate=avg_efficiency
    )


@router.get("/", response_model=List[ResourceUtilizationSummary])
def get_all_resources_utilization(
    resource_type: Optional[str] = Query(None),
    min_utilization: Optional[float] = Query(None, ge=0, le=100),
    max_utilization: Optional[float] = Query(None, ge=0, le=100),
    period_days: int = Query(30, ge=1, le=365),
    current_user: dict = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get utilization summary for all resources."""
    # Get all resources
    query = db.query(Resource).filter(Resource.is_active == True)
    
    if resource_type:
        query = query.filter(Resource.resource_type == resource_type)
    
    resources = query.all()
    
    # Calculate date range
    end_date = datetime.utcnow()
    start_date = end_date - timedelta(days=period_days)
    
    summaries = []
    
    for resource in resources:
        # Get utilization records
        utilization_records = db.query(ResourceUtilization).filter(
            ResourceUtilization.resource_id == resource.id,
            ResourceUtilization.period_start >= start_date,
            ResourceUtilization.period_end <= end_date
        ).all()
        
        # Calculate metrics
        if utilization_records:
            avg_utilization = sum(r.utilization_rate or 0 for r in utilization_records) / len(utilization_records)
            avg_efficiency = sum(r.efficiency_rate or 0 for r in utilization_records) / len(utilization_records)
            total_allocated = sum(r.allocated_hours or 0 for r in utilization_records)
            total_available = sum(r.total_available_hours or 0 for r in utilization_records)
            total_overtime = sum(r.overtime_hours or 0 for r in utilization_records)
            total_tasks_completed = sum(r.tasks_completed or 0 for r in utilization_records)
        else:
            avg_utilization = Decimal("0")
            avg_efficiency = Decimal("0")
            total_allocated = Decimal("0")
            total_available = Decimal("0")
            total_overtime = Decimal("0")
            total_tasks_completed = 0
        
        # Apply filters
        if min_utilization is not None and float(avg_utilization) < min_utilization:
            continue
        if max_utilization is not None and float(avg_utilization) > max_utilization:
            continue
        
        # Get current utilization
        current_utilization = db.query(ResourceUtilization).filter(
            ResourceUtilization.resource_id == resource.id
        ).order_by(desc(ResourceUtilization.period_start)).first()
        
        # Count active projects
        active_projects = db.query(func.count(func.distinct(ResourceAssignment.project_id))).filter(
            ResourceAssignment.resource_id == resource.id,
            ResourceAssignment.is_active == True
        ).scalar() or 0
        
        # Count assigned tasks
        assigned_tasks = db.query(func.count(Task.id)).join(
            ResourceAssignment,
            Task.id == ResourceAssignment.task_id
        ).filter(
            ResourceAssignment.resource_id == resource.id,
            Task.is_active == True,
            Task.status.in_(["pending", "in_progress"])
        ).scalar() or 0
        
        summaries.append(ResourceUtilizationSummary(
            resource_id=resource.id,
            resource_name=resource.name,
            resource_type=resource.resource_type,
            current_utilization_rate=current_utilization.utilization_rate if current_utilization else Decimal("0"),
            average_utilization_rate=avg_utilization,
            allocated_hours=total_allocated,
            available_hours=total_available,
            overtime_hours=total_overtime,
            active_projects=active_projects,
            tasks_assigned=assigned_tasks,
            tasks_completed=total_tasks_completed,
            efficiency_rate=avg_efficiency
        ))
    
    return summaries


@router.post("/calculate", status_code=status.HTTP_202_ACCEPTED)
def calculate_resource_utilization(
    resource_id: Optional[UUID] = Query(None),
    period_start: datetime = Query(...),
    period_end: datetime = Query(...),
    current_user: dict = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Calculate and store resource utilization for a period."""
    # Get resources to calculate
    if resource_id:
        resources = [db.query(Resource).filter(Resource.id == resource_id).first()]
        if not resources[0]:
            raise HTTPException(status_code=404, detail="Resource not found")
    else:
        resources = db.query(Resource).filter(Resource.is_active == True).all()
    
    calculated_count = 0
    
    for resource in resources:
        # Calculate total available hours (assuming 8 hours per day)
        days = (period_end - period_start).days
        total_available_hours = Decimal(str(days * 8))
        
        # Get all assignments for this resource in the period
        assignments = db.query(ResourceAssignment).filter(
            ResourceAssignment.resource_id == resource.id,
            ResourceAssignment.start_date <= period_end.date(),
            ResourceAssignment.end_date >= period_start.date()
        ).all()
        
        allocated_hours = sum(a.allocated_hours or 0 for a in assignments)
        
        # Get completed tasks
        completed_tasks = db.query(func.count(Task.id)).join(
            ResourceAssignment,
            Task.id == ResourceAssignment.task_id
        ).filter(
            ResourceAssignment.resource_id == resource.id,
            Task.status == "completed",
            Task.updated_at >= period_start,
            Task.updated_at <= period_end
        ).scalar() or 0
        
        # Count active projects
        projects_count = db.query(func.count(func.distinct(ResourceAssignment.project_id))).filter(
            ResourceAssignment.resource_id == resource.id,
            ResourceAssignment.is_active == True
        ).scalar() or 0
        
        # Calculate actual hours worked (simplified - using allocated hours)
        actual_hours_worked = allocated_hours * Decimal("0.9")  # Assuming 90% efficiency
        
        # Calculate overtime (if allocated > available)
        overtime_hours = max(allocated_hours - total_available_hours, Decimal("0"))
        
        # Create utilization record
        utilization = ResourceUtilization(
            resource_id=resource.id,
            period_start=period_start,
            period_end=period_end,
            total_available_hours=total_available_hours,
            allocated_hours=allocated_hours,
            actual_hours_worked=actual_hours_worked,
            overtime_hours=overtime_hours,
            projects_count=projects_count,
            tasks_completed=completed_tasks
        )
        
        # Calculate rates
        if total_available_hours > 0:
            utilization.utilization_rate = (allocated_hours / total_available_hours) * 100
            utilization.idle_hours = total_available_hours - allocated_hours
        
        if allocated_hours > 0:
            utilization.efficiency_rate = (actual_hours_worked / allocated_hours) * 100
        
        db.add(utilization)
        calculated_count += 1
    
    db.commit()
    
    return {
        "message": f"Calculated utilization for {calculated_count} resource(s)",
        "period_start": period_start,
        "period_end": period_end
    }


@router.post("/optimize", status_code=status.HTTP_200_OK)
def optimize_resource_allocation(
    project_id: Optional[UUID] = Query(None),
    target_utilization: float = Query(80.0, ge=0, le=100),
    current_user: dict = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Suggest resource allocation optimization."""
    # Get all active resources
    resources = db.query(Resource).filter(Resource.is_active == True).all()
    
    # Get current utilization for each resource
    recommendations = []
    
    for resource in resources:
        current_util = db.query(ResourceUtilization).filter(
            ResourceUtilization.resource_id == resource.id
        ).order_by(desc(ResourceUtilization.period_start)).first()
        
        if not current_util:
            continue
        
        util_rate = float(current_util.utilization_rate or 0)
        
        if util_rate < target_utilization - 10:
            # Under-utilized
            recommendations.append({
                "resource_id": str(resource.id),
                "resource_name": resource.name,
                "current_utilization": util_rate,
                "target_utilization": target_utilization,
                "status": "under_utilized",
                "recommendation": f"Can take on more work. Current utilization: {util_rate:.1f}%",
                "available_capacity": float(current_util.idle_hours or 0)
            })
        elif util_rate > target_utilization + 10:
            # Over-utilized
            recommendations.append({
                "resource_id": str(resource.id),
                "resource_name": resource.name,
                "current_utilization": util_rate,
                "target_utilization": target_utilization,
                "status": "over_utilized",
                "recommendation": f"Overloaded. Consider redistributing work. Current utilization: {util_rate:.1f}%",
                "overtime_hours": float(current_util.overtime_hours or 0)
            })
        else:
            # Optimally utilized
            recommendations.append({
                "resource_id": str(resource.id),
                "resource_name": resource.name,
                "current_utilization": util_rate,
                "target_utilization": target_utilization,
                "status": "optimal",
                "recommendation": f"Well balanced. Current utilization: {util_rate:.1f}%"
            })
    
    return {
        "target_utilization": target_utilization,
        "total_resources": len(resources),
        "recommendations": recommendations,
        "summary": {
            "under_utilized": len([r for r in recommendations if r["status"] == "under_utilized"]),
            "over_utilized": len([r for r in recommendations if r["status"] == "over_utilized"]),
            "optimal": len([r for r in recommendations if r["status"] == "optimal"])
        }
    }
