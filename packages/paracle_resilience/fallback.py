"""Fallback strategies for degraded operation.

This module provides fallback strategies to handle failures gracefully by
providing alternative responses when primary operations fail.

Strategies:
- CachedResponseFallback: Return cached response
- DefaultValueFallback: Return default value
- RetryFallback: Retry with exponential backoff
- DegradedServiceFallback: Use degraded service
- FallbackChain: Try multiple strategies in sequence

Example:
    >>> from paracle_resilience import FallbackChain, CachedResponseFallback, DefaultValueFallback
    >>>
    >>> fallback = FallbackChain([
    ...     CachedResponseFallback(cache_ttl=300),
    ...     DefaultValueFallback(default={"status": "degraded"}),
    ... ])
    >>>
    >>> try:
    ...     result = service.call()
    ... except Exception as e:
    ...     result = await fallback.execute(lambda: service.call(), e)
"""

import asyncio
import time
from abc import ABC, abstractmethod
from collections.abc import Callable
from typing import Any, TypeVar

T = TypeVar("T")


class FallbackError(Exception):
    """Base exception for fallback errors."""

    def __init__(self, message: str, original_error: Exception | None = None):
        self.original_error = original_error
        super().__init__(message)


class FallbackStrategy(ABC):
    """Base class for fallback strategies."""

    def __init__(self, name: str):
        """Initialize fallback strategy.

        Args:
            name: Strategy identifier
        """
        self.name = name
        self.execution_count = 0
        self.success_count = 0
        self.failure_count = 0

    @abstractmethod
    def execute(self, func: Callable[[], T], original_error: Exception) -> T:
        """Execute fallback strategy.

        Args:
            func: Original function that failed
            original_error: Exception from original call

        Returns:
            Fallback result

        Raises:
            FallbackError: If fallback fails
        """
        pass

    @abstractmethod
    async def execute_async(self, func: Callable, original_error: Exception) -> Any:
        """Execute async fallback strategy.

        Args:
            func: Original async function that failed
            original_error: Exception from original call

        Returns:
            Fallback result

        Raises:
            FallbackError: If fallback fails
        """
        pass

    def _record_execution(self, success: bool):
        """Record execution statistics."""
        self.execution_count += 1
        if success:
            self.success_count += 1
        else:
            self.failure_count += 1

    def get_stats(self) -> dict:
        """Get execution statistics."""
        return {
            "name": self.name,
            "executions": self.execution_count,
            "successes": self.success_count,
            "failures": self.failure_count,
            "success_rate": (
                self.success_count / self.execution_count
                if self.execution_count > 0
                else 0.0
            ),
        }


class CachedResponseFallback(FallbackStrategy):
    """Return cached response as fallback.

    Attributes:
        cache: Response cache
        cache_ttl: Cache time-to-live in seconds
    """

    def __init__(self, cache_ttl: int = 300, name: str = "cached_response"):
        """Initialize cached response fallback.

        Args:
            cache_ttl: Cache TTL in seconds (default: 300)
            name: Strategy name
        """
        super().__init__(name)
        self.cache: dict[str, tuple[Any, float]] = {}
        self.cache_ttl = cache_ttl

    def _get_cache_key(self, func: Callable) -> str:
        """Generate cache key from function."""
        return f"{func.__module__}.{func.__name__}"

    def _is_cache_valid(self, timestamp: float) -> bool:
        """Check if cache entry is still valid."""
        return time.time() - timestamp < self.cache_ttl

    def set_cache(self, key: str, value: Any):
        """Manually set cache entry.

        Args:
            key: Cache key
            value: Value to cache
        """
        self.cache[key] = (value, time.time())

    def execute(self, func: Callable[[], T], original_error: Exception) -> T:
        """Return cached response.

        Args:
            func: Original function
            original_error: Original exception

        Returns:
            Cached response

        Raises:
            FallbackError: If no valid cache entry
        """
        cache_key = self._get_cache_key(func)
        if cache_key in self.cache:
            value, timestamp = self.cache[cache_key]
            if self._is_cache_valid(timestamp):
                self._record_execution(success=True)
                return value

        self._record_execution(success=False)
        raise FallbackError(f"No valid cache entry for {func.__name__}", original_error)

    async def execute_async(self, func: Callable, original_error: Exception) -> Any:
        """Return cached response (async).

        Args:
            func: Original function
            original_error: Original exception

        Returns:
            Cached response

        Raises:
            FallbackError: If no valid cache entry
        """
        return self.execute(func, original_error)


class DefaultValueFallback(FallbackStrategy):
    """Return default value as fallback.

    Attributes:
        default: Default value to return
    """

    def __init__(self, default: Any, name: str = "default_value"):
        """Initialize default value fallback.

        Args:
            default: Default value to return
            name: Strategy name
        """
        super().__init__(name)
        self.default = default

    def execute(self, func: Callable[[], T], original_error: Exception) -> T:
        """Return default value.

        Args:
            func: Original function (unused)
            original_error: Original exception (unused)

        Returns:
            Default value
        """
        self._record_execution(success=True)
        return self.default

    async def execute_async(self, func: Callable, original_error: Exception) -> Any:
        """Return default value (async).

        Args:
            func: Original function (unused)
            original_error: Original exception (unused)

        Returns:
            Default value
        """
        self._record_execution(success=True)
        return self.default


