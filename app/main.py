"""Main FastAPI application."""

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api import (
    projects,
    tasks,
    resources,
    resource_assignments,
    schedules,
    budgets,
    dashboard,
)
from app.config import settings

app = FastAPI(
    title=settings.APP_NAME,
    version=settings.VERSION,
    description="Construction Project Management Service for OneImperial ERP",
    docs_url="/docs",
    redoc_url="/redoc",,
    servers=[
        {
            "url": "https://api.imperialhomesghana.com/api/projects",
            "description": "Production server"
        },
        {
            "url": "http://localhost/api/projects",
            "description": "Local development"
        },
        {
            "url": "/api/projects",
            "description": "Relative URL (current domain)"
        }
    ]
)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include routers
app.include_router(dashboard.router, prefix="/dashboard", tags=["Dashboard"])
app.include_router(projects.router, prefix="/projects", tags=["Projects"])
app.include_router(tasks.router, prefix="/tasks", tags=["Tasks"])
app.include_router(resources.router, prefix="/resources", tags=["Resources"])
app.include_router(resource_assignments.router, prefix="/assignments", tags=["Resource Assignments"])
app.include_router(schedules.router, prefix="/schedules", tags=["Schedules"])
app.include_router(budgets.router, prefix="/budgets", tags=["Budgets"])


@app.get("/")
async def root():
    """Root endpoint."""
    return {
        "service": settings.APP_NAME,
        "version": settings.VERSION,
        "status": "operational"
    }


@app.get("/health")
async def health_check():
    """Health check endpoint."""
    return {"status": "healthy"}
