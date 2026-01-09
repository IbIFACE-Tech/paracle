"""Core framework exceptions.

Exception hierarchy for Paracle core framework errors.
All exceptions include error codes for traceability and documentation.
"""


class ParacleError(Exception):
    """Base exception for all Paracle framework errors.

    Attributes:
        error_code: Unique error code (PARACLE-CORE-XXX)
        message: Human-readable error message
    """

    error_code: str = "PARACLE-CORE-000"

    def __init__(self, message: str) -> None:
        self.message = message
        super().__init__(message)


class ConfigurationError(ParacleError):
    """Raised when configuration is invalid or missing.

    Examples:
        - Missing required configuration key
        - Invalid YAML syntax in project.yaml
        - Conflicting configuration values
    """

    error_code = "PARACLE-CORE-001"

    def __init__(self, message: str, config_key: str | None = None) -> None:
        self.config_key = config_key
        if config_key:
            message = f"Configuration error for '{config_key}': {message}"
        super().__init__(message)


class InitializationError(ParacleError):
    """Raised when Paracle framework initialization fails.

    Examples:
        - .parac/ directory not found
        - Required dependencies missing
        - Invalid project structure
    """

    error_code = "PARACLE-CORE-002"

    def __init__(self, message: str, component: str | None = None) -> None:
        self.component = component
        if component:
            message = f"Failed to initialize {component}: {message}"
        super().__init__(message)


class ValidationError(ParacleError):
    """Raised when validation fails.

    Examples:
        - Invalid agent spec YAML
        - Invalid workflow definition
        - Schema validation failure
    """

    error_code = "PARACLE-CORE-003"

    def __init__(
        self,
        message: str,
        field: str | None = None,
        value: str | None = None,
    ) -> None:
        self.field = field
        self.value = value
        if field:
            message = f"Validation failed for '{field}': {message}"
        super().__init__(message)


class WorkspaceError(ParacleError):
    """Raised when workspace operations fail.

    Examples:
        - .parac/ directory creation failed
        - Invalid workspace structure
        - Permission denied on workspace files
    """

    error_code = "PARACLE-CORE-004"

    def __init__(self, message: str, path: str | None = None) -> None:
        self.path = path
        if path:
            message = f"Workspace error at '{path}': {message}"
        super().__init__(message)


class DependencyError(ParacleError):
    """Raised when required dependencies are missing or incompatible.

    Examples:
        - Required package not installed
        - Incompatible package version
        - Native library missing
    """

    error_code = "PARACLE-CORE-005"

    def __init__(
        self,
        message: str,
        dependency: str | None = None,
        required_version: str | None = None,
    ) -> None:
        self.dependency = dependency
        self.required_version = required_version
        if dependency:
            if required_version:
                message = f"Dependency '{dependency}' (>={required_version}): {message}"
            else:
                message = f"Dependency '{dependency}': {message}"
        super().__init__(message)


class ResourceError(ParacleError):
    """Raised when resource operations fail.

    Examples:
        - File not found
        - Insufficient disk space
        - Memory limit exceeded
    """

    error_code = "PARACLE-CORE-006"

    def __init__(
        self,
        message: str,
        resource_type: str | None = None,
        resource_id: str | None = None,
    ) -> None:
        self.resource_type = resource_type
        self.resource_id = resource_id
        if resource_type and resource_id:
            message = f"Resource error ({resource_type}:{resource_id}): {message}"
        elif resource_type:
            message = f"Resource error ({resource_type}): {message}"
        super().__init__(message)


class StateError(ParacleError):
    """Raised when state operations fail.

    Examples:
        - Invalid state transition
        - State file corrupted
        - Concurrent state modification
    """

    error_code = "PARACLE-CORE-007"

    def __init__(
        self,
        message: str,
        current_state: str | None = None,
        target_state: str | None = None,
    ) -> None:
        self.current_state = current_state
        self.target_state = target_state
        if current_state and target_state:
            message = (
                f"Invalid state transition {current_state} -> {target_state}: {message}"
            )
        super().__init__(message)


class PermissionError(ParacleError):
    """Raised when permission checks fail.

    Examples:
        - Insufficient privileges
        - Resource access denied
        - Policy violation
    """

    error_code = "PARACLE-CORE-008"

    def __init__(
        self,
        message: str,
        resource: str | None = None,
        required_permission: str | None = None,
    ) -> None:
        self.resource = resource
        self.required_permission = required_permission
        if resource and required_permission:
            message = f"Permission denied on '{resource}' (requires: {required_permission}): {message}"
        super().__init__(message)
