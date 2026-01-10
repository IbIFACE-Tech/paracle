"""Performance Benchmarking Examples for Paracle.

Phase 10 - Governance & v1.0 Release: Performance Benchmarking

This example demonstrates:
1. Basic benchmarking with decorator syntax
2. Suite organization (grouping benchmarks)
3. Warmup iterations for JIT optimization
4. Regression threshold configuration
5. Filtering benchmarks by pattern
6. Baseline comparison and reporting
7. Memory tracking (optional)
8. CI/CD integration patterns
9. Custom benchmark metrics

Run this example:
    python content/examples/26_performance_benchmarking.py

    Or use the CLI:
    paracle benchmark run --verbose
    paracle benchmark run --baseline .benchmarks/baseline.json
    paracle benchmark run --filter "cache"
    paracle benchmark compare baseline.json results.json
"""

import time
from pathlib import Path

from paracle_profiling.benchmark import (
    BenchmarkStatus,
    BenchmarkSuite,
)


# ============================================================================
# DEMO 1: Basic Benchmarking
# ============================================================================
def demo_1_basic_benchmarking():
    """Demo 1: Create and run a simple benchmark."""
    print("\n" + "=" * 70)
    print("DEMO 1: Basic Benchmarking")
    print("=" * 70)

    # Create a suite
    suite = BenchmarkSuite("demo-basic")

    # Define benchmarks using decorator
    @suite.benchmark(iterations=1000, description="Simple arithmetic")
    def bench_arithmetic():
        result = 2 + 2

    @suite.benchmark(iterations=500, description="String concatenation")
    def bench_string_concat():
        result = "Hello" + " " + "World"

    @suite.benchmark(iterations=100, description="List comprehension")
    def bench_list_comp():
        result = [x * 2 for x in range(100)]

    # Run benchmarks
    print("Running 3 basic benchmarks...")
    results = suite.run()

    # Display results
    print(f"\nSuite: {results.suite_name}")
    print(f"Total: {results.total_benchmarks} benchmarks")
    print(f"Passed: {results.passed}, Failed: {results.failed}")
    print()

    for result in results.results:
        print(f"✓ {result.name}")
        print(
            f"  Mean: {result.mean_ms:.4f}ms | Median: {result.median_ms:.4f}ms")
        print(f"  P95: {result.p95_ms:.4f}ms | P99: {result.p99_ms:.4f}ms")
        print()


# ============================================================================
# DEMO 2: Warmup Iterations
# ============================================================================
def demo_2_warmup_iterations():
    """Demo 2: Use warmup iterations for JIT optimization."""
    print("\n" + "=" * 70)
    print("DEMO 2: Warmup Iterations")
    print("=" * 70)

    suite = BenchmarkSuite("demo-warmup")

    # Without warmup - may include JIT compilation time
    @suite.benchmark(iterations=1000, warmup=0, description="No warmup")
    def bench_no_warmup():
        result = sum(range(1000))

    # With warmup - JIT optimized
    @suite.benchmark(iterations=1000, warmup=100, description="With warmup")
    def bench_with_warmup():
        result = sum(range(1000))

    print("Running benchmarks with and without warmup...")
    results = suite.run()

    print("\nComparison:")
    for result in results.results:
        print(f"{result.name}: Mean = {result.mean_ms:.4f}ms")


