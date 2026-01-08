"""Example: LLM response caching for cost reduction.

Demonstrates how to use paracle_cache to:
- Cache LLM responses automatically
- Track cache hit rates and cost savings
- Use @cached_llm_call decorator
- Manage cache via CLI commands
"""

import asyncio
import time
from datetime import datetime

from paracle_cache.cache_manager import CacheConfig
from paracle_cache.decorators import cached_llm_call
from paracle_cache.llm_cache import CacheKey, get_llm_cache
from paracle_cache.stats import get_stats_tracker


# Example 1: Manual caching
async def example_manual_caching():
    """Manually cache LLM responses."""
    print("=" * 60)
    print("Example 1: Manual Caching")
    print("=" * 60)

    # Get cache instance
    llm_cache = get_llm_cache(ttl=1800)  # 30 minute TTL

    # Create cache key
    key = CacheKey(
        provider="openai",
        model="gpt-4",
        messages=[
            {"role": "user", "content": "What is the capital of France?"}
        ],
        temperature=0.7,
    )

    # Simulate first call (cache miss)
    print("\n1. First call (cache miss):")
    start = time.perf_counter()

    cached_response = llm_cache.get(key)
    if cached_response is None:
        print("   Cache MISS - calling LLM...")
        # Simulate LLM call
        await asyncio.sleep(0.5)  # Simulate 500ms LLM call
        response = {
            "choices": [{"message": {"content": "Paris"}}],
            "usage": {"total_tokens": 15},
        }
        llm_cache.set(key, response)
    else:
        print("   Cache HIT - using cached response")
        response = cached_response

    duration = (time.perf_counter() - start) * 1000
    print(f"   Response: {response['choices'][0]['message']['content']}")
    print(f"   Time: {duration:.1f}ms")

    # Simulate second call (cache hit)
    print("\n2. Second call (cache hit):")
    start = time.perf_counter()

    cached_response = llm_cache.get(key)
    if cached_response is None:
        print("   Cache MISS - calling LLM...")
        await asyncio.sleep(0.5)
        response = {
            "choices": [{"message": {"content": "Paris"}}],
            "usage": {"total_tokens": 15},
        }
        llm_cache.set(key, response)
    else:
        print("   Cache HIT - using cached response")
        response = cached_response

    duration = (time.perf_counter() - start) * 1000
    print(f"   Response: {response['choices'][0]['message']['content']}")
    print(f"   Time: {duration:.1f}ms")

    # Show cache stats
    print("\n3. Cache Statistics:")
    stats = llm_cache.stats()
    print(f"   Hits: {stats['hits']}")
    print(f"   Misses: {stats['misses']}")
    print(f"   Hit Rate: {stats['hit_rate'] * 100:.1f}%")


# Example 2: Decorator-based caching
@cached_llm_call(ttl=1800)
async def call_llm_with_caching(
    provider: str,
    model: str,
    messages: list[dict[str, str]],
    temperature: float = 0.7,
    max_tokens: int | None = None,
) -> dict:
    """Call LLM with automatic caching."""
    # Simulate LLM call
    print(f"   Calling {provider}/{model}...")
    await asyncio.sleep(0.5)  # Simulate API latency

    return {
        "choices": [{"message": {"content": "The capital of France is Paris."}}],
        "usage": {"total_tokens": 20},
    }


async def example_decorator_caching():
    """Use @cached_llm_call decorator."""
    print("\n" + "=" * 60)
    print("Example 2: Decorator-based Caching")
    print("=" * 60)

    messages = [{"role": "user", "content": "What is the capital of France?"}]

    # First call (miss)
    print("\n1. First call (cache miss):")
    start = time.perf_counter()
    response = await call_llm_with_caching(
        provider="openai",
        model="gpt-4",
        messages=messages,
        temperature=0.7,
    )
    duration = (time.perf_counter() - start) * 1000
    print(f"   Time: {duration:.1f}ms")

    # Second call (hit)
    print("\n2. Second call (cache hit):")
    start = time.perf_counter()
    response = await call_llm_with_caching(
        provider="openai",
        model="gpt-4",
        messages=messages,
        temperature=0.7,
    )
    duration = (time.perf_counter() - start) * 1000
    print(f"   Time: {duration:.1f}ms")
    print(f"   Speedup: {500 / duration:.1f}x faster!")


