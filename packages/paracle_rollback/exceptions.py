"""Rollback exception types."""


class RollbackError(Exception):
    """Base exception for rollback-related errors."""

    def __init__(self, message: str, snapshot_id: str | None = None):
        """Initialize rollback error.

        Args:
            message: Error message
            snapshot_id: Optional snapshot identifier
        """
        super().__init__(message)
        self.snapshot_id = snapshot_id


class SnapshotError(RollbackError):
    """Raised when snapshot operation fails."""

    pass


class RestoreError(RollbackError):
    """Raised when restore operation fails."""

    def __init__(
        self,
        message: str,
        snapshot_id: str | None = None,
        partial_restore: bool = False,
    ):
        """Initialize restore error.

        Args:
            message: Error message
            snapshot_id: Snapshot identifier
            partial_restore: Whether restore was partially successful
        """
        super().__init__(message, snapshot_id)
        self.partial_restore = partial_restore


class SnapshotNotFoundError(RollbackError):
    """Raised when snapshot is not found."""

    pass
