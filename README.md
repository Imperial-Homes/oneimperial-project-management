# Project Management Service

OneImperial ERP Project Management Microservice - Complete construction project management with planning, task tracking, resource allocation, scheduling, and budget management.

## Features

### Project Management
- **Project Planning**: Create and manage construction projects with phases
- **Project Types**: Construction, renovation, development projects
- **Status Tracking**: Planning, active, on hold, completed, cancelled
- **Priority Levels**: Low, medium, high, critical
- **Client Linking**: Integration with CRM service
- **Budget Management**: Project budgets with contingency planning

### Task Management
- **Task Creation**: Hierarchical task structure with subtasks
- **Task Assignment**: Assign tasks to team members
- **Dependencies**: Task dependency management (FS, SS, FF, SF)
- **Progress Tracking**: Status and completion percentage
- **Time Tracking**: Estimated vs actual hours
- **Priority Management**: Task prioritization

### Resource Management
- **Resource Types**: Human, equipment, materials
- **Availability Tracking**: Real-time availability status
- **Capacity Planning**: Daily capacity management
- **Cost Management**: Per-hour and per-unit costs
- **Resource Allocation**: Assign resources to tasks/projects
- **Conflict Detection**: Prevent double-booking

### Project Scheduling
- **Schedule Versioning**: Multiple schedule versions
- **Baseline Management**: Set and track baseline schedules
- **Milestone Tracking**: Key project milestones
- **Gantt Chart Data**: Structured data for Gantt visualization
- **Critical Path**: Critical path analysis
- **Schedule Variance**: Track schedule performance

### Budget & Cost Tracking
- **Budget Planning**: Detailed budget breakdown (labor, material, equipment, other)
- **Contingency Management**: Percentage-based contingency
- **Cost Recording**: Track actual costs by category
- **Budget vs Actual**: Real-time variance analysis
- **Financial Forecasting**: Project cost forecasting
- **Earned Value**: Earned value management metrics

## Tech Stack
- Python 3.11+ with FastAPI
- PostgreSQL 15+ (async)
- JWT Authentication
- SQLAlchemy async ORM
- Pydantic v2 validation

## Quick Start

```bash
# Install dependencies
pip install -r requirements.txt

# Setup environment
cp .env.example .env

# Initialize database
python scripts/init_db.py

# Run service
uvicorn app.main:app --port 8005 --reload
```

## API Endpoints

**Projects**: 7 endpoints - CRUD, status management, dashboard
**Tasks**: 6 endpoints - CRUD, status tracking, dependencies
**Resources**: 6 endpoints - CRUD, availability, assignments
**Assignments**: 3 endpoints - Create, list, conflict detection
**Schedules**: 5 endpoints - Versioning, milestones, Gantt data
**Budgets**: 5 endpoints - Budget planning, cost tracking, variance

### Key Endpoints

```
# Projects
GET    /projects
POST   /projects
GET    /projects/{id}
PUT    /projects/{id}
PUT    /projects/{id}/status

# Tasks
GET    /tasks
POST   /tasks
PUT    /tasks/{id}

# Resources
GET    /resources
POST   /resources
GET    /resources/{id}

# Assignments
GET    /assignments
POST   /assignments

# Schedules
GET    /schedules/{project_id}
POST   /schedules
GET    /schedules/milestones/{project_id}

# Budgets
GET    /budgets/{project_id}
POST   /budgets
GET    /budgets/{project_id}/costs
POST   /budgets/costs
GET    /budgets/{project_id}/summary
```

## Documentation

- Swagger: http://localhost:8005/docs
- ReDoc: http://localhost:8005/redoc

## Database Models

- **Project**: Core project information with phases
- **ProjectPhase**: Project phases with sequence
- **Task**: Tasks with dependencies and assignments
- **TaskDependency**: Task relationship management
- **Resource**: Human/equipment/material resources
- **ResourceAssignment**: Resource allocation to tasks
- **ProjectSchedule**: Schedule versioning
- **Milestone**: Key project milestones
- **ProjectBudget**: Budget planning and approval
- **ProjectCost**: Actual cost tracking

## Workflow

1. **Create Project** → Set up project with phases
2. **Create Tasks** → Break down work into tasks
3. **Assign Resources** → Allocate team and equipment
4. **Set Schedule** → Define timeline and milestones
5. **Track Progress** → Update task status and hours
6. **Monitor Budget** → Record costs and track variance

## Testing

```bash
pytest --cov=app --cov-report=term-missing
