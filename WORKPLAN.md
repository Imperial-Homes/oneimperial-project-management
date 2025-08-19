# Project Management Service - Development Workplan

## Overview
The Project Management Service handles all construction and development projects, including planning, scheduling, resource allocation, task tracking, and progress reporting within the OneImperial ERP system. This document outlines the specific tasks and timeline for developing this service.

## Technology Stack
- **Backend**: Python 3.11+ with FastAPI
- **Database**: PostgreSQL 15+
- **Authentication**: JWT tokens (via User Management Service)
- **Documentation**: OpenAPI/Swagger
- **Testing**: pytest with 80%+ coverage

## Development Tasks

### Week 1: Core Setup & Project Management

#### Day 1-2: Project Setup
- [ ] Initialize FastAPI project structure
- [ ] Configure PostgreSQL database connection with SQLAlchemy
- [ ] Set up Docker configuration
- [ ] Configure environment variables and settings
- [ ] Implement logging and error handling
- [ ] Set up pytest testing framework
- [ ] Integrate with User Management Service for authentication

#### Day 3-4: Project Management Core
- [ ] Design and implement project database models
  - Project details
  - Project types
  - Project status tracking
  - Project phases
- [ ] Implement project CRUD operations
  - Create project endpoint
  - Read project endpoint
  - Update project endpoint
  - Archive project endpoint
- [ ] Implement project search and filtering
- [ ] Create project dashboard
- [ ] Implement project status reporting

#### Day 5: Task Management
- [ ] Design and implement task database models
- [ ] Create task management system
  - Task creation
  - Task assignment
  - Task dependencies
  - Task status tracking
- [ ] Implement task prioritization
- [ ] Add task notifications
- [ ] Create task search and filtering

### Week 2: Resource Management, Scheduling & Integration

#### Day 1-2: Resource Management
- [ ] Design and implement resource database models
  - Human resources
  - Equipment
  - Materials
- [ ] Create resource allocation system
- [ ] Implement resource availability tracking
- [ ] Add resource utilization reporting
- [ ] Create resource conflict detection
- [ ] Implement resource capacity planning

#### Day 3: Project Scheduling
- [ ] Design and implement schedule database models
- [ ] Create Gantt chart data structure
- [ ] Implement critical path calculation
- [ ] Add milestone tracking
- [ ] Create schedule baseline and variance tracking
- [ ] Implement schedule dependencies

#### Day 4: Budget & Cost Tracking
- [ ] Design and implement budget database models
- [ ] Create budget planning system
- [ ] Implement cost tracking
- [ ] Add budget vs. actual reporting
- [ ] Create financial forecasting
- [ ] Implement earned value management

#### Day 5: Testing & Documentation
- [ ] Write unit tests for all endpoints
- [ ] Write integration tests for project management workflows
- [ ] Create API documentation with Swagger/OpenAPI
- [ ] Document project management processes
- [ ] Performance testing and optimization

## API Endpoints

### Project Management
```
GET    /projects                       # List projects (with filtering)
POST   /projects                       # Create new project
GET    /projects/{project_id}          # Get project details
PUT    /projects/{project_id}          # Update project
DELETE /projects/{project_id}          # Archive project
GET    /projects/{project_id}/status   # Get project status
PUT    /projects/{project_id}/status   # Update project status
GET    /projects/{project_id}/dashboard # Get project dashboard data
```

### Task Management
```
GET    /tasks                          # List tasks (with filtering)
POST   /tasks                          # Create new task
GET    /tasks/{task_id}                # Get task details
PUT    /tasks/{task_id}                # Update task
DELETE /tasks/{task_id}                # Delete task
PUT    /tasks/{task_id}/status         # Update task status
GET    /tasks/{task_id}/dependencies   # Get task dependencies
POST   /tasks/{task_id}/dependencies   # Add task dependency
DELETE /tasks/{task_id}/dependencies/{dependency_id} # Remove task dependency
```

