"""ResilienceCapability Demo - Circuit Breaker, Retry, and Fallback Patterns.

This example demonstrates how to use ResilienceCapability for reliable
LLM API operations with circuit breaker, retry, and fallback patterns.

Key Benefits:
- Circuit Breaker: Prevents cascading failures
- Retry with Backoff: Handles transient errors
- Fallback: Provides degraded functionality
- Timeout Protection: Prevents hanging operations
- Bulkhead Isolation: Limits concurrent calls

Usage:
    python examples/resilience_demo.py
"""

import asyncio
from datetime import datetime

from paracle_meta.capabilities import (
    CircuitState,
    ResilienceCapability,
    ResilienceConfig,
    RetryStrategy,
)


async def simulate_flaky_api(success_rate: float = 0.5) -> dict:
    """Simulate a flaky API that fails randomly.

    Args:
        success_rate: Probability of success (0.0-1.0).

    Returns:
        API response.

    Raises:
        Exception: Random failures.
    """
    import random

    await asyncio.sleep(0.1)  # Simulate network latency

    if random.random() > success_rate:
        raise Exception("API temporarily unavailable")

    return {
        "response": "LLM completion result",
        "tokens": 150,
        "cost": 0.002,
    }


async def simulate_timeout_api() -> dict:
    """Simulate an API that times out."""
    await asyncio.sleep(10.0)  # Intentionally slow
    return {"response": "Should timeout"}


async def fallback_response() -> dict:
    """Fallback response when main API fails."""
    return {
        "response": "Cached or default response",
        "tokens": 0,
        "cost": 0.0,
        "cached": True,
    }


async def main():
    """Run resilience capability demo."""
    print("=" * 70)
    print("ResilienceCapability Demo")
    print("=" * 70)
    print()

    # Initialize capability
    print("1. Initializing ResilienceCapability...")
    config = ResilienceConfig(
        circuit_breaker_enabled=True,
        failure_threshold=3,  # Open after 3 failures
        recovery_timeout_seconds=5,  # Try recovery after 5s
        success_threshold=2,  # Close after 2 successes
        retry_enabled=True,
        max_retries=3,
        retry_strategy=RetryStrategy.EXPONENTIAL_BACKOFF,
        initial_retry_delay_ms=100,
        max_retry_delay_ms=5000,
        fallback_enabled=True,
        timeout_seconds=2.0,
        bulkhead_enabled=False,
    )
    resilience = ResilienceCapability(config)
    print("   [OK] Circuit breaker: 3 failures threshold")
    print("   [OK] Retry: 3 attempts with exponential backoff")
    print("   [OK] Timeout: 2 seconds")
    print()

    # Demo 1: Successful retry
    print("=" * 70)
    print("2. Demo 1: Retry with Eventual Success")
    print("=" * 70)
    print()

    call_count = 0

    async def flaky_operation_retry() -> dict:
        nonlocal call_count
        call_count += 1
        print(f"   Attempt {call_count}...")
        if call_count < 3:
            raise Exception("Temporary API failure")
        return {"response": "Success after retries", "attempts": call_count}

    result = await resilience.execute_with_resilience(
        operation=flaky_operation_retry,
        operation_name="llm_completion",
    )

    print(f"\n[RESULT] Success: {result.success}")
    print(f"[RESULT] Total attempts: {result.output['attempts']}")
    print(f"[RESULT] Response: {result.output['result']['response']}")
    print()

    # Demo 2: Fallback on failure
    print("=" * 70)
    print("3. Demo 2: Fallback After Max Retries")
    print("=" * 70)
    print()

    async def always_failing() -> dict:
        print("   Main API failed...")
        raise Exception("Permanent API failure")

    result = await resilience.execute_with_resilience(
        operation=always_failing,
        operation_name="failing_api",
        fallback=fallback_response,
    )

    print(f"\n[RESULT] Success: {result.success}")
    print(f"[RESULT] Used fallback: {result.output['used_fallback']}")
    print(f"[RESULT] Response: {result.output['result']['response']}")
    print()

    # Demo 3: Circuit breaker
    print("=" * 70)
    print("4. Demo 3: Circuit Breaker Protection")
    print("=" * 70)
    print()

    async def failing_service() -> dict:
        raise Exception("Service down")

    # Trigger failures to open circuit
    print("Triggering failures to open circuit breaker...")
    for i in range(4):
        result = await resilience.execute_with_resilience(
            operation=failing_service,
            operation_name="unreliable_service",
        )
        state = await resilience.get_circuit_state(
            operation_name="unreliable_service"
        )
        print(
            f"   Call {i+1}: State = {state.output['state']}, "
            f"Failures = {state.output.get('failure_count', 0)}"
        )

    print()

    # Circuit should be OPEN now
    state = await resilience.get_circuit_state(
        operation_name="unreliable_service"
    )
    print(f"[CIRCUIT STATE] {state.output['state'].upper()}")
    print(
        "[INFO] Circuit is OPEN - subsequent calls will be rejected "
        "immediately"
    )
    print()

    # Demo 4: Timeout protection
    print("=" * 70)
    print("5. Demo 4: Timeout Protection")
    print("=" * 70)
    print()

    resilience.config.timeout_seconds = 1.0
    resilience.config.max_retries = 0  # No retries for this demo

    print("Calling slow API with 1s timeout...")
    result = await resilience.execute_with_resilience(
        operation=simulate_timeout_api,
        operation_name="slow_api",
    )

    print(f"\n[RESULT] Success: {result.success}")
    print(f"[RESULT] Error: {result.output.get('error', 'N/A')}")
    print()

    # Demo 5: Metrics
    print("=" * 70)
    print("6. Metrics Summary")
    print("=" * 70)
    print()

    metrics = await resilience.get_metrics()
    print("Overall Metrics:")
    print(f"  - Total calls: {metrics.output['total_calls']}")
    print(f"  - Successful: {metrics.output['successful_calls']}")
    print(f"  - Failed: {metrics.output['failed_calls']}")
    print(f"  - Retried: {metrics.output['retried_calls']}")
    print(f"  - Fallback: {metrics.output['fallback_calls']}")
    print(f"  - Timeouts: {metrics.output['timeouts']}")
    print(f"  - Success rate: {metrics.output['success_rate']:.1%}")
    print()

    print("Circuit Breaker States:")
    for name, state in metrics.output.get("circuit_breakers", {}).items():
        print(f"  - {name}: {state['state'].upper()}")
    print()

    # Demo 6: Reset circuit
    print("=" * 70)
    print("7. Reset Circuit Breaker")
    print("=" * 70)
    print()

    reset_result = await resilience.reset_circuit(
        operation_name="unreliable_service"
    )
    print(f"[RESET] Circuit reset: {reset_result.output['reset']}")

    state = await resilience.get_circuit_state(
        operation_name="unreliable_service"
    )
    print(f"[CIRCUIT STATE] {state.output['state'].upper()}")
    print()

    print("=" * 70)
    print("Demo Complete!")
    print("=" * 70)
    print()
    print("Key Takeaways:")
    print("  1. Retry with backoff handles transient failures")
    print("  2. Circuit breaker prevents cascading failures")
    print("  3. Fallback provides degraded functionality")
    print("  4. Timeout protection prevents hanging operations")
    print(
        "  5. Together, they enable production-ready resilient systems"
    )
    print()


if __name__ == "__main__":
    asyncio.run(main())
