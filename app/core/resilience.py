"""Lightweight async-compatible circuit breaker for downstream service calls.

One CircuitBreaker instance is kept per downstream service name.  The breaker
transitions CLOSED → OPEN after `fail_max` consecutive failures, then moves to
HALF_OPEN after `reset_timeout` seconds to allow a single probe request.  A
successful probe closes the circuit; a failed probe re-opens it immediately.
"""

import logging
import time
from dataclasses import dataclass, field

logger = logging.getLogger(__name__)


@dataclass
class CircuitBreaker:
    name: str
    fail_max: int = 3            # consecutive failures before opening
    reset_timeout: float = 30.0  # seconds in OPEN before attempting HALF_OPEN

    _failures: int = field(default=0, init=False, repr=False)
    # "closed" | "open" | "half_open"
    _state: str = field(default="closed", init=False, repr=False)
    _opened_at: float = field(default=0.0, init=False, repr=False)

    def is_available(self) -> bool:
        """Return True if a request should be attempted."""
        if self._state == "closed":
            return True
        if self._state == "open":
            if time.monotonic() - self._opened_at >= self.reset_timeout:
                self._state = "half_open"
                logger.info("Circuit half-open — probing", extra={"circuit": self.name})
                return True
            return False
        # half_open: allow one probe through
        return True

    def record_success(self) -> None:
        """Call after a successful upstream response."""
        if self._state != "closed":
            logger.info("Circuit closed", extra={"circuit": self.name})
        self._failures = 0
        self._state = "closed"

    def record_failure(self) -> None:
        """Call after any upstream error or non-200 response."""
        self._failures += 1
        if self._failures >= self.fail_max or self._state == "half_open":
            self._state = "open"
            self._opened_at = time.monotonic()
            logger.warning(
                "Circuit OPENED",
                extra={"circuit": self.name, "consecutive_failures": self._failures},
            )


# Module-level singletons — one breaker per downstream service.
_breakers: dict[str, CircuitBreaker] = {}


def get_breaker(service: str) -> CircuitBreaker:
    """Return the shared CircuitBreaker for the named downstream service."""
    if service not in _breakers:
        _breakers[service] = CircuitBreaker(name=service)
    return _breakers[service]