### Resource Management
```
GET    /resources                      # List resources (with filtering)
POST   /resources                      # Create new resource
GET    /resources/{resource_id}        # Get resource details
PUT    /resources/{resource_id}        # Update resource
DELETE /resources/{resource_id}        # Delete resource
GET    /resources/{resource_id}/availability # Get resource availability
GET    /resources/{resource_id}/assignments # Get resource assignments
POST   /resources/allocate             # Allocate resources to tasks
GET    /resources/conflicts            # Get resource conflicts
```

### Project Scheduling
```
GET    /schedules/{project_id}         # Get project schedule
POST   /schedules/{project_id}         # Create project schedule
PUT    /schedules/{project_id}         # Update project schedule
GET    /schedules/{project_id}/gantt   # Get Gantt chart data
GET    /schedules/{project_id}/critical-path # Get critical path
GET    /schedules/{project_id}/milestones # Get project milestones
POST   /schedules/{project_id}/baseline # Set schedule baseline
GET    /schedules/{project_id}/variance # Get schedule variance
```

### Budget & Cost Tracking
```
GET    /budgets/{project_id}           # Get project budget
POST   /budgets/{project_id}           # Create project budget
PUT    /budgets/{project_id}           # Update project budget
GET    /budgets/{project_id}/costs     # Get project costs
POST   /budgets/{project_id}/costs     # Record project cost
GET    /budgets/{project_id}/forecast  # Get financial forecast
GET    /budgets/{project_id}/earned-value # Get earned value metrics
```

### Reporting
```
GET    /reports/projects/status        # Get projects status report
GET    /reports/resources/utilization  # Get resource utilization report
GET    /reports/tasks/completion       # Get task completion report
GET    /reports/budgets/variance       # Get budget variance report
GET    /reports/schedules/performance  # Get schedule performance report
```

## Database Schema

### Projects Table
```sql
CREATE TABLE projects (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    project_code VARCHAR(20) UNIQUE NOT NULL,
    name VARCHAR(255) NOT NULL,
    description TEXT,
    project_type VARCHAR(100) NOT NULL,
    client_id UUID,
    start_date DATE,
    target_end_date DATE,
    actual_end_date DATE,
    status VARCHAR(50) NOT NULL,
    priority VARCHAR(20) NOT NULL,
    budget DECIMAL(15,2),
    currency VARCHAR(3) DEFAULT 'USD',
    manager_id UUID,
    location VARCHAR(255),
    is_active BOOLEAN DEFAULT TRUE,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    created_by UUID,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_by UUID
);
```

### Project Phases Table
```sql
CREATE TABLE project_phases (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    project_id UUID REFERENCES projects(id) ON DELETE CASCADE,
    name VARCHAR(100) NOT NULL,
    description TEXT,
    sequence_number INTEGER NOT NULL,
    start_date DATE,
    end_date DATE,
    status VARCHAR(50) NOT NULL,
    completion_percentage DECIMAL(5,2) DEFAULT 0,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);
```

### Tasks Table
```sql
CREATE TABLE tasks (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    project_id UUID REFERENCES projects(id) ON DELETE CASCADE,
    phase_id UUID REFERENCES project_phases(id) ON DELETE SET NULL,
    parent_task_id UUID REFERENCES tasks(id) ON DELETE SET NULL,
    task_code VARCHAR(20) UNIQUE NOT NULL,
    name VARCHAR(255) NOT NULL,
    description TEXT,
    assignee_id UUID,
    start_date DATE,
    due_date DATE,
    completion_date DATE,
    estimated_hours DECIMAL(10,2),
    actual_hours DECIMAL(10,2) DEFAULT 0,
    status VARCHAR(50) NOT NULL,
    priority VARCHAR(20) NOT NULL,
    completion_percentage DECIMAL(5,2) DEFAULT 0,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);
```

### Task Dependencies Table
```sql
CREATE TABLE task_dependencies (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    task_id UUID REFERENCES tasks(id) ON DELETE CASCADE,
    dependency_task_id UUID REFERENCES tasks(id) ON DELETE CASCADE,
    dependency_type VARCHAR(50) NOT NULL,
    lag_days INTEGER DEFAULT 0,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    UNIQUE(task_id, dependency_task_id)
);
```

