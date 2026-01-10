"""Phase 8: Performance Profiling Example.

Demonstrates how to use Paracle's profiling tools to measure and optimize performance.
"""

import asyncio

from paracle_profiling import (
    PerformanceAnalyzer,
    cached,
    get_cache,
    get_profile_stats,
    profile,
    profile_async,
)


# Example 1: Profile synchronous function
@profile(track_memory=True)
def load_agent_spec(agent_id: str) -> dict:
    """Load agent specification (profiled)."""
    import time

    # Simulate file I/O
    time.sleep(0.1)

    return {
        "id": agent_id,
        "name": f"Agent {agent_id}",
        "provider": "openai",
        "model": "gpt-4",
    }


# Example 2: Profile async function
@profile_async(track_memory=True)
async def execute_workflow(workflow_id: str, inputs: dict) -> dict:
    """Execute workflow (profiled async)."""
    import asyncio

    # Simulate async operation
    await asyncio.sleep(0.2)

    return {
        "workflow_id": workflow_id,
        "status": "completed",
        "outputs": {"result": "success"},
    }


# Example 3: Cache expensive operations
@cached(ttl=60)  # Cache for 1 minute
def get_workflow_definition(workflow_id: str) -> dict:
    """Load workflow definition (cached)."""
    import time

    # Simulate expensive parsing
    time.sleep(0.15)

    return {
        "id": workflow_id,
        "name": f"Workflow {workflow_id}",
        "steps": ["step1", "step2", "step3"],
    }


# Example 4: Combine profiling and caching
@cached(ttl=300)
@profile(track_memory=True)
def load_all_agents() -> list[dict]:
    """Load all agents (cached and profiled)."""
    import time

    # Simulate loading multiple agents
    time.sleep(0.5)

    return [
        {"id": "agent1", "name": "Coder"},
        {"id": "agent2", "name": "Tester"},
        {"id": "agent3", "name": "Reviewer"},
    ]


async def main():
    """Run profiling examples."""
    print("=" * 80)
    print("Phase 8: Performance Profiling Example")
    print("=" * 80)
    print()

    # Example 1: Profile function calls
    print("1. Profiling function calls...")
    for i in range(5):
        load_agent_spec(f"agent{i}")

    stats = get_profile_stats("load_agent_spec")
    if stats:
        print(f"   Calls: {stats['calls']}")
        print(f"   Average: {stats['avg_time']:.3f}s")
        print(f"   P95: {stats['p95_time']:.3f}s")
    else:
        print("   No profiling data collected!")
    print()

    # Example 2: Profile async calls
    print("2. Profiling async calls...")
    for i in range(3):
        await execute_workflow(f"workflow{i}", {"input": "data"})

    stats = get_profile_stats("execute_workflow")
    print(f"   Calls: {stats['calls']}")
    print(f"   Average: {stats['avg_time']:.3f}s")
    print()

    # Example 3: Cache performance
    print("3. Testing cache performance...")

    # First call (cache miss)
    import time

    start = time.time()
    result1 = get_workflow_definition("workflow1")
    miss_time = time.time() - start
    print(f"   First call (cache miss): {miss_time:.3f}s")

    # Second call (cache hit)
    start = time.time()
    result2 = get_workflow_definition("workflow1")
    hit_time = time.time() - start
    print(f"   Second call (cache hit): {hit_time:.3f}s")
    print(f"   Speedup: {miss_time / hit_time:.1f}x")

    # Cache stats
    cache = get_cache()
    cache_stats = cache.get_stats()
    print(f"   Cache hit rate: {cache_stats['hit_rate']}")
    print()

    # Example 4: Combined profiling and caching
    print("4. Combined profiling and caching...")

    # First call
    agents1 = load_all_agents()

    # Second call (cached)
    agents2 = load_all_agents()

    stats = get_profile_stats("load_all_agents")
    print(f"   Total calls: {stats['calls']}")
    print(f"   Average time: {stats['avg_time']:.3f}s")
    print("   Note: Second call much faster due to caching")
    print()

    # Example 5: Performance analysis
    print("5. Performance analysis...")
    analyzer = PerformanceAnalyzer()

    # Get bottlenecks
    bottlenecks = analyzer.analyze_bottlenecks(top_n=5, min_calls=1)
    print(f"   Found {len(bottlenecks)} bottlenecks")

    for report in bottlenecks:
        print(f"   - {report.name}: {report.avg_time:.3f}s avg ({report.severity})")
    print()

    # Generate full report
    print("6. Full performance report:")
    print()
    report = analyzer.generate_report(top_n=10, min_calls=1)
    print(report)

    # Check Phase 8 targets
    print("\n7. Phase 8 Target Validation:")
    targets = analyzer.check_targets()
    print(f"   P95 < 500ms: {'✅' if targets['p95_under_500ms'] else '❌'}")
    print(f"   P99 < 1000ms: {'✅' if targets['p99_under_1000ms'] else '❌'}")
    print(f"   Average < 100ms: {'✅' if targets['avg_under_100ms'] else '❌'}")
    print()

    print("=" * 80)
    print("Profiling complete! See content/docs/technical/performance-profiling-guide.md for more.")
    print("=" * 80)


if __name__ == "__main__":
    asyncio.run(main())
