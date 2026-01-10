"""Circuit breaker pattern for fault tolerance.

This module provides circuit breaker functionality to prevent cascading failures
by automatically detecting and recovering from errors.

States:
- CLOSED: Normal operation, requests pass through
- OPEN: Too many failures, requests rejected immediately
- HALF_OPEN: Testing recovery, limited requests allowed

Example:
    >>> circuit = CircuitBreaker(name="api_service", failure_threshold=5, timeout=60)
    >>>
    >>> async def call_api():
    ...     async with circuit:
    ...         return await api.request()
"""

import asyncio
from collections.abc import Callable
from datetime import datetime
from enum import Enum
from typing import Any, TypeVar

from pydantic import BaseModel, Field

T = TypeVar("T")


class CircuitBreakerState(str, Enum):
    """Circuit breaker states."""

    CLOSED = "closed"  # Normal operation
    OPEN = "open"  # Failures exceed threshold, blocking requests
    HALF_OPEN = "half_open"  # Testing recovery


class CircuitBreakerError(Exception):
    """Base exception for circuit breaker errors."""

    def __init__(self, message: str, circuit_name: str):
        self.circuit_name = circuit_name
        super().__init__(f"[{circuit_name}] {message}")


class CircuitOpenError(CircuitBreakerError):
    """Raised when circuit breaker is open."""

    def __init__(self, circuit_name: str, retry_after: float):
        self.retry_after = retry_after
        super().__init__(
            f"Circuit breaker is OPEN. Retry after {retry_after:.1f}s",
            circuit_name,
        )


class CircuitBreakerConfig(BaseModel):
    """Circuit breaker configuration."""

    name: str = Field(..., description="Unique circuit breaker identifier")
    failure_threshold: int = Field(
        default=5, description="Number of failures before opening circuit", ge=1
    )
    success_threshold: int = Field(
        default=2, description="Number of successes before closing from half-open", ge=1
    )
    timeout: float = Field(
        default=60.0,
        description="Seconds to wait before half-open (reset timeout)",
        gt=0,
    )
    half_open_max_calls: int = Field(
        default=3, description="Max concurrent calls in half-open state", ge=1
    )


