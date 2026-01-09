"""Paracle Rollback - Automatic rollback for failed executions.

This package provides snapshot and restore functionality for sandbox
filesystems, allowing automatic rollback on execution failures.

Components:
- RollbackManager: Manages snapshots and rollback operations
- SnapshotStrategy: Different snapshot strategies
- RollbackPolicy: Rollback trigger policies

Example:
    ```python
    from paracle_rollback import RollbackManager, RollbackPolicy

    # Create rollback manager
    manager = RollbackManager()

    # Create snapshot before execution
    snapshot_id = await manager.create_snapshot(sandbox_id)

    try:
        # Execute agent code
        result = await sandbox.execute(code)
    except Exception:
        # Rollback on failure
        await manager.rollback(snapshot_id)
    ```
"""

from paracle_rollback.config import RollbackConfig, RollbackPolicy
from paracle_rollback.exceptions import RollbackError, SnapshotError
from paracle_rollback.manager import RollbackManager
from paracle_rollback.snapshot import SnapshotStrategy, VolumeSnapshot

__all__ = [
    "RollbackManager",
    "RollbackConfig",
    "RollbackPolicy",
    "SnapshotStrategy",
    "VolumeSnapshot",
    "RollbackError",
    "SnapshotError",
]