# ============================================================================
# DEMO 3: Regression Detection
# ============================================================================
def demo_3_regression_detection():
    """Demo 3: Detect performance regressions against baseline."""
    print("\n" + "=" * 70)
    print("DEMO 3: Regression Detection")
    print("=" * 70)

    # Create suite with regression threshold
    suite = BenchmarkSuite("demo-regression", regression_threshold=0.15)  # 15%

    @suite.benchmark(iterations=1000)
    def bench_operation():
        time.sleep(0.0001)  # 0.1ms

    # Run and create "baseline"
    print("Creating baseline...")
    baseline_results = suite.run()
    baseline_file = Path(".benchmarks/demo_baseline.json")
    baseline_file.parent.mkdir(exist_ok=True)
    suite.save_results(str(baseline_file))
    print(f"Baseline saved: {baseline_file}")

    # Simulate slower performance (regression)
    suite2 = BenchmarkSuite("demo-regression", regression_threshold=0.15)

    @suite2.benchmark(iterations=1000)
    def bench_operation_slow():
        time.sleep(0.00015)  # 0.15ms (50% slower!)

    # Load baseline and detect regression
    print("\nRunning with simulated regression...")
    suite2.load_baseline(str(baseline_file))
    results = suite2.run()

    # Check for regressions
    print("\nRegression Analysis:")
    for result in results.results:
        if result.status == BenchmarkStatus.REGRESSION:
            print("⚠️  REGRESSION DETECTED!")
            print(f"   Benchmark: {result.name}")
            print(f"   Current: {result.mean_ms:.4f}ms")
            print(f"   Baseline: {result.baseline_mean_ms:.4f}ms")
            print(f"   Regression: +{result.regression_percent:.1f}%")
        elif result.status == BenchmarkStatus.IMPROVEMENT:
            print("↗️  IMPROVEMENT!")
            print(f"   Benchmark: {result.name}")
            print(f"   Improvement: {-result.regression_percent:.1f}%")


# ============================================================================
# DEMO 4: Suite Organization
# ============================================================================
def demo_4_suite_organization():
    """Demo 4: Organize benchmarks into suites by category."""
    print("\n" + "=" * 70)
    print("DEMO 4: Suite Organization")
    print("=" * 70)

    # Core operations suite
    core_suite = BenchmarkSuite("core-operations")

    @core_suite.benchmark(iterations=5000)
    def bench_core_parse():
        data = {"key": "value"}

    @core_suite.benchmark(iterations=5000)
    def bench_core_validate():
        valid = isinstance("test", str)

    # API operations suite
    api_suite = BenchmarkSuite("api-operations")

    @api_suite.benchmark(iterations=100)
    def bench_api_serialize():
        import json

        data = {"users": [{"id": i, "name": f"User {i}"} for i in range(100)]}
        json.dumps(data)

    @api_suite.benchmark(iterations=100)
    def bench_api_deserialize():
        import json

        json_str = '{"users": [{"id": 1, "name": "User 1"}]}'
        json.loads(json_str)

    # Run each suite
    print("Running Core Operations suite...")
    core_results = core_suite.run()
    print(f"  {core_results.passed}/{core_results.total_benchmarks} passed")

    print("\nRunning API Operations suite...")
    api_results = api_suite.run()
    print(f"  {api_results.passed}/{api_results.total_benchmarks} passed")


# ============================================================================
# DEMO 5: Filtering Benchmarks
# ============================================================================
def demo_5_filtering_benchmarks():
    """Demo 5: Filter benchmarks by pattern matching."""
    print("\n" + "=" * 70)
    print("DEMO 5: Filtering Benchmarks")
    print("=" * 70)

    suite = BenchmarkSuite("demo-filtering")

    @suite.benchmark(iterations=1000)
    def bench_cache_set():
        cache = {"key": "value"}

    @suite.benchmark(iterations=1000)
    def bench_cache_get():
        cache = {"key": "value"}
        value = cache.get("key")

    @suite.benchmark(iterations=1000)
    def bench_db_query():
        # Simulate query
        pass

    @suite.benchmark(iterations=1000)
    def bench_db_insert():
        # Simulate insert
        pass

    # Run all
    print("Running ALL benchmarks:")
    results_all = suite.run()
    print(f"  Ran {len(results_all.results)} benchmarks")

    # Run only cache benchmarks
    print("\nRunning only 'cache' benchmarks:")
    results_cache = suite.run(filter_pattern="cache")
    print(f"  Ran {len(results_cache.results)} benchmarks")
    for r in results_cache.results:
        print(f"    - {r.name}")

    # Run only db benchmarks
    print("\nRunning only 'db' benchmarks:")
    results_db = suite.run(filter_pattern="db")
    print(f"  Ran {len(results_db.results)} benchmarks")
    for r in results_db.results:
        print(f"    - {r.name}")


