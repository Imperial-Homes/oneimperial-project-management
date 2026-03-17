"""Progress Report model for project status reporting."""

import uuid
from datetime import datetime

from sqlalchemy import Column, DateTime, Integer, String, Text
from sqlalchemy.dialects.postgresql import UUID

from app.database import Base


class ProgressReport(Base):
    """Progress Report model - tracks progress reports compiled by Admin Officer."""

    __tablename__ = "progress_reports"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    report_id = Column(String(50), unique=True, nullable=False, index=True)  # e.g., PR-2026-0001

    # Report details
    report_title = Column(String(500), nullable=False)
    project_name = Column(String(255))
    project_id = Column(UUID(as_uuid=True))
    reporting_period = Column(String(100))  # e.g., "January 2026", "Q1 2026", "Week 1-4"

    # Dates
    period_start_date = Column(DateTime(timezone=True))
    period_end_date = Column(DateTime(timezone=True))
    report_date = Column(DateTime(timezone=True), nullable=False)

    # Content
    executive_summary = Column(Text)
    achievements = Column(Text)
    challenges = Column(Text)
    next_steps = Column(Text)
    budget_status = Column(Text)
    timeline_status = Column(Text)

    # Metrics
    completion_percentage = Column(Integer)  # 0-100

    # Recipients
    submitted_to = Column(String(255))  # Who receives this report
    submitted_to_id = Column(UUID(as_uuid=True))

    # Status
    status = Column(String(50), nullable=False, default="draft")  # draft, submitted, approved, revision_needed

    # Attachments
    attachment_url = Column(String(500))

    # Audit
    compiled_by = Column(String(255))
    compiled_by_id = Column(UUID(as_uuid=True))
    created_at = Column(DateTime(timezone=True), default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime(timezone=True), default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)
