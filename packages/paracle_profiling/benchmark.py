"""Performance benchmarking suite for CI integration.

Phase 8 - Performance & Scale: Benchmarking Suite

Provides:
- Benchmark definitions with configurable iterations
- Performance regression detection
- JSON output for CI integration
- Baseline comparison
- Statistical analysis (mean, median, p95, p99)

Example:
    from paracle_profiling.benchmark import Benchmark, BenchmarkSuite

    suite = BenchmarkSuite("api-benchmarks")

    @suite.benchmark(iterations=100)
    def bench_agent_creation():
        AgentSpec(name="test", model="gpt-4")

    results = suite.run()
    suite.save_results("benchmark_results.json")
"""

import json
import statistics
import time
from collections.abc import Callable
from dataclasses import dataclass, field
from datetime import datetime, timezone
from enum import Enum
from pathlib import Path
from typing import Any


def _utcnow_iso() -> str:
    """Get current UTC time in ISO format."""
    return datetime.now(timezone.utc).isoformat()


# Benchmark result status
class BenchmarkStatus(str, Enum):
    """Status of a benchmark run."""

    PASSED = "passed"
    FAILED = "failed"
    REGRESSION = "regression"
    IMPROVEMENT = "improvement"
    NO_BASELINE = "no_baseline"


