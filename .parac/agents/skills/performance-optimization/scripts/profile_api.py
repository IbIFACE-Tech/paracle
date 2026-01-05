#!/usr/bin/env python3
"""Profile API endpoint performance.

Usage:
    python profile_api.py http://localhost:8000/agents
    python profile_api.py http://localhost:8000/agents --requests 100
"""

import asyncio
import statistics
import time

import httpx


async def measure_request(client: httpx.AsyncClient, url: str) -> float:
    """Measure single request duration."""
    start = time.time()
    try:
        response = await client.get(url)
        response.raise_for_status()
        return time.time() - start
    except Exception as e:
        print(f"Request failed: {e}")
        return -1


async def profile_endpoint(url: str, num_requests: int = 100):
    """Profile endpoint with multiple requests."""

    print(f"🔍 Profiling: {url}")
    print(f"📊 Requests: {num_requests}\n")

    async with httpx.AsyncClient() as client:
        # Warmup
        await measure_request(client, url)

        # Measure
        durations = []
        for i in range(num_requests):
            duration = await measure_request(client, url)
            if duration > 0:
                durations.append(duration * 1000)  # Convert to ms

            if (i + 1) % 10 == 0:
                print(f"  Progress: {i + 1}/{num_requests}")

    if not durations:
        print("❌ No successful requests")
        return

    # Calculate statistics
    durations.sort()

    print("\n📈 Results:")
    print(f"  Mean:   {statistics.mean(durations):.2f}ms")
    print(f"  Median: {statistics.median(durations):.2f}ms")
    print(f"  Min:    {min(durations):.2f}ms")
    print(f"  Max:    {max(durations):.2f}ms")
    print(f"  p50:    {durations[int(len(durations) * 0.50)]:.2f}ms")
    print(f"  p95:    {durations[int(len(durations) * 0.95)]:.2f}ms")
    print(f"  p99:    {durations[int(len(durations) * 0.99)]:.2f}ms")

    # Check target
    p95 = durations[int(len(durations) * 0.95)]
    if p95 < 500:
        print(f"\n✅ p95 ({p95:.2f}ms) meets target (<500ms)")
    else:
        print(f"\n⚠️  p95 ({p95:.2f}ms) exceeds target (500ms)")

if __name__ == "__main__":
    import sys

    if len(sys.argv) < 2:
        print("Usage: python profile_api.py URL [--requests N]")
        sys.exit(1)

    url = sys.argv[1]
    num_requests = 100

    if "--requests" in sys.argv:
        idx = sys.argv.index("--requests")
        num_requests = int(sys.argv[idx + 1])

    asyncio.run(profile_endpoint(url, num_requests))
