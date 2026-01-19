"""ResilienceCapability - Circuit breaker, retry, and fallback patterns.

This capability implements resilience patterns for reliable LLM operations:
- Circuit breaker to prevent cascading failures
- Retry with exponential backoff
- Fallback strategies
- Bulkhead isolation

Integration Points:
- Uses paracle_core for utilities and logging
- Integrates with paracle_observability for metrics
- Thread-safe async operations

Example:
    >>> from paracle_meta.capabilities import ResilienceCapability, ResilienceConfig
    >>>
    >>> config = ResilienceConfig(
    ...     circuit_breaker_enabled=True,
    ...     retry_enabled=True,
    ...     max_retries=3,
    ...     fallback_enabled=True
    ... )
    >>> resilience = ResilienceCapability(config)
    >>>
    >>> # Execute with resilience
    >>> result = await resilience.execute_with_resilience(
    ...     operation=my_llm_call,
    ...     operation_name="gpt-4-completion",
    ...     fallback=lambda: "Default response"
    ... )
"""

import asyncio
import time
from collections import defaultdict
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from enum import Enum
from typing import Any, Callable

from paracle_core.compat import UTC
from paracle_meta.capabilities.base import BaseCapability, CapabilityResult


class CircuitState(str, Enum):
    """Circuit breaker states."""

    CLOSED = "closed"  # Normal operation
    OPEN = "open"  # Rejecting requests
    HALF_OPEN = "half_open"  # Testing if service recovered


class RetryStrategy(str, Enum):
    """Retry strategies."""

    EXPONENTIAL_BACKOFF = "exponential_backoff"
    LINEAR_BACKOFF = "linear_backoff"
    CONSTANT_BACKOFF = "constant_backoff"


@dataclass
class ResilienceConfig:
    """Configuration for resilience capability.

    Attributes:
        circuit_breaker_enabled: Enable circuit breaker pattern.
        failure_threshold: Failures before opening circuit (default: 5).
        recovery_timeout_seconds: Time before trying half-open (default: 60).
        success_threshold: Successes in half-open to close (default: 2).
        retry_enabled: Enable retry pattern.
        max_retries: Maximum retry attempts (default: 3).
        retry_strategy: Retry backoff strategy.
        initial_retry_delay_ms: Initial retry delay in ms (default: 100).
        max_retry_delay_ms: Maximum retry delay in ms (default: 10000).
        fallback_enabled: Enable fallback pattern.
        timeout_seconds: Operation timeout (0 = no timeout).
        bulkhead_enabled: Enable bulkhead isolation.
        max_concurrent_calls: Max concurrent operations (default: 100).
    """

    circuit_breaker_enabled: bool = True
    failure_threshold: int = 5
    recovery_timeout_seconds: int = 60
    success_threshold: int = 2
    retry_enabled: bool = True
    max_retries: int = 3
    retry_strategy: RetryStrategy = RetryStrategy.EXPONENTIAL_BACKOFF
    initial_retry_delay_ms: int = 100
    max_retry_delay_ms: int = 10000
    fallback_enabled: bool = True
    timeout_seconds: float = 30.0
    bulkhead_enabled: bool = False
    max_concurrent_calls: int = 100


