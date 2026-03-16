"""Main FastAPI application."""

from contextlib import asynccontextmanager

from fastapi import FastAPI, Request, status
from fastapi.middleware.cors import CORSMiddleware
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
    variations,
    payments,
    incidents,
    dashboard,
    timeline,
    progress,
    resource_utilization,
)
from app.config import settings
from app.core.logging import configure_logging, RequestIDMiddleware

logger = logging.getLogger(__name__)
configure_logging("INFO", service_name=settings.APP_NAME)

@asynccontextmanager
async def lifespan(app: FastAPI):
    """Startup and graceful shutdown — dispose DB pool and Redis connections."""
    logger.info("Service starting up")
    yield
    logger.info("Service shutting down — draining connections")
    from app.database import engine
    await engine.dispose()
    redis_url = getattr(settings, 'REDIS_URL', None)
    if redis_url:
        import redis.asyncio as aioredis
        try:
            client = aioredis.from_url(redis_url)
            await client.aclose()
        except Exception:
            pass
    logger.info("Shutdown complete")


app = FastAPI(
    lifespan=lifespan,
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


# CORS middleware — belt-and-suspenders for direct-port access in development.
# In production all traffic flows through NGINX which enforces the origin allowlist
# via the $cors_origin map and proxy_hide_header strips upstream CORS headers.
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins_list,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
# Outermost middleware — runs first on request, last on response.
# Generates X-Request-ID and logs method/path/status/latency for every request.
app.add_middleware(RequestIDMiddleware)


# Include routers
app.include_router(dashboard.router, prefix="/dashboard", tags=["Dashboard"])
app.include_router(projects.router, prefix="/projects", tags=["Projects"])
app.include_router(tasks.router, prefix="/tasks", tags=["Tasks"])
app.include_router(resources.router, prefix="/resources", tags=["Resources"])
app.include_router(resource_assignments.router, prefix="/assignments", tags=["Resource Assignments"])
app.include_router(schedules.router, prefix="/schedules", tags=["Schedules"])
app.include_router(budgets.router, prefix="/budgets", tags=["Budgets"])
app.include_router(variations.router, prefix="/variations", tags=["Variations"])
app.include_router(payments.router, prefix="/payments", tags=["Payments"])
app.include_router(incidents.router, prefix="/incidents", tags=["Incidents"])
app.include_router(timeline.router, prefix="/timelines", tags=["Timeline & Gantt"])
app.include_router(progress.router, prefix="/progress", tags=["Progress Tracking"])
app.include_router(resource_utilization.router, prefix="/utilization", tags=["Resource Utilization"])


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
    """Health check — verifies DB and Redis connectivity. Returns 503 if either is down."""
    from sqlalchemy import text
    import redis.asyncio as aioredis
    from app.database import engine

    checks = {}
    healthy = True

    # --- Database ---
    try:
        async with engine.connect() as conn:
            await conn.execute(text("SELECT 1"))
        checks["db"] = "ok"
    except Exception as exc:
        checks["db"] = f"error: {exc}"
        healthy = False

    # --- Redis ---
    redis_url = settings.REDIS_URL
    if redis_url:
        try:
            client = aioredis.from_url(redis_url, socket_connect_timeout=2)
            await client.ping()
            await client.aclose()
            checks["cache"] = "ok"
        except Exception as exc:
            checks["cache"] = f"error: {exc}"
            healthy = False
    else:
        checks["cache"] = "not_configured"

    return JSONResponse(
        status_code=200 if healthy else 503,
        content={
            "status": "healthy" if healthy else "unhealthy",
            "service": settings.APP_NAME,
            "checks": checks,
        },
    )


# Global exception handlers
@app.exception_handler(StarletteHTTPException)
async def http_exception_handler(request: Request, exc: StarletteHTTPException):
    """Handle HTTP exceptions. NGINX adds CORS headers."""
    return JSONResponse(
        status_code=exc.status_code,
        content={
            "detail": exc.detail,
            "status_code": exc.status_code
        }
    )


@app.exception_handler(RequestValidationError)
async def validation_exception_handler(request: Request, exc: RequestValidationError):
    """Handle validation errors. NGINX adds CORS headers."""
    return JSONResponse(
        status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
        content={"detail": exc.errors()}
    )


@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    """Global exception handler. NGINX adds CORS headers."""
    logger.error(f"Unhandled exception: {exc}", exc_info=True)
    return JSONResponse(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        content={
            "detail": "An internal server error occurred",
            "error": str(exc) if settings.DEBUG else "Internal server error"
        }
    )
