"""Unit tests for health API router."""

from fastapi.testclient import TestClient
from paracle_api.main import app


class TestHealthRouter:
    """Tests for health endpoints."""

    def setup_method(self) -> None:
        """Setup test client."""
        self.client = TestClient(app)

    def test_root_endpoint(self) -> None:
        """Test root endpoint returns welcome message."""
        response = self.client.get("/")

        assert response.status_code == 200
        data = response.json()
        assert "message" in data
        assert "Paracle" in data["message"]
        assert data["version"] == "0.0.1"

    def test_health_endpoint(self) -> None:
        """Test health check endpoint."""
        response = self.client.get("/v1/health")

        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "ok"
        assert data["version"] == "0.0.1"
        assert data["service"] == "paracle"

    def test_openapi_available(self) -> None:
        """Test OpenAPI schema is available."""
        response = self.client.get("/openapi.json")

        assert response.status_code == 200
        data = response.json()
        assert "openapi" in data
        assert "info" in data
        assert data["info"]["title"] == "Paracle API"
