"""Structured JSON logging with per-request correlation ID.

Usage
-----
In main.py:
    from app.core.logging import configure_logging, RequestIDMiddleware, request_id_var
    configure_logging(settings.log_level)
    app.add_middleware(RequestIDMiddleware)

In any module:
    import logging
    logger = logging.getLogger(__name__)
    logger.info("something happened", extra={"key": "value"})
    # The current request_id is injected automatically by RequestIDFilter.
"""

import logging
import uuid
from collections.abc import Callable
from contextvars import ContextVar

from pythonjsonlogger import jsonlogger
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request
from starlette.responses import Response

# ---------------------------------------------------------------------------
# Request ID context — set once per request in RequestIDMiddleware.
# Readable anywhere in the call stack without passing it as an argument.
# ---------------------------------------------------------------------------
request_id_var: ContextVar[str] = ContextVar("request_id", default="")


class _RequestIDFilter(logging.Filter):
    """Injects the current request_id into every log record."""

    def filter(self, record: logging.LogRecord) -> bool:
        record.request_id = request_id_var.get("")
        return True


def configure_logging(log_level: str = "INFO", service_name: str = "") -> None:
    """Configure root logger to emit JSON lines.

    Call once at application startup (before the first request).
    All subsequent ``logging.getLogger(__name__)`` calls inherit this config.
    """
    handler = logging.StreamHandler()

    fmt = jsonlogger.JsonFormatter(
        fmt="%(asctime)s %(levelname)s %(name)s %(message)s",
        datefmt="%Y-%m-%dT%H:%M:%S",
        static_fields={"service": service_name} if service_name else {},
    )
    handler.setFormatter(fmt)
    handler.addFilter(_RequestIDFilter())

    root = logging.getLogger()
    root.setLevel(log_level.upper())

    # Remove any default handlers (uvicorn may add its own)
    root.handlers.clear()
    root.addHandler(handler)

    # Keep uvicorn access log quiet — we log requests ourselves
    logging.getLogger("uvicorn.access").propagate = False


class RequestIDMiddleware(BaseHTTPMiddleware):
    """Assign a unique X-Request-ID to every request and echo it in the response.

    * If the upstream already sent ``X-Request-ID`` (e.g. from NGINX or another
      service), that value is reused — enabling end-to-end correlation.
    * The ID is stored in a ``ContextVar`` so it is automatically included in
      every log line emitted during the request.
    * A companion request-logging block logs method, path, status, and latency.
    """

    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        import time

        req_id = request.headers.get("x-request-id") or str(uuid.uuid4())
        token = request_id_var.set(req_id)

        logger = logging.getLogger("request")
        start = time.perf_counter()

        try:
            response = await call_next(request)
        except Exception:
            logger.exception(
                "Unhandled exception during request",
                extra={
                    "method": request.method,
                    "path": request.url.path,
                    "request_id": req_id,
                },
            )
            raise
        finally:
            elapsed_ms = round((time.perf_counter() - start) * 1000, 1)
            logger.info(
                "request",
                extra={
                    "method": request.method,
                    "path": request.url.path,
                    "status": response.status_code if "response" in dir() else 500,
                    "duration_ms": elapsed_ms,
                    "request_id": req_id,
                },
            )
            request_id_var.reset(token)

        response.headers["X-Request-ID"] = req_id
        return response
