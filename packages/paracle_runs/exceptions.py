"""Run storage and replay exceptions.

Exception hierarchy for run storage operations with proper error codes.
"""


class RunStorageError(Exception):
    """Base exception for run storage errors.

    Attributes:
        error_code: Unique error code (PARACLE-RUNS-XXX)
        message: Human-readable error message
    """

    error_code: str = "PARACLE-RUNS-000"

    def __init__(self, message: str) -> None:
        self.message = message
        super().__init__(message)


class RunNotFoundError(RunStorageError):
    """Raised when a run is not found in storage.

    Examples:
        - Invalid run ID
        - Run deleted or expired
        - Wrong run type (agent vs workflow)
    """

    error_code = "PARACLE-RUNS-001"

    def __init__(self, run_id: str, run_type: str | None = None) -> None:
        self.run_id = run_id
        self.run_type = run_type
        message = f"Run '{run_id}' not found"
        if run_type:
            message = f"{run_type.capitalize()} run '{run_id}' not found"
        super().__init__(message)


class ReplayError(RunStorageError):
    """Raised when run replay fails.

    Examples:
        - Missing run data
        - Corrupted run files
        - Incompatible agent/workflow version
    """

    error_code = "PARACLE-RUNS-002"

    def __init__(self, run_id: str, reason: str) -> None:
        self.run_id = run_id
        self.reason = reason
        super().__init__(f"Failed to replay run '{run_id}': {reason}")


class RunSaveError(RunStorageError):
    """Raised when saving run data fails.

    Examples:
        - Disk space full
        - Permission denied
        - Invalid run metadata
    """

    error_code = "PARACLE-RUNS-003"

    def __init__(
        self,
        run_id: str,
        reason: str,
        original_error: Exception | None = None,
    ) -> None:
        self.run_id = run_id
        self.reason = reason
        self.original_error = original_error
        super().__init__(f"Failed to save run '{run_id}': {reason}")
        if original_error:
            self.__cause__ = original_error


class RunLoadError(RunStorageError):
    """Raised when loading run data fails.

    Examples:
        - Corrupted YAML/JSON
        - Missing required files
        - Schema version mismatch
    """

    error_code = "PARACLE-RUNS-004"

    def __init__(
        self,
        run_id: str,
        reason: str,
        original_error: Exception | None = None,
    ) -> None:
        self.run_id = run_id
        self.reason = reason
        self.original_error = original_error
        super().__init__(f"Failed to load run '{run_id}': {reason}")
        if original_error:
            self.__cause__ = original_error


class RunQueryError(RunStorageError):
    """Raised when run query/search fails.

    Examples:
        - Invalid query syntax
        - Unsupported filter
        - Database error
    """

    error_code = "PARACLE-RUNS-005"

    def __init__(self, reason: str, query_details: str | None = None) -> None:
        self.reason = reason
        self.query_details = query_details
        message = f"Run query failed: {reason}"
        if query_details:
            message = f"{message} (query: {query_details})"
        super().__init__(message)


class RunCleanupError(RunStorageError):
    """Raised when run cleanup/deletion fails.

    Examples:
        - File deletion failed
        - Run in use (locked)
        - Permission denied
    """

    error_code = "PARACLE-RUNS-006"

    def __init__(
        self,
        reason: str,
        run_id: str | None = None,
        failed_count: int | None = None,
    ) -> None:
        self.reason = reason
        self.run_id = run_id
        self.failed_count = failed_count
        message = f"Cleanup failed: {reason}"
        if run_id:
            message = f"Failed to delete run '{run_id}': {reason}"
        elif failed_count:
            message = f"Failed to delete {failed_count} run(s): {reason}"
        super().__init__(message)


class InvalidRunMetadataError(RunStorageError):
    """Raised when run metadata is invalid.

    Examples:
        - Missing required fields
        - Invalid status value
        - Negative duration/cost
    """

    error_code = "PARACLE-RUNS-007"

    def __init__(self, reason: str, field: str | None = None) -> None:
        self.reason = reason
        self.field = field
        message = f"Invalid run metadata: {reason}"
        if field:
            message = f"Invalid run metadata field '{field}': {reason}"
        super().__init__(message)