class RetryFallback(FallbackStrategy):
    """Retry with exponential backoff as fallback.

    Attributes:
        max_retries: Maximum retry attempts
        base_delay: Base delay in seconds
        max_delay: Maximum delay in seconds
    """

    def __init__(
        self,
        max_retries: int = 3,
        base_delay: float = 1.0,
        max_delay: float = 60.0,
        name: str = "retry",
    ):
        """Initialize retry fallback.

        Args:
            max_retries: Maximum retries (default: 3)
            base_delay: Base delay in seconds (default: 1.0)
            max_delay: Max delay in seconds (default: 60.0)
            name: Strategy name
        """
        super().__init__(name)
        self.max_retries = max_retries
        self.base_delay = base_delay
        self.max_delay = max_delay

    def _calculate_delay(self, attempt: int) -> float:
        """Calculate delay with exponential backoff."""
        delay = min(self.base_delay * (2**attempt), self.max_delay)
        return delay

    def execute(self, func: Callable[[], T], original_error: Exception) -> T:
        """Retry function with exponential backoff.

        Args:
            func: Function to retry
            original_error: Original exception

        Returns:
            Function result

        Raises:
            FallbackError: If all retries fail
        """
        last_error = original_error

        for attempt in range(self.max_retries):
            try:
                delay = self._calculate_delay(attempt)
                time.sleep(delay)
                result = func()
                self._record_execution(success=True)
                return result
            except Exception as e:
                last_error = e

        self._record_execution(success=False)
        raise FallbackError(f"All {self.max_retries} retries failed", last_error)

    async def execute_async(self, func: Callable, original_error: Exception) -> Any:
        """Retry async function with exponential backoff.

        Args:
            func: Async function to retry
            original_error: Original exception

        Returns:
            Function result

        Raises:
            FallbackError: If all retries fail
        """
        last_error = original_error

        for attempt in range(self.max_retries):
            try:
                delay = self._calculate_delay(attempt)
                await asyncio.sleep(delay)
                result = await func()
                self._record_execution(success=True)
                return result
            except Exception as e:
                last_error = e

        self._record_execution(success=False)
        raise FallbackError(f"All {self.max_retries} retries failed", last_error)


class DegradedServiceFallback(FallbackStrategy):
    """Use degraded service as fallback.

    Attributes:
        degraded_func: Function for degraded operation
    """

    def __init__(self, degraded_func: Callable, name: str = "degraded_service"):
        """Initialize degraded service fallback.

        Args:
            degraded_func: Function providing degraded service
            name: Strategy name
        """
        super().__init__(name)
        self.degraded_func = degraded_func

    def execute(self, func: Callable[[], T], original_error: Exception) -> T:
        """Execute degraded service function.

        Args:
            func: Original function (unused)
            original_error: Original exception

        Returns:
            Degraded service result

        Raises:
            FallbackError: If degraded service fails
        """
        try:
            result = self.degraded_func()
            self._record_execution(success=True)
            return result
        except Exception as e:
            self._record_execution(success=False)
            raise FallbackError(f"Degraded service failed: {e}", original_error)

    async def execute_async(self, func: Callable, original_error: Exception) -> Any:
        """Execute degraded service function (async).

        Args:
            func: Original function (unused)
            original_error: Original exception

        Returns:
            Degraded service result

        Raises:
            FallbackError: If degraded service fails
        """
        try:
            if asyncio.iscoroutinefunction(self.degraded_func):
                result = await self.degraded_func()
            else:
                result = self.degraded_func()
            self._record_execution(success=True)
            return result
        except Exception as e:
            self._record_execution(success=False)
            raise FallbackError(f"Degraded service failed: {e}", original_error)


class FallbackChain(FallbackStrategy):
    """Try multiple fallback strategies in sequence.

    Attributes:
        strategies: List of fallback strategies to try
    """

    def __init__(self, strategies: list[FallbackStrategy], name: str = "chain"):
        """Initialize fallback chain.

        Args:
            strategies: List of strategies to try in order
            name: Strategy name
        """
        super().__init__(name)
        self.strategies = strategies

    def execute(self, func: Callable[[], T], original_error: Exception) -> T:
        """Try strategies in sequence until one succeeds.

        Args:
            func: Original function
            original_error: Original exception

        Returns:
            First successful result

        Raises:
            FallbackError: If all strategies fail
        """
        last_error = original_error

        for strategy in self.strategies:
            try:
                result = strategy.execute(func, original_error)
                self._record_execution(success=True)
                return result
            except Exception as e:
                last_error = e

        self._record_execution(success=False)
        raise FallbackError(
            f"All {len(self.strategies)} fallback strategies failed", last_error
        )

    async def execute_async(self, func: Callable, original_error: Exception) -> Any:
        """Try strategies in sequence until one succeeds (async).

        Args:
            func: Original async function
            original_error: Original exception

        Returns:
            First successful result

        Raises:
            FallbackError: If all strategies fail
        """
        last_error = original_error

        for strategy in self.strategies:
            try:
                result = await strategy.execute_async(func, original_error)
                self._record_execution(success=True)
                return result
            except Exception as e:
                last_error = e

        self._record_execution(success=False)
        raise FallbackError(
            f"All {len(self.strategies)} fallback strategies failed", last_error
        )

    def get_stats(self) -> dict:
        """Get execution statistics for all strategies."""
        return {
            "name": self.name,
            "executions": self.execution_count,
            "successes": self.success_count,
            "failures": self.failure_count,
            "strategies": [s.get_stats() for s in self.strategies],
        }
