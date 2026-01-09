"""Tool execution exceptions.

Exception hierarchy for tool-related errors with proper chaining.
"""


class ToolError(Exception):
    """Base exception for tool errors.

    Attributes:
        error_code: Unique error code (PARACLE-TOOL-XXX)
        message: Human-readable error message
    """

    error_code: str = "PARACLE-TOOL-000"

    def __init__(self, message: str) -> None:
        self.message = message
        super().__init__(message)


class ToolExecutionError(ToolError):
    """Raised when tool execution fails.

    Examples:
        - Command execution failed
        - Tool crashed
        - Unexpected output
    """

    error_code = "PARACLE-TOOL-001"

    def __init__(
        self,
        tool_name: str,
        reason: str,
        original_error: Exception | None = None,
    ) -> None:
        self.tool_name = tool_name
        self.reason = reason
        self.original_error = original_error
        super().__init__(f"Tool '{tool_name}' execution failed: {reason}")
        if original_error:
            self.__cause__ = original_error


class ToolValidationError(ToolError):
    """Raised when tool validation fails.

    Examples:
        - Invalid tool spec
        - Missing required parameters
        - Parameter type mismatch
    """

    error_code = "PARACLE-TOOL-002"

    def __init__(
        self,
        tool_name: str,
        reason: str,
        field: str | None = None,
    ) -> None:
        self.tool_name = tool_name
        self.reason = reason
        self.field = field
        message = f"Tool '{tool_name}' validation failed: {reason}"
        if field:
            message = f"Tool '{tool_name}' field '{field}': {reason}"
        super().__init__(message)


class ToolNotFoundError(ToolError):
    """Raised when a tool is not found.

    Examples:
        - Tool not registered
        - Tool module not installed
        - Tool file missing
    """

    error_code = "PARACLE-TOOL-003"

    def __init__(self, tool_name: str) -> None:
        self.tool_name = tool_name
        super().__init__(f"Tool '{tool_name}' not found")


class ToolTimeoutError(ToolError):
    """Raised when tool execution times out.

    Examples:
        - Command takes too long
        - Network request timeout
        - Infinite loop detection
    """

    error_code = "PARACLE-TOOL-004"

    def __init__(self, tool_name: str, timeout_seconds: float) -> None:
        self.tool_name = tool_name
        self.timeout_seconds = timeout_seconds
        super().__init__(
            f"Tool '{tool_name}' execution timed out after {timeout_seconds}s"
        )


class ToolPermissionError(ToolError):
    """Raised when tool lacks required permissions.

    Examples:
        - Filesystem permission denied
        - Sandbox policy violation
        - Resource access denied
    """

    error_code = "PARACLE-TOOL-005"

    def __init__(
        self,
        tool_name: str,
        resource: str,
        required_permission: str | None = None,
    ) -> None:
        self.tool_name = tool_name
        self.resource = resource
        self.required_permission = required_permission
        message = f"Tool '{tool_name}' denied access to '{resource}'"
        if required_permission:
            message = f"{message} (requires: {required_permission})"
        super().__init__(message)


class ToolResourceError(ToolError):
    """Raised when tool resource operations fail.

    Examples:
        - Out of memory
        - Disk space full
        - CPU limit exceeded
    """

    error_code = "PARACLE-TOOL-006"

    def __init__(
        self,
        tool_name: str,
        resource_type: str,
        reason: str,
    ) -> None:
        self.tool_name = tool_name
        self.resource_type = resource_type
        self.reason = reason
        super().__init__(
            f"Tool '{tool_name}' resource error ({resource_type}): {reason}"
        )


class ToolRegistrationError(ToolError):
    """Raised when tool registration fails.

    Examples:
        - Duplicate tool name
        - Invalid tool spec
        - Registration error
    """

    error_code = "PARACLE-TOOL-007"

    def __init__(self, tool_name: str, reason: str) -> None:
        self.tool_name = tool_name
        self.reason = reason
        super().__init__(f"Failed to register tool '{tool_name}': {reason}")


class ToolConfigurationError(ToolError):
    """Raised when tool configuration is invalid.

    Examples:
        - Missing required config
        - Invalid config value
        - Config file parse error
    """

    error_code = "PARACLE-TOOL-008"

    def __init__(
        self,
        tool_name: str,
        reason: str,
        config_key: str | None = None,
    ) -> None:
        self.tool_name = tool_name
        self.reason = reason
        self.config_key = config_key
        message = f"Tool '{tool_name}' configuration error: {reason}"
        if config_key:
            message = f"Tool '{tool_name}' config '{config_key}': {reason}"
        super().__init__(message)
