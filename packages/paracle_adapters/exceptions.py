"""Exceptions for framework adapters."""


class AdapterError(Exception):
    """Base exception for all adapter errors."""

    def __init__(
        self,
        message: str,
        *,
        framework: str | None = None,
        original_error: Exception | None = None,
    ):
        super().__init__(message)
        self.framework = framework
        self.original_error = original_error


class AdapterNotFoundError(AdapterError):
    """Raised when a requested adapter is not registered."""

    def __init__(self, adapter_name: str):
        super().__init__(
            f"Adapter '{adapter_name}' not found in registry",
            framework=adapter_name,
        )
        self.adapter_name = adapter_name


class AdapterConfigurationError(AdapterError):
    """Raised when adapter configuration is invalid."""

    pass


class AdapterExecutionError(AdapterError):
    """Raised when adapter execution fails."""

    pass


class FeatureNotSupportedError(AdapterError):
    """Raised when a feature is not supported by the adapter."""

    def __init__(self, framework: str, feature: str):
        super().__init__(
            f"Feature '{feature}' is not supported by {framework} adapter",
            framework=framework,
        )
        self.feature = feature
