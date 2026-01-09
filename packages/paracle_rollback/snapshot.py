"""Snapshot strategies for filesystem state capture."""

import logging
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from typing import Protocol

from paracle_core.ids import generate_ulid

import docker
from docker.errors import APIError
from paracle_rollback.exceptions import RestoreError, SnapshotError

logger = logging.getLogger(__name__)


@dataclass
class VolumeSnapshot:
    """Represents a filesystem snapshot.

    Attributes:
        snapshot_id: Unique snapshot identifier
        sandbox_id: Source sandbox ID
        timestamp: When snapshot was created
        size_bytes: Snapshot size in bytes
        compressed: Whether snapshot is compressed
        metadata: Additional snapshot metadata
        storage_path: Path to snapshot data
    """

    snapshot_id: str
    sandbox_id: str
    timestamp: datetime
    size_bytes: int
    compressed: bool
    metadata: dict[str, str]
    storage_path: Path


class SnapshotStrategy(Protocol):
    """Protocol for snapshot strategies."""

    async def create_snapshot(
        self,
        container_id: str,
        path: str,
    ) -> VolumeSnapshot:
        """Create filesystem snapshot.

        Args:
            container_id: Container to snapshot
            path: Path to snapshot within container

        Returns:
            VolumeSnapshot metadata
        """
        ...

    async def restore_snapshot(
        self,
        snapshot: VolumeSnapshot,
        container_id: str,
        path: str,
    ) -> None:
        """Restore snapshot to container.

        Args:
            snapshot: Snapshot to restore
            container_id: Target container
            path: Path to restore to
        """
        ...

    async def delete_snapshot(self, snapshot: VolumeSnapshot) -> None:
        """Delete snapshot.

        Args:
            snapshot: Snapshot to delete
        """
        ...


class TarballSnapshotStrategy:
    """Snapshot strategy using tarball archives.

    Creates compressed tarballs of container filesystems for
    efficient storage and restore.
    """

    def __init__(self, storage_dir: Path | None = None):
        """Initialize tarball snapshot strategy.

        Args:
            storage_dir: Directory to store snapshots (default: ./snapshots)
        """
        self.storage_dir = storage_dir or Path("./snapshots")
        self.storage_dir.mkdir(parents=True, exist_ok=True)
        self._client: docker.DockerClient | None = None

    def _get_client(self) -> docker.DockerClient:
        """Get or create Docker client."""
        if not self._client:
            self._client = docker.from_env()
        return self._client

    async def create_snapshot(
        self,
        container_id: str,
        path: str = "/workspace",
    ) -> VolumeSnapshot:
        """Create tarball snapshot of container path.

        Args:
            container_id: Container to snapshot
            path: Path to snapshot

        Returns:
            VolumeSnapshot metadata

        Raises:
            SnapshotError: If snapshot creation fails
        """
        try:
            client = self._get_client()
            container = client.containers.get(container_id)

            # Generate snapshot ID
            snapshot_id = generate_ulid()
            timestamp = datetime.utcnow()

            # Create snapshot filename
            filename = f"snapshot-{snapshot_id}.tar.gz"
            storage_path = self.storage_dir / filename

            # Get archive from container
            logger.info(f"Creating snapshot {snapshot_id} from {container_id}:{path}")

            bits, stat = container.get_archive(path)

            # Write to compressed tarball
            with open(storage_path, "wb") as f:
                for chunk in bits:
                    f.write(chunk)

            size_bytes = storage_path.stat().st_size

            logger.info(
                f"Snapshot {snapshot_id} created: {size_bytes / 1024 / 1024:.2f} MB"
            )

            return VolumeSnapshot(
                snapshot_id=snapshot_id,
                sandbox_id=container_id,
                timestamp=timestamp,
                size_bytes=size_bytes,
                compressed=True,
                metadata={
                    "source_path": path,
                    "container_id": container_id,
                },
                storage_path=storage_path,
            )

        except APIError as e:
            raise SnapshotError(
                f"Failed to create snapshot: {e}",
                snapshot_id=snapshot_id,
            ) from e
        except Exception as e:
            raise SnapshotError(
                f"Snapshot creation failed: {e}",
                snapshot_id=snapshot_id,
            ) from e

    async def restore_snapshot(
        self,
        snapshot: VolumeSnapshot,
        container_id: str,
        path: str = "/workspace",
    ) -> None:
        """Restore tarball snapshot to container.

        Args:
            snapshot: Snapshot to restore
            container_id: Target container
            path: Path to restore to

        Raises:
            RestoreError: If restore fails
        """
        try:
            client = self._get_client()
            container = client.containers.get(container_id)

            if not snapshot.storage_path.exists():
                raise RestoreError(
                    f"Snapshot file not found: {snapshot.storage_path}",
                    snapshot.snapshot_id,
                )

            logger.info(
                f"Restoring snapshot {snapshot.snapshot_id} to {container_id}:{path}"
            )

            # Read snapshot tarball
            with open(snapshot.storage_path, "rb") as f:
                data = f.read()

            # Put archive into container
            container.put_archive(path, data)

            logger.info(f"Snapshot {snapshot.snapshot_id} restored successfully")

        except APIError as e:
            raise RestoreError(
                f"Failed to restore snapshot: {e}",
                snapshot.snapshot_id,
            ) from e
        except Exception as e:
            raise RestoreError(
                f"Restore failed: {e}",
                snapshot.snapshot_id,
            ) from e

    async def delete_snapshot(self, snapshot: VolumeSnapshot) -> None:
        """Delete snapshot tarball.

        Args:
            snapshot: Snapshot to delete
        """
        try:
            if snapshot.storage_path.exists():
                snapshot.storage_path.unlink()
                logger.info(f"Deleted snapshot {snapshot.snapshot_id}")
            else:
                logger.warning(f"Snapshot file not found: {snapshot.storage_path}")

        except Exception as e:
            logger.error(f"Failed to delete snapshot {snapshot.snapshot_id}: {e}")

    def get_total_size(self) -> int:
        """Get total size of all snapshots.

        Returns:
            Total size in bytes
        """
        total = 0
        for file in self.storage_dir.glob("snapshot-*.tar.gz"):
            total += file.stat().st_size
        return total

    def cleanup_old_snapshots(self, max_age_hours: int) -> int:
        """Clean up snapshots older than specified age.

        Args:
            max_age_hours: Maximum age in hours

        Returns:
            Number of snapshots deleted
        """
        cutoff = datetime.utcnow().timestamp() - (max_age_hours * 3600)
        deleted = 0

        for file in self.storage_dir.glob("snapshot-*.tar.gz"):
            if file.stat().st_mtime < cutoff:
                try:
                    file.unlink()
                    deleted += 1
                    logger.info(f"Deleted old snapshot: {file.name}")
                except Exception as e:
                    logger.error(f"Failed to delete {file.name}: {e}")

        return deleted

    def close(self) -> None:
        """Close Docker client."""
        if self._client:
            self._client.close()
            self._client = None
