"""Roadmap Manager.

Manages multiple roadmap files with validation and synchronization.
Supports a primary roadmap plus unlimited user-defined additional roadmaps.
"""

from __future__ import annotations

from datetime import date
from pathlib import Path
from typing import Any

import yaml
from pydantic import BaseModel, Field

from paracle_core.parac.file_config import FileManagementConfig, RoadmapConfig


class RoadmapPhase(BaseModel):
    """A phase within a roadmap."""

    id: str
    name: str
    status: str = "pending"
    progress: float = 0.0
    start_date: date | None = None
    end_date: date | None = None
    deliverables: list[str | dict[str, Any]] = Field(default_factory=list)
    metrics: dict[str, Any] = Field(default_factory=dict)


class RoadmapMetadata(BaseModel):
    """Metadata for a roadmap file."""

    name: str
    path: Path
    description: str = ""
    exists: bool = True
    phase_count: int = 0
    current_phase: str | None = None


class Roadmap(BaseModel):
    """Full roadmap content."""

    name: str
    path: Path
    description: str = ""
    version: str = "1.0"
    phases: list[RoadmapPhase] = Field(default_factory=list)
    metadata: dict[str, Any] = Field(default_factory=dict)
    raw_content: dict[str, Any] = Field(default_factory=dict)


class ValidationResult(BaseModel):
    """Result of roadmap validation."""

    roadmap_name: str
    is_valid: bool
    errors: list[str] = Field(default_factory=list)
    warnings: list[str] = Field(default_factory=list)


class SyncResult(BaseModel):
    """Result of roadmap synchronization."""

    synced_roadmaps: list[str] = Field(default_factory=list)
    errors: list[str] = Field(default_factory=list)
    changes: list[str] = Field(default_factory=list)


