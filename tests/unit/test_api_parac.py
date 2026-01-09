"""Unit tests for parac API router."""

import os
from pathlib import Path

import pytest
import yaml
from fastapi.testclient import TestClient

from paracle_api.main import app


class TestParacRouter:
    """Tests for parac governance endpoints."""

    def setup_method(self) -> None:
        """Setup test client."""
        self.client = TestClient(app)

    @pytest.fixture
    def temp_parac_project(self, tmp_path: Path) -> Path:
        """Create temporary project with .parac/ structure."""
        project = tmp_path / "project"
        project.mkdir()

        parac_root = project / ".parac"

        # Create required directories
        (parac_root / "roadmap").mkdir(parents=True)
        (parac_root / "memory" / "context").mkdir(parents=True)
        (parac_root / "policies").mkdir(parents=True)
        (parac_root / "agents").mkdir(parents=True)

        # Create required files
        roadmap = {
            "version": "0.0.1",
            "current_phase": "phase_1",
        }
        roadmap_file = parac_root / "roadmap" / "roadmap.yaml"
        with open(roadmap_file, "w", encoding="utf-8") as f:
            yaml.dump(roadmap, f)

        state = {
            "version": "1.0",
            "snapshot_date": "2025-12-24",
            "project": {"name": "test-project", "version": "0.0.1"},
            "current_phase": {
                "id": "phase_1",
                "name": "Test Phase",
                "status": "in_progress",
                "progress": "25%",
                "focus_areas": ["testing", "validation"],
                "completed": [],
                "in_progress": ["task_a"],
                "pending": ["task_b"],
            },
            "blockers": [],
            "next_actions": ["Do something"],
            "metrics": {},
        }
        state_file = parac_root / "memory" / "context" / "current_state.yaml"
        with open(state_file, "w", encoding="utf-8") as f:
            yaml.dump(state, f)

        policies = {"version": "1.0", "policies": []}
        policies_file = parac_root / "policies" / "policy-pack.yaml"
        with open(policies_file, "w", encoding="utf-8") as f:
            yaml.dump(policies, f)

        return project

    def test_status_no_parac(self, tmp_path: Path) -> None:
        """Test status endpoint when no .parac/ exists."""
        os.chdir(tmp_path)
        response = self.client.get("/parac/status")

        assert response.status_code == 404
        assert ".parac/" in response.json()["detail"]

    def test_status_success(self, temp_parac_project: Path) -> None:
        """Test status endpoint with valid .parac/."""
        os.chdir(temp_parac_project)
        response = self.client.get("/parac/status")

        assert response.status_code == 200
        data = response.json()
        assert "phase" in data
        assert data["phase"]["id"] == "phase_1"
        assert data["phase"]["progress"] == "25%"
        assert "git" in data
        assert "snapshot_date" in data

    def test_sync_success(self, temp_parac_project: Path) -> None:
        """Test sync endpoint."""
        os.chdir(temp_parac_project)
        response = self.client.post(
            "/parac/sync",
            json={"update_git": False, "update_metrics": True},
        )

        assert response.status_code == 200
        data = response.json()
        assert "success" in data
        assert "changes" in data

    def test_sync_default_options(self, temp_parac_project: Path) -> None:
        """Test sync endpoint with default options."""
        os.chdir(temp_parac_project)
        response = self.client.post("/parac/sync")

        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True

    def test_validate_success(self, temp_parac_project: Path) -> None:
        """Test validate endpoint with valid workspace."""
        os.chdir(temp_parac_project)
        response = self.client.get("/parac/validate")

        assert response.status_code == 200
        data = response.json()
        assert data["valid"] is True
        assert data["files_checked"] > 0
        assert data["errors"] == 0

    def test_session_start(self, temp_parac_project: Path) -> None:
        """Test session start endpoint."""
        os.chdir(temp_parac_project)
        response = self.client.post("/parac/session/start")

        assert response.status_code == 200
        data = response.json()
        assert data["phase"]["id"] == "phase_1"
        assert "testing" in data["focus_areas"]
        assert "Source of truth verified" in data["message"]

    def test_session_end_dry_run(self, temp_parac_project: Path) -> None:
        """Test session end endpoint with dry run."""
        os.chdir(temp_parac_project)
        response = self.client.post(
            "/parac/session/end",
            json={
                "progress": 50,
                "completed": ["task_a"],
                "dry_run": True,
            },
        )

        assert response.status_code == 200
        data = response.json()
        assert data["applied"] is False
        assert len(data["changes"]) > 0
        assert "Dry run" in data["message"]

    def test_session_end_apply_changes(self, temp_parac_project: Path) -> None:
        """Test session end endpoint applying changes."""
        os.chdir(temp_parac_project)
        response = self.client.post(
            "/parac/session/end",
            json={
                "progress": 75,
                "completed": ["task_a"],
                "in_progress": ["task_c"],
                "dry_run": False,
            },
        )

        assert response.status_code == 200
        data = response.json()
        assert data["applied"] is True
        assert len(data["changes"]) == 3  # progress + completed + in_progress
        assert "successfully" in data["message"]

        # Verify changes were saved
        state_file = (
            temp_parac_project / ".parac" / "memory" / "context" / "current_state.yaml"
        )
        with open(state_file, encoding="utf-8") as f:
            state = yaml.safe_load(f)

        assert state["current_phase"]["progress"] == "75%"
        assert "task_a" in state["current_phase"]["completed"]
        assert "task_c" in state["current_phase"]["in_progress"]

    def test_session_end_no_changes(self, temp_parac_project: Path) -> None:
        """Test session end endpoint with no changes."""
        os.chdir(temp_parac_project)
        response = self.client.post(
            "/parac/session/end",
            json={"dry_run": False},
        )

        assert response.status_code == 200
        data = response.json()
        assert data["applied"] is False
        assert len(data["changes"]) == 0
        assert "No changes" in data["message"]

    def test_session_end_progress_validation(self, temp_parac_project: Path) -> None:
        """Test session end progress validation."""
        os.chdir(temp_parac_project)

        # Test invalid progress (over 100)
        response = self.client.post(
            "/parac/session/end",
            json={"progress": 150},
        )
        assert response.status_code == 422  # Validation error

        # Test invalid progress (negative)
        response = self.client.post(
            "/parac/session/end",
            json={"progress": -10},
        )
        assert response.status_code == 422  # Validation error
