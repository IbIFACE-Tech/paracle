"""Isolation exception types."""


class IsolationError(Exception):
    """Base exception for isolation-related errors."""

    def __init__(self, message: str, resource_id: str | None = None):
        """Initialize isolation error.

        Args:
            message: Error message
            resource_id: Optional resource identifier
        """
        super().__init__(message)
        self.resource_id = resource_id


class NetworkIsolationError(IsolationError):
    """Raised when network isolation setup fails."""

    pass


class NetworkPolicyViolation(IsolationError):
    """Raised when network policy is violated."""

    def __init__(
        self,
        message: str,
        resource_id: str | None = None,
        violated_rule: str | None = None,
    ):
        """Initialize policy violation error.

        Args:
            message: Error message
            resource_id: Resource identifier
            violated_rule: The policy rule that was violated
        """
        super().__init__(message, resource_id)
        self.violated_rule = violated_rule
