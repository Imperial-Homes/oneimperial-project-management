"""Site Visit schemas for project site inspections."""

from datetime import datetime
from typing import Optional
from uuid import UUID

from pydantic import BaseModel, Field


class SiteVisitBase(BaseModel):
    """Base site visit schema."""
    project_name: str = Field(..., max_length=255, description="Project name")
    project_id: Optional[UUID] = Field(None, description="Project ID")
    site_location: str = Field(..., max_length=500, description="Site location")
    visit_date: datetime = Field(..., description="Visit date")
    visit_time: Optional[str] = Field(None, max_length=20, description="Visit time")

    visitors: Optional[str] = Field(None, description="Names of visitors")
    site_contact: Optional[str] = Field(None, max_length=255, description="Site contact person")
    site_contact_phone: Optional[str] = Field(None, max_length=50, description="Contact phone")

    visit_purpose: str = Field(..., max_length=255, description="Purpose of visit")
    observations: Optional[str] = Field(None, description="Observations made")
    issues_identified: Optional[str] = Field(None, description="Issues identified")
    recommendations: Optional[str] = Field(None, description="Recommendations")

    follow_up_required: str = Field(default="no", max_length=20, description="Follow-up required")
    follow_up_notes: Optional[str] = Field(None, description="Follow-up notes")
    next_visit_date: Optional[datetime] = Field(None, description="Next visit date")

    photos_url: Optional[str] = Field(None, max_length=500, description="Photos URL")
    report_url: Optional[str] = Field(None, max_length=500, description="Report URL")


class SiteVisitCreate(SiteVisitBase):
    """Create site visit schema."""
    status: str = Field(default="completed", max_length=50)
    logged_by: Optional[str] = Field(None, max_length=255)
    logged_by_id: Optional[UUID] = None


class SiteVisitUpdate(BaseModel):
    """Update site visit schema."""
    project_name: Optional[str] = Field(None, max_length=255)
    project_id: Optional[UUID] = None
    site_location: Optional[str] = Field(None, max_length=500)
    visit_date: Optional[datetime] = None
    visit_time: Optional[str] = Field(None, max_length=20)
    visitors: Optional[str] = None
    site_contact: Optional[str] = Field(None, max_length=255)
    site_contact_phone: Optional[str] = Field(None, max_length=50)
    visit_purpose: Optional[str] = Field(None, max_length=255)
    observations: Optional[str] = None
    issues_identified: Optional[str] = None
    recommendations: Optional[str] = None
    follow_up_required: Optional[str] = Field(None, max_length=20)
    follow_up_notes: Optional[str] = None
    next_visit_date: Optional[datetime] = None
    photos_url: Optional[str] = Field(None, max_length=500)
    report_url: Optional[str] = Field(None, max_length=500)
    status: Optional[str] = Field(None, max_length=50)


class SiteVisitResponse(SiteVisitBase):
    """Site visit response schema."""
    id: UUID
    visit_id: str
    status: str
    logged_by: Optional[str]
    logged_by_id: Optional[UUID]
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class SiteVisitList(BaseModel):
    """Site visit list response."""
    items: list[SiteVisitResponse]
    total: int
    page: int
    page_size: int
    pages: int


class SiteVisitStats(BaseModel):
    """Site visit stats response."""
    total: int = 0
    completed: int = 0
    scheduled: int = 0
    follow_up_required: int = 0
