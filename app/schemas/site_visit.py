"""Site Visit schemas for project site inspections."""

from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, Field


class SiteVisitBase(BaseModel):
    """Base site visit schema."""

    project_name: str = Field(..., max_length=255, description="Project name")
    project_id: UUID | None = Field(None, description="Project ID")
    site_location: str = Field(..., max_length=500, description="Site location")
    visit_date: datetime = Field(..., description="Visit date")
    visit_time: str | None = Field(None, max_length=20, description="Visit time")

    visitors: str | None = Field(None, description="Names of visitors")
    site_contact: str | None = Field(None, max_length=255, description="Site contact person")
    site_contact_phone: str | None = Field(None, max_length=50, description="Contact phone")

    visit_purpose: str = Field(..., max_length=255, description="Purpose of visit")
    observations: str | None = Field(None, description="Observations made")
    issues_identified: str | None = Field(None, description="Issues identified")
    recommendations: str | None = Field(None, description="Recommendations")

    follow_up_required: str = Field(default="no", max_length=20, description="Follow-up required")
    follow_up_notes: str | None = Field(None, description="Follow-up notes")
    next_visit_date: datetime | None = Field(None, description="Next visit date")

    photos_url: str | None = Field(None, max_length=500, description="Photos URL")
    report_url: str | None = Field(None, max_length=500, description="Report URL")


class SiteVisitCreate(SiteVisitBase):
    """Create site visit schema."""

    status: str = Field(default="completed", max_length=50)
    logged_by: str | None = Field(None, max_length=255)
    logged_by_id: UUID | None = None


class SiteVisitUpdate(BaseModel):
    """Update site visit schema."""

    project_name: str | None = Field(None, max_length=255)
    project_id: UUID | None = None
    site_location: str | None = Field(None, max_length=500)
    visit_date: datetime | None = None
    visit_time: str | None = Field(None, max_length=20)
    visitors: str | None = None
    site_contact: str | None = Field(None, max_length=255)
    site_contact_phone: str | None = Field(None, max_length=50)
    visit_purpose: str | None = Field(None, max_length=255)
    observations: str | None = None
    issues_identified: str | None = None
    recommendations: str | None = None
    follow_up_required: str | None = Field(None, max_length=20)
    follow_up_notes: str | None = None
    next_visit_date: datetime | None = None
    photos_url: str | None = Field(None, max_length=500)
    report_url: str | None = Field(None, max_length=500)
    status: str | None = Field(None, max_length=50)


class SiteVisitResponse(SiteVisitBase):
    """Site visit response schema."""

    id: UUID
    visit_id: str
    status: str
    logged_by: str | None
    logged_by_id: UUID | None
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