class RoadmapManager:
    """Manage multiple roadmap files.

    Supports:
    - Primary roadmap (required)
    - Additional user-defined roadmaps (optional)
    - Validation of all roadmaps
    - Synchronization with current state
    - Adding/removing roadmaps dynamically

    Example:
        >>> manager = RoadmapManager(parac_root)
        >>> roadmaps = manager.list_roadmaps()
        >>> primary = manager.get_roadmap("primary")
        >>> manager.add_roadmap("research", "research-roadmap.yaml", "Research initiatives")
    """

    def __init__(
        self,
        parac_root: Path,
        config: RoadmapConfig | None = None,
    ):
        """Initialize Roadmap manager.

        Args:
            parac_root: Path to .parac/ directory.
            config: Optional RoadmapConfig. If None, loads from project.yaml.
        """
        self.parac_root = parac_root

        if config is None:
            file_config = FileManagementConfig.from_project_yaml(parac_root)
            config = file_config.roadmap

        self.config = config
        self.roadmap_dir = parac_root / config.base_path

    def _ensure_dir(self) -> None:
        """Ensure roadmap directory exists."""
        self.roadmap_dir.mkdir(parents=True, exist_ok=True)

    def list_roadmaps(self) -> list[RoadmapMetadata]:
        """List all configured roadmaps.

        Returns:
            List of roadmap metadata objects.
        """
        roadmaps: list[RoadmapMetadata] = []

        # Primary roadmap
        primary_path = self.roadmap_dir / self.config.primary
        primary_exists = primary_path.exists()
        primary_meta = RoadmapMetadata(
            name="primary",
            path=primary_path,
            description="Primary project roadmap",
            exists=primary_exists,
        )

        if primary_exists:
            content = self._load_roadmap_file(primary_path)
            if content:
                phases = content.get("phases", [])
                primary_meta.phase_count = len(phases)
                # Find current phase
                for phase in phases:
                    if phase.get("status") == "in_progress":
                        primary_meta.current_phase = phase.get("id")
                        break

        roadmaps.append(primary_meta)

        # Additional roadmaps
        for additional in self.config.additional:
            add_path = self.roadmap_dir / additional.path
            add_exists = add_path.exists()
            add_meta = RoadmapMetadata(
                name=additional.name,
                path=add_path,
                description=additional.description,
                exists=add_exists,
            )

            if add_exists:
                content = self._load_roadmap_file(add_path)
                if content:
                    phases = content.get("phases", [])
                    add_meta.phase_count = len(phases)
                    for phase in phases:
                        if phase.get("status") == "in_progress":
                            add_meta.current_phase = phase.get("id")
                            break

            roadmaps.append(add_meta)

        return roadmaps

    def get_roadmap(self, name: str = "primary") -> Roadmap | None:
        """Load a specific roadmap.

        Args:
            name: Name of the roadmap ("primary" or additional roadmap name).

        Returns:
            Roadmap object or None if not found.
        """
        # Find path for this roadmap
        if name == "primary":
            roadmap_path = self.roadmap_dir / self.config.primary
            description = "Primary project roadmap"
        else:
            # Search in additional roadmaps
            roadmap_path = None
            description = ""
            for additional in self.config.additional:
                if additional.name == name:
                    roadmap_path = self.roadmap_dir / additional.path
                    description = additional.description
                    break

            if roadmap_path is None:
                return None

        if not roadmap_path.exists():
            return None

        content = self._load_roadmap_file(roadmap_path)
        if content is None:
            return None

        # Parse phases
        phases: list[RoadmapPhase] = []
        for phase_data in content.get("phases", []):
            phase = RoadmapPhase(
                id=phase_data.get("id", ""),
                name=phase_data.get("name", ""),
                status=phase_data.get("status", "pending"),
                progress=phase_data.get("progress", 0.0),
                start_date=self._parse_date(phase_data.get("start_date")),
                end_date=self._parse_date(phase_data.get("end_date")),
                deliverables=phase_data.get("deliverables", []),
                metrics=phase_data.get("metrics", {}),
            )
            phases.append(phase)

        return Roadmap(
            name=name,
            path=roadmap_path,
            description=description,
            version=content.get("version", "1.0"),
            phases=phases,
            metadata=content.get("metadata", {}),
            raw_content=content,
        )

    def add_roadmap(
        self,
        name: str,
        path: str,
        description: str = "",
        create_file: bool = True,
    ) -> bool:
        """Add a new roadmap file.

        Args:
            name: Unique name for the roadmap.
            path: Relative path within roadmap directory.
            description: Description of the roadmap's purpose.
            create_file: Whether to create the file if it doesn't exist.

        Returns:
            True if added successfully, False if name already exists.
        """
        # Check if name already exists
        if name == "primary":
            return False

        for existing in self.config.additional:
            if existing.name == name:
                return False

        # Add to configuration (note: this doesn't persist to project.yaml)
        from paracle_core.parac.file_config import RoadmapFileConfig

        new_roadmap = RoadmapFileConfig(
            name=name,
            path=path,
            description=description,
        )
        self.config.additional.append(new_roadmap)

        # Create file if requested
        if create_file:
            self._ensure_dir()
            file_path = self.roadmap_dir / path

            # Create parent directories
            file_path.parent.mkdir(parents=True, exist_ok=True)

            if not file_path.exists():
                template = self._get_roadmap_template(name, description)
                file_path.write_text(template, encoding="utf-8")

        return True

    def remove_roadmap(self, name: str, delete_file: bool = False) -> bool:
        """Remove a roadmap from configuration.

        Args:
            name: Name of the roadmap to remove.
            delete_file: Whether to also delete the file.

        Returns:
            True if removed successfully, False if not found.
        """
        if name == "primary":
            return False  # Cannot remove primary

        for i, roadmap in enumerate(self.config.additional):
            if roadmap.name == name:
                if delete_file:
                    file_path = self.roadmap_dir / roadmap.path
                    if file_path.exists():
                        file_path.unlink()

                self.config.additional.pop(i)
                return True

        return False

    def validate(self, name: str | None = None) -> list[ValidationResult]:
        """Validate roadmap files.

        Args:
            name: Specific roadmap to validate, or None for all.

        Returns:
            List of validation results.
        """
        results: list[ValidationResult] = []

        roadmaps_to_validate = []
        if name:
            roadmaps_to_validate = [name]
        else:
            roadmaps_to_validate = ["primary"] + [
                r.name for r in self.config.additional
            ]

        for roadmap_name in roadmaps_to_validate:
            result = self._validate_single_roadmap(roadmap_name)
            results.append(result)

        return results

    def _validate_single_roadmap(self, name: str) -> ValidationResult:
        """Validate a single roadmap."""
        result = ValidationResult(roadmap_name=name, is_valid=True)

        roadmap = self.get_roadmap(name)
        if roadmap is None:
            result.is_valid = False
            result.errors.append(f"Roadmap '{name}' not found or could not be loaded")
            return result

        # Validate phases
        phase_ids = set()
        for phase in roadmap.phases:
            # Check for duplicate IDs
            if phase.id in phase_ids:
                result.errors.append(f"Duplicate phase ID: {phase.id}")
                result.is_valid = False
            phase_ids.add(phase.id)

            # Check required fields
            if not phase.id:
                result.errors.append("Phase missing required 'id' field")
                result.is_valid = False
            if not phase.name:
                result.errors.append(f"Phase '{phase.id}' missing 'name' field")
                result.is_valid = False

            # Validate progress
            if not 0.0 <= phase.progress <= 100.0:
                result.warnings.append(
                    f"Phase '{phase.id}' has invalid progress: {phase.progress}"
                )

            # Validate status
            valid_statuses = ["pending", "in_progress", "completed", "blocked"]
            if phase.status not in valid_statuses:
                result.warnings.append(
                    f"Phase '{phase.id}' has non-standard status: {phase.status}"
                )

            # Validate date consistency
            if phase.start_date and phase.end_date:
                if phase.start_date > phase.end_date:
                    result.errors.append(
                        f"Phase '{phase.id}' has start_date after end_date"
                    )
                    result.is_valid = False

        # Check for exactly one in_progress phase
        in_progress_count = sum(1 for p in roadmap.phases if p.status == "in_progress")
        if in_progress_count > 1:
            result.warnings.append(
                f"Multiple phases in 'in_progress' status ({in_progress_count})"
            )

        return result

    def sync_with_state(self) -> SyncResult:
        """Synchronize all roadmaps with current state.

        Returns:
            Sync result with details of what changed.
        """
        result = SyncResult()

        if not self.config.sync.get("enabled", True):
            return result

        # Load current state
        state_path = self.parac_root / "memory" / "context" / "current_state.yaml"
        if not state_path.exists():
            result.errors.append("current_state.yaml not found")
            return result

        try:
            with open(state_path, encoding="utf-8") as f:
                current_state = yaml.safe_load(f)
        except Exception as e:
            result.errors.append(f"Failed to load current_state.yaml: {e}")
            return result

        # Sync primary roadmap
        primary = self.get_roadmap("primary")
        if primary and self.config.sync.get("validate_on_sync", True):
            # Validate before sync
            validation = self._validate_single_roadmap("primary")
            if not validation.is_valid:
                result.errors.extend(validation.errors)
                return result

        if primary and self.config.sync.get("auto_update_state", True):
            changes = self._sync_roadmap_to_state(primary, current_state)
            if changes:
                result.changes.extend(changes)
                result.synced_roadmaps.append("primary")

                # Write back updated state
                try:
                    with open(state_path, "w", encoding="utf-8") as f:
                        yaml.safe_dump(current_state, f, default_flow_style=False)
                except Exception as e:
                    result.errors.append(f"Failed to update current_state.yaml: {e}")

        return result

    def _sync_roadmap_to_state(
        self, roadmap: Roadmap, state: dict[str, Any]
    ) -> list[str]:
        """Sync a single roadmap to current state."""
        changes: list[str] = []

        current_phase = state.get("current_phase", {})
        roadmap_current_phase = None

        # Find current phase in roadmap
        for phase in roadmap.phases:
            if phase.status == "in_progress":
                roadmap_current_phase = phase
                break

        if roadmap_current_phase is None:
            return changes

        # Check for mismatches and update state
        state_phase_id = current_phase.get("id")
        if state_phase_id != roadmap_current_phase.id:
            current_phase["id"] = roadmap_current_phase.id
            changes.append(f"Updated current_phase.id to '{roadmap_current_phase.id}'")

        state_phase_name = current_phase.get("name")
        if state_phase_name != roadmap_current_phase.name:
            current_phase["name"] = roadmap_current_phase.name
            changes.append(
                f"Updated current_phase.name to '{roadmap_current_phase.name}'"
            )

        state_progress = current_phase.get("progress")
        if state_progress != roadmap_current_phase.progress:
            current_phase["progress"] = roadmap_current_phase.progress
            changes.append(
                f"Updated current_phase.progress to {roadmap_current_phase.progress}"
            )

        state["current_phase"] = current_phase
        return changes

    def get_current_phase(self, name: str = "primary") -> RoadmapPhase | None:
        """Get the current (in_progress) phase from a roadmap.

        Args:
            name: Name of the roadmap.

        Returns:
            The current phase or None.
        """
        roadmap = self.get_roadmap(name)
        if roadmap is None:
            return None

        for phase in roadmap.phases:
            if phase.status == "in_progress":
                return phase

        return None

    def get_next_phase(self, name: str = "primary") -> RoadmapPhase | None:
        """Get the next pending phase from a roadmap.

        Args:
            name: Name of the roadmap.

        Returns:
            The next pending phase or None.
        """
        roadmap = self.get_roadmap(name)
        if roadmap is None:
            return None

        for phase in roadmap.phases:
            if phase.status == "pending":
                return phase

        return None

    def update_phase_status(self, name: str, phase_id: str, new_status: str) -> bool:
        """Update a phase's status in a roadmap.

        Args:
            name: Name of the roadmap.
            phase_id: ID of the phase to update.
            new_status: New status (pending, in_progress, completed, blocked).

        Returns:
            True if updated, False if not found.
        """
        roadmap = self.get_roadmap(name)
        if roadmap is None:
            return False

        # Update in raw content
        for phase in roadmap.raw_content.get("phases", []):
            if phase.get("id") == phase_id:
                phase["status"] = new_status
                break
        else:
            return False

        # Write back
        try:
            with open(roadmap.path, "w", encoding="utf-8") as f:
                yaml.safe_dump(roadmap.raw_content, f, default_flow_style=False)
            return True
        except Exception:
            return False

    def update_phase_progress(self, name: str, phase_id: str, progress: float) -> bool:
        """Update a phase's progress in a roadmap.

        Args:
            name: Name of the roadmap.
            phase_id: ID of the phase to update.
            progress: New progress value (0-100).

        Returns:
            True if updated, False if not found.
        """
        if not 0.0 <= progress <= 100.0:
            return False

        roadmap = self.get_roadmap(name)
        if roadmap is None:
            return False

        # Update in raw content
        for phase in roadmap.raw_content.get("phases", []):
            if phase.get("id") == phase_id:
                phase["progress"] = progress
                break
        else:
            return False

        # Write back
        try:
            with open(roadmap.path, "w", encoding="utf-8") as f:
                yaml.safe_dump(roadmap.raw_content, f, default_flow_style=False)
            return True
        except Exception:
            return False

    def _load_roadmap_file(self, path: Path) -> dict[str, Any] | None:
        """Load a roadmap YAML file."""
        try:
            with open(path, encoding="utf-8") as f:
                return yaml.safe_load(f)
        except Exception:
            return None

    def _parse_date(self, date_str: str | date | None) -> date | None:
        """Parse a date string or return date object."""
        if date_str is None:
            return None
        if isinstance(date_str, date):
            return date_str
        try:
            return date.fromisoformat(str(date_str))
        except (ValueError, TypeError):
            return None

    def _get_roadmap_template(self, name: str, description: str) -> str:
        """Get template for new roadmap file."""
        return f"""# {name.title()} Roadmap
# {description}
# Created: {date.today().isoformat()}

version: "1.0"

metadata:
  name: {name}
  description: "{description}"
  created_at: "{date.today().isoformat()}"

phases:
  - id: phase_1
    name: "Phase 1"
    status: pending
    progress: 0
    description: "First phase"
    deliverables: []
    metrics: {{}}
"""

    def search_phases(
        self, query: str, roadmap_name: str | None = None
    ) -> list[tuple[str, RoadmapPhase]]:
        """Search phases across roadmaps.

        Args:
            query: Search term (case-insensitive).
            roadmap_name: Specific roadmap to search, or None for all.

        Returns:
            List of (roadmap_name, phase) tuples.
        """
        results: list[tuple[str, RoadmapPhase]] = []
        query_lower = query.lower()

        roadmaps_to_search = []
        if roadmap_name:
            roadmaps_to_search = [roadmap_name]
        else:
            roadmaps_to_search = ["primary"] + [r.name for r in self.config.additional]

        for name in roadmaps_to_search:
            roadmap = self.get_roadmap(name)
            if roadmap is None:
                continue

            for phase in roadmap.phases:
                # Search in id, name, and description
                if query_lower in phase.id.lower() or query_lower in phase.name.lower():
                    results.append((name, phase))

        return results

    def get_all_phases_by_status(self, status: str) -> list[tuple[str, RoadmapPhase]]:
        """Get all phases with a specific status across all roadmaps.

        Args:
            status: Status to filter by.

        Returns:
            List of (roadmap_name, phase) tuples.
        """
        results: list[tuple[str, RoadmapPhase]] = []

        roadmap_names = ["primary"] + [r.name for r in self.config.additional]

        for name in roadmap_names:
            roadmap = self.get_roadmap(name)
            if roadmap is None:
                continue

            for phase in roadmap.phases:
                if phase.status == status:
                    results.append((name, phase))

        return results

    def get_stats(self) -> dict[str, Any]:
        """Get statistics across all roadmaps.

        Returns:
            Dictionary with statistics.
        """
        stats: dict[str, Any] = {
            "total_roadmaps": 0,
            "total_phases": 0,
            "phases_by_status": {},
            "average_progress": 0.0,
            "roadmaps": {},
        }

        roadmap_names = ["primary"] + [r.name for r in self.config.additional]
        total_progress = 0.0
        phase_count = 0

        for name in roadmap_names:
            roadmap = self.get_roadmap(name)
            if roadmap is None:
                continue

            stats["total_roadmaps"] += 1
            roadmap_stats = {
                "phases": len(roadmap.phases),
                "current_phase": None,
                "progress": 0.0,
            }

            for phase in roadmap.phases:
                stats["total_phases"] += 1
                phase_count += 1
                total_progress += phase.progress

                status = phase.status
                stats["phases_by_status"][status] = (
                    stats["phases_by_status"].get(status, 0) + 1
                )

                if phase.status == "in_progress":
                    roadmap_stats["current_phase"] = phase.id
                    roadmap_stats["progress"] = phase.progress

            stats["roadmaps"][name] = roadmap_stats

        if phase_count > 0:
            stats["average_progress"] = total_progress / phase_count

        return stats
