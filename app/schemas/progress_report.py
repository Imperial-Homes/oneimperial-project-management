"""Progress Report schemas for project status reporting."""

from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, Field


class ProgressReportBase(BaseModel):
    """Base progress report schema."""

    report_title: str = Field(..., max_length=500, description="Report title")
    project_name: str | None = Field(None, max_length=255, description="Project name")
    project_id: UUID | None = Field(None, description="Project ID")
    reporting_period: str | None = Field(None, max_length=100, description="Reporting period")

    period_start_date: datetime | None = Field(None, description="Period start date")
    period_end_date: datetime | None = Field(None, description="Period end date")
    report_date: datetime = Field(..., description="Report date")

    executive_summary: str | None = Field(None, description="Executive summary")
    achievements: str | None = Field(None, description="Achievements")
    challenges: str | None = Field(None, description="Challenges")
    next_steps: str | None = Field(None, description="Next steps")
    budget_status: str | None = Field(None, description="Budget status")
    timeline_status: str | None = Field(None, description="Timeline status")

    completion_percentage: int | None = Field(None, ge=0, le=100, description="Completion %")

    submitted_to: str | None = Field(None, max_length=255, description="Submitted to")
    submitted_to_id: UUID | None = Field(None, description="Submitted to ID")
    attachment_url: str | None = Field(None, max_length=500, description="Attachment URL")


class ProgressReportCreate(ProgressReportBase):
    """Create progress report schema."""

    status: str = Field(default="draft", max_length=50)
    compiled_by: str | None = Field(None, max_length=255)
    compiled_by_id: UUID | None = None


class ProgressReportUpdate(BaseModel):
    """Update progress report schema."""

    report_title: str | None = Field(None, max_length=500)
    project_name: str | None = Field(None, max_length=255)
    project_id: UUID | None = None
    reporting_period: str | None = Field(None, max_length=100)
    period_start_date: datetime | None = None
    period_end_date: datetime | None = None
    report_date: datetime | None = None
    executive_summary: str | None = None
    achievements: str | None = None
    challenges: str | None = None
    next_steps: str | None = None
    budget_status: str | None = None
    timeline_status: str | None = None
    completion_percentage: int | None = Field(None, ge=0, le=100)
    submitted_to: str | None = Field(None, max_length=255)
    submitted_to_id: UUID | None = None
    status: str | None = Field(None, max_length=50)
    attachment_url: str | None = Field(None, max_length=500)


class ProgressReportResponse(ProgressReportBase):
    """Progress report response schema."""

    id: UUID
    report_id: str
    status: str
    compiled_by: str | None
    compiled_by_id: UUID | None
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class ProgressReportList(BaseModel):
    """Progress report list response."""

    items: list[ProgressReportResponse]
    total: int
    page: int
    page_size: int
    pages: int


class ProgressReportStats(BaseModel):
    """Progress report stats response."""

    total: int = 0
    draft: int = 0
    submitted: int = 0
    approved: int = 0
