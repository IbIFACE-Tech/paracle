"""Tests for benchmarking suite.

Phase 8 - Performance & Scale: Benchmarking Suite
"""

import json
import time
from pathlib import Path

import pytest

from paracle_profiling.benchmark import (
    Benchmark,
    BenchmarkResult,
    BenchmarkStatus,
    BenchmarkSuite,
    BenchmarkSuiteResult,
    get_default_suite,
)


class TestBenchmark:
    """Tests for Benchmark class."""

    def test_benchmark_runs_function(self):
        """Test benchmark runs function correct number of times."""
        call_count = 0

        def target():
            nonlocal call_count
            call_count += 1

        bench = Benchmark(
            name="test",
            func=target,
            iterations=10,
            warmup_iterations=2,
        )

        result = bench.run()

        assert result.iterations == 10
        # warmup (2) + benchmark (10)
        assert call_count == 12

    def test_benchmark_calculates_statistics(self):
        """Test benchmark calculates all statistics."""
        def target():
            time.sleep(0.001)  # 1ms

        bench = Benchmark(
            name="test",
            func=target,
            iterations=10,
            warmup_iterations=1,
        )

        result = bench.run()

        assert result.name == "test"
        assert result.iterations == 10
        assert result.mean_ms > 0
        assert result.median_ms > 0
        assert result.min_ms > 0
        assert result.max_ms >= result.min_ms
        assert result.p50_ms > 0
        assert result.p95_ms >= result.p50_ms
        assert result.p99_ms >= result.p95_ms
        assert result.status == BenchmarkStatus.PASSED

    def test_benchmark_handles_exception(self):
        """Test benchmark handles function exception."""
        def failing_func():
            raise ValueError("Test error")

        bench = Benchmark(
            name="failing",
            func=failing_func,
            iterations=10,
            warmup_iterations=0,
        )

        result = bench.run()

        assert result.status == BenchmarkStatus.FAILED
        assert result.error is not None
        assert "Test error" in result.error

    def test_benchmark_timeout(self):
        """Test benchmark respects timeout."""
        def slow_func():
            time.sleep(0.1)

        bench = Benchmark(
            name="slow",
            func=slow_func,
            iterations=100,
            warmup_iterations=0,
            timeout_seconds=0.2,  # Should timeout quickly
        )

        result = bench.run()

        # Should complete fewer iterations due to timeout
        assert result.iterations < 100
        assert "Timeout" in (result.error or "")


class TestBenchmarkResult:
    """Tests for BenchmarkResult dataclass."""

    def test_result_to_dict(self):
        """Test result serialization to dict."""
        result = BenchmarkResult(
            name="test",
            iterations=100,
            total_time_ms=1000.0,
            mean_ms=10.0,
            median_ms=9.5,
            min_ms=5.0,
            max_ms=20.0,
            std_dev_ms=2.5,
            p50_ms=9.5,
            p95_ms=18.0,
            p99_ms=19.5,
            status=BenchmarkStatus.PASSED,
        )

        data = result.to_dict()

        assert data["name"] == "test"
        assert data["iterations"] == 100
        assert data["mean_ms"] == 10.0
        assert data["status"] == "passed"

    def test_result_from_dict(self):
        """Test result deserialization from dict."""
        data = {
            "name": "test",
            "iterations": 100,
            "total_time_ms": 1000.0,
            "mean_ms": 10.0,
            "median_ms": 9.5,
            "min_ms": 5.0,
            "max_ms": 20.0,
            "std_dev_ms": 2.5,
            "p50_ms": 9.5,
            "p95_ms": 18.0,
            "p99_ms": 19.5,
            "status": "passed",
        }

        result = BenchmarkResult.from_dict(data)

        assert result.name == "test"
        assert result.iterations == 100
        assert result.status == BenchmarkStatus.PASSED

    def test_result_with_baseline_comparison(self):
        """Test result with baseline comparison data."""
        result = BenchmarkResult(
            name="test",
            iterations=100,
            total_time_ms=1000.0,
            mean_ms=10.0,
            median_ms=9.5,
            min_ms=5.0,
            max_ms=20.0,
            std_dev_ms=2.5,
            p50_ms=9.5,
            p95_ms=18.0,
            p99_ms=19.5,
            status=BenchmarkStatus.REGRESSION,
            baseline_mean_ms=8.0,
            change_percent=25.0,
        )

        data = result.to_dict()

        assert data["baseline_mean_ms"] == 8.0
        assert data["change_percent"] == 25.0
        assert data["status"] == "regression"