# ============================================================================
# DEMO 6: Benchmark Real Paracle Operations
# ============================================================================
def demo_6_real_paracle_operations():
    """Demo 6: Benchmark actual Paracle operations."""
    print("\n" + "=" * 70)
    print("DEMO 6: Real Paracle Operations")
    print("=" * 70)

    suite = BenchmarkSuite("paracle-operations")

    # Benchmark 1: Agent Spec Creation
    try:
        from paracle_domain.agent import AgentSpec

        @suite.benchmark(
            iterations=1000, warmup=10, description="Create AgentSpec model"
        )
        def bench_agent_spec():
            spec = AgentSpec(
                agent_id="test-agent",
                name="Test Agent",
                model="gpt-4",
                temperature=0.7,
                system_prompt="You are helpful.",
            )

    except ImportError:
        print("  ⚠️  paracle_domain not available")

    # Benchmark 2: Cache Operations
    try:
        from paracle_profiling import CacheManager

        cache = CacheManager(max_size=100)

        @suite.benchmark(
            iterations=5000, warmup=100, description="Cache set operation"
        )
        def bench_cache_set_real():
            cache.set("key", {"data": "value"})

        @suite.benchmark(
            iterations=5000, warmup=100, description="Cache get operation"
        )
        def bench_cache_get_real():
            cache.get("key")

    except ImportError:
        print("  ⚠️  CacheManager not available")

    # Benchmark 3: Agent Discovery
    try:
        from paracle_core.parac.agent_discovery import AgentDiscovery

        parac_dir = Path.cwd() / ".parac"
        if parac_dir.exists():

            @suite.benchmark(
                iterations=50, warmup=2, description="Agent discovery scan"
            )
            def bench_agent_discovery_real():
                discovery = AgentDiscovery(parac_dir)
                agents = discovery.discover_agents()

    except (ImportError, FileNotFoundError):
        print("  ⚠️  Agent discovery not available")

    if suite._benchmarks:
        print(f"Running {len(suite._benchmarks)} Paracle benchmarks...")
        results = suite.run()

        print("\nResults:")
        for result in results.results:
            print(f"✓ {result.description or result.name}")
            print(
                f"  Mean: {result.mean_ms:.4f}ms | P95: {result.p95_ms:.4f}ms | Iterations: {result.iterations}"
            )
    else:
        print("No Paracle operations available for benchmarking.")


# ============================================================================
# DEMO 7: Timeout Protection
# ============================================================================
def demo_7_timeout_protection():
    """Demo 7: Protect against long-running benchmarks with timeout."""
    print("\n" + "=" * 70)
    print("DEMO 7: Timeout Protection")
    print("=" * 70)

    suite = BenchmarkSuite("demo-timeout")

    @suite.benchmark(iterations=10, timeout_seconds=1)
    def bench_with_timeout():
        time.sleep(0.05)  # 50ms - OK

    @suite.benchmark(iterations=10, timeout_seconds=0.1)
    def bench_too_slow():
        time.sleep(0.2)  # 200ms - TIMEOUT!

    print("Running benchmarks with timeout...")
    results = suite.run()

    print("\nResults:")
    for result in results.results:
        if result.status == BenchmarkStatus.FAILED:
            print(f"⏱️  {result.name} - TIMEOUT")
            print(f"   Error: {result.error}")
        else:
            print(f"✓ {result.name} - PASSED ({result.mean_ms:.2f}ms)")


# ============================================================================
# DEMO 8: Baseline File Management
# ============================================================================
def demo_8_baseline_management():
    """Demo 8: Save, load, and compare baselines."""
    print("\n" + "=" * 70)
    print("DEMO 8: Baseline File Management")
    print("=" * 70)

    suite = BenchmarkSuite("demo-baseline")

    @suite.benchmark(iterations=1000)
    def bench_operation():
        result = sum(range(100))

    # Run and save as baseline
    print("1. Running benchmarks...")
    results = suite.run()

    baseline_file = Path(".benchmarks/demo_baseline_v1.json")
    baseline_file.parent.mkdir(exist_ok=True)

    print(f"2. Saving baseline to {baseline_file}...")
    suite.save_results(str(baseline_file))

    # Load baseline in new suite
    suite2 = BenchmarkSuite("demo-baseline")

    @suite2.benchmark(iterations=1000)
    def bench_operation_v2():
        result = sum(range(100))

    print("3. Loading baseline...")
    if suite2.load_baseline(str(baseline_file)):
        print("   ✓ Baseline loaded successfully")

        print("4. Running benchmarks with comparison...")
        results2 = suite2.run()

        print("\n5. Comparison:")
        for result in results2.results:
            if result.baseline_mean_ms:
                delta_pct = result.regression_percent or 0
                print(f"   {result.name}:")
                print(f"     Current:  {result.mean_ms:.4f}ms")
                print(f"     Baseline: {result.baseline_mean_ms:.4f}ms")
                print(f"     Delta:    {delta_pct:+.1f}%")


