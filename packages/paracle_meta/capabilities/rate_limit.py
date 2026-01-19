"""RateLimitCapability for preventing API quota exhaustion.

This capability implements token bucket algorithm for rate limiting across
capabilities, providers, and custom dimensions.

Integration Points:
- Uses paracle_core utilities for time handling
- Integrates with paracle_observability for metrics tracking
- Thread-safe implementation for concurrent access

Example:
    >>> from paracle_meta.capabilities import RateLimitCapability, RateLimitConfig
    >>>
    >>> config = RateLimitConfig(
    ...     default_requests_per_minute=60,
    ...     default_burst_size=10
    ... )
    >>> limiter = RateLimitCapability(config)
    >>>
    >>> # Check if request is allowed
    >>> result = await limiter.check_limit(resource="openai/gpt-4")
    >>> if result.output["allowed"]:
    ...     # Proceed with request
    ...     await limiter.consume(resource="openai/gpt-4", tokens=1)
"""

import asyncio
from collections import defaultdict
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from typing import Any

from paracle_core.compat import UTC
from paracle_meta.capabilities.base import BaseCapability, CapabilityResult


@dataclass
class RateLimitConfig:
    """Configuration for rate limiting.

    Attributes:
        default_requests_per_minute: Default rate limit (requests/min).
        default_burst_size: Default burst capacity (tokens).
        enable_metrics: Whether to track rate limit metrics.
        custom_limits: Custom limits per resource {resource: (rpm, burst)}.
        sliding_window_seconds: Time window for rate calculations (default: 60).
    """

    default_requests_per_minute: int = 60
    default_burst_size: int = 10
    enable_metrics: bool = True
    custom_limits: dict[str, tuple[int, int]] = field(default_factory=dict)
    sliding_window_seconds: int = 60


class TokenBucket:
    """Token bucket implementation for rate limiting.

    Thread-safe token bucket algorithm:
    - Tokens refill at a constant rate (refill_rate tokens/second)
    - Bucket has maximum capacity (burst_size)
    - Requests consume tokens
    - If bucket is empty, requests are rate limited
    """

    def __init__(self, refill_rate: float, burst_size: int):
        """Initialize token bucket.

        Args:
            refill_rate: Tokens added per second (requests_per_minute / 60).
            burst_size: Maximum tokens in bucket (burst capacity).
        """
        self.refill_rate = refill_rate
        self.burst_size = burst_size
        self.tokens = float(burst_size)
        self.last_refill = datetime.now(UTC)
        self._lock = asyncio.Lock()

    async def _refill(self) -> None:
        """Refill tokens based on elapsed time."""
        now = datetime.now(UTC)
        elapsed = (now - self.last_refill).total_seconds()

        # Calculate tokens to add
        tokens_to_add = elapsed * self.refill_rate

        # Add tokens, capped at burst_size
        self.tokens = min(self.burst_size, self.tokens + tokens_to_add)
        self.last_refill = now

    async def consume(self, tokens: int = 1) -> bool:
        """Attempt to consume tokens.

        Args:
            tokens: Number of tokens to consume (default: 1).

        Returns:
            True if tokens were consumed, False if insufficient tokens.
        """
        async with self._lock:
            await self._refill()

            if self.tokens >= tokens:
                self.tokens -= tokens
                return True
            return False

    async def peek(self) -> float:
        """Check available tokens without consuming.

        Returns:
            Current number of tokens available.
        """
        async with self._lock:
            await self._refill()
            return self.tokens

    async def wait_time(self, tokens: int = 1) -> float:
        """Calculate time to wait for tokens to be available.

        Args:
            tokens: Number of tokens needed.

        Returns:
            Seconds to wait (0 if tokens already available).
        """
        async with self._lock:
            await self._refill()

            if self.tokens >= tokens:
                return 0.0

            # Calculate tokens needed
            tokens_needed = tokens - self.tokens

            # Calculate time to refill needed tokens
            return tokens_needed / self.refill_rate