# Example 3: Statistics tracking
async def example_statistics_tracking():
    """Track cache performance over time."""
    print("\n" + "=" * 60)
    print("Example 3: Statistics Tracking")
    print("=" * 60)

    tracker = get_stats_tracker(max_cache_size=1000)

    # Simulate multiple requests
    print("\nSimulating 10 requests (mix of hits and misses)...")

    for i in range(10):
        # Vary requests to get mix of hits/misses
        is_hit = i >= 3  # First 3 are misses, rest are hits

        if is_hit:
            # Cache hit
            tracker.record_hit(response_time_ms=5.0, tokens=20)
        else:
            # Cache miss
            tracker.record_miss(
                response_time_ms=500.0,
                tokens=20,
                cost=0.0004,  # ~$0.0004 per request
            )

    # Update cache size
    tracker.update_cache_size(3)

    # Show summary
    print("\n" + tracker.summary())

    # Detailed stats
    stats = tracker.get_stats()
    print("\nDetailed Statistics:")
    print(f"  Total Requests: {stats.total_requests}")
    print(f"  Cache Hits: {stats.hits}")
    print(f"  Cache Misses: {stats.misses}")
    print(f"  Hit Rate: {stats.hit_rate * 100:.1f}%")
    print(f"  Speedup: {stats.speedup_factor:.1f}x")
    print(f"  Cost Saved: ${stats.estimated_cost_saved:.4f}")


# Example 4: Configuration
def example_configuration():
    """Configure cache behavior."""
    print("\n" + "=" * 60)
    print("Example 4: Cache Configuration")
    print("=" * 60)

    # Load config from environment
    config = CacheConfig.from_env()

    print("\nCurrent Configuration:")
    print(f"  Enabled: {config.enabled}")
    print(f"  Backend: {config.backend}")
    print(f"  Redis URL: {config.redis_url}")
    print(
        f"  Default TTL: {config.default_ttl}s ({config.default_ttl // 60}min)")
    print(f"  Max Memory Size: {config.max_memory_size}")

    # Custom config
    custom_config = CacheConfig(
        enabled=True,
        backend="redis",
        redis_url="redis://localhost:6379/1",
        default_ttl=7200,  # 2 hours
        max_memory_size=5000,
    )

    print("\nCustom Configuration:")
    print(f"  Backend: {custom_config.backend}")
    print(f"  TTL: {custom_config.default_ttl // 3600}h")
    print(f"  Max Size: {custom_config.max_memory_size}")


# Example 5: CLI integration
def example_cli_usage():
    """Demonstrate CLI commands."""
    print("\n" + "=" * 60)
    print("Example 5: CLI Commands")
    print("=" * 60)

    print("\nAvailable CLI commands:")
    print("  paracle cache stats         - Show cache statistics")
    print("  paracle cache stats --format json  - JSON output")
    print("  paracle cache clear         - Clear all cached responses")
    print("  paracle cache config        - Show configuration")
    print("  paracle cache benchmark     - Benchmark performance")
    print("  paracle cache health        - Check cache health")

    print("\nExample usage:")
    print("  $ paracle cache stats")
    print("  Cache Statistics:")
    print("    Requests: 100 (70 hits, 30 misses)")
    print("    Hit Rate: 70.0%")
    print("    Speedup: 100.0x faster (cached)")
    print("    Cost Saved: $0.0120")


async def main():
    """Run all examples."""
    print("\n" + "=" * 60)
    print("Paracle Cache Examples")
    print("Phase 8: Response Caching")
    print("=" * 60)
    print(f"\nStarted: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")

    # Run examples
    await example_manual_caching()
    await example_decorator_caching()
    await example_statistics_tracking()
    example_configuration()
    example_cli_usage()

    print("\n" + "=" * 60)
    print("All examples completed!")
    print("=" * 60)

    # Final summary
    print("\nKey Takeaways:")
    print("1. Use @cached_llm_call decorator for automatic caching")
    print("2. CacheKey generates semantic keys from prompts/params")
    print("3. Track hit rates and cost savings with CacheStatsTracker")
    print("4. Manage cache via CLI: stats, clear, benchmark, health")
    print("5. Configure via environment variables or CacheConfig")

    print("\nNext Steps:")
    print("- Set PARACLE_CACHE_ENABLED=true")
    print("- Configure Redis: PARACLE_CACHE_BACKEND=redis")
    print("- Monitor with: paracle cache stats")
    print("- Target: >40% hit rate, >30% cost reduction")


if __name__ == "__main__":
    asyncio.run(main())
