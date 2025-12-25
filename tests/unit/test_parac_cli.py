"""Unit tests for paracle_cli parac commands."""

import os
from pathlib import Path

import pytest
import yaml
from click.testing import CliRunner

from paracle_cli.main import cli


class TestParacCommands:
    """Tests for parac CLI commands."""

    def setup_method(self) -> None:
        """Setup test fixtures."""
        self.runner = CliRunner()

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
                "focus_areas": ["testing"],
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

    def test_parac_help(self) -> None:
        """Test parac command help."""
        result = self.runner.invoke(cli, ["parac", "--help"])
        assert result.exit_code == 0
        assert "workspace" in result.output.lower()

    def test_parac_status_no_parac(self, tmp_path: Path) -> None:
        """Test status command when no .parac/ exists."""
        os.chdir(tmp_path)
        result = self.runner.invoke(
            cli, ["parac", "status"], catch_exceptions=False
        )
        # Should fail with exit code 1
        assert result.exit_code == 1
        assert "No .parac/" in result.output or "Error" in result.output

    def test_parac_status(self, temp_parac_project: Path) -> None:
        """Test status command with valid .parac/."""
        os.chdir(temp_parac_project)
        result = self.runner.invoke(cli, ["parac", "status"])

        assert result.exit_code == 0
        assert "test-project" in result.output
        assert "phase_1" in result.output
        assert "25%" in result.output

    def test_parac_status_json(self, temp_parac_project: Path) -> None:
        """Test status command with JSON output."""
        os.chdir(temp_parac_project)
        result = self.runner.invoke(cli, ["parac", "status", "--json"])

        assert result.exit_code == 0
        assert '"phase"' in result.output
        assert '"phase_1"' in result.output

    def test_parac_validate(self, temp_parac_project: Path) -> None:
        """Test validate command with valid workspace."""
        os.chdir(temp_parac_project)
        result = self.runner.invoke(cli, ["parac", "validate"])

        assert result.exit_code == 0
        assert "passed" in result.output.lower()

    def test_parac_sync(self, temp_parac_project: Path) -> None:
        """Test sync command."""
        os.chdir(temp_parac_project)
        result = self.runner.invoke(cli, ["parac", "sync", "--no-git"])

        assert result.exit_code == 0
        assert "complete" in result.output.lower()

    def test_parac_session_start(self, temp_parac_project: Path) -> None:
        """Test session start command."""
        os.chdir(temp_parac_project)
        result = self.runner.invoke(cli, ["parac", "session", "start"])

        assert result.exit_code == 0
        assert "SESSION START" in result.output
        assert "phase_1" in result.output

    def test_parac_session_end_dry_run(self, temp_parac_project: Path) -> None:
        """Test session end command with dry run."""
        os.chdir(temp_parac_project)
        result = self.runner.invoke(
            cli,
            ["parac", "session", "end", "--progress", "50", "--dry-run"],
        )

        assert result.exit_code == 0
        assert "Dry run" in result.output
        assert "progress" in result.output

    def test_parac_session_end_with_changes(
        self, temp_parac_project: Path
    ) -> None:
        """Test session end command with actual changes."""
        os.chdir(temp_parac_project)
        result = self.runner.invoke(
            cli,
            [
                "parac", "session", "end",
                "--progress", "75",
                "--complete", "task_a",
                "--start", "task_c",
            ],
        )

        assert result.exit_code == 0
        assert "applied" in result.output.lower()

        # Verify changes were saved
        state_file = (
            temp_parac_project / ".parac" / "memory" / "context"
            / "current_state.yaml"
        )
        with open(state_file, encoding="utf-8") as f:
            state = yaml.safe_load(f)

        assert state["current_phase"]["progress"] == "75%"
        assert "task_a" in state["current_phase"]["completed"]
        assert "task_c" in state["current_phase"]["in_progress"]