class RateLimitCapability(BaseCapability):
    """Rate limiting capability using token bucket algorithm.

    Prevents API quota exhaustion by limiting requests per resource.

    Features:
    - Token bucket algorithm (constant refill rate)
    - Per-resource rate limiting
    - Burst capacity handling
    - Custom limits per resource
    - Metrics tracking (rate limit hits, allowed/denied)
    - Thread-safe for concurrent access

    Example:
        >>> config = RateLimitConfig(
        ...     default_requests_per_minute=60,
        ...     custom_limits={
        ...         "openai/gpt-4": (20, 5),  # 20 RPM, burst of 5
        ...         "anthropic/claude": (100, 20)
        ...     }
        ... )
        >>> limiter = RateLimitCapability(config)
        >>>
        >>> # Check and consume
        >>> result = await limiter.check_and_consume(resource="openai/gpt-4")
        >>> if not result.output["allowed"]:
        ...     wait_time = result.output["retry_after_seconds"]
        ...     await asyncio.sleep(wait_time)
    """

    name = "rate_limit"

    def __init__(self, config: RateLimitConfig | None = None):
        """Initialize rate limiter.

        Args:
            config: Rate limit configuration (uses defaults if None).
        """
        super().__init__(config or RateLimitConfig())
        self._buckets: dict[str, TokenBucket] = {}
        self._metrics: dict[str, dict[str, int]] = defaultdict(
            lambda: {"allowed": 0, "denied": 0, "total": 0}
        )

    def _get_bucket(self, resource: str) -> TokenBucket:
        """Get or create token bucket for resource.

        Args:
            resource: Resource identifier (e.g., "openai/gpt-4").

        Returns:
            TokenBucket for the resource.
        """
        if resource not in self._buckets:
            # Get custom limit or use default
            if resource in self.config.custom_limits:
                rpm, burst = self.config.custom_limits[resource]
            else:
                rpm = self.config.default_requests_per_minute
                burst = self.config.default_burst_size

            # Create bucket (refill_rate = requests per second)
            refill_rate = rpm / 60.0
            self._buckets[resource] = TokenBucket(refill_rate, burst)

        return self._buckets[resource]

    async def check_limit(self, resource: str, tokens: int = 1) -> CapabilityResult:
        """Check if request would be allowed without consuming tokens.

        Args:
            resource: Resource identifier.
            tokens: Number of tokens needed (default: 1).

        Returns:
            CapabilityResult with:
            - allowed: bool (True if enough tokens available)
            - available_tokens: float (current tokens)
            - retry_after_seconds: float (time to wait if denied)
        """
        start = datetime.now(UTC)
        bucket = self._get_bucket(resource)
        available = await bucket.peek()
        allowed = available >= tokens

        if not allowed:
            retry_after = await bucket.wait_time(tokens)
        else:
            retry_after = 0.0

        duration = (datetime.now(UTC) - start).total_seconds() * 1000

        return CapabilityResult(
            capability=self.name,
            success=True,
            output={
                "allowed": allowed,
                "available_tokens": available,
                "retry_after_seconds": retry_after,
                "resource": resource,
                "tokens_requested": tokens,
            },
            duration_ms=duration,
        )

    async def consume(self, resource: str, tokens: int = 1) -> CapabilityResult:
        """Consume tokens from bucket.

        Args:
            resource: Resource identifier.
            tokens: Number of tokens to consume (default: 1).

        Returns:
            CapabilityResult with:
            - consumed: bool (True if tokens consumed)
            - remaining_tokens: float (tokens left after consumption)
        """
        start = datetime.now(UTC)
        bucket = self._get_bucket(resource)
        consumed = await bucket.consume(tokens)

        # Update metrics
        if self.config.enable_metrics:
            self._metrics[resource]["total"] += 1
            if consumed:
                self._metrics[resource]["allowed"] += 1
            else:
                self._metrics[resource]["denied"] += 1

        remaining = await bucket.peek()
        duration = (datetime.now(UTC) - start).total_seconds() * 1000

        return CapabilityResult(
            capability=self.name,
            success=True,
            output={
                "consumed": consumed,
                "remaining_tokens": remaining,
                "resource": resource,
                "tokens_consumed": tokens if consumed else 0,
            },
            duration_ms=duration,
        )

    async def check_and_consume(
        self, resource: str, tokens: int = 1
    ) -> CapabilityResult:
        """Check limit and consume tokens in one operation.

        This is the recommended method for most use cases.

        Args:
            resource: Resource identifier.
            tokens: Number of tokens to consume (default: 1).

        Returns:
            CapabilityResult with:
            - allowed: bool (True if tokens consumed)
            - remaining_tokens: float
            - retry_after_seconds: float (0 if allowed, >0 if denied)
        """
        start = datetime.now(UTC)
        bucket = self._get_bucket(resource)
        allowed = await bucket.consume(tokens)

        # Update metrics
        if self.config.enable_metrics:
            self._metrics[resource]["total"] += 1
            if allowed:
                self._metrics[resource]["allowed"] += 1
            else:
                self._metrics[resource]["denied"] += 1

        remaining = await bucket.peek()

        if not allowed:
            retry_after = await bucket.wait_time(tokens)
        else:
            retry_after = 0.0

        duration = (datetime.now(UTC) - start).total_seconds() * 1000

        return CapabilityResult(
            capability=self.name,
            success=True,
            output={
                "allowed": allowed,
                "remaining_tokens": remaining,
                "retry_after_seconds": retry_after,
                "resource": resource,
                "tokens_consumed": tokens if allowed else 0,
            },
            duration_ms=duration,
        )

    async def get_metrics(self, resource: str | None = None) -> CapabilityResult:
        """Get rate limit metrics.

        Args:
            resource: Specific resource (None for all resources).

        Returns:
            CapabilityResult with metrics:
            - If resource specified: {resource: {allowed, denied, total, rate}}
            - If None: {resource1: {...}, resource2: {...}, ...}
        """
        start = datetime.now(UTC)

        if resource:
            metrics = self._metrics.get(
                resource, {"allowed": 0, "denied": 0, "total": 0}
            )
            total = metrics["total"]
            rate = metrics["allowed"] / total if total > 0 else 1.0

            output = {
                resource: {
                    "allowed": metrics["allowed"],
                    "denied": metrics["denied"],
                    "total": total,
                    "allow_rate": rate,
                }
            }
        else:
            output = {}
            for res, metrics in self._metrics.items():
                total = metrics["total"]
                rate = metrics["allowed"] / total if total > 0 else 1.0
                output[res] = {
                    "allowed": metrics["allowed"],
                    "denied": metrics["denied"],
                    "total": total,
                    "allow_rate": rate,
                }

        duration = (datetime.now(UTC) - start).total_seconds() * 1000

        return CapabilityResult(
            capability=self.name,
            success=True,
            output=output,
            duration_ms=duration,
        )

    async def get_status(self, resource: str) -> CapabilityResult:
        """Get current status of rate limiter for resource.

        Args:
            resource: Resource identifier.

        Returns:
            CapabilityResult with:
            - available_tokens: float
            - capacity: int (burst size)
            - refill_rate: float (tokens/second)
            - estimated_wait_for_one: float (seconds)
        """
        start = datetime.now(UTC)
        bucket = self._get_bucket(resource)
        available = await bucket.peek()
        wait_time = await bucket.wait_time(1)

        duration = (datetime.now(UTC) - start).total_seconds() * 1000

        return CapabilityResult(
            capability=self.name,
            success=True,
            output={
                "resource": resource,
                "available_tokens": available,
                "capacity": bucket.burst_size,
                "refill_rate": bucket.refill_rate,
                "estimated_wait_for_one": wait_time,
            },
            duration_ms=duration,
        )

    async def reset_bucket(self, resource: str) -> CapabilityResult:
        """Reset token bucket for resource (testing/admin).

        Args:
            resource: Resource identifier.

        Returns:
            CapabilityResult indicating success.
        """
        start = datetime.now(UTC)

        if resource in self._buckets:
            bucket = self._buckets[resource]
            async with bucket._lock:
                bucket.tokens = float(bucket.burst_size)
                bucket.last_refill = datetime.now(UTC)

        duration = (datetime.now(UTC) - start).total_seconds() * 1000

        return CapabilityResult(
            capability=self.name,
            success=True,
            output={"resource": resource, "reset": True},
            duration_ms=duration,
        )

    async def reset_metrics(self) -> CapabilityResult:
        """Reset all metrics (testing/admin).

        Returns:
            CapabilityResult indicating success.
        """
        start = datetime.now(UTC)
        self._metrics.clear()
        duration = (datetime.now(UTC) - start).total_seconds() * 1000

        return CapabilityResult(
            capability=self.name,
            success=True,
            output={"metrics_reset": True},
            duration_ms=duration,
        )

    async def execute(self, **kwargs: Any) -> CapabilityResult:
        """Execute rate limit operation with action routing.

        Args:
            **kwargs: Must include 'action' and action-specific parameters.

        Supported actions:
        - check_limit: Check without consuming
        - consume: Consume tokens
        - check_and_consume: Check and consume (recommended)
        - get_metrics: Get rate limit metrics
        - get_status: Get current bucket status
        - reset_bucket: Reset bucket (testing)
        - reset_metrics: Reset metrics (testing)

        Returns:
            CapabilityResult from the executed action.

        Example:
            >>> result = await limiter.execute(
            ...     action="check_and_consume",
            ...     resource="openai/gpt-4",
            ...     tokens=1
            ... )
        """
        action_param = kwargs.pop("action", "check_and_consume")

        action_map = {
            "check_limit": self.check_limit,
            "consume": self.consume,
            "check_and_consume": self.check_and_consume,
            "get_metrics": self.get_metrics,
            "get_status": self.get_status,
            "reset_bucket": self.reset_bucket,
            "reset_metrics": self.reset_metrics,
        }

        if action_param in action_map:
            return await action_map[action_param](**kwargs)

        return CapabilityResult(
            capability=self.name,
            success=False,
            output={"error": f"Unknown action: {action_param}"},
        )
