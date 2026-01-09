"""State management for .parac/ workspace.

Handles reading, writing, and updating the current_state.yaml file
which represents the source of truth for project state.

This module implements file-level locking and optimistic concurrency control
to prevent lost updates and data corruption in multi-process scenarios.
"""

from dataclasses import dataclass, field
from datetime import date
from pathlib import Path
from typing import Any

import yaml
from filelock import FileLock
from filelock import Timeout as FileLockTimeout

from paracle_core.parac.state_logging import log_state_change


class StateConflictError(Exception):
    """Raised when state has been modified by another process."""

    pass


class StateLockError(Exception):
    """Raised when unable to acquire file lock."""

    pass


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
    """Represents the current state of a .parac/ workspace.

    Includes revision counter for optimistic locking to detect
    concurrent modifications.
    """

    version: str
    snapshot_date: str
    project_name: str
    project_version: str
    current_phase: PhaseState
    previous_phase: PhaseState | None = None
    metrics: dict[str, Any] = field(default_factory=dict)
    blockers: list[dict[str, Any]] = field(default_factory=list)
    next_actions: list[str] = field(default_factory=list)
    revision: int = 0  # Revision counter for optimistic locking
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
            revision=data.get("revision", 0),
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
        result["revision"] = self.revision
        return result

    def update_progress(self, progress: int) -> None:
        """Update current phase progress."""
        if 0 <= progress <= 100:
            old_progress = self.current_phase.progress
            self.current_phase.progress = f"{progress}%"
            self.snapshot_date = str(date.today())

            # Log change if parac_root is available
            try:
                parac_root = find_parac_root()
                if parac_root:
                    log_state_change(
                        parac_root,
                        "progress",
                        f"Updated phase progress from {old_progress} to {progress}%",
                        old_value=old_progress,
                        new_value=f"{progress}%",
                        revision=self.revision,
                    )
            except Exception:
                pass  # Don't fail on logging errors

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


def load_state(
    parac_root: Path | None = None, *, timeout: float = 10.0
) -> ParacState | None:
    """Load current state from .parac/memory/context/current_state.yaml.

    Uses file locking to prevent reading during concurrent writes.

    Args:
        parac_root: Path to .parac/ directory. If None, searches from cwd.
        timeout: Lock acquisition timeout in seconds.

    Returns:
        ParacState if found and valid, None otherwise.

    Raises:
        StateLockError: If unable to acquire lock within timeout.
    """
    if parac_root is None:
        parac_root = find_parac_root()

    if parac_root is None:
        return None

    state_file = parac_root / "memory" / "context" / "current_state.yaml"
    if not state_file.exists():
        return None

    lock_file = state_file.with_suffix(".yaml.lock")

    try:
        with FileLock(str(lock_file), timeout=timeout):
            with open(state_file, encoding="utf-8") as f:
                data = yaml.safe_load(f)
            return ParacState.from_dict(data)
    except FileLockTimeout as e:
        raise StateLockError(
            f"Could not acquire lock for {state_file} within {timeout}s"
        ) from e
    except (yaml.YAMLError, KeyError, TypeError):
        return None


def save_state(
    state: ParacState,
    parac_root: Path | None = None,
    *,
    timeout: float = 10.0,
    check_conflict: bool = True,
) -> bool:
    """Save state to .parac/memory/context/current_state.yaml.

    Implements:
    - File-level locking to prevent concurrent writes
    - Atomic writes using temp file + rename
    - Optimistic locking with revision counter

    Args:
        state: The state to save.
        parac_root: Path to .parac/ directory. If None, searches from cwd.
        timeout: Lock acquisition timeout in seconds.
        check_conflict: If True, check for revision conflicts.

    Returns:
        True if saved successfully, False otherwise.

    Raises:
        StateConflictError: If state was modified by another process.
        StateLockError: If unable to acquire lock within timeout.
    """
    if parac_root is None:
        parac_root = find_parac_root()

    if parac_root is None:
        return False

    state_file = parac_root / "memory" / "context" / "current_state.yaml"
    lock_file = state_file.with_suffix(".yaml.lock")
    temp_file = state_file.with_suffix(".yaml.tmp")

    state_file.parent.mkdir(parents=True, exist_ok=True)

    try:
        with FileLock(str(lock_file), timeout=timeout):
            # Optimistic locking: check for conflicts
            if check_conflict and state_file.exists():
                with open(state_file, encoding="utf-8") as f:
                    current_data = yaml.safe_load(f)
                current_revision = current_data.get("revision", 0)

                if current_revision != state.revision:
                    raise StateConflictError(
                        f"State modified by another process "
                        f"(expected revision={state.revision}, "
                        f"got revision={current_revision}). "
                        f"Reload state and retry."
                    )

            # Increment revision before saving
            state.revision += 1

            # Atomic write: write to temp file, then rename
            with open(temp_file, "w", encoding="utf-8") as f:
                yaml.dump(
                    state.to_dict(),
                    f,
                    default_flow_style=False,
                    allow_unicode=True,
                    sort_keys=False,
                )

            # Atomic rename (overwrites existing file)
            temp_file.replace(state_file)

        return True
    except FileLockTimeout as e:
        raise StateLockError(
            f"Could not acquire lock for {state_file} within {timeout}s"
        ) from e
    except (StateConflictError, StateLockError):
        # Re-raise these exceptions
        raise
    except (OSError, yaml.YAMLError):
        # Clean up temp file on error
        if temp_file.exists():
            try:
                temp_file.unlink()
            except OSError:
                pass
        return False
