"""A2A Protocol Exceptions.

Defines error types following the A2A protocol specification.
https://a2a-protocol.org/latest/#error-handling
"""

from typing import Any


class A2AError(Exception):
    """Base exception for A2A protocol errors."""

    code: int = -32000
    message: str = "A2A Error"

    def __init__(
        self,
        message: str | None = None,
        code: int | None = None,
        data: dict[str, Any] | None = None,
    ):
        """Initialize A2A error.

        Args:
            message: Error message (overrides class default)
            code: JSON-RPC error code (overrides class default)
            data: Additional error data
        """
        super().__init__(message or self.message)
        if code is not None:
            self.code = code
        if message is not None:
            self.message = message
        self.data = data or {}

    def to_jsonrpc_error(self) -> dict[str, Any]:
        """Convert to JSON-RPC error object.

        Returns:
            JSON-RPC 2.0 error object
        """
        error: dict[str, Any] = {
            "code": self.code,
            "message": self.message,
        }
        if self.data:
            error["data"] = self.data
        return error


# JSON-RPC 2.0 Standard Errors


class ParseError(A2AError):
    """Invalid JSON was received."""

    code = -32700
    message = "Parse error"


class InvalidRequestError(A2AError):
    """The JSON sent is not a valid Request object."""

    code = -32600
    message = "Invalid Request"


class MethodNotFoundError(A2AError):
    """The method does not exist / is not available."""

    code = -32601
    message = "Method not found"


class InvalidParamsError(A2AError):
    """Invalid method parameter(s)."""

    code = -32602
    message = "Invalid params"


class InternalError(A2AError):
    """Internal JSON-RPC error."""

    code = -32603
    message = "Internal error"


# A2A Protocol Specific Errors


class TaskNotFoundError(A2AError):
    """Task not found in the system."""

    code = -32001
    message = "Task not found"

    def __init__(self, task_id: str):
        """Initialize with task ID.

        Args:
            task_id: The task ID that was not found
        """
        super().__init__(
            message=f"Task not found: {task_id}",
            data={"task_id": task_id},
        )
        self.task_id = task_id


class TaskCancelledError(A2AError):
    """Task has been cancelled."""

    code = -32002
    message = "Task cancelled"

    def __init__(self, task_id: str, reason: str | None = None):
        """Initialize with task ID and optional reason.

        Args:
            task_id: The cancelled task ID
            reason: Optional cancellation reason
        """
        data = {"task_id": task_id}
        if reason:
            data["reason"] = reason
        super().__init__(
            message=f"Task cancelled: {task_id}",
            data=data,
        )
        self.task_id = task_id
        self.reason = reason


class AgentNotFoundError(A2AError):
    """Agent not found or not available."""

    code = -32003
    message = "Agent not found"

    def __init__(self, agent_id: str):
        """Initialize with agent ID.

        Args:
            agent_id: The agent ID that was not found
        """
        super().__init__(
            message=f"Agent not found: {agent_id}",
            data={"agent_id": agent_id},
        )
        self.agent_id = agent_id


class ContentTypeNotSupportedError(A2AError):
    """Content type is not supported by the agent."""

    code = -32004
    message = "Content type not supported"

    def __init__(self, content_type: str, supported_types: list[str] | None = None):
        """Initialize with unsupported content type.

        Args:
            content_type: The unsupported content type
            supported_types: List of supported content types
        """
        data: dict[str, Any] = {"content_type": content_type}
        if supported_types:
            data["supported_types"] = supported_types
        super().__init__(
            message=f"Content type not supported: {content_type}",
            data=data,
        )
        self.content_type = content_type
        self.supported_types = supported_types


class PushNotificationError(A2AError):
    """Error in push notification delivery."""

    code = -32005
    message = "Push notification error"

    def __init__(self, url: str, reason: str | None = None):
        """Initialize with notification URL.

        Args:
            url: The notification URL that failed
            reason: Optional failure reason
        """
        data = {"url": url}
        if reason:
            data["reason"] = reason
        super().__init__(
            message=f"Push notification failed: {url}",
            data=data,
        )
        self.url = url
        self.reason = reason


class AuthenticationError(A2AError):
    """Authentication failed or required."""

    code = -32006
    message = "Authentication required"

    def __init__(
        self,
        message: str = "Authentication required",
        schemes: list[str] | None = None,
    ):
        """Initialize authentication error.

        Args:
            message: Error message
            schemes: Supported authentication schemes
        """
        data = {}
        if schemes:
            data["supported_schemes"] = schemes
        super().__init__(message=message, data=data)
        self.schemes = schemes


class AuthorizationError(A2AError):
    """Authorization failed - insufficient permissions."""

    code = -32007
    message = "Authorization failed"

    def __init__(
        self,
        message: str = "Insufficient permissions",
        required_permissions: list[str] | None = None,
    ):
        """Initialize authorization error.

        Args:
            message: Error message
            required_permissions: List of required permissions
        """
        data = {}
        if required_permissions:
            data["required_permissions"] = required_permissions
        super().__init__(message=message, data=data)
        self.required_permissions = required_permissions


class TaskTimeoutError(A2AError):
    """Task execution timed out."""

    code = -32008
    message = "Task timeout"

    def __init__(self, task_id: str, timeout_seconds: float | None = None):
        """Initialize with task ID.

        Args:
            task_id: The task that timed out
            timeout_seconds: The timeout value in seconds
        """
        data = {"task_id": task_id}
        if timeout_seconds is not None:
            data["timeout_seconds"] = timeout_seconds
        super().__init__(
            message=f"Task timed out: {task_id}",
            data=data,
        )
        self.task_id = task_id
        self.timeout_seconds = timeout_seconds


class RateLimitError(A2AError):
    """Rate limit exceeded."""

    code = -32009
    message = "Rate limit exceeded"

    def __init__(
        self,
        message: str = "Rate limit exceeded",
        retry_after: float | None = None,
    ):
        """Initialize rate limit error.

        Args:
            message: Error message
            retry_after: Seconds to wait before retry
        """
        data = {}
        if retry_after is not None:
            data["retry_after"] = retry_after
        super().__init__(message=message, data=data)
        self.retry_after = retry_after


class StreamingError(A2AError):
    """Error in SSE streaming."""

    code = -32010
    message = "Streaming error"

    def __init__(self, task_id: str, reason: str | None = None):
        """Initialize streaming error.

        Args:
            task_id: The task being streamed
            reason: Error reason
        """
        data = {"task_id": task_id}
        if reason:
            data["reason"] = reason
        super().__init__(
            message=f"Streaming error for task: {task_id}",
            data=data,
        )
        self.task_id = task_id
        self.reason = reason
