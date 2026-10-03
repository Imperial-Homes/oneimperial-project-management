"""Concurrent creates must not collide on generated sequential IDs."""

import asyncio

import pytest
from httpx import AsyncClient


@pytest.mark.asyncio
async def test_concurrent_site_visits_get_unique_ids(concurrent_client: AsyncClient, auth_headers: dict):
    payload = {
        "project_name": "Tower A",
        "site_location": "Accra",
        "visit_date": "2026-10-01T09:00:00",
        "visit_purpose": "Inspection",
    }
    responses = await asyncio.gather(
        *(concurrent_client.post("/site-visits", json=payload, headers=auth_headers) for _ in range(10))
    )

    assert [r.status_code for r in responses] == [201] * 10
    assert len({r.json()["visit_id"] for r in responses}) == 10
