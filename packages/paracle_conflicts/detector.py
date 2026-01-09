"""Conflict detection for concurrent file modifications.

Detects conflicts when multiple agents modify the same files
at the same time or in sequence.
"""

import hashlib
from datetime import datetime
from pathlib import Path

from pydantic import BaseModel


class FileConflict(BaseModel):
    """Represents a conflict between agent modifications.

    Attributes:
        file_path: Path to conflicting file
        agent1_id: First agent involved
        agent2_id: Second agent involved
        agent1_hash: Hash of file after agent1's changes
        agent2_hash: Hash of file after agent2's changes
        detected_at: When conflict was detected
        resolved: Whether conflict has been resolved
    """

    file_path: str
    agent1_id: str
    agent2_id: str
    agent1_hash: str
    agent2_hash: str
    detected_at: datetime
    resolved: bool = False


class ConflictDetector:
    """Detects conflicts in concurrent agent executions.

    Tracks file modifications by multiple agents and identifies
    conflicts when the same file is modified concurrently.
    """

    def __init__(self):
        """Initialize conflict detector."""
        self.modifications: dict[str, list[tuple[str, str]]] = (
            {}
        )  # file -> [(agent_id, hash)]
        self.conflicts: list[FileConflict] = []

    def _hash_file(self, file_path: Path) -> str:
        """Calculate hash of file contents.

        Args:
            file_path: Path to file

        Returns:
            SHA256 hash of file
        """
        try:
            with open(file_path, "rb") as f:
                return hashlib.sha256(f.read()).hexdigest()
        except Exception:
            return ""

    def record_modification(
        self,
        file_path: str,
        agent_id: str,
    ) -> FileConflict | None:
        """Record a file modification by an agent.

        Args:
            file_path: Path to modified file
            agent_id: ID of agent making modification

        Returns:
            FileConflict if conflict detected, None otherwise
        """
        # Calculate file hash
        path = Path(file_path)
        if not path.exists():
            return None

        file_hash = self._hash_file(path)

        # Check if file was modified by another agent
        if file_path in self.modifications:
            existing_mods = self.modifications[file_path]

            # Check for conflict
            for existing_agent, existing_hash in existing_mods:
                if existing_agent != agent_id and existing_hash != file_hash:
                    # Conflict detected
                    conflict = FileConflict(
                        file_path=file_path,
                        agent1_id=existing_agent,
                        agent2_id=agent_id,
                        agent1_hash=existing_hash,
                        agent2_hash=file_hash,
                        detected_at=datetime.utcnow(),
                    )
                    self.conflicts.append(conflict)
                    return conflict

        # Record modification
        if file_path not in self.modifications:
            self.modifications[file_path] = []

        self.modifications[file_path].append((agent_id, file_hash))
        return None

    def get_conflicts(self, resolved: bool | None = None) -> list[FileConflict]:
        """Get detected conflicts.

        Args:
            resolved: Filter by resolution status (None = all)

        Returns:
            List of conflicts
        """
        if resolved is None:
            return self.conflicts

        return [c for c in self.conflicts if c.resolved == resolved]

    def mark_resolved(self, conflict: FileConflict) -> None:
        """Mark a conflict as resolved.

        Args:
            conflict: Conflict to mark resolved
        """
        for c in self.conflicts:
            if (
                c.file_path == conflict.file_path
                and c.agent1_id == conflict.agent1_id
                and c.agent2_id == conflict.agent2_id
            ):
                c.resolved = True

    def clear_modifications(self, file_path: str | None = None) -> None:
        """Clear tracked modifications.

        Args:
            file_path: Specific file to clear, or None for all
        """
        if file_path:
            self.modifications.pop(file_path, None)
        else:
            self.modifications.clear()

    def get_agents_modifying(self, file_path: str) -> list[str]:
        """Get list of agents that modified a file.

        Args:
            file_path: Path to file

        Returns:
            List of agent IDs
        """
        if file_path not in self.modifications:
            return []

        return [agent_id for agent_id, _ in self.modifications[file_path]]
