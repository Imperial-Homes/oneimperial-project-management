"""Progress Report schemas for project status reporting."""

from datetime import datetime
from typing import Optional
from uuid import UUID

from pydantic import BaseModel, Field


class ProgressReportBase(BaseModel):
    """Base progress report schema."""
    report_title: str = Field(..., max_length=500, description="Report title")
    project_name: Optional[str] = Field(None, max_length=255, description="Project name")
    project_id: Optional[UUID] = Field(None, description="Project ID")
    reporting_period: Optional[str] = Field(None, max_length=100, description="Reporting period")

    period_start_date: Optional[datetime] = Field(None, description="Period start date")
    period_end_date: Optional[datetime] = Field(None, description="Period end date")
    report_date: datetime = Field(..., description="Report date")

    executive_summary: Optional[str] = Field(None, description="Executive summary")
    achievements: Optional[str] = Field(None, description="Achievements")
    challenges: Optional[str] = Field(None, description="Challenges")
    next_steps: Optional[str] = Field(None, description="Next steps")
    budget_status: Optional[str] = Field(None, description="Budget status")
    timeline_status: Optional[str] = Field(None, description="Timeline status")

    completion_percentage: Optional[int] = Field(None, ge=0, le=100, description="Completion %")

    submitted_to: Optional[str] = Field(None, max_length=255, description="Submitted to")
    submitted_to_id: Optional[UUID] = Field(None, description="Submitted to ID")
    attachment_url: Optional[str] = Field(None, max_length=500, description="Attachment URL")


class ProgressReportCreate(ProgressReportBase):
    """Create progress report schema."""
    status: str = Field(default="draft", max_length=50)
    compiled_by: Optional[str] = Field(None, max_length=255)
    compiled_by_id: Optional[UUID] = None


class ProgressReportUpdate(BaseModel):
    """Update progress report schema."""
    report_title: Optional[str] = Field(None, max_length=500)
    project_name: Optional[str] = Field(None, max_length=255)
    project_id: Optional[UUID] = None
    reporting_period: Optional[str] = Field(None, max_length=100)
    period_start_date: Optional[datetime] = None
    period_end_date: Optional[datetime] = None
    report_date: Optional[datetime] = None
    executive_summary: Optional[str] = None
    achievements: Optional[str] = None
    challenges: Optional[str] = None
    next_steps: Optional[str] = None
    budget_status: Optional[str] = None
    timeline_status: Optional[str] = None
    completion_percentage: Optional[int] = Field(None, ge=0, le=100)
    submitted_to: Optional[str] = Field(None, max_length=255)
    submitted_to_id: Optional[UUID] = None
    status: Optional[str] = Field(None, max_length=50)
    attachment_url: Optional[str] = Field(None, max_length=500)


class ProgressReportResponse(ProgressReportBase):
    """Progress report response schema."""
    id: UUID
    report_id: str
    status: str
    compiled_by: Optional[str]
    compiled_by_id: Optional[UUID]
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
