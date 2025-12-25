"""State management for .parac/ workspace.

Handles reading, writing, and updating the current_state.yaml file
which represents the source of truth for project state.
"""

from dataclasses import dataclass, field
from datetime import date
from pathlib import Path
from typing import Any

import yaml


@dataclass
class PhaseState:
    """Current phase information."""

    id: str
    name: str
    status: str
    progress: str
    started_date: str | None = None
    completed_date: str | None = None
    focus_areas: list[str] = field(default_factory=list)
    completed: list[str] = field(default_factory=list)
    in_progress: list[str] = field(default_factory=list)
    pending: list[str] = field(default_factory=list)

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "PhaseState":
        """Create PhaseState from dictionary."""
        return cls(
            id=data.get("id", "unknown"),
            name=data.get("name", "unknown"),
            status=data.get("status", "unknown"),
            progress=data.get("progress", "0%"),
            started_date=data.get("started_date"),
            completed_date=data.get("completed_date"),
            focus_areas=data.get("focus_areas", []),
            completed=data.get("completed", []),
            in_progress=data.get("in_progress", []),
            pending=data.get("pending", []),
        )

    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary."""
        result: dict[str, Any] = {
            "id": self.id,
            "name": self.name,
            "status": self.status,
            "progress": self.progress,
        }
        if self.started_date:
            result["started_date"] = self.started_date
        if self.completed_date:
            result["completed_date"] = self.completed_date
        if self.focus_areas:
            result["focus_areas"] = self.focus_areas
        if self.completed:
            result["completed"] = self.completed
        if self.in_progress:
            result["in_progress"] = self.in_progress
        if self.pending:
            result["pending"] = self.pending
        return result


@dataclass
class ParacState:
    """Represents the current state of a .parac/ workspace."""

    version: str
    snapshot_date: str
    project_name: str
    project_version: str
    current_phase: PhaseState
    previous_phase: PhaseState | None = None
    metrics: dict[str, Any] = field(default_factory=dict)
    blockers: list[dict[str, Any]] = field(default_factory=list)
    next_actions: list[str] = field(default_factory=list)
    raw_data: dict[str, Any] = field(default_factory=dict)

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "ParacState":
        """Create ParacState from dictionary."""
        project = data.get("project", {})
        current_phase_data = data.get("current_phase", {})
        previous_phase_data = data.get("previous_phase")

        return cls(
            version=data.get("version", "1.0"),
            snapshot_date=data.get("snapshot_date", str(date.today())),
            project_name=project.get("name", "unknown"),
            project_version=project.get("version", "0.0.0"),
            current_phase=PhaseState.from_dict(current_phase_data),
            previous_phase=(
                PhaseState.from_dict(previous_phase_data)
                if previous_phase_data
                else None
            ),
            metrics=data.get("metrics", {}),
            blockers=data.get("blockers", []),
            next_actions=data.get("next_actions", []),
            raw_data=data,
        )

    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary for YAML serialization."""
        result = dict(self.raw_data)
        result["version"] = self.version
        result["snapshot_date"] = self.snapshot_date
        result["current_phase"] = self.current_phase.to_dict()
        if self.previous_phase:
            result["previous_phase"] = self.previous_phase.to_dict()
        result["metrics"] = self.metrics
        result["blockers"] = self.blockers
        result["next_actions"] = self.next_actions
        return result

    def update_progress(self, progress: int) -> None:
        """Update current phase progress."""
        if 0 <= progress <= 100:
            self.current_phase.progress = f"{progress}%"
            self.snapshot_date = str(date.today())

    def add_completed(self, item: str) -> None:
        """Add item to completed list."""
        if item not in self.current_phase.completed:
            self.current_phase.completed.append(item)
        if item in self.current_phase.in_progress:
            self.current_phase.in_progress.remove(item)
        if item in self.current_phase.pending:
            self.current_phase.pending.remove(item)
        self.snapshot_date = str(date.today())

    def add_in_progress(self, item: str) -> None:
        """Add item to in_progress list."""
        if item not in self.current_phase.in_progress:
            self.current_phase.in_progress.append(item)
        if item in self.current_phase.pending:
            self.current_phase.pending.remove(item)
        self.snapshot_date = str(date.today())

    def add_blocker(self, description: str, severity: str = "medium") -> None:
        """Add a blocker."""
        blocker = {
            "id": f"blocker_{len(self.blockers) + 1}",
            "description": description,
            "severity": severity,
            "added_date": str(date.today()),
        }
        self.blockers.append(blocker)
        self.snapshot_date = str(date.today())

    def remove_blocker(self, blocker_id: str) -> bool:
        """Remove a blocker by ID."""
        for i, blocker in enumerate(self.blockers):
            if blocker.get("id") == blocker_id:
                self.blockers.pop(i)
                self.snapshot_date = str(date.today())
                return True
        return False


def find_parac_root(start_path: Path | None = None) -> Path | None:
    """Find the .parac/ directory starting from a path and going up.

    Args:
        start_path: Starting directory. Defaults to current working directory.

    Returns:
        Path to .parac/ directory if found, None otherwise.
    """
    if start_path is None:
        start_path = Path.cwd()

    current = start_path.resolve()
    while current != current.parent:
        parac_dir = current / ".parac"
        if parac_dir.is_dir():
            return parac_dir
        current = current.parent

    # Check root
    parac_dir = current / ".parac"
    if parac_dir.is_dir():
        return parac_dir

    return None


def load_state(parac_root: Path | None = None) -> ParacState | None:
    """Load current state from .parac/memory/context/current_state.yaml.

    Args:
        parac_root: Path to .parac/ directory. If None, searches from cwd.

    Returns:
        ParacState if found and valid, None otherwise.
    """
    if parac_root is None:
        parac_root = find_parac_root()

    if parac_root is None:
        return None

    state_file = parac_root / "memory" / "context" / "current_state.yaml"
    if not state_file.exists():
        return None

    try:
        with open(state_file, encoding="utf-8") as f:
            data = yaml.safe_load(f)
        return ParacState.from_dict(data)
    except (yaml.YAMLError, KeyError, TypeError):
        return None


def save_state(state: ParacState, parac_root: Path | None = None) -> bool:
    """Save state to .parac/memory/context/current_state.yaml.

    Args:
        state: The state to save.
        parac_root: Path to .parac/ directory. If None, searches from cwd.

    Returns:
        True if saved successfully, False otherwise.
    """
    if parac_root is None:
        parac_root = find_parac_root()

    if parac_root is None:
        return False

    state_file = parac_root / "memory" / "context" / "current_state.yaml"
    state_file.parent.mkdir(parents=True, exist_ok=True)

    try:
        with open(state_file, "w", encoding="utf-8") as f:
            yaml.dump(
                state.to_dict(),
                f,
                default_flow_style=False,
                allow_unicode=True,
                sort_keys=False,
            )
        return True
    except (OSError, yaml.YAMLError):
        return False
