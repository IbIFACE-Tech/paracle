"""Unit tests for Workflow CRUD API endpoints."""

import uuid

import pytest
from fastapi.testclient import TestClient
from paracle_api.main import app
from paracle_api.routers import workflow_crud


class TestWorkflowCRUD:
    """Tests for /api/workflows CRUD endpoints."""

    @pytest.fixture(autouse=True)
    def reset_repository(self, monkeypatch) -> None:
        """Reset the workflow repository before each test."""
        workflow_crud._repository.clear()
        # Mock the loader to return None so tests use the repository
        monkeypatch.setattr("paracle_api.routers.workflow_crud._loader", None)
        monkeypatch.setattr("paracle_api.routers.workflow_crud._get_loader", lambda: None)

    @pytest.fixture
    def client(self) -> TestClient:
        """Create test client."""
        return TestClient(app)

    @pytest.fixture
    def sample_workflow_spec(self) -> dict:
        """Sample workflow spec for testing with unique name."""
        return {
            "name": f"test-workflow-{uuid.uuid4().hex[:8]}",
            "description": "Test workflow",
            "steps": [
                {
                    "id": "step1",
                    "name": "First step",
                    "agent": "test-agent",
                    "depends_on": [],
                },
                {
                    "id": "step2",
                    "name": "Second step",
                    "agent": "test-agent",
                    "depends_on": ["step1"],
                },
            ],
        }

    def test_create_workflow(
        self, client: TestClient, sample_workflow_spec: dict
    ) -> None:
        """Test POST /api/workflows."""
        response = client.post("/api/workflows", json={"spec": sample_workflow_spec})

        assert response.status_code == 201
        data = response.json()
        assert "id" in data
        assert data["name"] == sample_workflow_spec["name"]
        assert data["status"] == "pending"
        assert data["steps_count"] == 2

    def test_list_workflows(
        self, client: TestClient, sample_workflow_spec: dict
    ) -> None:
        """Test GET /api/workflows."""
        # Create some workflows
        for i in range(3):
            spec = sample_workflow_spec.copy()
            spec["name"] = f"workflow-{i}"
            create_response = client.post("/api/workflows", json={"spec": spec})
            assert create_response.status_code == 201, f"Failed to create workflow {i}: {create_response.json()}"

        response = client.get("/api/workflows")

        assert response.status_code == 200
        data = response.json()
        assert "workflows" in data
        assert data["total"] >= 3

    def test_get_workflow(self, client: TestClient, sample_workflow_spec: dict) -> None:
        """Test GET /api/workflows/{workflow_id}."""
        # Create a workflow
        create_response = client.post(
            "/api/workflows", json={"spec": sample_workflow_spec}
        )
        workflow_id = create_response.json()["id"]

        # Get the workflow
        response = client.get(f"/api/workflows/{workflow_id}")

        assert response.status_code == 200
        data = response.json()
        assert data["id"] == workflow_id
        assert data["name"] == sample_workflow_spec["name"]

    def test_get_workflow_not_found(self, client: TestClient) -> None:
        """Test GET /api/workflows/{workflow_id} with invalid ID."""
        response = client.get("/api/workflows/non-existent-id")

        assert response.status_code == 404

    def test_update_workflow(
        self, client: TestClient, sample_workflow_spec: dict
    ) -> None:
        """Test PUT /api/workflows/{workflow_id}."""
        # Create a workflow
        create_response = client.post(
            "/api/workflows", json={"spec": sample_workflow_spec}
        )
        workflow_id = create_response.json()["id"]

        # Update the workflow
        update_data = {
            "description": "Updated workflow description",
        }
        response = client.put(f"/api/workflows/{workflow_id}", json=update_data)

        assert response.status_code == 200

    def test_delete_workflow(
        self, client: TestClient, sample_workflow_spec: dict
    ) -> None:
        """Test DELETE /api/workflows/{workflow_id}."""
        # Create a workflow
        create_response = client.post(
            "/api/workflows", json={"spec": sample_workflow_spec}
        )
        workflow_id = create_response.json()["id"]

        # Delete the workflow
        response = client.delete(f"/api/workflows/{workflow_id}")

        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True

        # Verify it's deleted
        get_response = client.get(f"/api/workflows/{workflow_id}")
        assert get_response.status_code == 404

    def test_execute_workflow(
        self, client: TestClient, sample_workflow_spec: dict
    ) -> None:
        """Test POST /api/workflows/{workflow_id}/execute."""
        # Create a workflow
        create_response = client.post(
            "/api/workflows", json={"spec": sample_workflow_spec}
        )
        workflow_id = create_response.json()["id"]

        # Execute the workflow
        response = client.post(
            f"/api/workflows/{workflow_id}/execute",
            json={"inputs": {}, "config": {}},
        )

        assert response.status_code == 200
        data = response.json()
        assert data["workflow_id"] == workflow_id
        assert data["status"] == "running"

    def test_execute_workflow_not_found(self, client: TestClient) -> None:
        """Test POST /api/workflows/{workflow_id}/execute with invalid ID."""
        response = client.post(
            "/api/workflows/non-existent/execute",
            json={"inputs": {}},
        )

        assert response.status_code == 404

    def test_list_workflows_with_status_filter(
        self, client: TestClient, sample_workflow_spec: dict
    ) -> None:
        """Test GET /api/workflows with status filter."""
        # Create and execute a workflow
        create_response = client.post(
            "/api/workflows", json={"spec": sample_workflow_spec}
        )
        workflow_id = create_response.json()["id"]
        client.post(f"/api/workflows/{workflow_id}/execute", json={})

        # Filter by running status
        response = client.get("/api/workflows?status=running")

        assert response.status_code == 200
        data = response.json()
        assert all(w["status"] == "running" for w in data["workflows"])

    def test_update_running_workflow_fails(
        self, client: TestClient, sample_workflow_spec: dict
    ) -> None:
        """Test that updating a running workflow fails."""
        # Create and execute a workflow
        create_response = client.post(
            "/api/workflows", json={"spec": sample_workflow_spec}
        )
        workflow_id = create_response.json()["id"]
        client.post(f"/api/workflows/{workflow_id}/execute", json={})

        # Try to update it
        response = client.put(
            f"/api/workflows/{workflow_id}",
            json={"description": "Updated"},
        )

        assert response.status_code == 400
        assert "running" in response.json()["detail"].lower()

    def test_delete_running_workflow_fails(
        self, client: TestClient, sample_workflow_spec: dict
    ) -> None:
        """Test that deleting a running workflow fails."""
        # Create and execute a workflow
        create_response = client.post(
            "/api/workflows", json={"spec": sample_workflow_spec}
        )
        workflow_id = create_response.json()["id"]
        client.post(f"/api/workflows/{workflow_id}/execute", json={})

        # Try to delete it
        response = client.delete(f"/api/workflows/{workflow_id}")

        assert response.status_code == 400
        assert "running" in response.json()["detail"].lower()
