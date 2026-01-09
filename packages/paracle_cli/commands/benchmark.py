"""Benchmark CLI commands.

Phase 8 - Performance & Scale: Benchmarking Suite

Commands:
    paracle benchmark run     - Run all benchmarks
    paracle benchmark list    - List available benchmarks
    paracle benchmark compare - Compare results with baseline
    paracle benchmark save    - Save results as baseline
"""

import json
import sys
from pathlib import Path

import click
from paracle_profiling.benchmark import BenchmarkSuite, BenchmarkSuiteResult

# Default paths
DEFAULT_BASELINE_PATH = Path(".benchmarks/baseline.json")
DEFAULT_RESULTS_PATH = Path(".benchmarks/results.json")


def get_core_benchmark_suite() -> BenchmarkSuite:
    """Create benchmark suite with core Paracle operations."""
    suite = BenchmarkSuite("paracle-core", regression_threshold=0.15)

    # Import here to avoid circular imports
    try:
        from paracle_domain.agent import AgentSpec

        @suite.benchmark(
            iterations=1000, warmup=10, description="Create AgentSpec model"
        )
        def bench_agent_spec_creation():
            AgentSpec(
                agent_id="test-agent",
                name="Test Agent",
                model="gpt-4",
                temperature=0.7,
                system_prompt="You are a helpful assistant.",
            )

    except ImportError:
        pass

    try:
        from paracle_core.parac.file_config import ParacConfig

        @suite.benchmark(iterations=100, warmup=5, description="Load parac config")
        def bench_config_load():
            try:
                ParacConfig.load()
            except FileNotFoundError:
                pass  # Expected in test environments

    except ImportError:
        pass

    try:
        from paracle_profiling import CacheManager

        cache = CacheManager(max_size=100)

        @suite.benchmark(iterations=5000, warmup=100, description="Cache set operation")
        def bench_cache_set():
            cache.set("key", {"data": "value"})

        @suite.benchmark(iterations=5000, warmup=100, description="Cache get operation")
        def bench_cache_get():
            cache.get("key")

        @suite.benchmark(iterations=1000, warmup=10, description="Cache set+get cycle")
        def bench_cache_cycle():
            cache.set("cycle_key", {"data": "test"})
            cache.get("cycle_key")

    except ImportError:
        pass

    try:
        from pathlib import Path as PathLib

        from paracle_core.parac.agent_discovery import AgentDiscovery

        # Find .parac directory if it exists
        # AgentDiscovery expects parac_root to be the .parac/ directory
        parac_dir = PathLib.cwd() / ".parac"
        agents_dir = parac_dir / "agents" / "specs"
        if agents_dir.exists():

            @suite.benchmark(
                iterations=50, warmup=2, description="Agent discovery scan"
            )
            def bench_agent_discovery():
                discovery = AgentDiscovery(parac_dir)
                discovery.discover_agents()

    except ImportError:
        pass

    return suite


@click.group(invoke_without_command=True)
@click.pass_context
@click.option(
    "-l", "--list", "list_flag", is_flag=True, help="List available benchmarks"
)
def benchmark(ctx, list_flag: bool):
    """Run performance benchmarks.

    Example:
        paracle benchmark run
        paracle benchmark run --verbose
        paracle benchmark compare --baseline .benchmarks/baseline.json
    """
    if list_flag:
        ctx.invoke(list_benchmarks)
    elif ctx.invoked_subcommand is None:
        click.echo(ctx.get_help())


@benchmark.command("run")
@click.option(
    "--output",
    "-o",
    type=click.Path(),
    default=str(DEFAULT_RESULTS_PATH),
    help="Output file for results",
)
@click.option(
    "--baseline",
    "-b",
    type=click.Path(exists=True),
    help="Baseline file for comparison",
)
@click.option(
    "--filter",
    "-f",
    type=str,
    help="Filter benchmarks by name pattern",
)
@click.option(
    "--verbose",
    "-v",
    is_flag=True,
    help="Show detailed statistics",
)
@click.option(
    "--json-output",
    "-j",
    is_flag=True,
    help="Output results as JSON",
)
@click.option(
    "--fail-on-regression",
    is_flag=True,
    help="Exit with error code if regression detected",
)
def run(
    output: str,
    baseline: str | None,
    filter: str | None,
    verbose: bool,
    json_output: bool,
    fail_on_regression: bool,
):
    """Run performance benchmarks.

    Example:
        paracle benchmark run
        paracle benchmark run --verbose
        paracle benchmark run --baseline .benchmarks/baseline.json
        paracle benchmark run --fail-on-regression
    """
    suite = get_core_benchmark_suite()

    if not suite._benchmarks:
        click.secho(
            "No benchmarks available. Check that paracle packages are installed.",
            fg="yellow",
        )
        return

    # Load baseline if provided
    if baseline:
        if suite.load_baseline(baseline):
            click.echo(f"Loaded baseline from {baseline}")
        else:
            click.secho(
                f"Warning: Could not load baseline from {baseline}", fg="yellow"
            )

    click.echo(f"Running {len(suite._benchmarks)} benchmarks...")
    click.echo()

    # Run benchmarks
    results = suite.run(filter_pattern=filter)

    # Output results
    if json_output:
        click.echo(json.dumps(results.to_dict(), indent=2))
    else:
        click.echo(suite.format_results(verbose=verbose))

    # Save results
    output_path = Path(output)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    suite.save_results(output_path)
    click.echo()
    click.echo(f"Results saved to {output_path}")

    # Exit with error if regression detected
    if fail_on_regression and results.has_regressions:
        click.secho(f"\n[FAIL] {results.regressions} regression(s) detected!", fg="red")
        sys.exit(1)

    if results.failed > 0:
        click.secho(f"\n[WARN] {results.failed} benchmark(s) failed", fg="yellow")


