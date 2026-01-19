"""Production Capabilities Demo - RateLimitCapability + CachingCapability + ObservabilityCapability.

This example demonstrates how to use the three CRITICAL production capabilities
together for optimal LLM API usage: rate limiting, caching, and observability.

Key Benefits:
- RateLimitCapability: Prevents API quota exhaustion
- CachingCapability: Reduces costs via deduplication (30-70% savings)
- ObservabilityCapability: Tracks metrics, costs, and performance

Usage:
    python examples/production_capabilities_demo.py
"""

import asyncio

from paracle_meta.capabilities import (
    CachingCapability,
    CachingConfig,
    ObservabilityCapability,
    ObservabilityConfig,
    RateLimitCapability,
    RateLimitConfig,
)


async def simulate_llm_call(prompt: str, model: str = "gpt-4") -> dict:
    """Simulate an LLM API call with latency.

    Args:
        prompt: User prompt.
        model: Model name.

    Returns:
        Simulated response.
    """
    # Simulate API latency
    await asyncio.sleep(0.1)

    # Simulate response
    return {
        "response": f"Simulated response for: {prompt[:50]}...",
        "model": model,
        "tokens": 150,
        "cost": 0.002,
    }


async def llm_call_with_safeguards(
    prompt: str,
    model: str,
    temperature: float,
    rate_limiter: RateLimitCapability,
    cache: CachingCapability,
    observability: ObservabilityCapability,
) -> dict:
    """Make LLM call with rate limiting, caching, and observability.

    Args:
        prompt: User prompt.
        model: Model name.
        temperature: Temperature parameter.
        rate_limiter: Rate limiting capability.
        cache: Caching capability.
        observability: Observability capability.

    Returns:
        LLM response (from cache or API).
    """
    import time

    start = time.time()

    # Step 1: Generate cache key
    key_result = await cache.generate_key(
        prompt=prompt, model=model, temperature=temperature
    )
    cache_key = key_result.output["key"]

    # Step 2: Check cache
    cache_result = await cache.get(key=cache_key)

    if cache_result.output["found"]:
        # Cache HIT - return immediately
        latency_ms = (time.time() - start) * 1000

        # Track in observability
        await observability.track_capability_usage(
            capability="llm_call",
            operation=f"{model}/cached",
            latency_ms=latency_ms,
            success=True,
            tokens_used=0,
            cost=0.0,  # No cost for cache hit
        )

        return {
            **cache_result.output["value"],
            "cached": True,
            "age_seconds": cache_result.output["age_seconds"],
        }

    # Cache MISS - need to call API

    # Step 3: Check rate limit
    resource = f"{model}"
    rate_check = await rate_limiter.check_and_consume(resource=resource, tokens=1)

    if not rate_check.output["allowed"]:
        # Rate limited - wait and retry
        wait_time = rate_check.output["retry_after_seconds"]
        print(f"  ⚠️ Rate limited. Waiting {wait_time:.2f}s...")
        await asyncio.sleep(wait_time)

        # Retry (should succeed now)
        rate_check = await rate_limiter.check_and_consume(resource=resource, tokens=1)

    # Step 4: Make API call
    response = await simulate_llm_call(prompt, model)
    latency_ms = (time.time() - start) * 1000

    # Step 5: Cache response
    await cache.set(key=cache_key, value=response, ttl=3600)

    # Step 6: Track in observability
    await observability.track_llm_call(
        provider="openai",
        model=model,
        prompt_tokens=response["tokens"],
        completion_tokens=response["tokens"],
        latency_ms=latency_ms,
        success=True,
        cost=response["cost"],
    )

    return {**response, "cached": False}


