"""Exceptions for LLM providers."""


class LLMProviderError(Exception):
    """Base exception for all LLM provider errors."""

    def __init__(
        self,
        message: str,
        *,
        provider: str | None = None,
        model: str | None = None,
        original_error: Exception | None = None,
    ):
        super().__init__(message)
        self.provider = provider
        self.model = model
        self.original_error = original_error


class ProviderNotFoundError(LLMProviderError):
    """Raised when a requested provider is not registered."""

    def __init__(self, provider_name: str):
        super().__init__(
            f"Provider '{provider_name}' not found in registry",
            provider=provider_name,
        )
        self.provider_name = provider_name


class ProviderRateLimitError(LLMProviderError):
    """Raised when provider rate limit is exceeded."""

    def __init__(
        self,
        message: str,
        *,
        provider: str | None = None,
        retry_after: int | None = None,
    ):
        super().__init__(message, provider=provider)
        self.retry_after = retry_after


class ProviderTimeoutError(LLMProviderError):
    """Raised when provider request times out."""

    def __init__(
        self,
        message: str,
        *,
        provider: str | None = None,
        timeout: float | None = None,
    ):
        super().__init__(message, provider=provider)
        self.timeout = timeout


class ProviderAuthenticationError(LLMProviderError):
    """Raised when provider authentication fails."""

    pass


class ProviderInvalidRequestError(LLMProviderError):
    """Raised when request to provider is invalid."""

    pass
