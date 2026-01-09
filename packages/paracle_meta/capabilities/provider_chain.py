"""Provider chain with fallback strategies.

This module provides a chain of LLM providers with automatic fallback
when providers fail or become unavailable.

Example:
    >>> from paracle_meta.capabilities.provider_chain import (
    ...     ProviderChain, FallbackStrategy
    ... )
    >>> from paracle_meta.capabilities.providers import (
    ...     AnthropicProvider, OpenAIProvider, MockProvider
    ... )
    >>>
    >>> chain = ProviderChain(
    ...     providers=[
    ...         AnthropicProvider(),
    ...         OpenAIProvider(),
    ...         MockProvider(),  # Last resort
    ...     ],
    ...     strategy=FallbackStrategy.PRIMARY_WITH_FALLBACK
    ... )
    >>> await chain.initialize()
    >>>
    >>> # Will try Anthropic first, then OpenAI, then Mock
    >>> response = await chain.complete(request)
"""

from __future__ import annotations

import asyncio
import random
import time
from collections.abc import AsyncIterator
from dataclasses import dataclass, field
from datetime import datetime, timezone
from enum import Enum
from typing import TYPE_CHECKING, Any

from paracle_meta.capabilities.provider_protocol import (
    BaseProvider,
    CapabilityProvider,
    LLMRequest,
    LLMResponse,
    ProviderError,
    ProviderRateLimitError,
    StreamChunk,
)

if TYPE_CHECKING:
    pass


class FallbackStrategy(Enum):
    """Provider selection and fallback strategies."""

    # Try primary first, fall to others on failure
    PRIMARY_WITH_FALLBACK = "primary_with_fallback"

    # Distribute requests across providers
    ROUND_ROBIN = "round_robin"

    # Use cheapest available provider
    COST_OPTIMIZED = "cost_optimized"

    # Use best model available, fall to cheaper
    QUALITY_FIRST = "quality_first"

    # Random selection (for load balancing)
    RANDOM = "random"


@dataclass
class ProviderMetrics:
    """Metrics for a provider.

    Attributes:
        success_count: Number of successful requests.
        failure_count: Number of failed requests.
        total_latency_ms: Total latency in milliseconds.
        last_failure: Timestamp of last failure.
        last_success: Timestamp of last success.
        consecutive_failures: Number of consecutive failures.
    """

    success_count: int = 0
    failure_count: int = 0
    total_latency_ms: float = 0.0
    last_failure: datetime | None = None
    last_success: datetime | None = None
    consecutive_failures: int = 0

    @property
    def total_requests(self) -> int:
        """Total number of requests."""
        return self.success_count + self.failure_count

    @property
    def success_rate(self) -> float:
        """Success rate (0.0-1.0)."""
        if self.total_requests == 0:
            return 1.0
        return self.success_count / self.total_requests

    @property
    def avg_latency_ms(self) -> float:
        """Average latency in milliseconds."""
        if self.success_count == 0:
            return 0.0
        return self.total_latency_ms / self.success_count


@dataclass
class CircuitBreaker:
    """Circuit breaker for provider health management.

    Prevents hammering failing providers by temporarily excluding them.

    Attributes:
        failure_threshold: Failures before opening circuit.
        reset_timeout_seconds: Seconds before trying again.
        half_open_max_requests: Requests allowed in half-open state.
    """

    failure_threshold: int = 3
    reset_timeout_seconds: float = 60.0
    half_open_max_requests: int = 1

    # Internal state per provider
    _states: dict[str, str] = field(default_factory=dict)  # closed, open, half_open
    _failures: dict[str, int] = field(default_factory=dict)
    _last_failure_time: dict[str, float] = field(default_factory=dict)
    _half_open_requests: dict[str, int] = field(default_factory=dict)

    def is_open(self, provider_name: str) -> bool:
        """Check if circuit is open (provider should not be used)."""
        state = self._states.get(provider_name, "closed")

        if state == "open":
            # Check if reset timeout has passed
            last_failure = self._last_failure_time.get(provider_name, 0)
            if time.time() - last_failure >= self.reset_timeout_seconds:
                self._states[provider_name] = "half_open"
                self._half_open_requests[provider_name] = 0
                return False
            return True

        return False

    def record_success(self, provider_name: str) -> None:
        """Record successful request."""
        state = self._states.get(provider_name, "closed")

        if state == "half_open":
            # Close circuit after successful request in half-open state
            self._states[provider_name] = "closed"
            self._failures[provider_name] = 0

        self._failures[provider_name] = 0

    def record_failure(self, provider_name: str) -> None:
        """Record failed request."""
        self._failures[provider_name] = self._failures.get(provider_name, 0) + 1
        self._last_failure_time[provider_name] = time.time()

        state = self._states.get(provider_name, "closed")

        if state == "half_open":
            # Immediately open circuit on failure in half-open state
            self._states[provider_name] = "open"
        elif self._failures[provider_name] >= self.failure_threshold:
            self._states[provider_name] = "open"

    def get_state(self, provider_name: str) -> str:
        """Get current circuit state."""
        return self._states.get(provider_name, "closed")

    def reset(self, provider_name: str | None = None) -> None:
        """Reset circuit breaker state."""
        if provider_name:
            self._states.pop(provider_name, None)
            self._failures.pop(provider_name, None)
            self._last_failure_time.pop(provider_name, None)
            self._half_open_requests.pop(provider_name, None)
        else:
            self._states.clear()
            self._failures.clear()
            self._last_failure_time.clear()
            self._half_open_requests.clear()