class CircuitBreaker:
    """Circuit breaker for fault tolerance.

    Automatically detects failures and prevents cascading failures by opening
    the circuit after threshold is exceeded.

    Attributes:
        name: Circuit breaker identifier
        state: Current state (CLOSED, OPEN, HALF_OPEN)
        failure_count: Number of consecutive failures
        success_count: Number of consecutive successes in half-open
        last_failure_time: Timestamp of last failure
        opened_at: Timestamp when circuit opened

    Example:
        >>> circuit = CircuitBreaker("service", failure_threshold=5, timeout=60)
        >>>
        >>> # Synchronous usage
        >>> with circuit:
        ...     result = service.call()
        >>>
        >>> # Async usage
        >>> async with circuit:
        ...     result = await service.call_async()
        >>>
        >>> # Manual call
        >>> result = circuit.call(service.call)
    """

    def __init__(
        self,
        name: str,
        failure_threshold: int = 5,
        success_threshold: int = 2,
        timeout: float = 60.0,
        half_open_max_calls: int = 3,
    ):
        """Initialize circuit breaker.

        Args:
            name: Unique identifier for this circuit
            failure_threshold: Failures before opening (default: 5)
            success_threshold: Successes before closing from half-open (default: 2)
            timeout: Seconds before attempting half-open (default: 60)
            half_open_max_calls: Max concurrent calls in half-open (default: 3)
        """
        self.config = CircuitBreakerConfig(
            name=name,
            failure_threshold=failure_threshold,
            success_threshold=success_threshold,
            timeout=timeout,
            half_open_max_calls=half_open_max_calls,
        )

        self.state = CircuitBreakerState.CLOSED
        self.failure_count = 0
        self.success_count = 0
        self.last_failure_time: datetime | None = None
        self.opened_at: datetime | None = None
        self.half_open_calls = 0
        self._lock = asyncio.Lock()

        # Metrics tracking
        self.total_calls = 0
        self.total_failures = 0
        self.total_successes = 0
        self.total_rejected = 0  # Calls rejected when circuit is open
        self.total_timeouts = 0  # Times circuit stayed open full duration

    @property
    def name(self) -> str:
        """Circuit breaker name."""
        return self.config.name

    def _should_attempt_reset(self) -> bool:
        """Check if circuit should attempt reset to half-open."""
        if self.state != CircuitBreakerState.OPEN:
            return False

        if self.opened_at is None:
            return False

        elapsed = (datetime.now() - self.opened_at).total_seconds()
        return elapsed >= self.config.timeout

    def _record_success(self):
        """Record successful call."""
        self.total_successes += 1
        if self.state == CircuitBreakerState.HALF_OPEN:
            self.success_count += 1
            if self.success_count >= self.config.success_threshold:
                self._close()
        elif self.state == CircuitBreakerState.CLOSED:
            self.failure_count = 0  # Reset failure count on success

    def _record_failure(self):
        """Record failed call."""
        self.total_failures += 1
        self.last_failure_time = datetime.now()

        if self.state == CircuitBreakerState.HALF_OPEN:
            self._open()
        elif self.state == CircuitBreakerState.CLOSED:
            self.failure_count += 1
            if self.failure_count >= self.config.failure_threshold:
                self._open()

    def _open(self):
        """Open the circuit."""
        self.state = CircuitBreakerState.OPEN
        self.opened_at = datetime.now()
        self.success_count = 0

    def _close(self):
        """Close the circuit."""
        self.state = CircuitBreakerState.CLOSED
        self.failure_count = 0
        self.success_count = 0
        self.opened_at = None

    def _half_open(self):
        """Transition to half-open state."""
        self.state = CircuitBreakerState.HALF_OPEN
        self.success_count = 0
        self.half_open_calls = 0

    def call(self, func: Callable[[], T], *args, **kwargs) -> T:
        """Execute function with circuit breaker protection.

        Args:
            func: Function to call
            *args: Positional arguments
            **kwargs: Keyword arguments

        Returns:
            Function result

        Raises:
            CircuitOpenError: If circuit is open
            Exception: Original exception from function
        """
        # Check if should attempt reset
        if self._should_attempt_reset():
            self._half_open()

        # Check state
        if self.state == CircuitBreakerState.OPEN:
            self.total_rejected += 1
            retry_after = (
                self.config.timeout -
                (datetime.now() - self.opened_at).total_seconds()
            )
            raise CircuitOpenError(self.name, max(0, retry_after))

        self.total_calls += 1
        if self.state == CircuitBreakerState.HALF_OPEN:
            if self.half_open_calls >= self.config.half_open_max_calls:
                raise CircuitOpenError(self.name, 1.0)
            self.half_open_calls += 1

        # Execute function
        try:
            result = func(*args, **kwargs)
            self._record_success()
            return result
        except Exception:
            self._record_failure()
            raise

    async def call_async(self, func: Callable, *args, **kwargs) -> Any:
        """Execute async function with circuit breaker protection.

        Args:
            func: Async function to call
            *args: Positional arguments
            **kwargs: Keyword arguments

        Returns:
            Function result

        Raises:
            CircuitOpenError: If circuit is open
            Exception: Original exception from function
        """
        async with self._lock:
            # Check if should attempt reset
            if self._should_attempt_reset():
                self._half_open()

            # Check state
            if self.state == CircuitBreakerState.OPEN:
                retry_after = (
                    self.config.timeout
                    - (datetime.now() - self.opened_at).total_seconds()
                )
                raise CircuitOpenError(self.name, max(0, retry_after))

            if self.state == CircuitBreakerState.HALF_OPEN:
                if self.half_open_calls >= self.config.half_open_max_calls:
                    raise CircuitOpenError(self.name, 1.0)
                self.half_open_calls += 1

        # Execute function (outside lock)
        try:
            result = await func(*args, **kwargs)
            async with self._lock:
                self._record_success()
            return result
        except Exception:
            async with self._lock:
                self._record_failure()
            raise

    def reset(self):
        """Manually reset circuit to closed state."""
        self.state = CircuitBreakerState.CLOSED
        self.failure_count = 0
        self.success_count = 0
        self.opened_at = None
        self.last_failure_time = None
        self.half_open_calls = 0

    def get_state(self) -> dict:
        """Get current circuit breaker state with comprehensive metrics.

        Returns detailed information about the circuit breaker's current state,
        configuration, and accumulated metrics for monitoring and debugging.

        Returns:
            Dictionary containing:
                - name (str): Circuit breaker identifier
                - state (str): Current state (closed/open/half_open)
                - failure_count (int): Consecutive failures in current state
                - success_count (int): Consecutive successes in half-open state
                - opened_at (str|None): ISO timestamp when circuit opened
                - last_failure (str|None): ISO timestamp of last failure
                - config (dict): Circuit configuration
                    - failure_threshold (int): Failures before opening
                    - success_threshold (int): Successes to close from half-open
                    - timeout (float): Seconds before attempting reset
                - metrics (dict): Accumulated metrics
                    - total_calls (int): Total attempted calls
                    - total_successes (int): Total successful calls
                    - total_failures (int): Total failed calls
                    - total_rejected (int): Calls rejected while open
                    - success_rate (float): Successes / total_calls (0.0-1.0)
                    - failure_rate (float): Failures / total_calls (0.0-1.0)
                    - rejection_rate (float): Rejected / (calls + rejected)

        Example:
            >>> circuit = CircuitBreaker("api_service", failure_threshold=5)
            >>> # ... execute some calls ...
            >>> state = circuit.get_state()
            >>> print(f"State: {state['state']}")
            >>> print(f"Success Rate: {state['metrics']['success_rate']:.2%}")
            >>> print(f"Total Calls: {state['metrics']['total_calls']}")

        Note:
            Rates are calculated as ratios (0.0 to 1.0). Multiply by 100
            for percentage values. All metrics accumulate across the circuit's
            lifetime and persist through state transitions.
        """
        return {
            "name": self.name,
            "state": self.state.value,
            "failure_count": self.failure_count,
            "success_count": self.success_count,
            "opened_at": self.opened_at.isoformat() if self.opened_at else None,
            "last_failure": (
                self.last_failure_time.isoformat() if self.last_failure_time else None
            ),
            "config": {
                "failure_threshold": self.config.failure_threshold,
                "success_threshold": self.config.success_threshold,
                "timeout": self.config.timeout,
            },
            # NEW: Metrics tracking
            "metrics": {
                "total_calls": self.total_calls,
                "total_successes": self.total_successes,
                "total_failures": self.total_failures,
                "total_rejected": self.total_rejected,
                "success_rate": (
                    self.total_successes / self.total_calls
                    if self.total_calls > 0
                    else 0.0
                ),
                "failure_rate": (
                    self.total_failures / self.total_calls
                    if self.total_calls > 0
                    else 0.0
                ),
                "rejection_rate": (
                    self.total_rejected /
                    (self.total_calls + self.total_rejected)
                    if (self.total_calls + self.total_rejected) > 0
                    else 0.0
                ),
            },
        }

    def __enter__(self):
        """Context manager entry."""
        if self._should_attempt_reset():
            self._half_open()

        if self.state == CircuitBreakerState.OPEN:
            retry_after = (
                self.config.timeout -
                (datetime.now() - self.opened_at).total_seconds()
            )
            raise CircuitOpenError(self.name, max(0, retry_after))

        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        """Context manager exit."""
        if exc_type is None:
            self._record_success()
        else:
            self._record_failure()
        return False

    async def __aenter__(self):
        """Async context manager entry."""
        async with self._lock:
            if self._should_attempt_reset():
                self._half_open()

            if self.state == CircuitBreakerState.OPEN:
                retry_after = (
                    self.config.timeout
                    - (datetime.now() - self.opened_at).total_seconds()
                )
                raise CircuitOpenError(self.name, max(0, retry_after))

        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Async context manager exit."""
        async with self._lock:
            if exc_type is None:
                self._record_success()
            else:
                self._record_failure()
        return False
