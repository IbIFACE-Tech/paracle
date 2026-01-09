"""Exceptions for LLM providers.

Exception hierarchy with error codes and proper exception chaining.
"""


class LLMProviderError(Exception):
    """Base exception for all LLM provider errors.

    Attributes:
        error_code: Unique error code (PARACLE-PROV-XXX)
        provider: Provider name (e.g., 'openai', 'anthropic')
        model: Model name if applicable
        original_error: Original exception that caused this error
    """

    error_code: str = "PARACLE-PROV-000"

    def __init__(
        self,
        message: str,
        *,
        provider: str | None = None,
        model: str | None = None,
        original_error: Exception | None = None,
    ):
        super().__init__(message)
        self.message = message
        self.provider = provider
        self.model = model
        self.original_error = original_error
        if original_error:
            self.__cause__ = original_error  # Proper exception chaining


class ProviderNotFoundError(LLMProviderError):
    """Raised when a requested provider is not registered."""

    error_code = "PARACLE-PROV-001"

    def __init__(self, provider_name: str):
        super().__init__(
            f"Provider '{provider_name}' not found in registry",
            provider=provider_name,
        )
        self.provider_name = provider_name


class ProviderRateLimitError(LLMProviderError):
    """Raised when provider rate limit is exceeded.

    Attributes:
        retry_after: Seconds to wait before retrying (if provided by API)
    """

    error_code = "PARACLE-PROV-002"

    def __init__(
        self,
        message: str,
        *,
        provider: str | None = None,
        retry_after: int | None = None,
        original_error: Exception | None = None,
    ):
        super().__init__(message, provider=provider, original_error=original_error)
        self.retry_after = retry_after


class ProviderTimeoutError(LLMProviderError):
    """Raised when provider request times out.

    Attributes:
        timeout: The timeout value that was exceeded
    """

    error_code = "PARACLE-PROV-003"

    def __init__(
        self,
        message: str,
        *,
        provider: str | None = None,
        timeout: float | None = None,
        original_error: Exception | None = None,
    ):
        super().__init__(message, provider=provider, original_error=original_error)
        self.timeout = timeout


class ProviderAuthenticationError(LLMProviderError):
    """Raised when provider authentication fails."""

    error_code = "PARACLE-PROV-004"


class ProviderInvalidRequestError(LLMProviderError):
    """Raised when request to provider is invalid."""

    error_code = "PARACLE-PROV-005"


class ProviderConnectionError(LLMProviderError):
    """Raised when connection to provider fails."""

    error_code = "PARACLE-PROV-006"

    def __init__(
        self,
        message: str,
        *,
        provider: str | None = None,
        original_error: Exception | None = None,
    ):
        super().__init__(message, provider=provider, original_error=original_error)
