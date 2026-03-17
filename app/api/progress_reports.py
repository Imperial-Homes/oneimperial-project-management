"""Progress Report API endpoints for project status reporting."""

import logging
from datetime import datetime
from math import ceil
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.deps import get_current_user
from app.database import get_db
from app.models.progress_report import ProgressReport
from app.schemas.progress_report import (
    ProgressReportCreate,
    ProgressReportList,
    ProgressReportResponse,
    ProgressReportStats,
    ProgressReportUpdate,
)

router = APIRouter()
logger = logging.getLogger(__name__)


async def generate_report_id(db: AsyncSession) -> str:
    """Generate a unique report ID like PR-2026-0001."""
    year = datetime.utcnow().year
    prefix = f"PR-{year}-"

    query = (
        select(ProgressReport.report_id)
        .where(ProgressReport.report_id.like(f"{prefix}%"))
        .order_by(ProgressReport.report_id.desc())
        .limit(1)
    )

    result = await db.execute(query)
    last_id = result.scalar_one_or_none()

    if last_id:
        try:
            last_num = int(last_id.split("-")[-1])
            next_num = last_num + 1
        except (ValueError, IndexError):
            next_num = 1
    else:
        next_num = 1

    return f"{prefix}{next_num:04d}"


@router.get("/stats", response_model=ProgressReportStats)
async def get_progress_report_stats(
    db: AsyncSession = Depends(get_db),
    current_user: dict = Depends(get_current_user),
):
    """Get progress report statistics."""
    total = await db.scalar(select(func.count(ProgressReport.id)))
    draft = await db.scalar(select(func.count(ProgressReport.id)).where(ProgressReport.status == "draft"))
    submitted = await db.scalar(select(func.count(ProgressReport.id)).where(ProgressReport.status == "submitted"))
    approved = await db.scalar(select(func.count(ProgressReport.id)).where(ProgressReport.status == "approved"))

    return ProgressReportStats(
        total=total or 0,
        draft=draft or 0,
        submitted=submitted or 0,
        approved=approved or 0,
    )


@router.get("", response_model=ProgressReportList)
async def list_progress_reports(
    page: int = Query(1, ge=1),
    page_size: int = Query(50, ge=1, le=100),
    search: str | None = Query(None),
    status_filter: str | None = Query(None, alias="status"),
    db: AsyncSession = Depends(get_db),
    current_user: dict = Depends(get_current_user),
):
    """List progress reports with pagination and filtering."""
    query = select(ProgressReport)

    if search:
        query = query.where(
            (ProgressReport.report_title.ilike(f"%{search}%"))
            | (ProgressReport.report_id.ilike(f"%{search}%"))
            | (ProgressReport.project_name.ilike(f"%{search}%"))
        )

    if status_filter:
        query = query.where(ProgressReport.status == status_filter)

    count_query = select(func.count()).select_from(query.subquery())
    total = await db.scalar(count_query)

    query = query.order_by(ProgressReport.report_date.desc()).offset((page - 1) * page_size).limit(page_size)
    result = await db.execute(query)
    reports = result.scalars().all()

    return ProgressReportList(
        items=reports,
        total=total or 0,
        page=page,
        page_size=page_size,
        pages=ceil(total / page_size) if total and total > 0 else 0,
    )


@router.get("/{report_id}", response_model=ProgressReportResponse)
async def get_progress_report(
    report_id: UUID,
    db: AsyncSession = Depends(get_db),
    current_user: dict = Depends(get_current_user),
):
    """Get a single progress report by ID."""
    result = await db.execute(select(ProgressReport).where(ProgressReport.id == report_id))
    report = result.scalar_one_or_none()

    if not report:
        raise HTTPException(status_code=404, detail="Progress report not found")

    return report


@router.post("", response_model=ProgressReportResponse, status_code=status.HTTP_201_CREATED)
async def create_progress_report(
    data: ProgressReportCreate,
    db: AsyncSession = Depends(get_db),
    current_user: dict = Depends(get_current_user),
):
    """Create a new progress report."""
    report_id = await generate_report_id(db)

    report = ProgressReport(
        report_id=report_id,
        report_title=data.report_title,
        project_name=data.project_name,
        project_id=data.project_id,
        reporting_period=data.reporting_period,
        period_start_date=data.period_start_date,
        period_end_date=data.period_end_date,
        report_date=data.report_date,
        executive_summary=data.executive_summary,
        achievements=data.achievements,
        challenges=data.challenges,
        next_steps=data.next_steps,
        budget_status=data.budget_status,
        timeline_status=data.timeline_status,
        completion_percentage=data.completion_percentage,
        submitted_to=data.submitted_to,
        submitted_to_id=data.submitted_to_id,
        status=data.status or "draft",
        attachment_url=data.attachment_url,
        compiled_by=data.compiled_by or current_user.get("name", ""),
        compiled_by_id=data.compiled_by_id or (UUID(current_user["sub"]) if current_user.get("sub") else None),
    )

    db.add(report)
    await db.commit()
    await db.refresh(report)

    logger.info(f"Progress report created: {report_id}")

    return report


@router.put("/{report_id}", response_model=ProgressReportResponse)
async def update_progress_report(
    report_id: UUID,
    data: ProgressReportUpdate,
    db: AsyncSession = Depends(get_db),
    current_user: dict = Depends(get_current_user),
):
    """Update a progress report."""
    result = await db.execute(select(ProgressReport).where(ProgressReport.id == report_id))
    report = result.scalar_one_or_none()

    if not report:
        raise HTTPException(status_code=404, detail="Progress report not found")

    update_data = data.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        setattr(report, field, value)

    report.updated_at = datetime.utcnow()
    await db.commit()
    await db.refresh(report)

    logger.info(f"Progress report updated: {report.report_id}")

    return report


@router.delete("/{report_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_progress_report(
    report_id: UUID,
    db: AsyncSession = Depends(get_db),
    current_user: dict = Depends(get_current_user),
):
    """Delete a progress report."""
    result = await db.execute(select(ProgressReport).where(ProgressReport.id == report_id))
    report = result.scalar_one_or_none()

    if not report:
        raise HTTPException(status_code=404, detail="Progress report not found")

    await db.delete(report)
    await db.commit()

    logger.info(f"Progress report deleted: {report.report_id}")
