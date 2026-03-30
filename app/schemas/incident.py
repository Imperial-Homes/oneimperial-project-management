"""Project Incident schemas."""

from datetime import date, datetime
from uuid import UUID

from pydantic import BaseModel, Field

from app.models.incident import IncidentSeverity, IncidentStatus, IncidentType


class IncidentBase(BaseModel):
    """Base incident schema."""

    incident_type: IncidentType
    severity: IncidentSeverity
    title: str = Field(..., max_length=255)
    description: str
    location: str | None = Field(None, max_length=255)
    incident_date: date
    reported_date: date
    reported_by_name: str | None = Field(None, max_length=255)
    assigned_to: UUID | None = None
    assigned_to_name: str | None = Field(None, max_length=255)
    injuries_count: str | None = Field(None, max_length=50)
    property_damage: str | None = Field(None, max_length=255)
    work_stoppage_hours: str | None = Field(None, max_length=50)
    estimated_cost: str | None = Field(None, max_length=100)
    notes: str | None = None
    attachments: str | None = None


class IncidentCreate(IncidentBase):
    """Schema for creating an incident."""

    project_id: UUID


class IncidentUpdate(BaseModel):
    """Schema for updating an incident."""

    incident_type: IncidentType | None = None
    severity: IncidentSeverity | None = None
    status: IncidentStatus | None = None
    title: str | None = Field(None, max_length=255)
    description: str | None = None
    location: str | None = Field(None, max_length=255)
    incident_date: date | None = None
    reported_date: date | None = None
    reported_by_name: str | None = Field(None, max_length=255)
    assigned_to: UUID | None = None
    assigned_to_name: str | None = Field(None, max_length=255)
    injuries_count: str | None = Field(None, max_length=50)
    property_damage: str | None = Field(None, max_length=255)
    work_stoppage_hours: str | None = Field(None, max_length=50)
    estimated_cost: str | None = Field(None, max_length=100)
    root_cause: str | None = None
    corrective_actions: str | None = None
    preventive_measures: str | None = None
    notes: str | None = None
    attachments: str | None = None
    requires_investigation: bool | None = None
    investigation_completed: bool | None = None
    follow_up_required: bool | None = None
    follow_up_date: date | None = None


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
    project: ProjectInfo | None = None
    status: IncidentStatus
    reported_by: UUID | None = None
    root_cause: str | None = None
    corrective_actions: str | None = None
    preventive_measures: str | None = None
    resolved_date: date | None = None
    resolved_by: UUID | None = None
    requires_investigation: bool
    investigation_completed: bool
    follow_up_required: bool
    follow_up_date: date | None = None
    created_at: datetime
    created_by: UUID | None = None
    updated_at: datetime
    updated_by: UUID | None = None

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
    preventive_measures: str | None = None
    resolved_date: date
    notes: str | None = None
