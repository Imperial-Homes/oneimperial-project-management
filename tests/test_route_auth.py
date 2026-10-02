"""Routes that were previously reachable without a login must stay authenticated."""

import pytest
from app.core.deps import get_current_user
from app.main import app
from fastapi.routing import APIRoute

pytestmark = pytest.mark.unit

PROTECTED_PREFIXES = (
    "/handover-packs",
)


def _dependency_calls(dependant):
    for dep in dependant.dependencies:
        yield dep.call
        yield from _dependency_calls(dep)


@pytest.mark.parametrize("prefix", PROTECTED_PREFIXES)
def test_router_requires_authentication(prefix):
    routes = [r for r in app.routes if isinstance(r, APIRoute) and r.path.startswith(prefix)]
    assert routes, f"no routes mounted under {prefix}"
    for route in routes:
        calls = set(_dependency_calls(route.dependant))
        assert get_current_user in calls, f"{sorted(route.methods)} {route.path} is reachable without a login"
