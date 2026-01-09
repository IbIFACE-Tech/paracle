"""Unit tests for Agent CRUD API endpoints."""

import uuid

import pytest
from fastapi.testclient import TestClient
from paracle_api.main import app
from paracle_api.routers import agent_crud


class TestAgentCRUD:
    """Tests for /api/agents CRUD endpoints."""

    @pytest.fixture(autouse=True)
    def reset_repository(self) -> None:
        """Reset the agent repository before each test."""
        agent_crud._repository.clear()
        agent_crud._repository._specs.clear()

    @pytest.fixture
    def client(self) -> TestClient:
        """Create test client."""
        return TestClient(app)

    @pytest.fixture
    def sample_spec(self) -> dict:
        """Sample agent spec for testing with unique name."""
        return {
            "name": f"test-agent-{uuid.uuid4().hex[:8]}",
            "description": "Test agent",
            "provider": "openai",
            "model": "gpt-4",
            "temperature": 0.7,
        }

    def test_create_agent_from_inline_spec(
        self, client: TestClient, sample_spec: dict
    ) -> None:
        """Test POST /api/agents with inline spec."""
        response = client.post(
            "/api/agents",
            json={"spec": sample_spec, "resolve_inheritance": False},
        )

        assert response.status_code == 201
        data = response.json()
        assert "id" in data
        assert data["spec_name"] == sample_spec["name"]
        assert data["provider"] == "openai"
        assert data["model"] == "gpt-4"
        assert data["status"] == "pending"

    def test_create_agent_requires_spec_or_spec_name(self, client: TestClient) -> None:
        """Test POST /api/agents requires either spec or spec_name."""
        response = client.post("/api/agents", json={})

        assert response.status_code == 422  # Validation error

    def test_create_agent_from_registered_spec(
        self, client: TestClient, sample_spec: dict
    ) -> None:
        """Test creating agent from registered spec."""
        # First, register a spec
        client.post("/api/specs", json={"spec": sample_spec})

        # Then create agent from it
        response = client.post(
            "/api/agents",
            json={"spec_name": sample_spec["name"], "resolve_inheritance": False},
        )

        assert response.status_code == 201
        data = response.json()
        assert data["spec_name"] == sample_spec["name"]

    def test_create_agent_spec_not_found(self, client: TestClient) -> None:
        """Test POST /api/agents with non-existent spec_name."""
        response = client.post(
            "/api/agents",
            json={"spec_name": "non-existent", "resolve_inheritance": False},
        )

        assert response.status_code == 404
        assert "not found" in response.json()["detail"].lower()

    def test_list_agents(self, client: TestClient, sample_spec: dict) -> None:
        """Test GET /api/agents."""
        # Create some agents first
        for i in range(3):
            spec = sample_spec.copy()
            spec["name"] = f"agent-{i}"
            client.post("/api/agents", json={"spec": spec})

        response = client.get("/api/agents")

        assert response.status_code == 200
        data = response.json()
        assert "agents" in data
        assert data["total"] >= 3
        assert "limit" in data
        assert "offset" in data

    def test_list_agents_with_filters(
        self, client: TestClient, sample_spec: dict
    ) -> None:
        """Test GET /api/agents with filters."""
        # Create agents with different providers
        spec1 = sample_spec.copy()
        spec1["name"] = "openai-agent"
        spec1["provider"] = "openai"
        client.post("/api/agents", json={"spec": spec1})

        spec2 = sample_spec.copy()
        spec2["name"] = "anthropic-agent"
        spec2["provider"] = "anthropic"
        client.post("/api/agents", json={"spec": spec2})

        # Filter by provider
        response = client.get("/api/agents?provider=openai")

        assert response.status_code == 200
        data = response.json()
        assert all(a["provider"] == "openai" for a in data["agents"])

    def test_list_agents_pagination(
        self, client: TestClient, sample_spec: dict
    ) -> None:
        """Test GET /api/agents pagination."""
        response = client.get("/api/agents?limit=2&offset=0")

        assert response.status_code == 200
        data = response.json()
        assert data["limit"] == 2
        assert data["offset"] == 0
        assert len(data["agents"]) <= 2

    def test_get_agent(self, client: TestClient, sample_spec: dict) -> None:
        """Test GET /api/agents/{agent_id}."""
        # Create an agent
        create_response = client.post("/api/agents", json={"spec": sample_spec})
        agent_id = create_response.json()["id"]

        # Get the agent
        response = client.get(f"/api/agents/{agent_id}")

        assert response.status_code == 200
        data = response.json()
        assert data["id"] == agent_id
        assert data["spec_name"] == sample_spec["name"]

    def test_get_agent_not_found(self, client: TestClient) -> None:
        """Test GET /api/agents/{agent_id} with invalid ID."""
        response = client.get("/api/agents/non-existent-id")

        assert response.status_code == 404
        assert "not found" in response.json()["detail"].lower()

    def test_update_agent(self, client: TestClient, sample_spec: dict) -> None:
        """Test PUT /api/agents/{agent_id}."""
        # Create an agent
        create_response = client.post("/api/agents", json={"spec": sample_spec})
        agent_id = create_response.json()["id"]

        # Update the agent
        update_data = {
            "description": "Updated description",
            "temperature": 0.5,
        }
        response = client.put(f"/api/agents/{agent_id}", json=update_data)

        assert response.status_code == 200
        # Note: Response schema doesn't include temperature
        # This is expected as it returns summary data

    def test_update_agent_not_found(self, client: TestClient) -> None:
        """Test PUT /api/agents/{agent_id} with invalid ID."""
        response = client.put(
            "/api/agents/non-existent-id",
            json={"description": "New description"},
        )

        assert response.status_code == 404

    def test_delete_agent(self, client: TestClient, sample_spec: dict) -> None:
        """Test DELETE /api/agents/{agent_id}."""
        # Create an agent
        create_response = client.post("/api/agents", json={"spec": sample_spec})
        agent_id = create_response.json()["id"]

        # Delete the agent
        response = client.delete(f"/api/agents/{agent_id}")

        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        assert data["agent_id"] == agent_id

        # Verify it's deleted
        get_response = client.get(f"/api/agents/{agent_id}")
        assert get_response.status_code == 404

    def test_delete_agent_not_found(self, client: TestClient) -> None:
        """Test DELETE /api/agents/{agent_id} with invalid ID."""
        response = client.delete("/api/agents/non-existent-id")

        assert response.status_code == 404

    def test_update_agent_status(self, client: TestClient, sample_spec: dict) -> None:
        """Test PUT /api/agents/{agent_id}/status."""
        # Create an agent
        create_response = client.post("/api/agents", json={"spec": sample_spec})
        agent_id = create_response.json()["id"]

        # Update status
        status_data = {
            "phase": "active",
            "message": "Agent is now active",
        }
        response = client.put(f"/api/agents/{agent_id}/status", json=status_data)

        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "active"


