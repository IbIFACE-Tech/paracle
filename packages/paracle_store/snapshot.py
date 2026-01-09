"""State Snapshot and Versioning System.

Provides snapshot-based state management with rollback capabilities:
- Point-in-time snapshots of aggregate state
- Version tracking for optimistic concurrency
- Rollback to previous versions
- Snapshot pruning and retention policies

This is the foundation for transaction-like semantics in Paracle.
"""

from __future__ import annotations

import threading
from abc import ABC, abstractmethod
from datetime import datetime, timezone
from typing import Any, Generic, TypeVar
from uuid import uuid4

from pydantic import BaseModel, ConfigDict, Field


def _utcnow() -> datetime:
    """Return current UTC time."""
    return datetime.now(timezone.utc)


def _generate_snapshot_id() -> str:
    """Generate unique snapshot ID."""
    return f"snap_{uuid4().hex[:12]}"


T = TypeVar("T", bound=BaseModel)


class StateSnapshot(BaseModel):
    """Immutable snapshot of aggregate state at a point in time.

    Stores the complete state of an entity/aggregate for later retrieval
    or rollback purposes.
    """

    model_config = ConfigDict(frozen=True)

    id: str = Field(default_factory=_generate_snapshot_id)
    aggregate_id: str = Field(
        ..., description="ID of the aggregate this snapshot belongs to"
    )
    aggregate_type: str = Field(
        ..., description="Type of the aggregate (e.g., 'Agent', 'Workflow')"
    )
    version: int = Field(..., description="Version number of this snapshot")
    state: dict[str, Any] = Field(..., description="Serialized state data")
    created_at: datetime = Field(default_factory=_utcnow)
    metadata: dict[str, Any] = Field(default_factory=dict)

    # Optional fields for context
    created_by: str | None = Field(
        None, description="ID of who/what created this snapshot"
    )
    reason: str | None = Field(None, description="Reason for creating snapshot")
    parent_snapshot_id: str | None = Field(
        None, description="Previous snapshot ID in chain"
    )

    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary for serialization."""
        return self.model_dump(mode="json")

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> StateSnapshot:
        """Create snapshot from dictionary."""
        return cls(**data)


class SnapshotStore(ABC):
    """Abstract interface for snapshot storage.

    Defines the contract for persisting and retrieving snapshots.
    Implementations may use SQLite, PostgreSQL, or other backends.
    """

    @abstractmethod
    def save(self, snapshot: StateSnapshot) -> None:
        """Save a snapshot."""
        pass

    @abstractmethod
    def get(self, snapshot_id: str) -> StateSnapshot | None:
        """Get snapshot by ID."""
        pass

    @abstractmethod
    def get_latest(self, aggregate_id: str) -> StateSnapshot | None:
        """Get the latest snapshot for an aggregate."""
        pass

    @abstractmethod
    def get_by_version(self, aggregate_id: str, version: int) -> StateSnapshot | None:
        """Get snapshot by aggregate ID and version."""
        pass

    @abstractmethod
    def get_history(
        self,
        aggregate_id: str,
        limit: int | None = None,
    ) -> list[StateSnapshot]:
        """Get snapshot history for an aggregate (newest first)."""
        pass

    @abstractmethod
    def delete(self, snapshot_id: str) -> bool:
        """Delete a snapshot."""
        pass

    @abstractmethod
    def prune(
        self,
        aggregate_id: str,
        keep_versions: int = 10,
    ) -> int:
        """Prune old snapshots, keeping the N most recent versions.

        Returns number of snapshots deleted.
        """
        pass


class InMemorySnapshotStore(SnapshotStore):
    """In-memory implementation of snapshot storage.

    Thread-safe implementation suitable for testing and development.
    """

    def __init__(self) -> None:
        """Initialize the store."""
        self._snapshots: dict[str, StateSnapshot] = {}
        self._by_aggregate: dict[str, list[str]] = {}  # aggregate_id -> [snapshot_ids]
        self._lock = threading.RLock()

    def save(self, snapshot: StateSnapshot) -> None:
        """Save a snapshot."""
        with self._lock:
            self._snapshots[snapshot.id] = snapshot

            # Track by aggregate
            if snapshot.aggregate_id not in self._by_aggregate:
                self._by_aggregate[snapshot.aggregate_id] = []
            self._by_aggregate[snapshot.aggregate_id].append(snapshot.id)

    def get(self, snapshot_id: str) -> StateSnapshot | None:
        """Get snapshot by ID."""
        with self._lock:
            return self._snapshots.get(snapshot_id)

    def get_latest(self, aggregate_id: str) -> StateSnapshot | None:
        """Get the latest snapshot for an aggregate."""
        with self._lock:
            snapshot_ids = self._by_aggregate.get(aggregate_id, [])
            if not snapshot_ids:
                return None

            # Find the one with highest version
            latest = None
            for sid in snapshot_ids:
                snap = self._snapshots.get(sid)
                if snap and (latest is None or snap.version > latest.version):
                    latest = snap
            return latest

    def get_by_version(self, aggregate_id: str, version: int) -> StateSnapshot | None:
        """Get snapshot by aggregate ID and version."""
        with self._lock:
            snapshot_ids = self._by_aggregate.get(aggregate_id, [])
            for sid in snapshot_ids:
                snap = self._snapshots.get(sid)
                if snap and snap.version == version:
                    return snap
            return None

    def get_history(
        self,
        aggregate_id: str,
        limit: int | None = None,
    ) -> list[StateSnapshot]:
        """Get snapshot history for an aggregate (newest first)."""
        with self._lock:
            snapshot_ids = self._by_aggregate.get(aggregate_id, [])
            snapshots = [
                self._snapshots[sid] for sid in snapshot_ids if sid in self._snapshots
            ]
            # Sort by version descending
            snapshots.sort(key=lambda s: s.version, reverse=True)

            if limit:
                snapshots = snapshots[:limit]

            return snapshots

    def delete(self, snapshot_id: str) -> bool:
        """Delete a snapshot."""
        with self._lock:
            if snapshot_id not in self._snapshots:
                return False

            snapshot = self._snapshots.pop(snapshot_id)

            # Remove from aggregate index
            if snapshot.aggregate_id in self._by_aggregate:
                self._by_aggregate[snapshot.aggregate_id] = [
                    sid
                    for sid in self._by_aggregate[snapshot.aggregate_id]
                    if sid != snapshot_id
                ]

            return True

    def prune(
        self,
        aggregate_id: str,
        keep_versions: int = 10,
    ) -> int:
        """Prune old snapshots, keeping the N most recent versions."""
        with self._lock:
            history = self.get_history(aggregate_id)

            if len(history) <= keep_versions:
                return 0

            # Delete old snapshots
            to_delete = history[keep_versions:]
            deleted = 0
            for snap in to_delete:
                if self.delete(snap.id):
                    deleted += 1

            return deleted

    def count(self) -> int:
        """Get total number of snapshots."""
        with self._lock:
            return len(self._snapshots)

    def clear(self) -> int:
        """Clear all snapshots."""
        with self._lock:
            count = len(self._snapshots)
            self._snapshots.clear()
            self._by_aggregate.clear()
            return count


class VersionedEntity(BaseModel):
    """Mixin for entities that support versioning.

    Adds version tracking to any Pydantic model.
    """

    _version: int = 0

    @property
    def version(self) -> int:
        """Get current version."""
        return self._version

    def increment_version(self) -> int:
        """Increment and return new version."""
        self._version += 1
        return self._version


class Snapshottable(Generic[T]):
    """Mixin providing snapshot capabilities for aggregates.

    Enables any repository to support:
    - Creating snapshots on state changes
    - Rolling back to previous versions
    - Version tracking
    """

    def __init__(
        self,
        snapshot_store: SnapshotStore,
        aggregate_type: str,
        serializer: callable[[T], dict[str, Any]] | None = None,
        deserializer: callable[[dict[str, Any]], T] | None = None,
    ) -> None:
        """Initialize snapshotting support.

        Args:
            snapshot_store: Store for persisting snapshots
            aggregate_type: Type name for the aggregate
            serializer: Function to serialize entity to dict
            deserializer: Function to deserialize dict to entity
        """
        self._snapshot_store = snapshot_store
        self._aggregate_type = aggregate_type
        self._serializer = serializer or self._default_serializer
        self._deserializer = deserializer or self._default_deserializer
        self._versions: dict[str, int] = {}  # aggregate_id -> current version

    def _default_serializer(self, entity: T) -> dict[str, Any]:
        """Default serializer using Pydantic."""
        if hasattr(entity, "model_dump"):
            return entity.model_dump(mode="json")
        return dict(entity)

    def _default_deserializer(self, data: dict[str, Any]) -> T:
        """Default deserializer - must be overridden for actual use."""
        raise NotImplementedError(
            "Provide a deserializer function or override _default_deserializer"
        )

    def create_snapshot(
        self,
        entity: T,
        entity_id: str,
        reason: str | None = None,
        created_by: str | None = None,
        metadata: dict[str, Any] | None = None,
    ) -> StateSnapshot:
        """Create a snapshot of the current entity state.

        Args:
            entity: Entity to snapshot
            entity_id: ID of the entity
            reason: Optional reason for creating snapshot
            created_by: Optional creator ID
            metadata: Optional additional metadata

        Returns:
            Created snapshot
        """
        # Get next version
        current_version = self._versions.get(entity_id, 0)
        new_version = current_version + 1
        self._versions[entity_id] = new_version

        # Get parent snapshot
        parent = self._snapshot_store.get_latest(entity_id)
        parent_id = parent.id if parent else None

        # Create snapshot
        snapshot = StateSnapshot(
            aggregate_id=entity_id,
            aggregate_type=self._aggregate_type,
            version=new_version,
            state=self._serializer(entity),
            created_by=created_by,
            reason=reason,
            parent_snapshot_id=parent_id,
            metadata=metadata or {},
        )

        self._snapshot_store.save(snapshot)
        return snapshot

    def get_snapshot(
        self, entity_id: str, version: int | None = None
    ) -> StateSnapshot | None:
        """Get a snapshot for an entity.

        Args:
            entity_id: Entity ID
            version: Specific version to get (latest if None)

        Returns:
            Snapshot if found
        """
        if version is not None:
            return self._snapshot_store.get_by_version(entity_id, version)
        return self._snapshot_store.get_latest(entity_id)

    def restore_from_snapshot(self, snapshot: StateSnapshot) -> T:
        """Restore entity state from a snapshot.

        Args:
            snapshot: Snapshot to restore from

        Returns:
            Restored entity
        """
        return self._deserializer(snapshot.state)

    def rollback(self, entity_id: str, to_version: int) -> T | None:
        """Rollback entity to a previous version.

        Args:
            entity_id: Entity ID
            to_version: Version to rollback to

        Returns:
            Restored entity, or None if version not found
        """
        snapshot = self._snapshot_store.get_by_version(entity_id, to_version)
        if not snapshot:
            return None

        return self.restore_from_snapshot(snapshot)

    def get_version_history(
        self,
        entity_id: str,
        limit: int | None = None,
    ) -> list[StateSnapshot]:
        """Get version history for an entity.

        Args:
            entity_id: Entity ID
            limit: Maximum number of versions to return

        Returns:
            List of snapshots (newest first)
        """
        return self._snapshot_store.get_history(entity_id, limit)

    def get_current_version(self, entity_id: str) -> int:
        """Get current version number for an entity."""
        return self._versions.get(entity_id, 0)

    def prune_history(self, entity_id: str, keep_versions: int = 10) -> int:
        """Prune old snapshots for an entity.

        Args:
            entity_id: Entity ID
            keep_versions: Number of versions to keep

        Returns:
            Number of snapshots deleted
        """
        return self._snapshot_store.prune(entity_id, keep_versions)