### Resources Table
```sql
CREATE TABLE resources (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    resource_code VARCHAR(20) UNIQUE NOT NULL,
    name VARCHAR(255) NOT NULL,
    description TEXT,
    resource_type VARCHAR(50) NOT NULL,
    employee_id UUID,
    equipment_id UUID,
    material_id UUID,
    cost_per_hour DECIMAL(10,2),
    cost_per_unit DECIMAL(10,2),
    currency VARCHAR(3) DEFAULT 'USD',
    availability_status VARCHAR(50) NOT NULL,
    capacity_per_day DECIMAL(10,2),
    unit_of_measure VARCHAR(50),
    is_active BOOLEAN DEFAULT TRUE,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);
```

### Resource Assignments Table
```sql
CREATE TABLE resource_assignments (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    resource_id UUID REFERENCES resources(id) ON DELETE CASCADE,
    task_id UUID REFERENCES tasks(id) ON DELETE CASCADE,
    project_id UUID REFERENCES projects(id) ON DELETE CASCADE,
    start_date DATE NOT NULL,
    end_date DATE NOT NULL,
    allocation_percentage DECIMAL(5,2) NOT NULL,
    hours_per_day DECIMAL(5,2),
    total_hours DECIMAL(10,2),
    status VARCHAR(50) NOT NULL,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    created_by UUID
);
```

### Project Schedules Table
```sql
CREATE TABLE project_schedules (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    project_id UUID REFERENCES projects(id) ON DELETE CASCADE,
    version INTEGER NOT NULL,
    is_baseline BOOLEAN DEFAULT FALSE,
    start_date DATE NOT NULL,
    end_date DATE NOT NULL,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    created_by UUID,
    notes TEXT
);
```

### Milestones Table
```sql
CREATE TABLE milestones (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    project_id UUID REFERENCES projects(id) ON DELETE CASCADE,
    name VARCHAR(255) NOT NULL,
    description TEXT,
    due_date DATE NOT NULL,
    completion_date DATE,
    status VARCHAR(50) NOT NULL,
    priority VARCHAR(20) NOT NULL,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);
```

### Project Budgets Table
```sql
CREATE TABLE project_budgets (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    project_id UUID REFERENCES projects(id) ON DELETE CASCADE,
    version INTEGER NOT NULL,
    is_approved BOOLEAN DEFAULT FALSE,
    total_budget DECIMAL(15,2) NOT NULL,
    labor_budget DECIMAL(15,2) DEFAULT 0,
    material_budget DECIMAL(15,2) DEFAULT 0,
    equipment_budget DECIMAL(15,2) DEFAULT 0,
    other_budget DECIMAL(15,2) DEFAULT 0,
    contingency_percentage DECIMAL(5,2) DEFAULT 0,
    contingency_amount DECIMAL(15,2) DEFAULT 0,
    currency VARCHAR(3) DEFAULT 'USD',
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    created_by UUID,
    approved_at TIMESTAMP WITH TIME ZONE,
    approved_by UUID
);
```

### Project Costs Table
```sql
CREATE TABLE project_costs (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    project_id UUID REFERENCES projects(id) ON DELETE CASCADE,
    task_id UUID REFERENCES tasks(id) ON DELETE SET NULL,
    cost_category VARCHAR(100) NOT NULL,
    description TEXT,
    amount DECIMAL(15,2) NOT NULL,
    currency VARCHAR(3) DEFAULT 'USD',
    transaction_date DATE NOT NULL,
    reference_number VARCHAR(100),
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    created_by UUID
);
```

## Testing Requirements

### Unit Tests
- Test all API endpoints
- Test project management workflows
- Test task management and dependencies
- Test resource allocation algorithms
- Test scheduling and critical path calculations
- Test budget and cost tracking

### Integration Tests
- Test complete project lifecycle
- Test resource allocation and conflict resolution
- Test schedule updates and dependency management
- Test budget vs. actual reporting

## Performance Goals
- API response time < 100ms for most endpoints
- Support 500+ concurrent users
- Efficient database queries with proper indexing
- Fast search and filtering capabilities
- Support for large projects with 1000+ tasks
- Gantt chart data generation < 2 seconds for large projects

## Deliverables
- Fully functional Project Management Service
- API documentation
- Test suite with 80%+ coverage
- Docker configuration for deployment
- Database migration scripts
