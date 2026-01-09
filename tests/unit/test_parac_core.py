"""Unit tests for paracle_core.parac module."""

from pathlib import Path

import pytest
import yaml
from paracle_core.parac.state import (
    ParacState,
    PhaseState,
    find_parac_root,
    load_state,
    save_state,
)
from paracle_core.parac.sync import ParacSynchronizer
from paracle_core.parac.validator import ParacValidator


class TestPhaseState:
    """Tests for PhaseState dataclass."""

    def test_from_dict(self) -> None:
        """Test creating PhaseState from dictionary."""
        data = {
            "id": "phase_1",
            "name": "Core Domain",
            "status": "in_progress",
            "progress": "25%",
            "focus_areas": ["testing", "validation"],
            "completed": ["setup"],
            "in_progress": ["core"],
        }
        phase = PhaseState.from_dict(data)

        assert phase.id == "phase_1"
        assert phase.name == "Core Domain"
        assert phase.status == "in_progress"
        assert phase.progress == "25%"
        assert "testing" in phase.focus_areas
        assert "setup" in phase.completed

    def test_to_dict(self) -> None:
        """Test converting PhaseState to dictionary."""
        phase = PhaseState(
            id="phase_1",
            name="Test",
            status="completed",
            progress="100%",
            completed=["item1"],
        )
        data = phase.to_dict()

        assert data["id"] == "phase_1"
        assert data["completed"] == ["item1"]


class TestParacState:
    """Tests for ParacState dataclass."""

    @pytest.fixture
    def sample_state_data(self) -> dict:
        """Sample state data for testing."""
        return {
            "version": "1.0",
            "snapshot_date": "2025-12-24",
            "project": {
                "name": "test-project",
                "version": "0.1.0",
            },
            "current_phase": {
                "id": "phase_1",
                "name": "Development",
                "status": "in_progress",
                "progress": "50%",
                "in_progress": ["feature_a"],
                "pending": ["feature_b"],
            },
            "metrics": {"coverage": "80%"},
            "blockers": [],
            "next_actions": ["Complete feature A"],
        }

    def test_from_dict(self, sample_state_data: dict) -> None:
        """Test creating ParacState from dictionary."""
        state = ParacState.from_dict(sample_state_data)

        assert state.version == "1.0"
        assert state.project_name == "test-project"
        assert state.current_phase.progress == "50%"

    def test_update_progress(self, sample_state_data: dict) -> None:
        """Test updating progress."""
        state = ParacState.from_dict(sample_state_data)
        state.update_progress(75)

        assert state.current_phase.progress == "75%"

    def test_add_completed(self, sample_state_data: dict) -> None:
        """Test adding completed item."""
        state = ParacState.from_dict(sample_state_data)
        state.add_completed("feature_a")

        assert "feature_a" in state.current_phase.completed
        assert "feature_a" not in state.current_phase.in_progress

    def test_add_in_progress(self, sample_state_data: dict) -> None:
        """Test adding in-progress item."""
        state = ParacState.from_dict(sample_state_data)
        state.add_in_progress("feature_b")

        assert "feature_b" in state.current_phase.in_progress
        assert "feature_b" not in state.current_phase.pending

    def test_add_blocker(self, sample_state_data: dict) -> None:
        """Test adding blocker."""
        state = ParacState.from_dict(sample_state_data)
        state.add_blocker("Dependency issue", "high")

        assert len(state.blockers) == 1
        assert state.blockers[0]["description"] == "Dependency issue"
        assert state.blockers[0]["severity"] == "high"


class TestStateIO:
    """Tests for state loading and saving."""

    @pytest.fixture
    def temp_parac(self, tmp_path: Path) -> Path:
        """Create temporary .parac/ structure."""
        parac_root = tmp_path / ".parac"
        state_dir = parac_root / "memory" / "context"
        state_dir.mkdir(parents=True)

        state_data = {
            "version": "1.0",
            "snapshot_date": "2025-12-24",
            "project": {"name": "test", "version": "0.1.0"},
            "current_phase": {
                "id": "phase_1",
                "name": "Test",
                "status": "in_progress",
                "progress": "0%",
            },
        }

        state_file = state_dir / "current_state.yaml"
        with open(state_file, "w") as f:
            yaml.dump(state_data, f)

        return parac_root

    def test_find_parac_root(self, temp_parac: Path) -> None:
        """Test finding .parac/ directory."""
        # From parent
        found = find_parac_root(temp_parac.parent)
        assert found == temp_parac

        # From inside
        subdir = temp_parac.parent / "src"
        subdir.mkdir()
        found = find_parac_root(subdir)
        assert found == temp_parac

    def test_find_parac_root_not_found(self, tmp_path: Path) -> None:
        """Test when .parac/ doesn't exist."""
        found = find_parac_root(tmp_path)
        assert found is None

    def test_load_state(self, temp_parac: Path) -> None:
        """Test loading state from file."""
        state = load_state(temp_parac)

        assert state is not None
        assert state.project_name == "test"
        assert state.current_phase.id == "phase_1"

    def test_save_state(self, temp_parac: Path) -> None:
        """Test saving state to file."""
        state = load_state(temp_parac)
        assert state is not None

        state.update_progress(50)
        result = save_state(state, temp_parac)

        assert result is True

        # Verify saved
        reloaded = load_state(temp_parac)
        assert reloaded is not None
        assert reloaded.current_phase.progress == "50%"


