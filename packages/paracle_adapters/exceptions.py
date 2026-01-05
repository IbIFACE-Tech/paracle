"""Exceptions for framework adapters.

Exception hierarchy with error codes and proper exception chaining.
All exceptions include error codes for documentation and support.
"""


class AdapterError(Exception):
    """Base exception for all adapter errors.

    Attributes:
        error_code: Unique error code (PARACLE-ADPT-XXX)
        message: Human-readable error message
        framework: Framework name (e.g., 'langchain', 'msaf')
        original_error: Original exception that caused this error
    """

    error_code: str = "PARACLE-ADPT-000"

    def __init__(
        self,
        message: str,
        *,
        framework: str | None = None,
        original_error: Exception | None = None,
    ):
        super().__init__(message)
        self.message = message
        self.framework = framework
        self.original_error = original_error
        if original_error:
            self.__cause__ = original_error  # Proper exception chaining


class AdapterNotFoundError(AdapterError):
    """Raised when a requested adapter is not registered."""

    error_code = "PARACLE-ADPT-001"

    def __init__(self, adapter_name: str):
        super().__init__(
            f"Adapter '{adapter_name}' not found in registry",
            framework=adapter_name,
        )
        self.adapter_name = adapter_name


class AdapterConfigurationError(AdapterError):
    """Raised when adapter configuration is invalid."""

    error_code = "PARACLE-ADPT-002"

    def __init__(
        self,
        message: str,
        *,
        framework: str | None = None,
        config_key: str | None = None,
        original_error: Exception | None = None,
    ):
        super().__init__(message, framework=framework, original_error=original_error)
        self.config_key = config_key


class AdapterExecutionError(AdapterError):
    """Raised when adapter execution fails."""

    error_code = "PARACLE-ADPT-003"

    def __init__(
        self,
        message: str,
        *,
        framework: str | None = None,
        operation: str | None = None,
        original_error: Exception | None = None,
    ):
        super().__init__(message, framework=framework, original_error=original_error)
        self.operation = operation


class FeatureNotSupportedError(AdapterError):
    """Raised when a feature is not supported by the adapter."""

    error_code = "PARACLE-ADPT-004"

    def __init__(self, framework: str, feature: str):
        super().__init__(
            f"Feature '{feature}' is not supported by {framework} adapter",
            framework=framework,
        )
        self.feature = feature