class TestBenchmarkSuite:
    """Tests for BenchmarkSuite class."""

    def test_suite_registers_benchmark_decorator(self):
        """Test benchmark decorator registers function."""
        suite = BenchmarkSuite("test-suite")

        @suite.benchmark(iterations=10)
        def my_bench():
            pass

        assert len(suite._benchmarks) == 1
        assert suite._benchmarks[0].name == "my_bench"
        assert suite._benchmarks[0].iterations == 10

    def test_suite_add_benchmark_programmatically(self):
        """Test adding benchmark programmatically."""
        suite = BenchmarkSuite("test-suite")

        def my_func():
            pass

        suite.add_benchmark("custom-name", my_func, iterations=50)

        assert len(suite._benchmarks) == 1
        assert suite._benchmarks[0].name == "custom-name"
        assert suite._benchmarks[0].iterations == 50

    def test_suite_runs_all_benchmarks(self):
        """Test suite runs all registered benchmarks."""
        suite = BenchmarkSuite("test-suite")

        @suite.benchmark(iterations=5, warmup=1)
        def bench_a():
            pass

        @suite.benchmark(iterations=5, warmup=1)
        def bench_b():
            pass

        results = suite.run()

        assert len(results.results) == 2
        assert results.passed == 2
        assert results.failed == 0

    def test_suite_filter_by_pattern(self):
        """Test suite filters benchmarks by name pattern."""
        suite = BenchmarkSuite("test-suite")

        @suite.benchmark(iterations=5)
        def bench_cache_get():
            pass

        @suite.benchmark(iterations=5)
        def bench_cache_set():
            pass

        @suite.benchmark(iterations=5)
        def bench_agent_create():
            pass

        results = suite.run(filter_pattern="cache")

        assert len(results.results) == 2
        assert all("cache" in r.name for r in results.results)

    def test_suite_detects_regression(self):
        """Test suite detects performance regression."""
        suite = BenchmarkSuite(
            "test-suite",
            regression_threshold=0.10,  # 10%
        )

        # Slower function (with sleep)
        @suite.benchmark(iterations=10, warmup=1)
        def bench_test():
            time.sleep(0.001)  # 1ms

        # Run first time (no baseline)
        results1 = suite.run()
        assert results1.results[0].status == BenchmarkStatus.NO_BASELINE

        # Create artificial baseline that is faster (simulating old code was faster)
        # Current benchmark takes ~1ms, baseline says 0.5ms = regression
        suite._baseline["bench_test"] = BenchmarkResult(
            name="bench_test",
            iterations=100,
            total_time_ms=50.0,
            mean_ms=0.5,  # 0.5ms baseline - faster than current ~1ms
            median_ms=0.5,
            min_ms=0.4,
            max_ms=0.6,
            std_dev_ms=0.05,
            p50_ms=0.5,
            p95_ms=0.55,
            p99_ms=0.58,
        )

        # Run again - should detect regression since real timing (~1ms) > baseline (0.5ms)
        results2 = suite.run()
        assert results2.results[0].status == BenchmarkStatus.REGRESSION
        assert results2.has_regressions

    def test_suite_detects_improvement(self):
        """Test suite detects performance improvement."""
        suite = BenchmarkSuite(
            "test-suite",
            improvement_threshold=0.10,  # 10%
        )

        @suite.benchmark(iterations=100, warmup=5)
        def bench_test():
            pass

        # Create artificial baseline with slower mean
        suite._baseline["bench_test"] = BenchmarkResult(
            name="bench_test",
            iterations=100,
            total_time_ms=10000.0,
            mean_ms=100.0,  # Very slow baseline
            median_ms=100.0,
            min_ms=100.0,
            max_ms=100.0,
            std_dev_ms=0.0,
            p50_ms=100.0,
            p95_ms=100.0,
            p99_ms=100.0,
        )

        results = suite.run()
        assert results.results[0].status == BenchmarkStatus.IMPROVEMENT

    def test_suite_save_and_load_results(self, tmp_path: Path):
        """Test saving and loading results."""
        suite = BenchmarkSuite("test-suite")

        @suite.benchmark(iterations=10)
        def bench_test():
            pass

        # Run and save
        suite.run()
        output_path = tmp_path / "results.json"
        suite.save_results(output_path)

        assert output_path.exists()

        # Load and verify
        with open(output_path) as f:
            data = json.load(f)

        assert data["suite_name"] == "test-suite"
        assert len(data["results"]) == 1
        assert data["results"][0]["name"] == "bench_test"

    def test_suite_load_baseline(self, tmp_path: Path):
        """Test loading baseline from file."""
        # Create baseline file
        baseline_data = {
            "suite_name": "test-suite",
            "results": [
                {
                    "name": "bench_test",
                    "iterations": 100,
                    "total_time_ms": 1000.0,
                    "mean_ms": 10.0,
                    "median_ms": 9.5,
                    "min_ms": 5.0,
                    "max_ms": 20.0,
                    "std_dev_ms": 2.5,
                    "p50_ms": 9.5,
                    "p95_ms": 18.0,
                    "p99_ms": 19.5,
                    "status": "passed",
                }
            ],
            "summary": {
                "total_benchmarks": 1,
                "passed": 1,
                "failed": 0,
                "regressions": 0,
                "improvements": 0,
                "total_time_ms": 1000.0,
            },
        }

        baseline_path = tmp_path / "baseline.json"
        with open(baseline_path, "w") as f:
            json.dump(baseline_data, f)

        suite = BenchmarkSuite("test-suite")
        success = suite.load_baseline(baseline_path)

        assert success
        assert "bench_test" in suite._baseline
        assert suite._baseline["bench_test"].mean_ms == 10.0

    def test_suite_format_results(self):
        """Test formatting results as text."""
        suite = BenchmarkSuite("test-suite")

        @suite.benchmark(iterations=10)
        def bench_test():
            pass

        suite.run()
        output = suite.format_results()

        assert "test-suite" in output
        assert "bench_test" in output
        assert "Summary:" in output

    def test_suite_format_results_verbose(self):
        """Test verbose formatting includes details."""
        suite = BenchmarkSuite("test-suite")

        @suite.benchmark(iterations=10)
        def bench_test():
            pass

        suite.run()
        output = suite.format_results(verbose=True)

        assert "Iterations:" in output
        assert "Min:" in output
        assert "Max:" in output
        assert "P50:" in output
        assert "P95:" in output


class TestBenchmarkSuiteResult:
    """Tests for BenchmarkSuiteResult dataclass."""

    def test_suite_result_has_regressions(self):
        """Test has_regressions property."""
        result = BenchmarkSuiteResult(
            suite_name="test",
            results=[],
            total_time_ms=100.0,
            passed=5,
            failed=0,
            regressions=1,
            improvements=0,
        )

        assert result.has_regressions

    def test_suite_result_all_passed(self):
        """Test all_passed property."""
        result = BenchmarkSuiteResult(
            suite_name="test",
            results=[],
            total_time_ms=100.0,
            passed=5,
            failed=0,
            regressions=0,
            improvements=1,
        )

        assert result.all_passed

        result2 = BenchmarkSuiteResult(
            suite_name="test",
            results=[],
            total_time_ms=100.0,
            passed=4,
            failed=1,
            regressions=0,
            improvements=0,
        )

        assert not result2.all_passed


class TestGlobalBenchmarkSuite:
    """Tests for global benchmark suite functions."""

    def test_get_default_suite_singleton(self):
        """Test get_default_suite returns singleton."""
        suite1 = get_default_suite("test")
        suite2 = get_default_suite("test")

        assert suite1 is suite2