async def main():
    """Run production capabilities demo."""
    print("=" * 70)
    print("Production Capabilities Demo")
    print("=" * 70)
    print()

    # Initialize capabilities
    print("1. Initializing capabilities...")

    # Rate limiter: 10 requests per minute for gpt-4
    rate_limiter = RateLimitCapability(
        RateLimitConfig(
            default_requests_per_minute=60,
            custom_limits={
                "gpt-4": (10, 3),  # 10 RPM, burst of 3
                "gpt-3.5-turbo": (60, 10),  # 60 RPM, burst of 10
            },
        )
    )

    # Cache: 50MB memory, 1 hour TTL
    cache = CachingCapability(
        CachingConfig(
            cache_type="memory",
            default_ttl_seconds=3600,
            max_cache_size_mb=50,
        )
    )

    # Observability: Track everything
    observability = ObservabilityCapability(
        ObservabilityConfig(
            enable_prometheus=True,
            enable_cost_tracking=True,
            cost_budget_daily=10.0,  # $10/day budget
        )
    )

    print("   [OK] Rate limiter: 10 RPM for gpt-4, burst of 3")
    print("   [OK] Cache: 50MB, 1 hour TTL")
    print("   [OK] Observability: Cost tracking, metrics")
    print()

    # Simulate requests
    print("2. Simulating LLM requests...")
    print()

    prompts = [
        "What is the capital of France?",  # First request
        "What is the capital of France?",  # Duplicate (cache hit)
        "What is Python?",  # New request
        "What is the capital of France?",  # Duplicate (cache hit)
        "Explain machine learning",  # New request
        "What is Python?",  # Duplicate (cache hit)
    ]

    for i, prompt in enumerate(prompts, 1):
        print(f"Request {i}: {prompt[:40]}...")

        response = await llm_call_with_safeguards(
            prompt=prompt,
            model="gpt-4",
            temperature=0.7,
            rate_limiter=rate_limiter,
            cache=cache,
            observability=observability,
        )

        if response["cached"]:
            print(
                f"  [CACHE HIT] Age: {response['age_seconds']:.1f}s - "
                f"No API call, $0 cost"
            )
        else:
            print(
                f"  [CACHE MISS] API call made, ${response['cost']:.4f} cost"
            )

        print()

    # Show metrics
    print("=" * 70)
    print("3. Metrics Summary")
    print("=" * 70)
    print()

    # Cache metrics
    cache_metrics = await cache.get_metrics()
    print("Cache Metrics:")
    print(f"  - Hit rate: {cache_metrics.output['hit_rate']:.1%}")
    print(f"  - Hits: {cache_metrics.output['hits']}")
    print(f"  - Misses: {cache_metrics.output['misses']}")
    print(
        f"  - Cache utilization: "
        f"{cache_metrics.output['cache_stats']['utilization']:.1%}"
    )
    print()

    # Rate limit metrics
    rate_metrics = await rate_limiter.get_metrics(resource="gpt-4")
    print("Rate Limit Metrics (gpt-4):")
    print(f"  - Total requests: {rate_metrics.output['gpt-4']['total']}")
    print(f"  - Allowed: {rate_metrics.output['gpt-4']['allowed']}")
    print(f"  - Denied: {rate_metrics.output['gpt-4']['denied']}")
    print(
        f"  - Allow rate: {rate_metrics.output['gpt-4']['allow_rate']:.1%}"
    )
    print()

    # Observability metrics
    obs_metrics = await observability.get_summary()
    print("Observability Metrics:")
    print(f"  - Total cost: ${obs_metrics.output['cost']['total_cost']:.4f}")
    print(
        f"  - Success rate: {obs_metrics.output['quality']['success_rate']:.1%}"
    )
    print(
        f"  - Avg latency: {obs_metrics.output['performance']['avg_latency']:.3f}s"
    )
    print(
        f"  - Health score: {obs_metrics.output['health_score']:.2f}/100"
    )
    print()

    # Calculate savings
    total_requests = len(prompts)
    cache_hits = cache_metrics.output["hits"]
    cost_per_request = 0.002  # $0.002 per request
    cost_without_cache = total_requests * cost_per_request
    actual_cost = obs_metrics.output["cost"]["total_cost"]
    savings = cost_without_cache - actual_cost
    savings_pct = (savings / cost_without_cache * 100) if cost_without_cache > 0 else 0

    print("=" * 70)
    print("4. Cost Savings Analysis")
    print("=" * 70)
    print()
    print(f"Total requests: {total_requests}")
    print(f"Cache hits: {cache_hits} ({cache_hits/total_requests:.1%})")
    print(f"Cost without cache: ${cost_without_cache:.4f}")
    print(f"Actual cost: ${actual_cost:.4f}")
    print(f"Savings: ${savings:.4f} ({savings_pct:.1f}%)")
    print()

    print("=" * 70)
    print("Demo Complete!")
    print("=" * 70)
    print()
    print("Key Takeaways:")
    print("  1. Cache hits = instant response + $0 cost")
    print("  2. Rate limiting prevents quota exhaustion")
    print("  3. Observability provides complete visibility")
    print("  4. Together, they enable production-ready LLM deployments")
    print()


if __name__ == "__main__":
    asyncio.run(main())