class TestParacValidator:
    """Tests for ParacValidator."""

    @pytest.fixture
    def valid_parac(self, tmp_path: Path) -> Path:
        """Create valid .parac/ structure."""
        parac_root = tmp_path / ".parac"

        # Create required directories
        (parac_root / "roadmap").mkdir(parents=True)
        (parac_root / "memory" / "context").mkdir(parents=True)
        (parac_root / "policies").mkdir(parents=True)
        (parac_root / "agents").mkdir(parents=True)

        # Create required files
        roadmap = {"version": "0.0.1", "current_phase": "phase_1"}
        with open(parac_root / "roadmap" / "roadmap.yaml", "w") as f:
            yaml.dump(roadmap, f)

        state = {
            "version": "1.0",
            "project": {"name": "test", "version": "0.0.1"},
            "current_phase": {
                "id": "phase_1",
                "name": "Test",
                "status": "active",
                "progress": "0%",
            },
        }
        with open(parac_root / "memory" / "context" / "current_state.yaml", "w") as f:
            yaml.dump(state, f)

        policies = {"version": "1.0", "policies": []}
        with open(parac_root / "policies" / "policy-pack.yaml", "w") as f:
            yaml.dump(policies, f)

        return parac_root

    def test_validate_valid_workspace(self, valid_parac: Path) -> None:
        """Test validating a valid workspace."""
        validator = ParacValidator(valid_parac)
        result = validator.validate()

        assert result.valid
        assert len(result.errors) == 0

    def test_validate_missing_directory(self, tmp_path: Path) -> None:
        """Test validating non-existent workspace."""
        validator = ParacValidator(tmp_path / ".parac")
        result = validator.validate()

        assert not result.valid
        assert len(result.errors) > 0

    def test_validate_invalid_yaml(self, valid_parac: Path) -> None:
        """Test validating workspace with invalid YAML."""
        # Write invalid YAML
        with open(valid_parac / "roadmap" / "roadmap.yaml", "w") as f:
            f.write("invalid: yaml: content: [")

        validator = ParacValidator(valid_parac)
        result = validator.validate()

        assert not result.valid
        yaml_errors = [e for e in result.errors if "YAML" in e.message]
        assert len(yaml_errors) > 0


class TestParacSynchronizer:
    """Tests for ParacSynchronizer."""

    @pytest.fixture
    def project_with_parac(self, tmp_path: Path) -> tuple[Path, Path]:
        """Create project with .parac/ structure."""
        project_root = tmp_path / "project"
        project_root.mkdir()

        parac_root = project_root / ".parac"
        state_dir = parac_root / "memory" / "context"
        state_dir.mkdir(parents=True)

        state_data = {
            "version": "1.0",
            "snapshot_date": "2025-01-01",
            "project": {"name": "test", "version": "0.1.0"},
            "current_phase": {
                "id": "phase_1",
                "name": "Test",
                "status": "in_progress",
                "progress": "0%",
            },
            "metrics": {},
        }
        with open(state_dir / "current_state.yaml", "w") as f:
            yaml.dump(state_data, f)

        # Create packages dir with some files
        packages = project_root / "packages"
        packages.mkdir()
        (packages / "module.py").touch()

        return parac_root, project_root

    def test_sync_updates_metrics(self, project_with_parac: tuple[Path, Path]) -> None:
        """Test that sync updates file metrics."""
        parac_root, project_root = project_with_parac

        sync = ParacSynchronizer(parac_root, project_root)
        result = sync.sync(update_git=False, update_metrics=True)

        assert result.success
        assert len(result.changes) > 0

    def test_get_summary(self, project_with_parac: tuple[Path, Path]) -> None:
        """Test getting project summary."""
        parac_root, project_root = project_with_parac

        sync = ParacSynchronizer(parac_root, project_root)
        summary = sync.get_summary()

        assert "phase" in summary
        assert summary["phase"]["id"] == "phase_1"
