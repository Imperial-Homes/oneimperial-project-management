"""Project Incident schemas."""

from datetime import date, datetime
from typing import Optional
from uuid import UUID

from pydantic import BaseModel, Field

from app.models.incident import IncidentSeverity, IncidentStatus, IncidentType


class IncidentBase(BaseModel):
    """Base incident schema."""
    incident_type: IncidentType
    severity: IncidentSeverity
    title: str = Field(..., max_length=255)
    description: str
    location: Optional[str] = Field(None, max_length=255)
    incident_date: date
    reported_date: date
    reported_by_name: Optional[str] = Field(None, max_length=255)
    assigned_to: Optional[UUID] = None
    assigned_to_name: Optional[str] = Field(None, max_length=255)
    injuries_count: Optional[str] = Field(None, max_length=50)
    property_damage: Optional[str] = Field(None, max_length=255)
    work_stoppage_hours: Optional[str] = Field(None, max_length=50)
    estimated_cost: Optional[str] = Field(None, max_length=100)
    notes: Optional[str] = None
    attachments: Optional[str] = None


class IncidentCreate(IncidentBase):
    """Schema for creating an incident."""
    project_id: UUID


class IncidentUpdate(BaseModel):
    """Schema for updating an incident."""
    incident_type: Optional[IncidentType] = None
    severity: Optional[IncidentSeverity] = None
    status: Optional[IncidentStatus] = None
    title: Optional[str] = Field(None, max_length=255)
    description: Optional[str] = None
    location: Optional[str] = Field(None, max_length=255)
    incident_date: Optional[date] = None
    reported_date: Optional[date] = None
    reported_by_name: Optional[str] = Field(None, max_length=255)
    assigned_to: Optional[UUID] = None
    assigned_to_name: Optional[str] = Field(None, max_length=255)
    injuries_count: Optional[str] = Field(None, max_length=50)
    property_damage: Optional[str] = Field(None, max_length=255)
    work_stoppage_hours: Optional[str] = Field(None, max_length=50)
    estimated_cost: Optional[str] = Field(None, max_length=100)
    root_cause: Optional[str] = None
    corrective_actions: Optional[str] = None
    preventive_measures: Optional[str] = None
    notes: Optional[str] = None
    attachments: Optional[str] = None
    requires_investigation: Optional[bool] = None
    investigation_completed: Optional[bool] = None
    follow_up_required: Optional[bool] = None
    follow_up_date: Optional[date] = None


class ProjectInfo(BaseModel):
    """Basic project info for incident response."""
    id: UUID
    name: str
    
    class Config:
        from_attributes = True


class IncidentResponse(IncidentBase):
    """Schema for incident response."""
    id: UUID
    incident_number: str
    project_id: UUID
    project: Optional[ProjectInfo] = None
    status: IncidentStatus
    reported_by: Optional[UUID] = None
    root_cause: Optional[str] = None
    corrective_actions: Optional[str] = None
    preventive_measures: Optional[str] = None
    resolved_date: Optional[date] = None
    resolved_by: Optional[UUID] = None
    requires_investigation: bool
    investigation_completed: bool
    follow_up_required: bool
    follow_up_date: Optional[date] = None
    created_at: datetime
    created_by: Optional[UUID] = None
    updated_at: datetime
    updated_by: Optional[UUID] = None
    
    class Config:
        from_attributes = True


class IncidentList(BaseModel):
    """Schema for paginated incident list."""
    items: list[IncidentResponse]
    total: int
    page: int
    page_size: int
    pages: int


class IncidentResolve(BaseModel):
    """Schema for resolving an incident."""
    root_cause: str
    corrective_actions: str
    preventive_measures: Optional[str] = None
    resolved_date: date
    notes: Optional[str] = None
