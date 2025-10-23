"""Budget and Cost models."""

from datetime import date, datetime
from decimal import Decimal
from uuid import UUID, uuid4

from sqlalchemy import Boolean, Column, Date, DateTime, ForeignKey, Integer, Numeric, String, Text
from sqlalchemy.dialects.postgresql import UUID as PostgreSQLUUID
from sqlalchemy.orm import relationship

from app.database import Base


class ProjectBudget(Base):
    """Project Budget model - versions of project budgets."""
    
    __tablename__ = "project_budgets"
    
    id = Column(PostgreSQLUUID(as_uuid=True), primary_key=True, default=uuid4)
    project_id = Column(PostgreSQLUUID(as_uuid=True), ForeignKey("projects.id", ondelete="CASCADE"), nullable=False, index=True)
    version = Column(Integer, nullable=False, default=1)
    is_approved = Column(Boolean, default=False, index=True)
    total_budget = Column(Numeric(15, 2), nullable=False)
    labor_budget = Column(Numeric(15, 2), default=0)
    material_budget = Column(Numeric(15, 2), default=0)
    equipment_budget = Column(Numeric(15, 2), default=0)
    other_budget = Column(Numeric(15, 2), default=0)
    contingency_percentage = Column(Numeric(5, 2), default=0)
    contingency_amount = Column(Numeric(15, 2), default=0)
    currency = Column(String(3), default="GHS")
    created_at = Column(DateTime, default=datetime.utcnow)
    created_by = Column(PostgreSQLUUID(as_uuid=True))
    approved_at = Column(DateTime)
    approved_by = Column(PostgreSQLUUID(as_uuid=True))
    
    # Relationships
    project = relationship("Project", back_populates="budgets")


class ProjectCost(Base):
    """Project Cost model - tracks actual costs."""
    
    __tablename__ = "project_costs"
    
    id = Column(PostgreSQLUUID(as_uuid=True), primary_key=True, default=uuid4)
    project_id = Column(PostgreSQLUUID(as_uuid=True), ForeignKey("projects.id", ondelete="CASCADE"), nullable=False, index=True)
    task_id = Column(PostgreSQLUUID(as_uuid=True), ForeignKey("tasks.id", ondelete="SET NULL"), index=True)
    cost_category = Column(String(100), nullable=False, index=True)  # labor, material, equipment, other
    description = Column(Text)
    amount = Column(Numeric(15, 2), nullable=False)
    currency = Column(String(3), default="GHS")
    transaction_date = Column(Date, nullable=False, default=date.today)
    reference_number = Column(String(100))
    created_at = Column(DateTime, default=datetime.utcnow)
    created_by = Column(PostgreSQLUUID(as_uuid=True))
    
    # Relationships
    project = relationship("Project", back_populates="costs")
    task = relationship("Task", back_populates="costs")
