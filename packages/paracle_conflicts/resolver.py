"""Conflict resolution strategies and resolver.

Provides different strategies for resolving conflicts when
multiple agents modify the same files.
"""

import shutil
from datetime import datetime
from enum import Enum
from pathlib import Path

from pydantic import BaseModel

from paracle_conflicts.detector import FileConflict


class ResolutionStrategy(str, Enum):
    """Conflict resolution strategies."""

    MANUAL = "manual"  # Require human intervention
    FIRST_WINS = "first_wins"  # Keep first agent's changes
    LAST_WINS = "last_wins"  # Keep last agent's changes
    MERGE = "merge"  # Attempt automatic merge
    BACKUP_BOTH = "backup_both"  # Save both versions


class ResolutionResult(BaseModel):
    """Result of conflict resolution.

    Attributes:
        conflict: The resolved conflict
        strategy: Strategy used
        success: Whether resolution succeeded
        message: Description of resolution
        backup_paths: Optional backup file paths
    """

    conflict: FileConflict
    strategy: ResolutionStrategy
    success: bool
    message: str
    backup_paths: list[str] = []


class ConflictResolver:
    """Resolves conflicts between agent modifications.

    Provides different strategies for handling conflicts
    when multiple agents modify the same files.
    """

    def __init__(self, backup_dir: Path | None = None):
        """Initialize conflict resolver.

        Args:
            backup_dir: Directory for backup files
        """
        if backup_dir is None:
            backup_dir = Path(".parac") / "memory" / "data" / "backups"

        self.backup_dir = Path(backup_dir)
        self.backup_dir.mkdir(parents=True, exist_ok=True)

    def _create_backup(
        self,
        file_path: str,
        agent_id: str,
    ) -> str:
        """Create backup of file.

        Args:
            file_path: Path to file
            agent_id: Agent that modified file

        Returns:
            Path to backup file
        """
        source = Path(file_path)
        if not source.exists():
            return ""

        # Create backup filename
        timestamp = datetime.utcnow().strftime("%Y%m%d_%H%M%S")
        backup_name = f"{source.stem}_{agent_id}_{timestamp}{source.suffix}"
        backup_path = self.backup_dir / backup_name

        # Copy file
        shutil.copy2(source, backup_path)
        return str(backup_path)

    def resolve(
        self,
        conflict: FileConflict,
        strategy: ResolutionStrategy,
    ) -> ResolutionResult:
        """Resolve a conflict using specified strategy.

        Args:
            conflict: Conflict to resolve
            strategy: Resolution strategy to use

        Returns:
            ResolutionResult with outcome
        """
        if strategy == ResolutionStrategy.MANUAL:
            return self._resolve_manual(conflict)
        elif strategy == ResolutionStrategy.FIRST_WINS:
            return self._resolve_first_wins(conflict)
        elif strategy == ResolutionStrategy.LAST_WINS:
            return self._resolve_last_wins(conflict)
        elif strategy == ResolutionStrategy.MERGE:
            return self._resolve_merge(conflict)
        elif strategy == ResolutionStrategy.BACKUP_BOTH:
            return self._resolve_backup_both(conflict)
        else:
            return ResolutionResult(
                conflict=conflict,
                strategy=strategy,
                success=False,
                message=f"Unknown strategy: {strategy}",
            )

    def _resolve_manual(self, conflict: FileConflict) -> ResolutionResult:
        """Resolve conflict manually (require human intervention).

        Args:
            conflict: Conflict to resolve

        Returns:
            ResolutionResult
        """
        # Create backups of both versions
        backup1 = self._create_backup(conflict.file_path, conflict.agent1_id)
        backup2 = self._create_backup(conflict.file_path, conflict.agent2_id)

        return ResolutionResult(
            conflict=conflict,
            strategy=ResolutionStrategy.MANUAL,
            success=True,
            message="Conflict requires manual resolution. Backups created.",
            backup_paths=[backup1, backup2],
        )

    def _resolve_first_wins(self, conflict: FileConflict) -> ResolutionResult:
        """Resolve conflict by keeping first agent's changes.

        Args:
            conflict: Conflict to resolve

        Returns:
            ResolutionResult
        """
        # Backup second agent's changes
        backup = self._create_backup(conflict.file_path, conflict.agent2_id)

        return ResolutionResult(
            conflict=conflict,
            strategy=ResolutionStrategy.FIRST_WINS,
            success=True,
            message=f"Kept {conflict.agent1_id}'s changes, backed up {conflict.agent2_id}'s",
            backup_paths=[backup] if backup else [],
        )

    def _resolve_last_wins(self, conflict: FileConflict) -> ResolutionResult:
        """Resolve conflict by keeping last agent's changes.

        Args:
            conflict: Conflict to resolve

        Returns:
            ResolutionResult
        """
        # Backup first agent's changes
        backup = self._create_backup(conflict.file_path, conflict.agent1_id)

        return ResolutionResult(
            conflict=conflict,
            strategy=ResolutionStrategy.LAST_WINS,
            success=True,
            message=f"Kept {conflict.agent2_id}'s changes, backed up {conflict.agent1_id}'s",
            backup_paths=[backup] if backup else [],
        )

    def _resolve_merge(self, conflict: FileConflict) -> ResolutionResult:
        """Attempt automatic merge of changes.

        Args:
            conflict: Conflict to resolve

        Returns:
            ResolutionResult
        """
        # For now, this falls back to manual
        # In a full implementation, this would use git merge or similar
        return ResolutionResult(
            conflict=conflict,
            strategy=ResolutionStrategy.MERGE,
            success=False,
            message="Automatic merge not yet implemented, requires manual resolution",
        )

    def _resolve_backup_both(self, conflict: FileConflict) -> ResolutionResult:
        """Save both versions as backups.

        Args:
            conflict: Conflict to resolve

        Returns:
            ResolutionResult
        """
        backup1 = self._create_backup(conflict.file_path, conflict.agent1_id)
        backup2 = self._create_backup(conflict.file_path, conflict.agent2_id)

        return ResolutionResult(
            conflict=conflict,
            strategy=ResolutionStrategy.BACKUP_BOTH,
            success=True,
            message="Both versions saved as backups",
            backup_paths=[backup1, backup2],
        )

    def list_backups(self) -> list[Path]:
        """List all backup files.

        Returns:
            List of backup file paths
        """
        return sorted(
            self.backup_dir.glob("*"), key=lambda p: p.stat().st_mtime, reverse=True
        )

    def cleanup_backups(self, older_than_days: int = 30) -> int:
        """Clean up old backup files.

        Args:
            older_than_days: Delete backups older than this

        Returns:
            Number of backups deleted
        """
        import time

        cutoff_time = time.time() - (older_than_days * 86400)
        deleted = 0

        for backup in self.backup_dir.glob("*"):
            if backup.stat().st_mtime < cutoff_time:
                backup.unlink()
                deleted += 1

        return deleted
