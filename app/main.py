"""Main FastAPI application."""

from fastapi import FastAPI, Request, status
# from fastapi.middleware.cors import CORSMiddleware  # Disabled - NGINX handles CORS
from fastapi.responses import JSONResponse
from fastapi.exceptions import RequestValidationError
from starlette.exceptions import HTTPException as StarletteHTTPException
import logging

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

logger = logging.getLogger(__name__)

app = FastAPI(
    title=settings.APP_NAME,
    version=settings.VERSION,
    description="Construction Project Management Service for OneImperial ERP",
    docs_url="/docs",
    redoc_url="/redoc",
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

# CORS middleware - DISABLED (NGINX handles CORS to prevent duplicate headers)
# app.add_middleware(
#     CORSMiddleware,
#     allow_origins=settings.cors_origins_list,
#     allow_credentials=True,
#     allow_methods=["*"],
#     allow_headers=["*"],
# )

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


# Global exception handlers
@app.exception_handler(StarletteHTTPException)
async def http_exception_handler(request: Request, exc: StarletteHTTPException):
    """Handle HTTP exceptions with proper CORS headers."""
    return JSONResponse(
        status_code=exc.status_code,
        content={
            "detail": exc.detail,
            "status_code": exc.status_code
        },
        headers={
            "Access-Control-Allow-Origin": request.headers.get("origin", "*"),
            "Access-Control-Allow-Credentials": "true",
        }
    )


@app.exception_handler(RequestValidationError)
async def validation_exception_handler(request: Request, exc: RequestValidationError):
    """Handle validation errors with proper CORS headers."""
    return JSONResponse(
        status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
        content={"detail": exc.errors()},
        headers={
            "Access-Control-Allow-Origin": request.headers.get("origin", "*"),
            "Access-Control-Allow-Credentials": "true",
        }
    )


@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    """Global exception handler with CORS headers."""
    logger.error(f"Unhandled exception: {exc}", exc_info=True)
    return JSONResponse(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        content={
            "detail": "An internal server error occurred",
            "error": str(exc) if settings.DEBUG else "Internal server error"
        },
        headers={
            "Access-Control-Allow-Origin": request.headers.get("origin", "*"),
            "Access-Control-Allow-Credentials": "true",
        }
    )
