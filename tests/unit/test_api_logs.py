"""Unit tests for paracle_api logs endpoints."""

from pathlib import Path

import pytest
import yaml
from fastapi.testclient import TestClient
from paracle_api.main import app


class TestLogsAPI:
    """Tests for /logs endpoints."""

    @pytest.fixture
    def client(self) -> TestClient:
        """Create test client."""
        return TestClient(app)

    @pytest.fixture
    def temp_parac_project(self, tmp_path: Path, monkeypatch) -> Path:
        """Create temporary project with .parac/ structure."""
        project = tmp_path / "project"
        project.mkdir()

        parac_root = project / ".parac"

        # Create required directories
        (parac_root / "roadmap").mkdir(parents=True)
        (parac_root / "memory" / "context").mkdir(parents=True)
        (parac_root / "memory" / "logs").mkdir(parents=True)

        # Create minimal state
        state = {
            "version": "1.0",
            "snapshot_date": "2025-12-25",
            "project": {"name": "test-project", "version": "0.0.1"},
            "current_phase": {
                "id": "phase_1",
                "name": "Test Phase",
                "status": "in_progress",
                "progress": "25%",
                "focus_areas": ["testing"],
                "completed": [],
                "in_progress": [],
                "pending": [],
            },
            "blockers": [],
            "next_actions": [],
        }
        state_file = parac_root / "memory" / "context" / "current_state.yaml"
        with open(state_file, "w", encoding="utf-8") as f:
            yaml.dump(state, f)

        # Change to project directory
        monkeypatch.chdir(project)

        return project

    def test_log_action(self, client: TestClient, temp_parac_project: Path) -> None:
        """Test POST /logs/action endpoint."""
        response = client.post(
            "/v1/logs/action",
            json={
                "action": "SYNC",
                "description": "Test sync action",
                "agent": "SystemAgent",
            },
        )

        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        assert data["action"] == "SYNC"
        assert data["agent"] == "SystemAgent"
        assert data["description"] == "Test sync action"
        assert "timestamp" in data

    def test_log_action_with_details(
        self, client: TestClient, temp_parac_project: Path
    ) -> None:
        """Test POST /logs/action with details."""
        response = client.post(
            "/v1/logs/action",
            json={
                "action": "IMPLEMENTATION",
                "description": "Added new feature",
                "agent": "CoderAgent",
                "details": {"files_changed": 3, "tests_added": 5},
            },
        )

        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        assert data["agent"] == "CoderAgent"

    def test_log_action_default_agent(
        self, client: TestClient, temp_parac_project: Path
    ) -> None:
        """Test POST /logs/action uses SystemAgent by default."""
        response = client.post(
            "/v1/logs/action",
            json={
                "action": "UPDATE",
                "description": "Updated configuration",
            },
        )

        assert response.status_code == 200
        data = response.json()
        assert data["agent"] == "SystemAgent"

    def test_log_decision(self, client: TestClient, temp_parac_project: Path) -> None:
        """Test POST /logs/decision endpoint."""
        response = client.post(
            "/v1/logs/decision",
            json={
                "agent": "ArchitectAgent",
                "decision": "Use hexagonal architecture",
                "rationale": "Better separation of concerns",
                "impact": "High - affects all packages",
            },
        )

        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        assert data["agent"] == "ArchitectAgent"
        assert data["decision"] == "Use hexagonal architecture"
        assert "timestamp" in data

    def test_get_recent_logs(
        self, client: TestClient, temp_parac_project: Path
    ) -> None:
        """Test GET /logs/recent endpoint."""
        # First, log some actions
        for i in range(5):
            client.post(
                "/v1/logs/action",
                json={
                    "action": "UPDATE",
                    "description": f"Action {i}",
                },
            )

        response = client.get("/v1/logs/recent?count=3")

        assert response.status_code == 200
        data = response.json()
        assert "logs" in data
        assert data["count"] == 3

    def test_get_recent_logs_default_count(
        self, client: TestClient, temp_parac_project: Path
    ) -> None:
        """Test GET /logs/recent with default count."""
        response = client.get("/v1/logs/recent")

        assert response.status_code == 200
        data = response.json()
        assert "logs" in data
        assert "count" in data

    def test_get_today_logs(self, client: TestClient, temp_parac_project: Path) -> None:
        """Test GET /logs/today endpoint."""
        # Log an action today
        client.post(
            "/v1/logs/action",
            json={
                "action": "SYNC",
                "description": "Today's action",
            },
        )

        response = client.get("/v1/logs/today")

        assert response.status_code == 200
        data = response.json()
        assert "logs" in data
        assert data["count"] >= 1

    def test_get_agent_logs(self, client: TestClient, temp_parac_project: Path) -> None:
        """Test GET /logs/agent/{agent} endpoint."""
        # Log actions from different agents
        client.post(
            "/v1/logs/action",
            json={
                "action": "IMPLEMENTATION",
                "description": "Code 1",
                "agent": "CoderAgent",
            },
        )
        client.post(
            "/v1/logs/action",
            json={"action": "TEST", "description": "Test 1", "agent": "TesterAgent"},
        )
        client.post(
            "/v1/logs/action",
            json={"action": "BUGFIX", "description": "Code 2", "agent": "CoderAgent"},
        )

        response = client.get("/v1/logs/agent/CoderAgent")

        assert response.status_code == 200
        data = response.json()
        assert data["agent"] == "CoderAgent"
        assert data["count"] == 2
        assert all("[CoderAgent]" in log for log in data["logs"])

    def test_get_agent_logs_invalid_agent(
        self, client: TestClient, temp_parac_project: Path
    ) -> None:
        """Test GET /logs/agent/{agent} with invalid agent."""
        response = client.get("/v1/logs/agent/InvalidAgent")

        assert response.status_code == 400
        assert "Invalid agent" in response.json()["detail"]

    def test_log_action_no_parac(
        self, client: TestClient, tmp_path: Path, monkeypatch
    ) -> None:
        """Test POST /logs/action when no .parac/ exists."""
        # Change to directory without .parac/
        empty_dir = tmp_path / "empty"
        empty_dir.mkdir()
        monkeypatch.chdir(empty_dir)

        response = client.post(
            "/v1/logs/action",
            json={
                "action": "SYNC",
                "description": "Should fail",
            },
        )

        assert response.status_code == 404
        assert "No .parac/" in response.json()["detail"]

    def test_log_action_invalid_action_type(
        self, client: TestClient, temp_parac_project: Path
    ) -> None:
        """Test POST /logs/action with invalid action type."""
        response = client.post(
            "/v1/logs/action",
            json={
                "action": "INVALID_ACTION",
                "description": "Should fail",
            },
        )

        assert response.status_code == 422  # Validation error

    def test_all_action_types_valid(
        self, client: TestClient, temp_parac_project: Path
    ) -> None:
        """Test that all ActionType values are accepted."""
        action_types = [
            "IMPLEMENTATION",
            "TEST",
            "REVIEW",
            "DOCUMENTATION",
            "DECISION",
            "PLANNING",
            "REFACTORING",
            "BUGFIX",
            "UPDATE",
            "SESSION",
            "SYNC",
            "VALIDATION",
            "INIT",
        ]

        for action_type in action_types:
            response = client.post(
                "/v1/logs/action",
                json={
                    "action": action_type,
                    "description": f"Test {action_type}",
                },
            )
            assert response.status_code == 200, f"Failed for {action_type}"

    def test_all_agent_types_valid(
        self, client: TestClient, temp_parac_project: Path
    ) -> None:
        """Test that all AgentType values are accepted."""
        agent_types = [
            "PMAgent",
            "ArchitectAgent",
            "CoderAgent",
            "TesterAgent",
            "ReviewerAgent",
            "DocumenterAgent",
            "SystemAgent",
        ]

        for agent_type in agent_types:
            response = client.post(
                "/v1/logs/action",
                json={
                    "action": "UPDATE",
                    "description": f"Test {agent_type}",
                    "agent": agent_type,
                },
            )
            assert response.status_code == 200, f"Failed for {agent_type}"
