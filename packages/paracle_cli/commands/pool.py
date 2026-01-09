"""Connection pool management CLI commands."""

import asyncio
import json

import click
from paracle_connection_pool.db_pool import get_db_pool
from paracle_connection_pool.http_pool import get_http_pool
from paracle_connection_pool.monitor import get_pool_monitor


@click.group()
def pool():
    """Manage connection pools."""
    pass


@pool.command()
@click.option(
    "--format",
    type=click.Choice(["text", "json"]),
    default="text",
    help="Output format",
)
def status(format: str):
    """Display connection pool status.

    Shows statistics for HTTP and database connection pools.

    Example:
        paracle pool status
        paracle pool status --format json
    """
    monitor = get_pool_monitor()

    # Get pools
    try:
        http_pool = asyncio.run(get_http_pool())
    except Exception:
        http_pool = None

    try:
        db_pool = get_db_pool()
    except Exception:
        db_pool = None

    # Get stats
    stats = monitor.get_current_stats(http_pool, db_pool)

    if format == "json":
        click.echo(json.dumps(stats.to_dict(), indent=2))
    else:
        click.echo(monitor.summary(http_pool, db_pool))


@pool.command()
def health():
    """Check connection pool health.

    Verifies that pools are functioning correctly.

    Example:
        paracle pool health
    """
    monitor = get_pool_monitor()

    # Get pools
    try:
        http_pool = asyncio.run(get_http_pool())
    except Exception:
        http_pool = None

    try:
        db_pool = get_db_pool()
    except Exception:
        db_pool = None

    # Run health check
    results = monitor.health_check(http_pool, db_pool)

    click.echo("Connection Pool Health Check:")

    if results["healthy"]:
        click.echo("  Status: [OK] Healthy")
    else:
        click.echo("  Status: [FAIL] Unhealthy")

    if results["issues"]:
        click.echo("\n  Issues:")
        for issue in results["issues"]:
            click.secho(f"    • {issue}", fg="red")

    if results["warnings"]:
        click.echo("\n  Warnings:")
        for warning in results["warnings"]:
            click.secho(f"    • {warning}", fg="yellow")

    if not results["issues"] and not results["warnings"]:
        click.echo("  All pools functioning normally")


@pool.command()
@click.confirmation_option(
    prompt="Are you sure you want to reset connection pools?",
)
def reset():
    """Reset connection pools.

    Closes all connections and reinitializes pools.

    Example:
        paracle pool reset
    """
    count = 0

    # Reset HTTP pool
    try:
        http_pool = asyncio.run(get_http_pool())
        asyncio.run(http_pool.close())
        click.echo("[OK] HTTP pool reset")
        count += 1
    except Exception as e:
        click.secho(f"[FAIL] HTTP pool reset failed: {e}", fg="red")

    # Reset database pool
    try:
        db_pool = get_db_pool()
        db_pool.close()
        click.echo("[OK] Database pool reset")
        count += 1
    except Exception as e:
        click.secho(f"[FAIL] Database pool reset failed: {e}", fg="red")

    if count > 0:
        click.echo(f"\n{count} pool(s) reset successfully")


@pool.command()
def config():
    """Display connection pool configuration.

    Shows current pool settings and limits.

    Example:
        paracle pool config
    """
    click.echo("Connection Pool Configuration:")

    # HTTP pool config
    try:
        http_pool = asyncio.run(get_http_pool())
        http_stats = http_pool.stats()
        config = http_stats.get("config", {})

        click.echo("\nHTTP Pool:")
        click.echo(f"  Max Connections: {config.get('max_connections', 'N/A')}")
        click.echo(f"  Max Keepalive: {config.get('max_keepalive', 'N/A')}")
        click.echo(f"  Keepalive Expiry: {config.get('keepalive_expiry', 'N/A')}s")
        click.echo(f"  Timeout: {config.get('timeout', 'N/A')}s")
    except Exception as e:
        click.secho(f"\nHTTP Pool: Not configured ({e})", fg="yellow")

    # Database pool config
    try:
        db_pool = get_db_pool()
        db_stats = db_pool.stats()
        config = db_stats.get("config", {})

        click.echo("\nDatabase Pool:")
        click.echo(f"  Pool Size: {config.get('pool_size', 'N/A')}")
        click.echo(f"  Max Overflow: {config.get('max_overflow', 'N/A')}")
        click.echo(f"  Pool Timeout: {config.get('pool_timeout', 'N/A')}s")
        click.echo(f"  Pool Recycle: {config.get('pool_recycle', 'N/A')}s")
    except Exception as e:
        click.secho(f"\nDatabase Pool: Not configured ({e})", fg="yellow")


@pool.command()
@click.option(
    "--requests",
    type=int,
    default=100,
    help="Number of test requests",
)
@click.option(
    "--concurrent",
    type=int,
    default=10,
    help="Concurrent requests",
)
def benchmark(requests: int, concurrent: int):
    """Benchmark connection pool performance.

    Runs concurrent requests to measure pool efficiency.

    Args:
        requests: Total number of requests
        concurrent: Number of concurrent requests

    Example:
        paracle pool benchmark --requests 1000 --concurrent 50
    """
    import time

    async def run_benchmark():
        click.echo(
            f"Running benchmark: {requests} requests, {concurrent} concurrent..."
        )

        http_pool = await get_http_pool()
        start = time.perf_counter()

        # Simple benchmark - repeated requests
        sem = asyncio.Semaphore(concurrent)

        async def make_request():
            async with sem:
                try:
                    # Simple request to httpbin.org for testing
                    await http_pool.get("https://httpbin.org/delay/0")
                except Exception:
                    pass

        tasks = [make_request() for _ in range(requests)]
        await asyncio.gather(*tasks)

        duration = time.perf_counter() - start

        # Results
        click.echo("\nBenchmark Results:")
        click.echo(f"  Total Requests: {requests}")
        click.echo(f"  Concurrent: {concurrent}")
        click.echo(f"  Total Time: {duration:.2f}s")
        click.echo(f"  Requests/Second: {requests / duration:.0f}")
        click.echo(f"  Avg Time per Request: {duration * 1000 / requests:.1f}ms")

        # Pool stats
        stats = http_pool.stats()
        click.echo(f"\n  Pool Requests: {stats['requests']}")
        click.echo(f"  Pool Errors: {stats['errors']}")
        click.echo(f"  Error Rate: {stats['error_rate'] * 100:.1f}%")

    asyncio.run(run_benchmark())
