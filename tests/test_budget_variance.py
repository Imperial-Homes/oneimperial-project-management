"""Budget vs actual by category (BOQ and Budget Variance pages)."""

from uuid import uuid4

import pytest
from httpx import AsyncClient

pytestmark = [pytest.mark.unit, pytest.mark.asyncio]


async def test_variance_by_category(client: AsyncClient, auth_headers: dict):
    created = await client.post(
        "/projects",
        json={"project_code": f"PRJ-{uuid4().hex[:6]}", "name": "Estate phase 1", "project_type": "construction"},
        headers=auth_headers,
    )
    assert created.status_code == 201, created.text
    project = created.json()["id"]
    r = await client.post(
        "/budgets",
        json={"project_id": project, "total_budget": 1000, "labor_budget": 600, "material_budget": 400},
        headers=auth_headers,
    )
    assert r.status_code == 201, r.text
    for category, amount in (("labor", 250), ("Material", 500)):
        r = await client.post(
            "/budgets/costs",
            json={"project_id": project, "cost_category": category, "amount": amount, "transaction_date": "2026-10-01"},
            headers=auth_headers,
        )
        assert r.status_code == 201, r.text

    body = (await client.get("/budgets/variance", params={"project_id": project}, headers=auth_headers)).json()
    by_cat = {row["category"]: (row["budgeted"], row["spent"]) for row in body["rows"]}
    assert by_cat["labor"] == (600, 250) and by_cat["material"] == (400, 500)
    assert body["variance"] == 250
