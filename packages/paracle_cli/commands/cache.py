"""Cache management CLI commands."""

import json

import click
from paracle_cache.cache_manager import get_cache_manager
from paracle_cache.llm_cache import get_llm_cache
from paracle_cache.stats import get_stats_tracker


@click.group()
def cache():
    """Manage LLM response cache."""
    pass


@cache.command()
@click.option(
    "--format",
    type=click.Choice(["text", "json"]),
    default="text",
    help="Output format",
)
def stats(format: str):
    """Display cache statistics.

    Shows hit/miss rates, cost savings, and performance metrics.

    Example:
        paracle cache stats
        paracle cache stats --format json
    """
    tracker = get_stats_tracker()
    stats = tracker.get_stats()

    if format == "json":
        click.echo(json.dumps(stats.to_dict(), indent=2))
    else:
        click.echo(tracker.summary())
        click.echo()

        # Additional details
        if stats.avg_cached_time_ms > 0:
            click.echo(
                f"Average cached response time: {stats.avg_cached_time_ms:.1f}ms"
            )

        if stats.avg_uncached_time_ms > 0:
            click.echo(
                f"Average uncached response time: {stats.avg_uncached_time_ms:.1f}ms"
            )

        if stats.cached_tokens > 0:
            click.echo(f"Cached tokens: {stats.cached_tokens:,}")

        if stats.uncached_tokens > 0:
            click.echo(f"Uncached tokens: {stats.uncached_tokens:,}")


@cache.command()
@click.confirmation_option(
    prompt="Are you sure you want to clear the cache?",
)
def clear():
    """Clear all cached responses.

    Removes all entries from the cache and resets statistics.

    Example:
        paracle cache clear
    """
    llm_cache = get_llm_cache()
    count = llm_cache.clear()

    # Reset stats
    tracker = get_stats_tracker()
    tracker.reset()

    click.echo(f"[OK] Cleared {count} cached responses")


@cache.command()
def config():
    """Display cache configuration.

    Shows current cache backend, TTL, and other settings.

    Example:
        paracle cache config
    """
    cache_manager = get_cache_manager()
    config = cache_manager.config

    click.echo("Cache Configuration:")
    click.echo(f"  Enabled: {config.enabled}")
    click.echo(f"  Backend: {config.backend}")

    if config.backend in ("redis", "valkey"):
        click.echo(f"  Redis URL: {config.redis_url}")

    click.echo(f"  Default TTL: {config.default_ttl}s ({config.default_ttl // 60}min)")
    click.echo(f"  Max Memory Size: {config.max_memory_size}")
    click.echo(f"  Key Prefix: {config.key_prefix}")


@cache.command()
@click.option(
    "--requests",
    type=int,
    default=100,
    help="Number of test requests",
)
def benchmark(requests: int):
    """Benchmark cache performance.

    Runs a series of test requests to measure cache performance.

    Args:
        requests: Number of requests to run

    Example:
        paracle cache benchmark --requests 1000
    """
    import time

    from paracle_cache.llm_cache import CacheKey

    llm_cache = get_llm_cache()
    get_stats_tracker()

    click.echo(f"Running benchmark with {requests} requests...")

    # Generate test data
    test_key = CacheKey(
        provider="openai",
        model="gpt-4",
        messages=[{"role": "user", "content": "Hello, world!"}],
        temperature=0.7,
    )

    test_response = {
        "choices": [{"message": {"content": "Hello! How can I help you?"}}],
        "usage": {"total_tokens": 25},
    }

    # Warm up cache
    llm_cache.set(test_key, test_response)

    # Run benchmark
    start = time.perf_counter()
    hits = 0

    for _i in range(requests):
        result = llm_cache.get(test_key)
        if result is not None:
            hits += 1

    duration = (time.perf_counter() - start) * 1000  # ms

    # Results
    click.echo()
    click.echo("Benchmark Results:")
    click.echo(f"  Total Requests: {requests}")
    click.echo(f"  Cache Hits: {hits}")
    click.echo(f"  Total Time: {duration:.1f}ms")
    click.echo(f"  Avg Time per Request: {duration / requests:.3f}ms")
    click.echo(f"  Requests per Second: {requests / (duration / 1000):.0f}")


@cache.command()
def health():
    """Check cache health and connectivity.

    Verifies that the cache backend is accessible and functioning.

    Example:
        paracle cache health
    """
    cache_manager = get_cache_manager()
    config = cache_manager.config

    click.echo("Cache Health Check:")
    click.echo(f"  Backend: {config.backend}")

    try:
        # Test write
        test_key = "health_check"
        test_value = {"test": "data"}

        cache_manager.set(test_key, test_value, ttl=10)

        # Test read
        result = cache_manager.get(test_key)

        if result == test_value:
            click.echo("  Status: [OK] Healthy")

            # Cleanup
            cache_manager.delete(test_key)
        else:
            click.echo("  Status: [FAIL] Unhealthy (read mismatch)")
            click.secho("  Cache is not returning expected values", fg="red")

    except Exception as e:
        click.echo("  Status: [FAIL] Unhealthy")
        click.secho(f"  Error: {e}", fg="red")
