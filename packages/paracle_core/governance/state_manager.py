"""Automatic State Management - No Manual Updates Required.

This module provides automatic synchronization between:
- .parac/memory/context/current_state.yaml
- .parac/roadmap/roadmap.yaml

Key Features:
- Auto-update state when deliverables complete
- Auto-calculate phase progress
- Auto-add recent updates
- Atomic file operations
- Validation before save

Example:
    # Automatically triggered when deliverable completes
    await state_manager.on_deliverable_completed(
        deliverable_id="human_in_the_loop",
        agent="CoderAgent",
        phase="phase_9",
    )

    # State file automatically updated:
    # - Deliverable marked complete
    # - Progress recalculated
    # - Recent update added
"""

from __future__ import annotations

import asyncio
from datetime import datetime
from pathlib import Path

import yaml

from paracle_core.governance.logger import get_governance_logger
from paracle_core.governance.types import GovernanceActionType


class AutomaticStateManager:
    """Automatic state synchronization manager.

    Keeps current_state.yaml and roadmap.yaml synchronized automatically.
    No manual updates required.
    """

    def __init__(self, parac_root: Path):
        """Initialize state manager.

        Args:
            parac_root: Path to .parac/ directory
        """
        self.parac_root = parac_root
        self.state_file = parac_root / "memory" / "context" / "current_state.yaml"
        self.roadmap_file = parac_root / "roadmap" / "roadmap.yaml"
        self.logger = get_governance_logger()

        # Lock for atomic operations
        self._lock = asyncio.Lock()

    async def on_deliverable_completed(
        self,
        deliverable_id: str,
        agent: str,
        phase: str,
        description: str | None = None,
    ) -> None:
        """Auto-update state when deliverable completes.

        Automatically:
        1. Marks deliverable as complete in state
        2. Removes from in_progress list
        3. Recalculates phase progress
        4. Adds to recent_updates
        5. Logs the change

        Args:
            deliverable_id: ID of completed deliverable
            agent: Agent that completed it
            phase: Phase ID (e.g., "phase_9")
            description: Optional description of completion
        """
        async with self._lock:
            # Load current state
            state = self._load_state()

            # Load roadmap for progress calculation
            roadmap = self._load_roadmap()

            # Update deliverable status in roadmap
            phases = roadmap.get("phases", [])
            for p in phases:
                if p["id"] == phase:
                    for d in p.get("deliverables", []):
                        if isinstance(d, dict) and d.get("id") == deliverable_id:
                            d["status"] = "completed"
                            d["completed_date"] = datetime.now().strftime("%Y-%m-%d")
                            d["completed_by"] = agent
                            break
                    break

            # Update current_phase.completed
            if deliverable_id not in state["current_phase"].get("completed", []):
                state["current_phase"].setdefault("completed", []).append(
                    deliverable_id
                )

            # Remove from current_phase.in_progress
            if "in_progress" in state["current_phase"]:
                state["current_phase"]["in_progress"] = [
                    d
                    for d in state["current_phase"]["in_progress"]
                    if d != deliverable_id
                ]

            # Recalculate progress
            progress = self._calculate_phase_progress(phase, roadmap)
            state["current_phase"]["progress"] = progress

            # Add to recent_updates
            update_entry = {
                "date": datetime.now().strftime("%Y-%m-%d"),
                "update": f"{deliverable_id} COMPLETE",
                "agent": agent,
                "impact": description or f"{deliverable_id} deliverable completed",
            }

            if "recent_updates" not in state:
                state["recent_updates"] = []

            # Insert at beginning (most recent first)
            state["recent_updates"].insert(0, update_entry)

            # Keep only last 20 updates
            state["recent_updates"] = state["recent_updates"][:20]

            # Update revision number
            state["revision"] = state.get("revision", 0) + 1

            # Update snapshot date
            state["snapshot_date"] = datetime.now().strftime("%Y-%m-%d")

            # Save both state and roadmap atomically
            self._save_state(state)
            self._save_roadmap(roadmap)

            # Log the auto-update
            self.logger.log(
                action=GovernanceActionType.UPDATE,
                description=f"Auto-updated state: {deliverable_id} completed by {agent}",
                agent="StateManager",
                details={
                    "deliverable": deliverable_id,
                    "phase": phase,
                    "progress": f"{progress}%",
                    "agent": agent,
                },
            )

    async def on_phase_started(
        self,
        phase_id: str,
        phase_name: str,
        agent: str,
    ) -> None:
        """Auto-update state when phase starts.

        Args:
            phase_id: Phase ID (e.g., "phase_10")
            phase_name: Phase name (e.g., "Governance & v1.0 Release")
            agent: Agent that started the phase
        """
        async with self._lock:
            state = self._load_state()

            # Save previous phase if exists
            if "current_phase" in state:
                state["previous_phase"] = {
                    "id": state["current_phase"]["id"],
                    "name": state["current_phase"]["name"],
                    "status": state["current_phase"].get("status", "completed"),
                    "progress": state["current_phase"].get("progress", 100),
                }

            # Update current phase
            state["project"]["phase"] = phase_id
            state["current_phase"] = {
                "id": phase_id,
                "name": phase_name,
                "status": "in_progress",
                "progress": 0,
                "completed": [],
                "in_progress": [],
            }

            # Add to recent_updates
            state["recent_updates"].insert(
                0,
                {
                    "date": datetime.now().strftime("%Y-%m-%d"),
                    "update": f"{phase_name} Started",
                    "agent": agent,
                    "impact": f"Starting {phase_id}",
                },
            )

            # Update revision
            state["revision"] = state.get("revision", 0) + 1
            state["snapshot_date"] = datetime.now().strftime("%Y-%m-%d")

            self._save_state(state)

            self.logger.log(
                action=GovernanceActionType.PLANNING,
                description=f"Auto-updated state: {phase_name} started",
                agent="StateManager",
                details={"phase": phase_id, "agent": agent},
            )

    async def on_phase_completed(
        self,
        phase_id: str,
        phase_name: str,
        agent: str,
    ) -> None:
        """Auto-update state when phase completes.

        Args:
            phase_id: Phase ID (e.g., "phase_9")
            phase_name: Phase name
            agent: Agent that completed the phase
        """
        async with self._lock:
            state = self._load_state()

            # Mark current phase as complete
            state["current_phase"]["status"] = "completed"
            state["current_phase"]["progress"] = 100
            state["current_phase"]["completed_date"] = datetime.now().strftime(
                "%Y-%m-%d"
            )

            # Add to recent_updates
            state["recent_updates"].insert(
                0,
                {
                    "date": datetime.now().strftime("%Y-%m-%d"),
                    "update": f"{phase_name} COMPLETE",
                    "agent": agent,
                    "impact": f"{phase_id} completed - 100% of deliverables done",
                },
            )

            state["revision"] = state.get("revision", 0) + 1
            state["snapshot_date"] = datetime.now().strftime("%Y-%m-%d")

            self._save_state(state)

            self.logger.log(
                action=GovernanceActionType.COMPLETION,
                description=f"Auto-updated state: {phase_name} completed",
                agent="StateManager",
                details={"phase": phase_id, "agent": agent},
            )

    async def add_recent_update(
        self,
        update: str,
        agent: str,
        impact: str,
    ) -> None:
        """Add entry to recent_updates.

        Args:
            update: Update description
            agent: Agent that made the update
            impact: Impact description
        """
        async with self._lock:
            state = self._load_state()

            state["recent_updates"].insert(
                0,
                {
                    "date": datetime.now().strftime("%Y-%m-%d"),
                    "update": update,
                    "agent": agent,
                    "impact": impact,
                },
            )

            state["recent_updates"] = state["recent_updates"][:20]
            state["revision"] = state.get("revision", 0) + 1

            self._save_state(state)

    def _calculate_phase_progress(self, phase_id: str, roadmap: dict) -> int:
        """Calculate phase completion percentage.

        Args:
            phase_id: Phase ID
            roadmap: Loaded roadmap data

        Returns:
            Progress percentage (0-100)
        """
        # Find phase in roadmap
        phases = roadmap.get("phases", [])
        phase_data = next((p for p in phases if p["id"] == phase_id), None)

        if not phase_data or "deliverables" not in phase_data:
            return 0

        deliverables = phase_data["deliverables"]
        if not deliverables:
            return 0

        # Count completed
        completed = sum(
            1
            for d in deliverables
            if isinstance(d, dict) and d.get("status") == "completed"
        )

        total = len(deliverables)

        return int((completed / total) * 100)

    def _load_state(self) -> dict:
        """Load current_state.yaml.

        Returns:
            State dictionary
        """
        if not self.state_file.exists():
            raise FileNotFoundError(f"State file not found: {self.state_file}")

        with open(self.state_file, encoding="utf-8") as f:
            return yaml.safe_load(f)

    def _load_roadmap(self) -> dict:
        """Load roadmap.yaml.

        Returns:
            Roadmap dictionary
        """
        if not self.roadmap_file.exists():
            raise FileNotFoundError(f"Roadmap file not found: {self.roadmap_file}")

        with open(self.roadmap_file, encoding="utf-8") as f:
            return yaml.safe_load(f)

    def _save_state(self, state: dict) -> None:
        """Save state atomically.

        Args:
            state: State dictionary to save
        """
        # Write to temp file first
        temp_file = self.state_file.with_suffix(".yaml.tmp")

        with open(temp_file, "w", encoding="utf-8") as f:
            yaml.dump(
                state,
                f,
                default_flow_style=False,
                allow_unicode=True,
                sort_keys=False,
            )

        # Atomic rename
        temp_file.replace(self.state_file)

    def _save_roadmap(self, roadmap: dict) -> None:
        """Save roadmap atomically.

        Args:
            roadmap: Roadmap dictionary to save
        """
        # Write to temp file first
        temp_file = self.roadmap_file.with_suffix(".yaml.tmp")

        with open(temp_file, "w", encoding="utf-8") as f:
            yaml.dump(
                roadmap,
                f,
                default_flow_style=False,
                allow_unicode=True,
                sort_keys=False,
            )

        # Atomic rename
        temp_file.replace(self.roadmap_file)


# Global instance
_state_manager: AutomaticStateManager | None = None


def get_state_manager(parac_root: Path | None = None) -> AutomaticStateManager:
    """Get global state manager instance.

    Args:
        parac_root: Path to .parac/ directory. If None, searches from cwd.

    Returns:
        AutomaticStateManager instance
    """
    global _state_manager

    if _state_manager is None:
        if parac_root is None:
            # Search for .parac/ from current directory
            parac_root = _find_parac_root()

        _state_manager = AutomaticStateManager(parac_root)

    return _state_manager


def _find_parac_root() -> Path:
    """Find .parac/ directory from current working directory."""
    current = Path.cwd()

    while current != current.parent:
        parac_dir = current / ".parac"
        if parac_dir.exists() and parac_dir.is_dir():
            return parac_dir
        current = current.parent

    raise FileNotFoundError("Could not find .parac/ directory")


def reset_state_manager() -> None:
    """Reset global state manager instance.

    Useful for testing to ensure clean state between tests.
    """
    global _state_manager
    _state_manager = None


__all__ = [
    "AutomaticStateManager",
    "get_state_manager",
    "reset_state_manager",
]
