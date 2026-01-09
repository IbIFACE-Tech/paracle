"""Sandbox exception types."""


class SandboxError(Exception):
    """Base exception for sandbox-related errors."""

    def __init__(self, message: str, sandbox_id: str | None = None):
        """Initialize sandbox error.

        Args:
            message: Error message
            sandbox_id: Optional sandbox identifier
        """
        super().__init__(message)
        self.sandbox_id = sandbox_id


class SandboxCreationError(SandboxError):
    """Raised when sandbox creation fails."""

    pass


class SandboxExecutionError(SandboxError):
    """Raised when code execution in sandbox fails."""

    def __init__(
        self,
        message: str,
        sandbox_id: str | None = None,
        exit_code: int | None = None,
        stderr: str | None = None,
    ):
        """Initialize execution error.

        Args:
            message: Error message
            sandbox_id: Sandbox identifier
            exit_code: Process exit code
            stderr: Standard error output
        """
        super().__init__(message, sandbox_id)
        self.exit_code = exit_code
        self.stderr = stderr


class ResourceLimitError(SandboxError):
    """Raised when resource limits are exceeded."""

    def __init__(
        self,
        message: str,
        sandbox_id: str | None = None,
        resource_type: str | None = None,
        limit: float | None = None,
        usage: float | None = None,
    ):
        """Initialize resource limit error.

        Args:
            message: Error message
            sandbox_id: Sandbox identifier
            resource_type: Type of resource (cpu, memory, disk, time)
            limit: Resource limit
            usage: Actual usage
        """
        super().__init__(message, sandbox_id)
        self.resource_type = resource_type
        self.limit = limit
        self.usage = usage


class SandboxTimeoutError(SandboxError):
    """Raised when sandbox execution times out."""

    def __init__(
        self,
        message: str,
        sandbox_id: str | None = None,
        timeout_seconds: int | None = None,
    ):
        """Initialize timeout error.

        Args:
            message: Error message
            sandbox_id: Sandbox identifier
            timeout_seconds: Timeout duration
        """
        super().__init__(message, sandbox_id)
        self.timeout_seconds = timeout_seconds


class SandboxCleanupError(SandboxError):
    """Raised when sandbox cleanup fails."""

    pass


class DockerConnectionError(SandboxError):
    """Raised when Docker connection fails."""

    pass
