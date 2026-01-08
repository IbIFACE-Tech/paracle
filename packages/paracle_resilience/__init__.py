"""Paracle Resilience - Circuit breakers, fallback strategies, and fault tolerance."""

from paracle_resilience.circuit_breaker import (
    CircuitBreaker,
    CircuitBreakerConfig,
    CircuitBreakerError,
    CircuitBreakerState,
    CircuitOpenError,
)
from paracle_resilience.fallback import (
    CachedResponseFallback,
    DefaultValueFallback,
    DegradedServiceFallback,
    FallbackChain,
    FallbackError,
    FallbackStrategy,
    RetryFallback,
)

__all__ = [
    "CircuitBreaker",
    "CircuitBreakerState",
    "CircuitBreakerConfig",
    "CircuitBreakerError",
    "CircuitOpenError",
    "FallbackStrategy",
    "CachedResponseFallback",
    "DefaultValueFallback",
    "RetryFallback",
    "DegradedServiceFallback",
    "FallbackChain",
    "FallbackError",
]
