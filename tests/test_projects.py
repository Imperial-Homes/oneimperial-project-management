"""Tests for project endpoints."""

import pytest
from fastapi.testclient import TestClient


@pytest.mark.asyncio
async def test_create_project(client: TestClient, auth_headers: dict):
    """Test creating a project."""
    project_data = {
        "project_code": "PRJ-2024-001",
        "name": "Imperial Tower Construction",
        "description": "High-rise residential building",
        "project_type": "construction",
        "priority": "high",
        "budget": 5000000.00,
        "currency": "GHS",
        "location": "Accra, Ghana",
        "phases": [
            {
                "name": "Foundation",
                "description": "Foundation and basement work",
                "sequence_number": 1
            },
            {
                "name": "Structure",
                "description": "Main structure construction",
                "sequence_number": 2
            }
        ]
    }
    
    response = client.post("/projects", json=project_data, headers=auth_headers)
    
    assert response.status_code == 201
    data = response.json()
    assert data["project_code"] == "PRJ-2024-001"
    assert data["name"] == "Imperial Tower Construction"
    assert len(data["phases"]) == 2
    assert data["is_active"] is True


@pytest.mark.asyncio
async def test_list_projects(client: TestClient, auth_headers: dict):
    """Test listing projects."""
    # Create test projects
    for i in range(3):
        project_data = {
            "project_code": f"PRJ-TEST-00{i+1}",
            "name": f"Project {i+1}",
            "project_type": "construction",
            "currency": "GHS",
            "phases": []
        }
        client.post("/projects", json=project_data, headers=auth_headers)
    
    # List projects
    response = client.get("/projects", headers=auth_headers)
    
    assert response.status_code == 200
    data = response.json()
    assert "items" in data
    assert len(data["items"]) == 3
    assert data["total"] == 3


@pytest.mark.asyncio
async def test_get_project(client: TestClient, auth_headers: dict):
    """Test getting a specific project."""
    # Create project
    project_data = {
        "project_code": "PRJ-GET-TEST",
        "name": "Test Project",
        "project_type": "construction",
        "currency": "GHS",
        "phases": []
    }
    create_response = client.post("/projects", json=project_data, headers=auth_headers)
    project_id = create_response.json()["id"]
    
    # Get project
    response = client.get(f"/projects/{project_id}", headers=auth_headers)
    
    assert response.status_code == 200
    data = response.json()
    assert data["project_code"] == "PRJ-GET-TEST"
    assert data["name"] == "Test Project"


@pytest.mark.asyncio
async def test_update_project_status(client: TestClient, auth_headers: dict):
    """Test updating project status."""
    # Create project
    project_data = {
        "project_code": "PRJ-STATUS-TEST",
        "name": "Status Test Project",
        "project_type": "construction",
        "currency": "GHS",
        "phases": []
    }
    create_response = client.post("/projects", json=project_data, headers=auth_headers)
    project_id = create_response.json()["id"]
    
    # Update status
    response = client.put(
        f"/projects/{project_id}/status",
        params={"new_status": "active"},
        headers=auth_headers
    )
    
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "active"