@dataclass
class BenchmarkResult:
    """Result of a single benchmark."""

    name: str
    iterations: int
    total_time_ms: float
    mean_ms: float
    median_ms: float
    min_ms: float
    max_ms: float
    std_dev_ms: float
    p50_ms: float
    p95_ms: float
    p99_ms: float
    status: BenchmarkStatus = BenchmarkStatus.PASSED
    baseline_mean_ms: float | None = None
    change_percent: float | None = None
    error: str | None = None
    timestamp: str = field(default_factory=_utcnow_iso)

    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary for JSON serialization."""
        return {
            "name": self.name,
            "iterations": self.iterations,
            "total_time_ms": round(self.total_time_ms, 3),
            "mean_ms": round(self.mean_ms, 3),
            "median_ms": round(self.median_ms, 3),
            "min_ms": round(self.min_ms, 3),
            "max_ms": round(self.max_ms, 3),
            "std_dev_ms": round(self.std_dev_ms, 3),
            "p50_ms": round(self.p50_ms, 3),
            "p95_ms": round(self.p95_ms, 3),
            "p99_ms": round(self.p99_ms, 3),
            "status": self.status.value,
            "baseline_mean_ms": (
                round(self.baseline_mean_ms, 3) if self.baseline_mean_ms else None
            ),
            "change_percent": (
                round(self.change_percent, 2) if self.change_percent else None
            ),
            "error": self.error,
            "timestamp": self.timestamp,
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "BenchmarkResult":
        """Create from dictionary."""
        return cls(
            name=data["name"],
            iterations=data["iterations"],
            total_time_ms=data["total_time_ms"],
            mean_ms=data["mean_ms"],
            median_ms=data["median_ms"],
            min_ms=data["min_ms"],
            max_ms=data["max_ms"],
            std_dev_ms=data["std_dev_ms"],
            p50_ms=data["p50_ms"],
            p95_ms=data["p95_ms"],
            p99_ms=data["p99_ms"],
            status=BenchmarkStatus(data.get("status", "passed")),
            baseline_mean_ms=data.get("baseline_mean_ms"),
            change_percent=data.get("change_percent"),
            error=data.get("error"),
            timestamp=data.get("timestamp", _utcnow_iso()),
        )


@dataclass
class Benchmark:
    """A benchmark definition."""

    name: str
    func: Callable[[], Any]
    iterations: int = 100
    warmup_iterations: int = 5
    timeout_seconds: float = 60.0
    description: str = ""

    def run(self) -> BenchmarkResult:
        """Run the benchmark and return results."""
        timings_ms: list[float] = []
        error_msg: str | None = None

        try:
            # Warmup phase
            for _ in range(self.warmup_iterations):
                self.func()

            # Benchmark phase
            start_total = time.perf_counter()

            for _ in range(self.iterations):
                # Check timeout
                if time.perf_counter() - start_total > self.timeout_seconds:
                    error_msg = f"Timeout after {self.timeout_seconds}s"
                    break

                start = time.perf_counter()
                self.func()
                end = time.perf_counter()
                timings_ms.append((end - start) * 1000)

            total_time = (time.perf_counter() - start_total) * 1000

        except Exception as e:
            error_msg = str(e)
            # Return error result
            return BenchmarkResult(
                name=self.name,
                iterations=len(timings_ms),
                total_time_ms=0,
                mean_ms=0,
                median_ms=0,
                min_ms=0,
                max_ms=0,
                std_dev_ms=0,
                p50_ms=0,
                p95_ms=0,
                p99_ms=0,
                status=BenchmarkStatus.FAILED,
                error=error_msg,
            )

        if not timings_ms:
            return BenchmarkResult(
                name=self.name,
                iterations=0,
                total_time_ms=0,
                mean_ms=0,
                median_ms=0,
                min_ms=0,
                max_ms=0,
                std_dev_ms=0,
                p50_ms=0,
                p95_ms=0,
                p99_ms=0,
                status=BenchmarkStatus.FAILED,
                error=error_msg or "No iterations completed",
            )

        # Calculate statistics
        sorted_timings = sorted(timings_ms)
        n = len(sorted_timings)

        return BenchmarkResult(
            name=self.name,
            iterations=n,
            total_time_ms=total_time,
            mean_ms=statistics.mean(timings_ms),
            median_ms=statistics.median(timings_ms),
            min_ms=min(timings_ms),
            max_ms=max(timings_ms),
            std_dev_ms=statistics.stdev(timings_ms) if n > 1 else 0,
            p50_ms=sorted_timings[int(n * 0.50)],
            p95_ms=sorted_timings[int(n * 0.95)] if n > 1 else sorted_timings[0],
            p99_ms=sorted_timings[int(n * 0.99)] if n > 1 else sorted_timings[0],
            status=BenchmarkStatus.PASSED if not error_msg else BenchmarkStatus.FAILED,
            error=error_msg,
        )


@dataclass
class BenchmarkSuiteResult:
    """Result of running a benchmark suite."""

    suite_name: str
    results: list[BenchmarkResult]
    total_time_ms: float
    passed: int
    failed: int
    regressions: int
    improvements: int
    timestamp: str = field(default_factory=_utcnow_iso)
    git_sha: str | None = None
    git_branch: str | None = None

    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary for JSON serialization."""
        return {
            "suite_name": self.suite_name,
            "results": [r.to_dict() for r in self.results],
            "summary": {
                "total_benchmarks": len(self.results),
                "passed": self.passed,
                "failed": self.failed,
                "regressions": self.regressions,
                "improvements": self.improvements,
                "total_time_ms": round(self.total_time_ms, 3),
            },
            "timestamp": self.timestamp,
            "git_sha": self.git_sha,
            "git_branch": self.git_branch,
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "BenchmarkSuiteResult":
        """Create from dictionary."""
        return cls(
            suite_name=data["suite_name"],
            results=[BenchmarkResult.from_dict(r) for r in data["results"]],
            total_time_ms=data["summary"]["total_time_ms"],
            passed=data["summary"]["passed"],
            failed=data["summary"]["failed"],
            regressions=data["summary"]["regressions"],
            improvements=data["summary"]["improvements"],
            timestamp=data.get("timestamp", _utcnow_iso()),
            git_sha=data.get("git_sha"),
            git_branch=data.get("git_branch"),
        )

    @property
    def has_regressions(self) -> bool:
        """Check if any benchmark regressed."""
        return self.regressions > 0

    @property
    def all_passed(self) -> bool:
        """Check if all benchmarks passed (no failures or regressions)."""
        return self.failed == 0 and self.regressions == 0


class BenchmarkSuite:
    """Collection of benchmarks with baseline comparison.

    Example:
        suite = BenchmarkSuite("core-benchmarks")

        @suite.benchmark(iterations=100)
        def bench_operation():
            do_something()

        results = suite.run()
        suite.save_results("results.json")

        # Compare with baseline
        suite.load_baseline("baseline.json")
        results = suite.run()
        if results.has_regressions:
            print("Performance regression detected!")
    """

    def __init__(
        self,
        name: str,
        regression_threshold: float = 0.10,  # 10% slowdown = regression
        improvement_threshold: float = 0.10,  # 10% speedup = improvement
    ):
        """Initialize benchmark suite.

        Args:
            name: Suite name for identification
            regression_threshold: % slowdown to flag as regression (0.10 = 10%)
            improvement_threshold: % speedup to flag as improvement (0.10 = 10%)
        """
        self.name = name
        self.regression_threshold = regression_threshold
        self.improvement_threshold = improvement_threshold
        self._benchmarks: list[Benchmark] = []
        self._baseline: dict[str, BenchmarkResult] = {}
        self._last_results: BenchmarkSuiteResult | None = None

    def benchmark(
        self,
        iterations: int = 100,
        warmup: int = 5,
        timeout: float = 60.0,
        description: str = "",
    ) -> Callable:
        """Decorator to register a benchmark function.

        Args:
            iterations: Number of benchmark iterations
            warmup: Number of warmup iterations before timing
            timeout: Maximum seconds for benchmark
            description: Human-readable description
        """

        def decorator(func: Callable) -> Callable:
            bench = Benchmark(
                name=func.__name__,
                func=func,
                iterations=iterations,
                warmup_iterations=warmup,
                timeout_seconds=timeout,
                description=description,
            )
            self._benchmarks.append(bench)
            return func

        return decorator

    def add_benchmark(
        self,
        name: str,
        func: Callable,
        iterations: int = 100,
        warmup: int = 5,
        timeout: float = 60.0,
        description: str = "",
    ) -> None:
        """Add a benchmark programmatically."""
        bench = Benchmark(
            name=name,
            func=func,
            iterations=iterations,
            warmup_iterations=warmup,
            timeout_seconds=timeout,
            description=description,
        )
        self._benchmarks.append(bench)

    def load_baseline(self, path: str | Path) -> bool:
        """Load baseline results from file.

        Args:
            path: Path to baseline JSON file

        Returns:
            True if baseline loaded successfully
        """
        path = Path(path)
        if not path.exists():
            return False

        try:
            with open(path) as f:
                data = json.load(f)

            suite_result = BenchmarkSuiteResult.from_dict(data)
            self._baseline = {r.name: r for r in suite_result.results}
            return True
        except (json.JSONDecodeError, KeyError, TypeError):
            return False

    def run(self, filter_pattern: str | None = None) -> BenchmarkSuiteResult:
        """Run all benchmarks and return results.

        Args:
            filter_pattern: Optional name filter (substring match)

        Returns:
            Suite results with all benchmark results
        """
        results: list[BenchmarkResult] = []
        start_time = time.perf_counter()

        for bench in self._benchmarks:
            # Filter if pattern provided
            if filter_pattern and filter_pattern not in bench.name:
                continue

            # Run benchmark
            result = bench.run()

            # Compare with baseline if available
            if bench.name in self._baseline:
                baseline = self._baseline[bench.name]
                result.baseline_mean_ms = baseline.mean_ms

                if baseline.mean_ms > 0:
                    change = (result.mean_ms - baseline.mean_ms) / baseline.mean_ms
                    result.change_percent = change * 100

                    # Determine status based on thresholds
                    if result.status == BenchmarkStatus.PASSED:
                        if change > self.regression_threshold:
                            result.status = BenchmarkStatus.REGRESSION
                        elif change < -self.improvement_threshold:
                            result.status = BenchmarkStatus.IMPROVEMENT
            elif result.error is None:
                result.status = BenchmarkStatus.NO_BASELINE

            results.append(result)

        total_time = (time.perf_counter() - start_time) * 1000

        # Count statuses
        passed = sum(
            1
            for r in results
            if r.status in (BenchmarkStatus.PASSED, BenchmarkStatus.NO_BASELINE)
        )
        failed = sum(1 for r in results if r.status == BenchmarkStatus.FAILED)
        regressions = sum(1 for r in results if r.status == BenchmarkStatus.REGRESSION)
        improvements = sum(
            1 for r in results if r.status == BenchmarkStatus.IMPROVEMENT
        )

        # Get git info if available
        git_sha, git_branch = self._get_git_info()

        suite_result = BenchmarkSuiteResult(
            suite_name=self.name,
            results=results,
            total_time_ms=total_time,
            passed=passed,
            failed=failed,
            regressions=regressions,
            improvements=improvements,
            git_sha=git_sha,
            git_branch=git_branch,
        )

        self._last_results = suite_result
        return suite_result

    def save_results(self, path: str | Path) -> None:
        """Save results to JSON file.

        Args:
            path: Output file path
        """
        if self._last_results is None:
            raise RuntimeError("No results to save. Run benchmarks first.")

        path = Path(path)
        path.parent.mkdir(parents=True, exist_ok=True)

        with open(path, "w") as f:
            json.dump(self._last_results.to_dict(), f, indent=2)

    def save_as_baseline(self, path: str | Path) -> None:
        """Save current results as baseline.

        Args:
            path: Baseline file path
        """
        self.save_results(path)

    def format_results(self, verbose: bool = False) -> str:
        """Format results as human-readable text.

        Args:
            verbose: Include detailed statistics

        Returns:
            Formatted string
        """
        if self._last_results is None:
            return "No results available. Run benchmarks first."

        lines = [
            f"Benchmark Suite: {self._last_results.suite_name}",
            f"Timestamp: {self._last_results.timestamp}",
            "",
        ]

        if self._last_results.git_sha:
            lines.append(f"Git SHA: {self._last_results.git_sha}")
        if self._last_results.git_branch:
            lines.append(f"Git Branch: {self._last_results.git_branch}")
        if self._last_results.git_sha or self._last_results.git_branch:
            lines.append("")

        lines.append("Results:")
        lines.append("-" * 80)

        for result in self._last_results.results:
            status_icon = self._status_icon(result.status)
            line = f"{status_icon} {result.name}: {result.mean_ms:.3f}ms (avg)"

            if result.change_percent is not None:
                sign = "+" if result.change_percent > 0 else ""
                line += f" [{sign}{result.change_percent:.1f}%]"

            if result.error:
                line += f" ERROR: {result.error}"

            lines.append(line)

            if verbose:
                lines.append(f"    Iterations: {result.iterations}")
                lines.append(
                    f"    Min: {result.min_ms:.3f}ms | Max: {result.max_ms:.3f}ms"
                )
                lines.append(
                    f"    P50: {result.p50_ms:.3f}ms | "
                    f"P95: {result.p95_ms:.3f}ms | P99: {result.p99_ms:.3f}ms"
                )
                lines.append(f"    Std Dev: {result.std_dev_ms:.3f}ms")
                lines.append("")

        lines.append("-" * 80)
        lines.append("")
        lines.append("Summary:")
        lines.append(f"  Total benchmarks: {len(self._last_results.results)}")
        lines.append(f"  Passed: {self._last_results.passed}")
        lines.append(f"  Failed: {self._last_results.failed}")
        lines.append(f"  Regressions: {self._last_results.regressions}")
        lines.append(f"  Improvements: {self._last_results.improvements}")
        lines.append(f"  Total time: {self._last_results.total_time_ms:.1f}ms")

        return "\n".join(lines)

    def _status_icon(self, status: BenchmarkStatus) -> str:
        """Get status icon for display."""
        icons = {
            BenchmarkStatus.PASSED: "[OK]",
            BenchmarkStatus.FAILED: "[FAIL]",
            BenchmarkStatus.REGRESSION: "[REGR]",
            BenchmarkStatus.IMPROVEMENT: "[IMPR]",
            BenchmarkStatus.NO_BASELINE: "[NEW]",
        }
        return icons.get(status, "[?]")

    def _get_git_info(self) -> tuple[str | None, str | None]:
        """Get git SHA and branch if available."""
        import subprocess

        try:
            sha = subprocess.run(
                ["git", "rev-parse", "HEAD"],
                capture_output=True,
                text=True,
                timeout=5,
            )
            git_sha = sha.stdout.strip() if sha.returncode == 0 else None

            branch = subprocess.run(
                ["git", "rev-parse", "--abbrev-ref", "HEAD"],
                capture_output=True,
                text=True,
                timeout=5,
            )
            git_branch = branch.stdout.strip() if branch.returncode == 0 else None

            return git_sha, git_branch
        except (subprocess.TimeoutExpired, FileNotFoundError):
            return None, None


# Global suite for easy usage
_default_suite: BenchmarkSuite | None = None


def get_default_suite(name: str = "paracle-benchmarks") -> BenchmarkSuite:
    """Get or create the default benchmark suite."""
    global _default_suite
    if _default_suite is None:
        _default_suite = BenchmarkSuite(name)
    return _default_suite


def benchmark(
    iterations: int = 100,
    warmup: int = 5,
    timeout: float = 60.0,
    description: str = "",
) -> Callable:
    """Decorator to register benchmark with default suite.

    Example:
        @benchmark(iterations=100)
        def bench_my_function():
            my_function()
    """
    suite = get_default_suite()
    return suite.benchmark(
        iterations=iterations, warmup=warmup, timeout=timeout, description=description
    )


def run_benchmarks(
    filter_pattern: str | None = None,
    baseline_path: str | Path | None = None,
) -> BenchmarkSuiteResult:
    """Run all benchmarks in default suite.

    Args:
        filter_pattern: Optional name filter
        baseline_path: Optional baseline file for comparison

    Returns:
        Suite results
    """
    suite = get_default_suite()
    if baseline_path:
        suite.load_baseline(baseline_path)
    return suite.run(filter_pattern)