class CircuitBreaker:
    """Circuit breaker implementation."""

    def __init__(
        self,
        failure_threshold: int,
        recovery_timeout_seconds: int,
        success_threshold: int,
    ):
        """Initialize circuit breaker.

        Args:
            failure_threshold: Failures before opening circuit.
            recovery_timeout_seconds: Time before half-open attempt.
            success_threshold: Successes needed to close from half-open.
        """
        self.failure_threshold = failure_threshold
        self.recovery_timeout = timedelta(seconds=recovery_timeout_seconds)
        self.success_threshold = success_threshold

        self.state = CircuitState.CLOSED
        self.failure_count = 0
        self.success_count = 0
        self.last_failure_time: datetime | None = None
        self.opened_at: datetime | None = None

        self._lock = asyncio.Lock()

    async def call(self, operation: Callable, *args, **kwargs) -> Any:
        """Execute operation through circuit breaker.

        Args:
            operation: Async callable to execute.
            *args: Positional arguments for operation.
            **kwargs: Keyword arguments for operation.

        Returns:
            Operation result.

        Raises:
            Exception: If circuit is open or operation fails.
        """
        async with self._lock:
            current_state = self._get_state()

            if current_state == CircuitState.OPEN:
                raise Exception(
                    f"Circuit breaker OPEN (opened at {self.opened_at}). "
                    f"Service unavailable."
                )

        # Execute operation
        try:
            result = await operation(*args, **kwargs)
            await self._on_success()
            return result
        except Exception as e:
            await self._on_failure()
            raise

    def _get_state(self) -> CircuitState:
        """Get current circuit state with automatic state transitions."""
        if self.state == CircuitState.OPEN:
            # Check if recovery timeout elapsed
            if (
                self.opened_at
                and datetime.now(UTC) - self.opened_at >= self.recovery_timeout
            ):
                self.state = CircuitState.HALF_OPEN
                self.success_count = 0

        return self.state

    async def _on_success(self) -> None:
        """Handle successful operation."""
        async with self._lock:
            if self.state == CircuitState.HALF_OPEN:
                self.success_count += 1
                if self.success_count >= self.success_threshold:
                    # Recovered! Close circuit
                    self.state = CircuitState.CLOSED
                    self.failure_count = 0
                    self.success_count = 0
            elif self.state == CircuitState.CLOSED:
                # Reset failure count on success
                self.failure_count = 0

    async def _on_failure(self) -> None:
        """Handle failed operation."""
        async with self._lock:
            self.last_failure_time = datetime.now(UTC)

            if self.state == CircuitState.HALF_OPEN:
                # Failed during recovery -> back to open
                self.state = CircuitState.OPEN
                self.opened_at = datetime.now(UTC)
                self.success_count = 0
            elif self.state == CircuitState.CLOSED:
                self.failure_count += 1
                if self.failure_count >= self.failure_threshold:
                    # Too many failures -> open circuit
                    self.state = CircuitState.OPEN
                    self.opened_at = datetime.now(UTC)

    def get_state(self) -> dict[str, Any]:
        """Get circuit breaker state.

        Returns:
            Dictionary with state information.
        """
        return {
            "state": self._get_state().value,
            "failure_count": self.failure_count,
            "success_count": self.success_count,
            "last_failure_time": (
                self.last_failure_time.isoformat() if self.last_failure_time else None
            ),
            "opened_at": self.opened_at.isoformat() if self.opened_at else None,
        }