@benchmark.command("list")
def list_benchmarks():
    """List available benchmarks.

    Example:
        paracle benchmark list
    """
    suite = get_core_benchmark_suite()

    if not suite._benchmarks:
        click.echo("No benchmarks available.")
        return

    click.echo(f"Available benchmarks ({len(suite._benchmarks)}):")
    click.echo()

    for bench in suite._benchmarks:
        click.echo(f"  {bench.name}")
        if bench.description:
            click.echo(f"    {bench.description}")
        click.echo(
            f"    Iterations: {bench.iterations}, Warmup: {bench.warmup_iterations}"
        )
        click.echo()


@benchmark.command("compare")
@click.argument("results_file", type=click.Path(exists=True))
@click.option(
    "--baseline",
    "-b",
    type=click.Path(exists=True),
    default=str(DEFAULT_BASELINE_PATH),
    help="Baseline file for comparison",
)
@click.option(
    "--threshold",
    "-t",
    type=float,
    default=0.10,
    help="Regression threshold (0.10 = 10%)",
)
def compare(results_file: str, baseline: str, threshold: float):
    """Compare benchmark results with baseline.

    Example:
        paracle benchmark compare .benchmarks/results.json
        paracle benchmark compare results.json --baseline main-baseline.json
    """
    # Load results
    try:
        with open(results_file) as f:
            results_data = json.load(f)
        results = BenchmarkSuiteResult.from_dict(results_data)
    except (json.JSONDecodeError, KeyError) as e:
        click.secho(f"Error loading results: {e}", fg="red")
        return

    # Load baseline
    try:
        with open(baseline) as f:
            baseline_data = json.load(f)
        baseline_results = BenchmarkSuiteResult.from_dict(baseline_data)
    except FileNotFoundError:
        click.secho(f"Baseline file not found: {baseline}", fg="red")
        return
    except (json.JSONDecodeError, KeyError) as e:
        click.secho(f"Error loading baseline: {e}", fg="red")
        return

    # Create comparison
    baseline_map = {r.name: r for r in baseline_results.results}

    click.echo(f"Comparing {results_file} vs {baseline}")
    click.echo(f"Regression threshold: {threshold * 100:.0f}%")
    click.echo()
    click.echo("-" * 80)

    regressions = 0
    improvements = 0

    for result in results.results:
        if result.name not in baseline_map:
            click.echo(f"[NEW]  {result.name}: {result.mean_ms:.3f}ms")
            continue

        baseline_result = baseline_map[result.name]
        change = (result.mean_ms - baseline_result.mean_ms) / baseline_result.mean_ms

        sign = "+" if change > 0 else ""
        change_str = f"{sign}{change * 100:.1f}%"

        if change > threshold:
            click.secho(
                f"[REGR] {result.name}: {result.mean_ms:.3f}ms ({change_str}) vs {baseline_result.mean_ms:.3f}ms",
                fg="red",
            )
            regressions += 1
        elif change < -threshold:
            click.secho(
                f"[IMPR] {result.name}: {result.mean_ms:.3f}ms ({change_str}) vs {baseline_result.mean_ms:.3f}ms",
                fg="green",
            )
            improvements += 1
        else:
            click.echo(
                f"[OK]   {result.name}: {result.mean_ms:.3f}ms ({change_str}) vs {baseline_result.mean_ms:.3f}ms"
            )

    click.echo("-" * 80)
    click.echo()
    click.echo(f"Regressions: {regressions}")
    click.echo(f"Improvements: {improvements}")

    if regressions > 0:
        sys.exit(1)


@benchmark.command("save-baseline")
@click.option(
    "--input",
    "-i",
    type=click.Path(exists=True),
    default=str(DEFAULT_RESULTS_PATH),
    help="Results file to save as baseline",
)
@click.option(
    "--output",
    "-o",
    type=click.Path(),
    default=str(DEFAULT_BASELINE_PATH),
    help="Baseline output file",
)
def save_baseline(input: str, output: str):
    """Save benchmark results as baseline.

    Example:
        paracle benchmark save-baseline
        paracle benchmark save-baseline --input results.json --output baseline.json
    """
    import shutil

    input_path = Path(input)
    output_path = Path(output)

    if not input_path.exists():
        click.secho(f"Results file not found: {input}", fg="red")
        click.echo("Run 'paracle benchmark run' first to generate results.")
        return

    output_path.parent.mkdir(parents=True, exist_ok=True)
    shutil.copy(input_path, output_path)

    click.echo(f"[OK] Saved baseline to {output_path}")
