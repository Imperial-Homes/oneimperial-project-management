"""Budget and Cost schemas."""

from datetime import date, datetime
from decimal import Decimal
from uuid import UUID

from pydantic import BaseModel, Field


class ProjectBudgetCreate(BaseModel):
    """Create project budget schema."""

    project_id: UUID
    version: int = Field(default=1, ge=1)
    total_budget: Decimal = Field(..., ge=0)
    labor_budget: Decimal = Field(default=0, ge=0)
    material_budget: Decimal = Field(default=0, ge=0)
    equipment_budget: Decimal = Field(default=0, ge=0)
    other_budget: Decimal = Field(default=0, ge=0)
    contingency_percentage: Decimal = Field(default=0, ge=0, le=100)
    currency: str = Field(default="GHS", max_length=10)


class ProjectBudgetResponse(ProjectBudgetCreate):
    """Project budget response schema."""

    id: UUID
    is_approved: bool
    contingency_amount: Decimal
    created_at: datetime
    created_by: UUID | None
    approved_at: datetime | None
    approved_by: UUID | None

    class Config:
        from_attributes = True


class ProjectCostCreate(BaseModel):
    """Create project cost schema."""

    project_id: UUID
    task_id: UUID | None = None
    cost_category: str = Field(..., max_length=100)
    description: str | None = None
    amount: Decimal = Field(..., ge=0)
    currency: str = Field(default="GHS", max_length=10)
    transaction_date: date
    reference_number: str | None = Field(None, max_length=100)


class ProjectCostResponse(ProjectCostCreate):
    """Project cost response schema."""

    id: UUID
    created_at: datetime
    created_by: UUID | None

    class Config:
        from_attributes = True
