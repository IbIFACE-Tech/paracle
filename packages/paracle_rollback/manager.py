"""Rollback manager for automatic state restoration."""

import logging
from datetime import datetime
from pathlib import Path

from paracle_rollback.config import RollbackConfig
from paracle_rollback.exceptions import RollbackError, SnapshotNotFoundError
from paracle_rollback.snapshot import TarballSnapshotStrategy, VolumeSnapshot

logger = logging.getLogger(__name__)


class RollbackManager:
    """Manages snapshots and rollback operations.

    Coordinates snapshot creation, automatic rollback on failures,
    and snapshot lifecycle management.

    Attributes:
        config: Rollback configuration
        snapshots: Active snapshots by ID
    """

    def __init__(
        self,
        config: RollbackConfig | None = None,
        storage_dir: Path | None = None,
    ):
        """Initialize rollback manager.

        Args:
            config: Rollback configuration
            storage_dir: Snapshot storage directory
        """
        self.config = config or RollbackConfig()
        self.snapshots: dict[str, VolumeSnapshot] = {}
        self._strategy = TarballSnapshotStrategy(storage_dir)
        # sandbox_id -> snapshot_ids
        self._sandbox_snapshots: dict[str, list[str]] = {}

    async def create_snapshot(
        self,
        container_id: str,
        path: str = "/workspace",
        metadata: dict[str, str] | None = None,
    ) -> str:
        """Create filesystem snapshot.

        Args:
            container_id: Container to snapshot
            path: Path to snapshot
            metadata: Additional metadata

        Returns:
            Snapshot ID

        Raises:
            RollbackError: If snapshot creation fails
        """
        try:
            # Create snapshot
            snapshot = await self._strategy.create_snapshot(container_id, path)

            # Add custom metadata
            if metadata:
                snapshot.metadata.update(metadata)

            # Track snapshot
            self.snapshots[snapshot.snapshot_id] = snapshot

            # Track by sandbox
            if container_id not in self._sandbox_snapshots:
                self._sandbox_snapshots[container_id] = []
            self._sandbox_snapshots[container_id].append(snapshot.snapshot_id)

            # Enforce max snapshots limit
            await self._enforce_snapshot_limit(container_id)

            logger.info(f"Created snapshot {snapshot.snapshot_id} for {container_id}")

            return snapshot.snapshot_id

        except Exception as e:
            raise RollbackError(f"Failed to create snapshot: {e}") from e

    async def rollback(
        self,
        snapshot_id: str,
        container_id: str | None = None,
        path: str = "/workspace",
    ) -> None:
        """Rollback to snapshot.

        Args:
            snapshot_id: Snapshot to restore
            container_id: Target container (uses snapshot source if None)
            path: Path to restore to

        Raises:
            SnapshotNotFoundError: If snapshot not found
            RollbackError: If rollback fails
        """
        snapshot = self.snapshots.get(snapshot_id)
        if not snapshot:
            raise SnapshotNotFoundError(
                f"Snapshot not found: {snapshot_id}",
                snapshot_id,
            )

        target_container = container_id or snapshot.sandbox_id

        try:
            logger.info(f"Rolling back {target_container} to snapshot {snapshot_id}")

            # Create backup before rollback if configured
            if self.config.backup_before_rollback:
                backup_id = await self.create_snapshot(
                    target_container,
                    path,
                    metadata={"type": "pre_rollback_backup"},
                )
                logger.info(f"Created backup snapshot {backup_id}")

            # Restore snapshot
            await self._strategy.restore_snapshot(snapshot, target_container, path)

            logger.info(f"Rollback to {snapshot_id} completed successfully")

        except Exception as e:
            raise RollbackError(
                f"Rollback failed: {e}",
                snapshot_id,
            ) from e

    async def auto_rollback_on_error(
        self,
        container_id: str,
        error: Exception,
    ) -> bool:
        """Automatically rollback on error if policy allows.

        Args:
            container_id: Container that failed
            error: Exception that occurred

        Returns:
            True if rollback was performed, False otherwise
        """
        if not self.config.policy.enabled:
            return False

        # Check if error type triggers rollback
        trigger = self._get_trigger_for_error(error)
        if trigger not in self.config.policy.triggers:
            logger.debug(f"Error type {trigger} not in rollback triggers")
            return False

        # Get latest snapshot for sandbox
        snapshot_ids = self._sandbox_snapshots.get(container_id, [])
        if not snapshot_ids:
            logger.warning(f"No snapshots available for {container_id}")
            return False

        latest_snapshot_id = snapshot_ids[-1]

        try:
            await self.rollback(latest_snapshot_id, container_id)
            logger.info(f"Auto-rollback successful for {container_id} due to {trigger}")
            return True

        except Exception as e:
            logger.error(f"Auto-rollback failed: {e}")
            return False

    def _get_trigger_for_error(self, error: Exception) -> str:
        """Determine rollback trigger from error type.

        Args:
            error: Exception that occurred

        Returns:
            Trigger name
        """
        error_type = type(error).__name__

        if "Timeout" in error_type:
            return "on_timeout"
        elif "Limit" in error_type or "Resource" in error_type:
            return "on_limit_exceeded"
        else:
            return "on_error"

    async def _enforce_snapshot_limit(self, container_id: str) -> None:
        """Enforce maximum snapshots per sandbox.

        Args:
            container_id: Container ID
        """
        snapshot_ids = self._sandbox_snapshots.get(container_id, [])

        if len(snapshot_ids) > self.config.policy.max_snapshots:
            # Remove oldest snapshots
            to_remove = len(snapshot_ids) - self.config.policy.max_snapshots

            for i in range(to_remove):
                old_snapshot_id = snapshot_ids[i]
                await self.delete_snapshot(old_snapshot_id)

            # Update tracking
            self._sandbox_snapshots[container_id] = snapshot_ids[to_remove:]

    async def delete_snapshot(self, snapshot_id: str) -> None:
        """Delete snapshot.

        Args:
            snapshot_id: Snapshot to delete

        Raises:
            SnapshotNotFoundError: If snapshot not found
        """
        snapshot = self.snapshots.get(snapshot_id)
        if not snapshot:
            raise SnapshotNotFoundError(
                f"Snapshot not found: {snapshot_id}",
                snapshot_id,
            )

        # Delete from storage
        await self._strategy.delete_snapshot(snapshot)

        # Remove from tracking
        self.snapshots.pop(snapshot_id, None)

        # Remove from sandbox tracking
        for _sandbox_id, ids in self._sandbox_snapshots.items():
            if snapshot_id in ids:
                ids.remove(snapshot_id)

        logger.info(f"Deleted snapshot {snapshot_id}")

    async def cleanup_old_snapshots(self) -> int:
        """Clean up snapshots older than retention period.

        Returns:
            Number of snapshots deleted
        """
        retention_hours = self.config.policy.snapshot_retention_hours
        cutoff = datetime.utcnow().timestamp() - (retention_hours * 3600)
        deleted = 0

        for snapshot_id, snapshot in list(self.snapshots.items()):
            if snapshot.timestamp.timestamp() < cutoff:
                try:
                    await self.delete_snapshot(snapshot_id)
                    deleted += 1
                except Exception as e:
                    logger.error(f"Failed to delete snapshot {snapshot_id}: {e}")

        logger.info(f"Cleaned up {deleted} old snapshots")
        return deleted

    def get_snapshot_info(self, snapshot_id: str) -> dict:
        """Get snapshot information.

        Args:
            snapshot_id: Snapshot ID

        Returns:
            Dict with snapshot details

        Raises:
            SnapshotNotFoundError: If snapshot not found
        """
        snapshot = self.snapshots.get(snapshot_id)
        if not snapshot:
            raise SnapshotNotFoundError(
                f"Snapshot not found: {snapshot_id}",
                snapshot_id,
            )

        return {
            "snapshot_id": snapshot.snapshot_id,
            "sandbox_id": snapshot.sandbox_id,
            "timestamp": snapshot.timestamp.isoformat(),
            "size_mb": snapshot.size_bytes / (1024 * 1024),
            "compressed": snapshot.compressed,
            "metadata": snapshot.metadata,
        }

    def list_snapshots(
        self,
        container_id: str | None = None,
    ) -> list[dict]:
        """List snapshots.

        Args:
            container_id: Filter by container ID (all if None)

        Returns:
            List of snapshot info dicts
        """
        snapshots = self.snapshots.values()

        if container_id:
            snapshots = [s for s in snapshots if s.sandbox_id == container_id]

        return [self.get_snapshot_info(s.snapshot_id) for s in snapshots]

    def close(self) -> None:
        """Close and cleanup resources."""
        self._strategy.close()