# Cost estimates per 1M tokens (input/output)
PROVIDER_COSTS: dict[str, tuple[float, float]] = {
    "anthropic": (3.0, 15.0),  # Claude Sonnet
    "openai": (2.5, 10.0),  # GPT-4o
    "ollama": (0.0, 0.0),  # Local
    "mock": (0.0, 0.0),
}

# Quality rankings (higher is better)
PROVIDER_QUALITY: dict[str, int] = {
    "anthropic": 95,
    "openai": 90,
    "ollama": 70,
    "mock": 0,
}


class ProviderChainError(Exception):
    """All providers in chain failed."""

    def __init__(self, errors: list[tuple[str, Exception]]):
        self.errors = errors
        providers = ", ".join(name for name, _ in errors)
        super().__init__(f"All providers failed: {providers}")


class ProviderChain(BaseProvider):
    """Chain of providers with automatic fallback.

    Manages multiple LLM providers with configurable fallback strategies.
    Includes circuit breaker pattern and metrics collection.

    Attributes:
        providers: List of providers in fallback order.
        strategy: Provider selection strategy.
        circuit_breaker: Circuit breaker configuration.
    """

    def __init__(
        self,
        providers: list[CapabilityProvider],
        strategy: FallbackStrategy = FallbackStrategy.PRIMARY_WITH_FALLBACK,
        circuit_breaker: CircuitBreaker | None = None,
    ):
        """Initialize provider chain.

        Args:
            providers: List of providers (in priority order for PRIMARY strategy).
            strategy: Provider selection strategy.
            circuit_breaker: Circuit breaker configuration.
        """
        super().__init__()
        self._providers = providers
        self._strategy = strategy
        self._circuit_breaker = circuit_breaker or CircuitBreaker()
        self._metrics: dict[str, ProviderMetrics] = {}
        self._round_robin_index = 0

    @property
    def name(self) -> str:
        """Provider name."""
        return "chain"

    @property
    def providers(self) -> list[CapabilityProvider]:
        """Available providers."""
        return self._providers

    @property
    def strategy(self) -> FallbackStrategy:
        """Current strategy."""
        return self._strategy

    def get_metrics(self, provider_name: str) -> ProviderMetrics:
        """Get metrics for a provider."""
        if provider_name not in self._metrics:
            self._metrics[provider_name] = ProviderMetrics()
        return self._metrics[provider_name]

    async def initialize(self) -> None:
        """Initialize all providers."""
        results = await asyncio.gather(
            *[self._safe_initialize(p) for p in self._providers],
            return_exceptions=True,
        )

        # Count available providers
        available = sum(1 for p in self._providers if p.is_available)

        if available == 0:
            self._set_error("No providers available")
        else:
            self._set_available()

    async def _safe_initialize(self, provider: CapabilityProvider) -> None:
        """Safely initialize a provider."""
        if hasattr(provider, "initialize"):
            await provider.initialize()

    async def complete(self, request: LLMRequest) -> LLMResponse:
        """Complete using provider chain with fallback.

        Args:
            request: The LLM request.

        Returns:
            Response from first successful provider.

        Raises:
            ProviderChainError: If all providers fail.
        """
        providers = self._select_providers()
        errors: list[tuple[str, Exception]] = []

        for provider in providers:
            if self._circuit_breaker.is_open(provider.name):
                continue

            try:
                start_time = time.time()
                response = await provider.complete(request)
                latency_ms = (time.time() - start_time) * 1000

                self._record_success(provider.name, latency_ms)
                return response

            except ProviderRateLimitError as e:
                # Rate limit - definitely try next provider
                self._record_failure(provider.name)
                errors.append((provider.name, e))
                continue

            except ProviderError as e:
                # Provider error - record and try next
                self._record_failure(provider.name)
                errors.append((provider.name, e))

                if not e.recoverable:
                    continue  # Skip to next provider

            except Exception as e:
                self._record_failure(provider.name)
                errors.append((provider.name, e))

        raise ProviderChainError(errors)

    async def stream(self, request: LLMRequest) -> AsyncIterator[StreamChunk]:
        """Stream using provider chain with fallback.

        Args:
            request: The LLM request.

        Yields:
            Stream chunks from first successful provider.

        Raises:
            ProviderChainError: If all providers fail.
        """
        providers = self._select_providers()
        errors: list[tuple[str, Exception]] = []

        for provider in providers:
            if self._circuit_breaker.is_open(provider.name):
                continue

            try:
                start_time = time.time()

                async for chunk in provider.stream(request):
                    yield chunk
                    if chunk.is_final:
                        latency_ms = (time.time() - start_time) * 1000
                        self._record_success(provider.name, latency_ms)

                return  # Successfully completed

            except ProviderError as e:
                self._record_failure(provider.name)
                errors.append((provider.name, e))
                continue

            except Exception as e:
                self._record_failure(provider.name)
                errors.append((provider.name, e))

        raise ProviderChainError(errors)

    def _select_providers(self) -> list[CapabilityProvider]:
        """Select providers based on strategy."""
        available = [p for p in self._providers if p.is_available]

        if not available:
            return self._providers  # Try all anyway

        if self._strategy == FallbackStrategy.PRIMARY_WITH_FALLBACK:
            return available

        if self._strategy == FallbackStrategy.ROUND_ROBIN:
            # Rotate through providers
            n = len(available)
            rotated = (
                available[self._round_robin_index :]
                + available[: self._round_robin_index]
            )
            self._round_robin_index = (self._round_robin_index + 1) % n
            return rotated

        if self._strategy == FallbackStrategy.COST_OPTIMIZED:
            # Sort by cost (cheapest first)
            return sorted(
                available,
                key=lambda p: PROVIDER_COSTS.get(p.name, (100, 100))[0],
            )

        if self._strategy == FallbackStrategy.QUALITY_FIRST:
            # Sort by quality (best first)
            return sorted(
                available,
                key=lambda p: PROVIDER_QUALITY.get(p.name, 0),
                reverse=True,
            )

        if self._strategy == FallbackStrategy.RANDOM:
            shuffled = available.copy()
            random.shuffle(shuffled)
            return shuffled

        return available

    def _record_success(self, provider_name: str, latency_ms: float) -> None:
        """Record successful request."""
        metrics = self.get_metrics(provider_name)
        metrics.success_count += 1
        metrics.total_latency_ms += latency_ms
        metrics.consecutive_failures = 0
        metrics.last_success = datetime.now(timezone.utc)

        self._circuit_breaker.record_success(provider_name)

    def _record_failure(self, provider_name: str) -> None:
        """Record failed request."""
        metrics = self.get_metrics(provider_name)
        metrics.failure_count += 1
        metrics.consecutive_failures += 1
        metrics.last_failure = datetime.now(timezone.utc)

        self._circuit_breaker.record_failure(provider_name)

    async def shutdown(self) -> None:
        """Shutdown all providers."""
        for provider in self._providers:
            if hasattr(provider, "shutdown"):
                await provider.shutdown()
        await super().shutdown()

    def reset_metrics(self) -> None:
        """Reset all metrics."""
        self._metrics.clear()
        self._circuit_breaker.reset()
        self._round_robin_index = 0


class SmartProviderChain(ProviderChain):
    """Provider chain with adaptive strategy selection.

    Automatically adjusts strategy based on provider performance
    and request characteristics.
    """

    def __init__(
        self,
        providers: list[CapabilityProvider],
        **kwargs: Any,
    ):
        """Initialize smart provider chain."""
        super().__init__(providers, **kwargs)
        self._request_count = 0

    async def complete(self, request: LLMRequest) -> LLMResponse:
        """Complete with adaptive strategy."""
        self._request_count += 1

        # Adapt strategy based on conditions
        original_strategy = self._strategy

        # High failure rate on primary? Switch to round robin
        if self._providers:
            primary_metrics = self.get_metrics(self._providers[0].name)
            if (
                primary_metrics.consecutive_failures >= 2
                and self._strategy == FallbackStrategy.PRIMARY_WITH_FALLBACK
            ):
                self._strategy = FallbackStrategy.ROUND_ROBIN

        try:
            return await super().complete(request)
        finally:
            # Restore strategy
            self._strategy = original_strategy