class TestSpecManagement:
    """Tests for /api/specs endpoints."""

    @pytest.fixture(autouse=True)
    def reset_repository(self) -> None:
        """Reset the agent repository before each test."""
        agent_crud._repository.clear()
        agent_crud._repository._specs.clear()

    @pytest.fixture
    def client(self) -> TestClient:
        """Create test client."""
        return TestClient(app)

    @pytest.fixture
    def sample_spec(self) -> dict:
        """Sample agent spec for testing with unique name."""
        return {
            "name": f"spec-test-{uuid.uuid4().hex[:8]}",
            "description": "Test spec",
            "provider": "openai",
            "model": "gpt-4",
        }

    def test_register_spec(self, client: TestClient, sample_spec: dict) -> None:
        """Test POST /api/specs."""
        response = client.post("/api/specs", json={"spec": sample_spec})

        assert response.status_code == 201
        data = response.json()
        assert data["name"] == sample_spec["name"]
        assert data["provider"] == "openai"

    def test_register_spec_duplicate(
        self, client: TestClient, sample_spec: dict
    ) -> None:
        """Test POST /api/specs with duplicate name."""
        # Register once
        client.post("/api/specs", json={"spec": sample_spec})

        # Try to register again
        response = client.post("/api/specs", json={"spec": sample_spec})

        assert response.status_code == 409
        assert "already exists" in response.json()["detail"].lower()

    def test_register_spec_overwrite(
        self, client: TestClient, sample_spec: dict
    ) -> None:
        """Test POST /api/specs with overwrite=true."""
        # Register once
        client.post("/api/specs", json={"spec": sample_spec})

        # Overwrite
        modified_spec = sample_spec.copy()
        modified_spec["description"] = "Modified"
        response = client.post(
            "/api/specs",
            json={"spec": modified_spec, "overwrite": True},
        )

        assert response.status_code == 201

    def test_list_specs(self, client: TestClient, sample_spec: dict) -> None:
        """Test GET /api/specs."""
        # Register some specs
        for i in range(3):
            spec = sample_spec.copy()
            spec["name"] = f"spec-{i}"
            client.post("/api/specs", json={"spec": spec})

        response = client.get("/api/specs")

        assert response.status_code == 200
        data = response.json()
        assert "specs" in data
        assert data["total"] >= 3

    def test_get_spec(self, client: TestClient, sample_spec: dict) -> None:
        """Test GET /api/specs/{name}."""
        # Register a spec
        client.post("/api/specs", json={"spec": sample_spec})

        # Get the spec
        response = client.get(f"/api/specs/{sample_spec['name']}")

        assert response.status_code == 200
        data = response.json()
        assert data["name"] == sample_spec["name"]

    def test_get_spec_not_found(self, client: TestClient) -> None:
        """Test GET /api/specs/{name} with invalid name."""
        response = client.get("/api/specs/non-existent")

        assert response.status_code == 404

    def test_delete_spec(self, client: TestClient, sample_spec: dict) -> None:
        """Test DELETE /api/specs/{name}."""
        # Register a spec
        client.post("/api/specs", json={"spec": sample_spec})

        # Delete it
        response = client.delete(f"/api/specs/{sample_spec['name']}")

        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True

        # Verify it's deleted
        get_response = client.get(f"/api/specs/{sample_spec['name']}")
        assert get_response.status_code == 404

    def test_delete_spec_not_found(self, client: TestClient) -> None:
        """Test DELETE /api/specs/{name} with invalid name."""
        response = client.delete("/api/specs/non-existent")

        assert response.status_code == 404