# ============================================================================
# DEMO 9: CI/CD Integration Pattern
# ============================================================================
def demo_9_cicd_integration():
    """Demo 9: Demonstrate CI/CD integration patterns."""
    print("\n" + "=" * 70)
    print("DEMO 9: CI/CD Integration Pattern")
    print("=" * 70)

    # Simulate CI environment
    suite = BenchmarkSuite("ci-benchmarks", regression_threshold=0.15)

    @suite.benchmark(iterations=500)
    def bench_ci_operation():
        time.sleep(0.001)  # 1ms

    # Step 1: Load baseline from CI artifact
    baseline_file = Path(".benchmarks/ci_baseline.json")
    print("Step 1: Loading baseline from CI artifact...")

    if baseline_file.exists():
        suite.load_baseline(str(baseline_file))
        print("   ✓ Baseline loaded")
    else:
        print("   ⚠️  No baseline found (first run)")

    # Step 2: Run benchmarks
    print("\nStep 2: Running benchmarks...")
    results = suite.run()

    # Step 3: Check for regressions
    print("\nStep 3: Checking for regressions...")
    has_regression = any(
        r.status == BenchmarkStatus.REGRESSION for r in results.results
    )

    if has_regression:
        print("   ❌ REGRESSION DETECTED - Build should FAIL")
        print("   Exit code: 1")
        # In CI: sys.exit(1)
    else:
        print("   ✅ No regressions - Build should PASS")
        print("   Exit code: 0")

    # Step 4: Save results for next run
    results_file = Path(".benchmarks/ci_results.json")
    results_file.parent.mkdir(exist_ok=True)
    suite.save_results(str(results_file))
    print(f"\nStep 4: Results saved to {results_file}")

    # Step 5: Update baseline (only on main branch)
    is_main_branch = True  # Simulate
    if is_main_branch and not has_regression:
        print("\nStep 5: Updating baseline (main branch)...")
        suite.save_results(str(baseline_file))
        print(f"   ✓ Baseline updated: {baseline_file}")


# ============================================================================
# Main Demo Runner
# ============================================================================
def main():
    """Run all demos."""
    print("=" * 70)
    print("PARACLE PERFORMANCE BENCHMARKING EXAMPLES")
    print("=" * 70)
    print()
    print("This demo shows:")
    print("  1. Basic benchmarking with decorator syntax")
    print("  2. Warmup iterations for JIT optimization")
    print("  3. Regression detection against baseline")
    print("  4. Suite organization by category")
    print("  5. Filtering benchmarks by pattern")
    print("  6. Benchmarking real Paracle operations")
    print("  7. Timeout protection for long benchmarks")
    print("  8. Baseline file save/load/compare")
    print("  9. CI/CD integration pattern")
    print()

    try:
        demo_1_basic_benchmarking()
        demo_2_warmup_iterations()
        demo_3_regression_detection()
        demo_4_suite_organization()
        demo_5_filtering_benchmarks()
        demo_6_real_paracle_operations()
        demo_7_timeout_protection()
        demo_8_baseline_management()
        demo_9_cicd_integration()

        print("\n" + "=" * 70)
        print("ALL DEMOS COMPLETE ✅")
        print("=" * 70)
        print()
        print("Next steps:")
        print("  1. Run CLI benchmarks: paracle benchmark run")
        print("  2. Create baseline: paracle benchmark save")
        print("  3. Compare results: paracle benchmark compare baseline.json results.json")
        print("  4. Add to CI/CD: See docs/performance-benchmarking-guide.md")
        print()

    except KeyboardInterrupt:
        print("\n\nDemo interrupted by user.")
    except Exception as e:
        print(f"\n\nDemo error: {e}")
        import traceback

        traceback.print_exc()


if __name__ == "__main__":
    main()
