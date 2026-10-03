"""Budget and Cost API endpoints."""

from uuid import UUID

from fastapi import APIRouter, Depends, Query, status
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.deps import get_current_user
from app.database import get_db
from app.models import ProjectBudget, ProjectCost
from app.schemas import ProjectBudgetCreate, ProjectBudgetResponse, ProjectCostCreate, ProjectCostResponse

router = APIRouter()


@router.get("", response_model=list[ProjectBudgetResponse])
async def list_budgets(
    db: AsyncSession = Depends(get_db),
    current_user: UUID = Depends(get_current_user),
):
    """List all project budgets."""
    result = await db.execute(select(ProjectBudget).order_by(ProjectBudget.version.desc()))
    return result.scalars().all()


CATEGORIES = ("labor", "material", "equipment", "other")


@router.get("/variance")
async def budget_variance(
    project_id: UUID | None = Query(None, description="One project, or every project with a budget"),
    db: AsyncSession = Depends(get_db),
    current_user: UUID = Depends(get_current_user),
):
    """Budget against recorded costs, by cost category, per project.

    Uses each project's latest approved budget, or its latest version if none is
    approved yet (flagged with approved=false).
    """
    query = select(ProjectBudget).order_by(
        ProjectBudget.project_id, ProjectBudget.is_approved.desc(), ProjectBudget.version.desc()
    )
    if project_id:
        query = query.where(ProjectBudget.project_id == project_id)
    latest: dict = {}
    for budget in (await db.execute(query)).scalars().all():
        latest.setdefault(budget.project_id, budget)

    costs_query = select(ProjectCost.project_id, func.lower(ProjectCost.cost_category), func.sum(ProjectCost.amount))
    if project_id:
        costs_query = costs_query.where(ProjectCost.project_id == project_id)
    spent: dict = {}
    for pid, category, total in (
        await db.execute(costs_query.group_by(ProjectCost.project_id, func.lower(ProjectCost.cost_category)))
    ).all():
        key = category if category in CATEGORIES else "other"
        spent[(pid, key)] = spent.get((pid, key), 0) + float(total or 0)

    rows = []
    for pid, budget in latest.items():
        for category in CATEGORIES:
            rows.append(
                {
                    "project_id": str(pid),
                    "category": category,
                    "budgeted": float(getattr(budget, f"{category}_budget") or 0),
                    "spent": round(spent.get((pid, category), 0), 2),
                    "currency": budget.currency,
                    "approved": bool(budget.is_approved),
                    "budget_version": budget.version,
                }
            )
    budgeted = round(sum(r["budgeted"] for r in rows), 2)
    total_spent = round(sum(r["spent"] for r in rows), 2)
    return {
        "rows": rows,
        "budgeted": budgeted,
        "spent": total_spent,
        "variance": round(budgeted - total_spent, 2),
        "contingency": round(sum(float(b.contingency_amount or 0) for b in latest.values()), 2),
    }


@router.get("/{project_id}", response_model=list[ProjectBudgetResponse])
async def get_project_budgets(
    project_id: UUID,
    db: AsyncSession = Depends(get_db),
    current_user: UUID = Depends(get_current_user),
):
    """Get all budgets for a project."""
    result = await db.execute(
        select(ProjectBudget).where(ProjectBudget.project_id == project_id).order_by(ProjectBudget.version.desc())
    )
    budgets = result.scalars().all()
    return budgets


@router.post("", response_model=ProjectBudgetResponse, status_code=status.HTTP_201_CREATED)
async def create_budget(
    budget_data: ProjectBudgetCreate,
    db: AsyncSession = Depends(get_db),
    current_user: UUID = Depends(get_current_user),
):
    """Create project budget."""
    # Calculate contingency amount
    contingency_amount = (budget_data.total_budget * budget_data.contingency_percentage) / 100

    budget = ProjectBudget(**budget_data.dict(), contingency_amount=contingency_amount, created_by=current_user)
    db.add(budget)
    await db.commit()
    await db.refresh(budget)
    return budget


@router.get("/{project_id}/costs", response_model=list[ProjectCostResponse])
async def get_project_costs(
    project_id: UUID,
    cost_category: str | None = Query(None),
    task_id: UUID | None = Query(None),
    db: AsyncSession = Depends(get_db),
    current_user: UUID = Depends(get_current_user),
):
    """Get project costs."""
    query = select(ProjectCost).where(ProjectCost.project_id == project_id)

    if cost_category:
        query = query.where(ProjectCost.cost_category == cost_category)

    if task_id:
        query = query.where(ProjectCost.task_id == task_id)

    query = query.order_by(ProjectCost.transaction_date.desc())
    result = await db.execute(query)
    costs = result.scalars().all()
    return costs


@router.post("/costs", response_model=ProjectCostResponse, status_code=status.HTTP_201_CREATED)
async def create_cost(
    cost_data: ProjectCostCreate,
    db: AsyncSession = Depends(get_db),
    current_user: UUID = Depends(get_current_user),
):
    """Record project cost."""
    cost = ProjectCost(**cost_data.dict(), created_by=current_user)
    db.add(cost)
    await db.commit()
    await db.refresh(cost)
    return cost


@router.get("/{project_id}/summary")
async def get_budget_summary(
    project_id: UUID,
    db: AsyncSession = Depends(get_db),
    current_user: UUID = Depends(get_current_user),
):
    """Get budget vs actual summary."""
    # Get approved budget
    result = await db.execute(
        select(ProjectBudget)
        .where(ProjectBudget.project_id == project_id, ProjectBudget.is_approved)
        .order_by(ProjectBudget.version.desc())
        .limit(1)  # latest approved version; several versions may be approved over time
    )
    budget = result.scalar_one_or_none()

    # Get total costs
    result = await db.execute(select(func.sum(ProjectCost.amount)).where(ProjectCost.project_id == project_id))
    total_costs = result.scalar() or 0

    # Get costs by category
    result = await db.execute(
        select(ProjectCost.cost_category, func.sum(ProjectCost.amount))
        .where(ProjectCost.project_id == project_id)
        .group_by(ProjectCost.cost_category)
    )
    costs_by_category = {row[0]: row[1] for row in result.all()}

    if not budget:
        return {"budget": None, "total_costs": total_costs, "variance": None, "costs_by_category": costs_by_category}

    variance = float(budget.total_budget) - float(total_costs)
    variance_percentage = (variance / float(budget.total_budget)) * 100 if budget.total_budget > 0 else 0

    return {
        "budget": {
            "total": float(budget.total_budget),
            "labor": float(budget.labor_budget),
            "material": float(budget.material_budget),
            "equipment": float(budget.equipment_budget),
            "other": float(budget.other_budget),
            "contingency": float(budget.contingency_amount),
        },
        "total_costs": float(total_costs),
        "variance": variance,
        "variance_percentage": variance_percentage,
        "costs_by_category": costs_by_category,
    }