class ResilienceCapability(BaseCapability):
    """Resilience capability for reliable operations.

    Implements multiple resilience patterns:
    - Circuit breaker: Prevents cascading failures
    - Retry with backoff: Handles transient failures
    - Fallback: Provides degraded functionality
    - Timeout: Prevents hanging operations
    - Bulkhead: Isolates failures

    Example:
        >>> config = ResilienceConfig(
        ...     circuit_breaker_enabled=True,
        ...     retry_enabled=True,
        ...     max_retries=3
        ... )
        >>> resilience = ResilienceCapability(config)
        >>>
        >>> # Execute with all patterns
        >>> result = await resilience.execute_with_resilience(
        ...     operation=my_api_call,
        ...     operation_name="external-api",
        ...     fallback=lambda: {"default": "response"}
        ... )
    """

    name = "resilience"

    def __init__(self, config: ResilienceConfig | None = None):
        """Initialize resilience capability.

        Args:
            config: Resilience configuration (uses defaults if None).
        """
        super().__init__(config or ResilienceConfig())

        # Circuit breakers per operation
        self._circuit_breakers: dict[str, CircuitBreaker] = {}

        # Bulkhead semaphores per operation
        self._bulkheads: dict[str, asyncio.Semaphore] = {}

        # Metrics
        self._metrics = {
            "total_calls": 0,
            "successful_calls": 0,
            "failed_calls": 0,
            "retried_calls": 0,
            "fallback_calls": 0,
            "circuit_breaker_open": 0,
            "timeouts": 0,
        }

    def _get_circuit_breaker(self, operation_name: str) -> CircuitBreaker:
        """Get or create circuit breaker for operation.

        Args:
            operation_name: Name of operation.

        Returns:
            CircuitBreaker instance.
        """
        if operation_name not in self._circuit_breakers:
            self._circuit_breakers[operation_name] = CircuitBreaker(
                failure_threshold=self.config.failure_threshold,
                recovery_timeout_seconds=self.config.recovery_timeout_seconds,
                success_threshold=self.config.success_threshold,
            )
        return self._circuit_breakers[operation_name]

    def _get_bulkhead(self, operation_name: str) -> asyncio.Semaphore:
        """Get or create bulkhead semaphore for operation.

        Args:
            operation_name: Name of operation.

        Returns:
            Semaphore for bulkhead isolation.
        """
        if operation_name not in self._bulkheads:
            self._bulkheads[operation_name] = asyncio.Semaphore(
                self.config.max_concurrent_calls
            )
        return self._bulkheads[operation_name]

    def _calculate_retry_delay(self, attempt: int) -> float:
        """Calculate retry delay based on strategy.

        Args:
            attempt: Retry attempt number (0-indexed).

        Returns:
            Delay in seconds.
        """
        delay_ms = self.config.initial_retry_delay_ms

        if self.config.retry_strategy == RetryStrategy.EXPONENTIAL_BACKOFF:
            # Exponential: delay * 2^attempt
            delay_ms = self.config.initial_retry_delay_ms * (2**attempt)
        elif self.config.retry_strategy == RetryStrategy.LINEAR_BACKOFF:
            # Linear: delay * (attempt + 1)
            delay_ms = self.config.initial_retry_delay_ms * (attempt + 1)
        # CONSTANT_BACKOFF uses initial delay

        # Cap at max
        delay_ms = min(delay_ms, self.config.max_retry_delay_ms)

        return delay_ms / 1000.0  # Convert to seconds

    async def execute_with_resilience(
        self,
        operation: Callable,
        operation_name: str,
        fallback: Callable | None = None,
        **operation_kwargs: Any,
    ) -> CapabilityResult:
        """Execute operation with all resilience patterns.

        Args:
            operation: Async callable to execute.
            operation_name: Name for metrics and circuit breaker.
            fallback: Optional fallback callable if operation fails.
            **operation_kwargs: Arguments passed to operation.

        Returns:
            CapabilityResult with operation result or fallback.
        """
        start = datetime.now(UTC)
        self._metrics["total_calls"] += 1

        last_exception = None
        attempt = 0

        # Bulkhead isolation
        if self.config.bulkhead_enabled:
            bulkhead = self._get_bulkhead(operation_name)
            if bulkhead.locked():
                # Bulkhead full
                if self.config.fallback_enabled and fallback:
                    self._metrics["fallback_calls"] += 1
                    fallback_result = (
                        await fallback()
                        if asyncio.iscoroutinefunction(fallback)
                        else fallback()
                    )
                    duration = (datetime.now(UTC) - start).total_seconds() * 1000
                    return CapabilityResult(
                        capability=self.name,
                        success=True,
                        output={
                            "result": fallback_result,
                            "used_fallback": True,
                            "reason": "bulkhead_full",
                        },
                        duration_ms=duration,
                    )
                else:
                    duration = (datetime.now(UTC) - start).total_seconds() * 1000
                    return CapabilityResult(
                        capability=self.name,
                        success=False,
                        output={
                            "error": "Bulkhead full - max concurrent calls reached"
                        },
                        duration_ms=duration,
                    )

            async with bulkhead:
                return await self._execute_with_patterns(
                    operation,
                    operation_name,
                    fallback,
                    start,
                    **operation_kwargs,
                )
        else:
            return await self._execute_with_patterns(
                operation,
                operation_name,
                fallback,
                start,
                **operation_kwargs,
            )

    async def _execute_with_patterns(
        self,
        operation: Callable,
        operation_name: str,
        fallback: Callable | None,
        start: datetime,
        **operation_kwargs: Any,
    ) -> CapabilityResult:
        """Execute with retry, circuit breaker, and timeout patterns."""
        last_exception = None
        attempt = 0

        while attempt <= (self.config.max_retries if self.config.retry_enabled else 0):
            try:
                # Timeout wrapper
                if self.config.timeout_seconds > 0:
                    result = await asyncio.wait_for(
                        self._execute_with_circuit_breaker(
                            operation, operation_name, **operation_kwargs
                        ),
                        timeout=self.config.timeout_seconds,
                    )
                else:
                    result = await self._execute_with_circuit_breaker(
                        operation, operation_name, **operation_kwargs
                    )

                # Success!
                self._metrics["successful_calls"] += 1
                if attempt > 0:
                    self._metrics["retried_calls"] += 1

                duration = (datetime.now(UTC) - start).total_seconds() * 1000
                return CapabilityResult(
                    capability=self.name,
                    success=True,
                    output={
                        "result": result,
                        "attempts": attempt + 1,
                        "used_fallback": False,
                    },
                    duration_ms=duration,
                )

            except asyncio.TimeoutError:
                self._metrics["timeouts"] += 1
                last_exception = Exception(
                    f"Operation timed out after {self.config.timeout_seconds}s"
                )

            except Exception as e:
                last_exception = e

                # Check if circuit breaker opened
                if "Circuit breaker OPEN" in str(e):
                    self._metrics["circuit_breaker_open"] += 1

            # Retry logic
            if attempt < (self.config.max_retries if self.config.retry_enabled else 0):
                delay = self._calculate_retry_delay(attempt)
                await asyncio.sleep(delay)
                attempt += 1
            else:
                break

        # All retries failed
        self._metrics["failed_calls"] += 1

        # Try fallback
        if self.config.fallback_enabled and fallback:
            self._metrics["fallback_calls"] += 1
            try:
                fallback_result = (
                    await fallback()
                    if asyncio.iscoroutinefunction(fallback)
                    else fallback()
                )
                duration = (datetime.now(UTC) - start).total_seconds() * 1000
                return CapabilityResult(
                    capability=self.name,
                    success=True,
                    output={
                        "result": fallback_result,
                        "used_fallback": True,
                        "reason": str(last_exception),
                        "attempts": attempt + 1,
                    },
                    duration_ms=duration,
                )
            except Exception as fallback_error:
                last_exception = Exception(
                    f"Operation and fallback failed. "
                    f"Operation error: {last_exception}. "
                    f"Fallback error: {fallback_error}"
                )

        # Complete failure
        duration = (datetime.now(UTC) - start).total_seconds() * 1000
        return CapabilityResult(
            capability=self.name,
            success=False,
            output={
                "error": str(last_exception),
                "attempts": attempt + 1,
            },
            duration_ms=duration,
        )

    async def _execute_with_circuit_breaker(
        self, operation: Callable, operation_name: str, **operation_kwargs: Any
    ) -> Any:
        """Execute operation through circuit breaker.

        Args:
            operation: Operation to execute.
            operation_name: Name for circuit breaker.
            **operation_kwargs: Arguments for operation.

        Returns:
            Operation result.

        Raises:
            Exception: If circuit is open or operation fails.
        """
        if self.config.circuit_breaker_enabled:
            circuit = self._get_circuit_breaker(operation_name)
            return await circuit.call(operation, **operation_kwargs)
        else:
            return await operation(**operation_kwargs)

    async def get_circuit_state(self, operation_name: str) -> CapabilityResult:
        """Get circuit breaker state for operation.

        Args:
            operation_name: Name of operation.

        Returns:
            CapabilityResult with circuit state.
        """
        start = datetime.now(UTC)

        if operation_name in self._circuit_breakers:
            state = self._circuit_breakers[operation_name].get_state()
        else:
            state = {"state": "not_initialized"}

        duration = (datetime.now(UTC) - start).total_seconds() * 1000

        return CapabilityResult(
            capability=self.name,
            success=True,
            output=state,
            duration_ms=duration,
        )

    async def reset_circuit(self, operation_name: str) -> CapabilityResult:
        """Reset circuit breaker for operation.

        Args:
            operation_name: Name of operation.

        Returns:
            CapabilityResult indicating success.
        """
        start = datetime.now(UTC)

        if operation_name in self._circuit_breakers:
            circuit = self._circuit_breakers[operation_name]
            async with circuit._lock:
                circuit.state = CircuitState.CLOSED
                circuit.failure_count = 0
                circuit.success_count = 0
                circuit.last_failure_time = None
                circuit.opened_at = None
            reset = True
        else:
            reset = False

        duration = (datetime.now(UTC) - start).total_seconds() * 1000

        return CapabilityResult(
            capability=self.name,
            success=True,
            output={"reset": reset, "operation": operation_name},
            duration_ms=duration,
        )

    async def get_metrics(self) -> CapabilityResult:
        """Get resilience metrics.

        Returns:
            CapabilityResult with metrics.
        """
        start = datetime.now(UTC)

        # Calculate success rate
        total = self._metrics["total_calls"]
        success_rate = self._metrics["successful_calls"] / total if total > 0 else 0.0

        # Circuit breaker states
        circuit_states = {
            name: breaker.get_state()
            for name, breaker in self._circuit_breakers.items()
        }

        duration = (datetime.now(UTC) - start).total_seconds() * 1000

        return CapabilityResult(
            capability=self.name,
            success=True,
            output={
                **self._metrics,
                "success_rate": success_rate,
                "circuit_breakers": circuit_states,
            },
            duration_ms=duration,
        )

    async def reset_metrics(self) -> CapabilityResult:
        """Reset metrics (testing/admin).

        Returns:
            CapabilityResult indicating success.
        """
        start = datetime.now(UTC)

        self._metrics = {
            "total_calls": 0,
            "successful_calls": 0,
            "failed_calls": 0,
            "retried_calls": 0,
            "fallback_calls": 0,
            "circuit_breaker_open": 0,
            "timeouts": 0,
        }

        duration = (datetime.now(UTC) - start).total_seconds() * 1000

        return CapabilityResult(
            capability=self.name,
            success=True,
            output={"metrics_reset": True},
            duration_ms=duration,
        )

    async def execute(self, **kwargs: Any) -> CapabilityResult:
        """Execute resilience operation with action routing.

        Args:
            **kwargs: Must include 'action' and action-specific parameters.

        Supported actions:
        - execute_with_resilience: Execute operation with resilience.
        - get_circuit_state: Get circuit breaker state.
        - reset_circuit: Reset circuit breaker.
        - get_metrics: Get resilience metrics.
        - reset_metrics: Reset metrics.

        Returns:
            CapabilityResult from the executed action.
        """
        action_param = kwargs.pop("action", "get_metrics")

        action_map = {
            "execute_with_resilience": self.execute_with_resilience,
            "get_circuit_state": self.get_circuit_state,
            "reset_circuit": self.reset_circuit,
            "get_metrics": self.get_metrics,
            "reset_metrics": self.reset_metrics,
        }

        if action_param in action_map:
            return await action_map[action_param](**kwargs)

        return CapabilityResult(
            capability=self.name,
            success=False,
            output={"error": f"Unknown action: {action_param}"},
        )
