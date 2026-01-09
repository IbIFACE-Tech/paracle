"""Unit tests for Tool CRUD API endpoints."""

import uuid

import pytest
from fastapi.testclient import TestClient
from paracle_api.main import app
from paracle_api.routers import tool_crud


class TestToolCRUD:
    """Tests for /api/tools CRUD endpoints."""

    @pytest.fixture(autouse=True)
    def reset_repository(self) -> None:
        """Reset the tool repository before each test."""
        tool_crud._repository.clear()

    @pytest.fixture
    def client(self) -> TestClient:
        """Create test client."""
        return TestClient(app)

    @pytest.fixture
    def sample_tool_spec(self) -> dict:
        """Sample tool spec for testing with unique name."""
        return {
            "name": f"test-tool-{uuid.uuid4().hex[:8]}",
            "description": "Test tool for unit testing",
            "parameters": {
                "type": "object",
                "properties": {
                    "input": {"type": "string"},
                },
            },
            "returns": {"type": "string"},
            "is_mcp": False,
        }

    def test_create_tool(self, client: TestClient, sample_tool_spec: dict) -> None:
        """Test POST /api/tools."""
        response = client.post(
            "/api/tools",
            json={"spec": sample_tool_spec, "enabled": True},
        )

        assert response.status_code == 201
        data = response.json()
        assert "id" in data
        assert data["name"] == sample_tool_spec["name"]
        assert data["enabled"] is True
        assert data["is_mcp"] is False

    def test_create_tool_duplicate_name(
        self, client: TestClient, sample_tool_spec: dict
    ) -> None:
        """Test POST /api/tools with duplicate name."""
        # Create once
        client.post("/api/tools", json={"spec": sample_tool_spec})

        # Try to create again
        response = client.post("/api/tools", json={"spec": sample_tool_spec})

        assert response.status_code == 409
        assert "already exists" in response.json()["detail"].lower()

    def test_list_tools(self, client: TestClient, sample_tool_spec: dict) -> None:
        """Test GET /api/tools."""
        # Create some tools
        for i in range(3):
            spec = sample_tool_spec.copy()
            spec["name"] = f"tool-{i}"
            client.post("/api/tools", json={"spec": spec})

        response = client.get("/api/tools")

        assert response.status_code == 200
        data = response.json()
        assert "tools" in data
        assert data["total"] >= 3

    def test_list_tools_filter_by_enabled(
        self, client: TestClient, sample_tool_spec: dict
    ) -> None:
        """Test GET /api/tools with enabled filter."""
        # Create enabled tool
        spec1 = sample_tool_spec.copy()
        spec1["name"] = "enabled-tool"
        response1 = client.post("/api/tools", json={"spec": spec1, "enabled": True})
        tool_id = response1.json()["id"]

        # Create disabled tool
        spec2 = sample_tool_spec.copy()
        spec2["name"] = "disabled-tool"
        response2 = client.post("/api/tools", json={"spec": spec2, "enabled": False})

        # Filter by enabled=true
        response = client.get("/api/tools?enabled=true")

        assert response.status_code == 200
        data = response.json()
        assert all(t["enabled"] for t in data["tools"])

    def test_list_tools_filter_by_mcp(
        self, client: TestClient, sample_tool_spec: dict
    ) -> None:
        """Test GET /api/tools with is_mcp filter."""
        # Create MCP tool
        mcp_spec = sample_tool_spec.copy()
        mcp_spec["name"] = "mcp-tool"
        mcp_spec["is_mcp"] = True
        mcp_spec["mcp_server"] = "http://localhost:3000"
        client.post("/api/tools", json={"spec": mcp_spec})

        # Create non-MCP tool
        regular_spec = sample_tool_spec.copy()
        regular_spec["name"] = "regular-tool"
        client.post("/api/tools", json={"spec": regular_spec})

        # Filter by MCP tools
        response = client.get("/api/tools?is_mcp=true")

        assert response.status_code == 200
        data = response.json()
        assert all(t["is_mcp"] for t in data["tools"])

    def test_get_tool(self, client: TestClient, sample_tool_spec: dict) -> None:
        """Test GET /api/tools/{tool_id}."""
        # Create a tool
        create_response = client.post("/api/tools", json={"spec": sample_tool_spec})
        tool_id = create_response.json()["id"]

        # Get the tool
        response = client.get(f"/api/tools/{tool_id}")

        assert response.status_code == 200
        data = response.json()
        assert data["id"] == tool_id
        assert data["name"] == sample_tool_spec["name"]

    def test_get_tool_not_found(self, client: TestClient) -> None:
        """Test GET /api/tools/{tool_id} with invalid ID."""
        response = client.get("/api/tools/non-existent-id")

        assert response.status_code == 404

    def test_update_tool(self, client: TestClient, sample_tool_spec: dict) -> None:
        """Test PUT /api/tools/{tool_id}."""
        # Create a tool
        create_response = client.post("/api/tools", json={"spec": sample_tool_spec})
        tool_id = create_response.json()["id"]

        # Update the tool
        update_data = {
            "description": "Updated tool description",
        }
        response = client.put(f"/api/tools/{tool_id}", json=update_data)

        assert response.status_code == 200

    def test_update_tool_not_found(self, client: TestClient) -> None:
        """Test PUT /api/tools/{tool_id} with invalid ID."""
        response = client.put(
            "/api/tools/non-existent-id",
            json={"description": "New description"},
        )

        assert response.status_code == 404

    def test_delete_tool(self, client: TestClient, sample_tool_spec: dict) -> None:
        """Test DELETE /api/tools/{tool_id}."""
        # Create a tool
        create_response = client.post("/api/tools", json={"spec": sample_tool_spec})
        tool_id = create_response.json()["id"]

        # Delete the tool
        response = client.delete(f"/api/tools/{tool_id}")

        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True

        # Verify it's deleted
        get_response = client.get(f"/api/tools/{tool_id}")
        assert get_response.status_code == 404

    def test_delete_tool_not_found(self, client: TestClient) -> None:
        """Test DELETE /api/tools/{tool_id} with invalid ID."""
        response = client.delete("/api/tools/non-existent-id")

        assert response.status_code == 404

    def test_enable_tool(self, client: TestClient, sample_tool_spec: dict) -> None:
        """Test PUT /api/tools/{tool_id}/enable."""
        # Create a disabled tool
        create_response = client.post(
            "/api/tools", json={"spec": sample_tool_spec, "enabled": False}
        )
        tool_id = create_response.json()["id"]

        # Enable the tool
        response = client.put(f"/api/tools/{tool_id}/enable", json={"enabled": True})

        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        assert data["enabled"] is True

        # Verify it's enabled
        get_response = client.get(f"/api/tools/{tool_id}")
        assert get_response.json()["enabled"] is True

    def test_disable_tool(self, client: TestClient, sample_tool_spec: dict) -> None:
        """Test PUT /api/tools/{tool_id}/enable with enabled=false."""
        # Create an enabled tool
        create_response = client.post(
            "/api/tools", json={"spec": sample_tool_spec, "enabled": True}
        )
        tool_id = create_response.json()["id"]

        # Disable the tool
        response = client.put(f"/api/tools/{tool_id}/enable", json={"enabled": False})

        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        assert data["enabled"] is False

        # Verify it's disabled
        get_response = client.get(f"/api/tools/{tool_id}")
        assert get_response.json()["enabled"] is False

    def test_enable_tool_not_found(self, client: TestClient) -> None:
        """Test PUT /api/tools/{tool_id}/enable with invalid ID."""
        response = client.put(
            "/api/tools/non-existent-id/enable", json={"enabled": True}
        )

        assert response.status_code == 404
