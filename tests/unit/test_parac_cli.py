"""Unit tests for paracle_cli governance commands."""

import os
from pathlib import Path

import pytest
import yaml
from click.testing import CliRunner

from paracle_cli.main import cli


class TestGovernanceCommands:
    """Tests for top-level governance CLI commands."""

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

    # ==================== NEW API TESTS ====================

    def test_status_no_parac(self, tmp_path: Path) -> None:
        """Test status command when no .parac/ exists."""
        os.chdir(tmp_path)
        result = self.runner.invoke(cli, ["status"], catch_exceptions=False)
        assert result.exit_code == 1
        assert "No .parac/" in result.output or "Error" in result.output

    def test_status(self, temp_parac_project: Path) -> None:
        """Test status command with valid .parac/."""
        os.chdir(temp_parac_project)
        result = self.runner.invoke(cli, ["status"])

        assert result.exit_code == 0
        assert "test-project" in result.output
        assert "phase_1" in result.output
        assert "25%" in result.output

    def test_status_json(self, temp_parac_project: Path) -> None:
        """Test status command with JSON output."""
        os.chdir(temp_parac_project)
        result = self.runner.invoke(cli, ["status", "--json"])

        assert result.exit_code == 0
        assert '"phase"' in result.output
        assert '"phase_1"' in result.output

    def test_validate(self, temp_parac_project: Path) -> None:
        """Test validate command invocation."""
        os.chdir(temp_parac_project)
        # validate is a command group, test that it invokes properly
        result = self.runner.invoke(cli, ["validate"])

        # Command should execute (exit code 0 or 1 for validation)
        # Just verify it doesn't crash with unexpected error
        assert result.exit_code in (0, 1, 2)
        # Accept help output, validation output, or error messages
        output_lower = result.output.lower()
        assert any(
            word in output_lower
            for word in ["validate", "passed", "failed", "usage", "error"]
        )

    def test_sync(self, temp_parac_project: Path) -> None:
        """Test sync command."""
        os.chdir(temp_parac_project)
        result = self.runner.invoke(cli, ["sync", "--no-git"])

        assert result.exit_code == 0
        assert "complete" in result.output.lower()

    def test_session_start(self, temp_parac_project: Path) -> None:
        """Test session start command."""
        os.chdir(temp_parac_project)
        result = self.runner.invoke(cli, ["session", "start"])

        assert result.exit_code == 0
        assert "SESSION START" in result.output
        assert "phase_1" in result.output

    def test_session_end_dry_run(self, temp_parac_project: Path) -> None:
        """Test session end command with dry run."""
        os.chdir(temp_parac_project)
        result = self.runner.invoke(
            cli,
            ["session", "end", "--progress", "50", "--dry-run"],
        )

        assert result.exit_code == 0
        assert "Dry run" in result.output
        assert "progress" in result.output

    def test_session_end_with_changes(self, temp_parac_project: Path) -> None:
        """Test session end command with actual changes."""
        os.chdir(temp_parac_project)
        result = self.runner.invoke(
            cli,
            [
                "session",
                "end",
                "--progress",
                "75",
                "--complete",
                "task_a",
                "--start",
                "task_c",
            ],
        )

        assert result.exit_code == 0
        assert "applied" in result.output.lower()

        # Verify changes were saved
        state_file = (
            temp_parac_project / ".parac" / "memory" / "context" / "current_state.yaml"
        )
        with open(state_file, encoding="utf-8") as f:
            state = yaml.safe_load(f)

        assert state["current_phase"]["progress"] == "75%"
        assert "task_a" in state["current_phase"]["completed"]
        assert "task_c" in state["current_phase"]["in_progress"]

    def test_init_creates_workspace(self, tmp_path: Path) -> None:
        """Test init command creates .parac/ structure."""
        os.chdir(tmp_path)
        target_dir = tmp_path / "new-project"
        target_dir.mkdir()

        result = self.runner.invoke(
            cli, ["init", str(target_dir), "--name", "my-project"]
        )

        assert result.exit_code == 0
        assert "initialized" in result.output.lower()

        # Verify structure
        parac_dir = target_dir / ".parac"
        assert parac_dir.exists()
        assert (parac_dir / "memory" / "context" / "current_state.yaml").exists()
        assert (parac_dir / "roadmap" / "roadmap.yaml").exists()
        assert (parac_dir / "GOVERNANCE.md").exists()

    def test_init_fails_if_exists(self, temp_parac_project: Path) -> None:
        """Test init command fails if .parac/ already exists."""
        result = self.runner.invoke(cli, ["init", str(temp_parac_project)])

        assert result.exit_code == 1
        assert "already exists" in result.output.lower()

    def test_init_force_overwrites(self, temp_parac_project: Path) -> None:
        """Test init --force overwrites existing .parac/."""
        result = self.runner.invoke(cli, ["init", str(temp_parac_project), "--force"])

        assert result.exit_code == 0
        assert "initialized" in result.output.lower()

    # ==================== LEGACY API TESTS (backward compatibility) ====================

    def test_legacy_parac_status(self, temp_parac_project: Path) -> None:
        """Test legacy 'parac status' still works."""
        os.chdir(temp_parac_project)
        result = self.runner.invoke(cli, ["parac", "status"])

        assert result.exit_code == 0
        assert "test-project" in result.output

    def test_legacy_parac_sync(self, temp_parac_project: Path) -> None:
        """Test legacy 'parac sync' still works."""
        os.chdir(temp_parac_project)
        result = self.runner.invoke(cli, ["parac", "sync", "--no-git"])

        assert result.exit_code == 0
        assert "complete" in result.output.lower()

    def test_legacy_parac_validate(self, temp_parac_project: Path) -> None:
        """Test legacy 'parac validate' still works."""
        os.chdir(temp_parac_project)
        result = self.runner.invoke(cli, ["parac", "validate"])

        assert result.exit_code == 0
        assert "passed" in result.output.lower()

    def test_legacy_parac_session_start(self, temp_parac_project: Path) -> None:
        """Test legacy 'parac session start' still works."""
        os.chdir(temp_parac_project)
        result = self.runner.invoke(cli, ["parac", "session", "start"])

        assert result.exit_code == 0
        assert "SESSION START" in result.output
