"""Retry logic with exponential backoff for LLM providers.

Implements retry patterns for transient failures with configurable
backoff strategies and jitter.
"""

import asyncio
import random
from collections.abc import Awaitable, Callable
from dataclasses import dataclass, field
from typing import Any, TypeVar

from paracle_core.logging import get_logger

from paracle_providers.exceptions import (
    ProviderConnectionError,
    ProviderRateLimitError,
    ProviderTimeoutError,
)

logger = get_logger(__name__)

T = TypeVar("T")


@dataclass
class RetryConfig:
    """Configuration for retry behavior.

    Attributes:
        max_attempts: Maximum number of retry attempts (including initial)
        base_delay: Base delay in seconds between retries
        max_delay: Maximum delay in seconds (caps exponential growth)
        exponential_base: Base for exponential backoff (default: 2)
        jitter: Whether to add random jitter to delays
        jitter_factor: Maximum jitter as fraction of delay (0.0-1.0)
        retryable_exceptions: Exception types that trigger retry
    """

    max_attempts: int = 3
    base_delay: float = 1.0
    max_delay: float = 60.0
    exponential_base: float = 2.0
    jitter: bool = True
    jitter_factor: float = 0.1
    retryable_exceptions: tuple[type[Exception], ...] = field(
        default_factory=lambda: (
            ProviderRateLimitError,
            ProviderTimeoutError,
            ProviderConnectionError,
        )
    )

    def is_retryable(self, exc: Exception) -> bool:
        """Check if exception is retryable."""
        return isinstance(exc, self.retryable_exceptions)

    def calculate_delay(self, attempt: int) -> float:
        """Calculate delay for given attempt number (0-indexed).

        Uses exponential backoff with optional jitter.

        Args:
            attempt: Current attempt number (0 = first retry)

        Returns:
            Delay in seconds
        """
        # Exponential backoff: base_delay * (exponential_base ^ attempt)
        delay = self.base_delay * (self.exponential_base**attempt)

        # Cap at max_delay
        delay = min(delay, self.max_delay)

        # Add jitter if enabled
        if self.jitter:
            jitter_range = delay * self.jitter_factor
            delay += random.uniform(-jitter_range, jitter_range)

        return max(0, delay)


@dataclass
class RetryResult:
    """Result of a retry operation.

    Attributes:
        success: Whether the operation succeeded
        result: The result if successful
        attempts: Number of attempts made
        total_delay: Total time spent in delays (seconds)
        last_error: Last error if failed
    """

    success: bool
    result: Any = None
    attempts: int = 0
    total_delay: float = 0.0
    last_error: Exception | None = None


async def retry_with_backoff(
    operation: Callable[[], Awaitable[T]],
    config: RetryConfig | None = None,
    operation_name: str = "operation",
) -> T:
    """Execute an async operation with retry and exponential backoff.

    Args:
        operation: Async callable to execute
        config: Retry configuration (uses defaults if None)
        operation_name: Name for logging purposes

    Returns:
        Result of the successful operation

    Raises:
        The last exception if all retries are exhausted
    """
    if config is None:
        config = RetryConfig()

    last_error: Exception | None = None
    total_delay = 0.0

    for attempt in range(config.max_attempts):
        try:
            result = await operation()
            if attempt > 0:
                logger.info(
                    f"{operation_name} succeeded after {attempt + 1} attempts "
                    f"(total delay: {total_delay:.2f}s)"
                )
            return result

        except Exception as exc:
            last_error = exc

            # Check if this is the last attempt
            if attempt >= config.max_attempts - 1:
                logger.error(
                    f"{operation_name} failed after {attempt + 1} attempts: {exc}"
                )
                raise

            # Check if exception is retryable
            if not config.is_retryable(exc):
                logger.error(f"{operation_name} failed with non-retryable error: {exc}")
                raise

            # Calculate delay, respecting retry_after for rate limits
            delay = config.calculate_delay(attempt)
            if isinstance(exc, ProviderRateLimitError) and exc.retry_after:
                delay = max(delay, float(exc.retry_after))
                delay = min(delay, config.max_delay)

            logger.warning(
                f"{operation_name} attempt {attempt + 1}/{config.max_attempts} "
                f"failed: {exc}. Retrying in {delay:.2f}s..."
            )

            await asyncio.sleep(delay)
            total_delay += delay

    # This should not be reached, but for type safety
    assert last_error is not None
    raise last_error


class RetryableProvider:
    """Mixin class to add retry capabilities to LLM providers.

    Usage:
        class MyProvider(LLMProvider, RetryableProvider):
            async def chat_completion(self, ...):
                async def _do_request():
                    return await self._raw_chat_completion(...)
                return await self.with_retry(_do_request, "chat_completion")
    """

    retry_config: RetryConfig = RetryConfig()

    def configure_retry(self, config: RetryConfig) -> None:
        """Configure retry behavior for this provider."""
        self.retry_config = config

    async def with_retry(
        self,
        operation: Callable[[], Awaitable[T]],
        operation_name: str = "LLM request",
    ) -> T:
        """Execute operation with retry logic.

        Args:
            operation: Async callable to execute
            operation_name: Name for logging purposes

        Returns:
            Result of the successful operation
        """
        return await retry_with_backoff(
            operation=operation,
            config=self.retry_config,
            operation_name=operation_name,
        )


def create_retry_decorator(
    config: RetryConfig | None = None,
) -> Callable[
    [Callable[..., Awaitable[T]]],
    Callable[..., Awaitable[T]],
]:
    """Create a decorator for adding retry logic to async functions.

    Args:
        config: Retry configuration (uses defaults if None)

    Returns:
        Decorator function

    Example:
        @create_retry_decorator(RetryConfig(max_attempts=5))
        async def my_function():
            ...
    """
    if config is None:
        config = RetryConfig()

    def decorator(
        func: Callable[..., Awaitable[T]],
    ) -> Callable[..., Awaitable[T]]:
        async def wrapper(*args: Any, **kwargs: Any) -> T:
            async def operation() -> T:
                return await func(*args, **kwargs)

            return await retry_with_backoff(
                operation=operation,
                config=config,
                operation_name=func.__name__,
            )

        # Preserve function metadata
        wrapper.__name__ = func.__name__
        wrapper.__doc__ = func.__doc__
        return wrapper

    return decorator
