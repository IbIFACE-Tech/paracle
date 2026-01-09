"""Roadmap synchronization for .parac/ workspace.

Synchronizes current_state.yaml with roadmap.yaml to prevent drift.
"""

from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

import yaml


@dataclass
class RoadmapSyncResult:
    """Result of roadmap synchronization."""

    success: bool
    changes: list[str] = field(default_factory=list)
    warnings: list[str] = field(default_factory=list)
    errors: list[str] = field(default_factory=list)
    suggestions: list[str] = field(default_factory=list)

    def add_change(self, description: str) -> None:
        """Record a change made."""
        self.changes.append(description)

    def add_warning(self, description: str) -> None:
        """Record a warning."""
        self.warnings.append(description)

    def add_error(self, description: str) -> None:
        """Record an error."""
        self.errors.append(description)
        self.success = False

    def add_suggestion(self, description: str) -> None:
        """Record a suggestion for manual action."""
        self.suggestions.append(description)


class RoadmapStateSynchronizer:
    """Synchronizes current_state.yaml with roadmap.yaml."""

    def __init__(self, parac_root: Path) -> None:
        """Initialize synchronizer.

        Args:
            parac_root: Path to .parac/ directory.
        """
        self.parac_root = parac_root
        self.roadmap_path = parac_root / "roadmap" / "roadmap.yaml"
        self.state_path = parac_root / "memory" / "context" / "current_state.yaml"

    def sync(self, dry_run: bool = False, auto_fix: bool = False) -> RoadmapSyncResult:
        """Synchronize current_state with roadmap.

        Args:
            dry_run: If True, only detect issues without making changes.
            auto_fix: If True, automatically fix safe mismatches.

        Returns:
            RoadmapSyncResult with changes and issues found.
        """
        result = RoadmapSyncResult(success=True)

        # Load both files
        roadmap = self._load_roadmap(result)
        state = self._load_state(result)

        if not roadmap or not state:
            result.add_error("Failed to load roadmap or state files")
            return result

        # Check phase alignment
        self._check_phase_alignment(roadmap, state, result, dry_run, auto_fix)

        # Check deliverables
        self._check_deliverables(roadmap, state, result, dry_run, auto_fix)

        # Check metrics
        self._check_metrics(roadmap, state, result, dry_run, auto_fix)

        # Save changes if not dry run
        if not dry_run and result.changes and auto_fix:
            self._save_state(state, result)

        return result

    def _load_roadmap(self, result: RoadmapSyncResult) -> dict[str, Any] | None:
        """Load roadmap.yaml."""
        if not self.roadmap_path.exists():
            result.add_error(f"Roadmap not found: {self.roadmap_path}")
            return None

        try:
            with open(self.roadmap_path, encoding="utf-8") as f:
                return yaml.safe_load(f)
        except Exception as e:
            result.add_error(f"Failed to load roadmap: {e}")
            return None

    def _load_state(self, result: RoadmapSyncResult) -> dict[str, Any] | None:
        """Load current_state.yaml."""
        if not self.state_path.exists():
            result.add_error(f"State not found: {self.state_path}")
            return None

        try:
            with open(self.state_path, encoding="utf-8") as f:
                return yaml.safe_load(f)
        except Exception as e:
            result.add_error(f"Failed to load state: {e}")
            return None

    def _check_phase_alignment(
        self,
        roadmap: dict[str, Any],
        state: dict[str, Any],
        result: RoadmapSyncResult,
        dry_run: bool,
        auto_fix: bool,
    ) -> None:
        """Check if phases align between roadmap and state."""
        roadmap_phases = {p["id"]: p for p in roadmap.get("phases", [])}
        current_phase_id = state.get("current_phase", {}).get("id")

        if not current_phase_id:
            result.add_warning("No current phase set in state")
            return

        # Check if current phase exists in roadmap
        if current_phase_id not in roadmap_phases:
            result.add_error(f"Current phase '{current_phase_id}' not found in roadmap")
            result.add_suggestion(
                "Update roadmap.yaml to include this phase or change current_state.yaml"
            )
            return

        roadmap_phase = roadmap_phases[current_phase_id]
        state_phase = state.get("current_phase", {})

        # Check phase name alignment
        roadmap_name = roadmap_phase.get("name", "")
        state_name = state_phase.get("name", "")

        if roadmap_name != state_name:
            result.add_warning(
                f"Phase name mismatch: roadmap='{roadmap_name}', state='{state_name}'"
            )
            if auto_fix and not dry_run:
                state["current_phase"]["name"] = roadmap_name
                result.add_change(f"Updated phase name to '{roadmap_name}'")

        # Check status alignment
        roadmap_status = roadmap_phase.get("status", "planned")
        state_status = state_phase.get("status", "unknown")

        if roadmap_status != state_status:
            result.add_warning(
                f"Phase {current_phase_id} status mismatch: "
                f"roadmap='{roadmap_status}', state='{state_status}'"
            )
            result.add_suggestion(
                "Consider updating roadmap.yaml status to match actual progress"
            )

        # Check completion percentage
        roadmap_completion = roadmap_phase.get("completion", 0)
        state_progress = state_phase.get("progress", "0%")

        # Handle both string ("75%") and int (75) formats
        if isinstance(state_progress, str):
            state_completion = int(state_progress.rstrip("%"))
        else:
            state_completion = int(state_progress)

        # Ensure roadmap_completion is also an int
        if isinstance(roadmap_completion, str):
            roadmap_completion = int(roadmap_completion.rstrip("%"))
        else:
            roadmap_completion = int(roadmap_completion)

        if abs(roadmap_completion - state_completion) > 10:  # Allow 10% tolerance
            result.add_warning(
                f"Phase {current_phase_id} completion mismatch: "
                f"roadmap={roadmap_completion}%, state={state_completion}%"
            )
            result.add_suggestion("Synchronize completion percentages between files")

    def _check_deliverables(
        self,
        roadmap: dict[str, Any],
        state: dict[str, Any],
        result: RoadmapSyncResult,
        dry_run: bool,
        auto_fix: bool,
    ) -> None:
        """Check if deliverables are consistent."""
        roadmap_phases = {p["id"]: p for p in roadmap.get("phases", [])}
        current_phase_id = state.get("current_phase", {}).get("id")

        if not current_phase_id or current_phase_id not in roadmap_phases:
            return

        roadmap_phase = roadmap_phases[current_phase_id]
        roadmap_deliverables = set(roadmap_phase.get("deliverables", []))

        # Get state deliverables (from various phase sections)
        state_deliverables = set()
        if f"phase_{current_phase_id.split('_')[1]}" in state.get("deliverables", {}):
            phase_deliverables = state["deliverables"][
                f"phase_{current_phase_id.split('_')[1]}"
            ]
            for item in phase_deliverables:
                if isinstance(item, dict):
                    state_deliverables.add(item.get("name", ""))

        # Check for missing deliverables in state
        missing = roadmap_deliverables - state_deliverables
        if missing:
            result.add_warning(
                f"Deliverables in roadmap but not in state: {', '.join(missing)}"
            )

        # Check for extra deliverables in state
        extra = state_deliverables - roadmap_deliverables
        if extra:
            result.add_suggestion(f"Consider adding to roadmap: {', '.join(extra)}")

    def _check_metrics(
        self,
        roadmap: dict[str, Any],
        state: dict[str, Any],
        result: RoadmapSyncResult,
        dry_run: bool,
        auto_fix: bool,
    ) -> None:
        """Check if metrics are consistent."""
        roadmap_metrics = roadmap.get("metrics", {})
        state_metrics = state.get("metrics", {})

        # Compare key metrics
        for key in ["test_coverage", "tests_passing"]:
            roadmap_value = roadmap_metrics.get(key)
            state_value = state_metrics.get(key)

            if roadmap_value and state_value and roadmap_value != state_value:
                # If it's a percentage string vs number
                if isinstance(roadmap_value, str) and roadmap_value.startswith(">"):
                    # Skip comparison for ">X%" format
                    continue

                result.add_suggestion(
                    f"Metric '{key}' differs: roadmap={roadmap_value}, state={state_value}"
                )

    def _save_state(self, state: dict[str, Any], result: RoadmapSyncResult) -> None:
        """Save updated state to current_state.yaml with file locking."""
        from filelock import FileLock
        from filelock import Timeout as FileLockTimeout

        lock_file = self.state_path.with_suffix(".yaml.lock")
        temp_file = self.state_path.with_suffix(".yaml.tmp")

        try:
            with FileLock(str(lock_file), timeout=10.0):
                # Atomic write: temp file + rename
                with open(temp_file, "w", encoding="utf-8") as f:
                    yaml.dump(
                        state,
                        f,
                        default_flow_style=False,
                        allow_unicode=True,
                        sort_keys=False,
                    )
                temp_file.replace(self.state_path)
            result.add_change("Updated current_state.yaml (with file locking)")
        except FileLockTimeout:
            result.add_error("Failed to acquire lock for state file (timeout)")
        except Exception as e:
            result.add_error(f"Failed to save state: {e}")
            # Clean up temp file on error
            if temp_file.exists():
                try:
                    temp_file.unlink()
                except OSError:
                    pass


def sync_roadmap_and_state(
    parac_root: Path, dry_run: bool = False, auto_fix: bool = False
) -> RoadmapSyncResult:
    """Synchronize roadmap and current_state.

    Args:
        parac_root: Path to .parac/ directory.
        dry_run: If True, only detect issues without making changes.
        auto_fix: If True, automatically fix safe mismatches.

    Returns:
        RoadmapSyncResult with changes and issues.
    """
    synchronizer = RoadmapStateSynchronizer(parac_root)
    return synchronizer.sync(dry_run=dry_run, auto_fix=auto_fix)
