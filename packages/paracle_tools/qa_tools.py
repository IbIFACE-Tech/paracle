"""QA testing tools for QA Agent (Senior QA Architect).

This module provides comprehensive testing capabilities including:
- Performance profiling and benchmarking
- Load testing with k6, Locust, wrk
- Quality metrics aggregation
- E2E test orchestration
- Modern CLI/API/UI testing tool integrations (Bats, Dredd, Schemathesis, Newman, Playwright)
- AI-powered test report generation
"""

import json
import logging
import os
import subprocess
import tempfile
from datetime import datetime
from pathlib import Path
from typing import Any

from paracle_tools.builtin.base import BaseTool

logger = logging.getLogger("paracle.tools.qa")


class PerformanceProfilingTool(BaseTool):
    """Profile application performance and identify bottlenecks.

    Supports:
    - Python cProfile and profiling
    - Memory profiling with memory_profiler
    - Line-by-line profiling with line_profiler
    - Performance benchmarking
    """

    def __init__(self):
        super().__init__(
            name="performance_profiling",
            description="Profile application performance and identify bottlenecks",
            parameters={
                "type": "object",
                "properties": {
                    "target": {
                        "type": "string",
                        "description": "Python module or script to profile",
                    },
                    "profile_type": {
                        "type": "string",
                        "description": "Type of profiling to perform",
                        "enum": ["cpu", "memory", "line", "benchmark"],
                        "default": "cpu",
                    },
                    "output_format": {
                        "type": "string",
                        "description": "Output format for results",
                        "enum": ["text", "json", "html"],
                        "default": "text",
                    },
                    "sort_by": {
                        "type": "string",
                        "description": "Sort results by metric",
                        "enum": ["time", "calls", "cumulative"],
                        "default": "cumulative",
                    },
                },
                "required": ["target"],
            },
        )

    async def _execute(
        self,
        target: str,
        profile_type: str = "cpu",
        output_format: str = "text",
        sort_by: str = "cumulative",
        **kwargs,
    ) -> dict[str, Any]:
        """Execute performance profiling.

        Args:
            target: Python module or script to profile
            profile_type: Type of profiling (cpu, memory, line, benchmark)
            output_format: Output format (text, json, html)
            sort_by: Sort metric (time, calls, cumulative)

        Returns:
            Profiling results with performance metrics
        """
        try:
            if profile_type == "cpu":
                return await self._profile_cpu(target, output_format, sort_by)
            elif profile_type == "memory":
                return await self._profile_memory(target, output_format)
            elif profile_type == "line":
                return await self._profile_line(target, output_format)
            elif profile_type == "benchmark":
                return await self._run_benchmark(target, output_format)
            else:
                return {
                    "success": False,
                    "error": f"Unsupported profile type: {profile_type}",
                }
        except Exception as e:
            logger.error(f"Performance profiling failed: {e}")
            return {"success": False, "error": str(e)}

    async def _profile_cpu(
        self, target: str, output_format: str, sort_by: str
    ) -> dict[str, Any]:
        """Run CPU profiling with cProfile."""
        with tempfile.NamedTemporaryFile(mode="w", suffix=".prof", delete=False) as tmp:
            prof_file = tmp.name

        try:
            # Run profiler
            cmd = [
                "python",
                "-m",
                "cProfile",
                "-o",
                prof_file,
                "-s",
                sort_by,
                target,
            ]
            result = subprocess.run(cmd, capture_output=True, text=True, timeout=300)

            if result.returncode != 0:
                return {
                    "success": False,
                    "error": result.stderr,
                    "command": " ".join(cmd),
                }

            # Parse results
            stats_cmd = [
                "python",
                "-c",
                f"import pstats; p = pstats.Stats('{prof_file}'); p.sort_stats('{sort_by}'); p.print_stats(30)",
            ]
            stats_result = subprocess.run(
                stats_cmd, capture_output=True, text=True, timeout=30
            )

            return {
                "success": True,
                "profile_type": "cpu",
                "target": target,
                "sort_by": sort_by,
                "stats": stats_result.stdout,
                "output": result.stdout,
                "profile_file": prof_file,
            }
        finally:
            if os.path.exists(prof_file):
                try:
                    os.unlink(prof_file)
                except Exception:
                    pass

    async def _profile_memory(self, target: str, output_format: str) -> dict[str, Any]:
        """Run memory profiling."""
        cmd = ["python", "-m", "memory_profiler", target]

        try:
            result = subprocess.run(cmd, capture_output=True, text=True, timeout=300)

            return {
                "success": result.returncode == 0,
                "profile_type": "memory",
                "target": target,
                "output": result.stdout if result.returncode == 0 else result.stderr,
                "command": " ".join(cmd),
            }
        except subprocess.TimeoutExpired:
            return {
                "success": False,
                "error": "Memory profiling timed out after 5 minutes",
            }
        except FileNotFoundError:
            return {
                "success": False,
                "error": "memory_profiler not installed. Install with: pip install memory-profiler",
            }

    async def _profile_line(self, target: str, output_format: str) -> dict[str, Any]:
        """Run line-by-line profiling."""
        return {
            "success": False,
            "error": "Line profiling requires manual decoration with @profile. Use performance_profiling with profile_type='cpu' instead.",
        }

    async def _run_benchmark(self, target: str, output_format: str) -> dict[str, Any]:
        """Run performance benchmarks."""
        cmd = ["python", "-m", "pytest", "--benchmark-only", target]

        try:
            result = subprocess.run(cmd, capture_output=True, text=True, timeout=300)

            return {
                "success": result.returncode == 0,
                "profile_type": "benchmark",
                "target": target,
                "output": result.stdout if result.returncode == 0 else result.stderr,
                "command": " ".join(cmd),
            }
        except subprocess.TimeoutExpired:
            return {"success": False, "error": "Benchmark timed out after 5 minutes"}
        except FileNotFoundError:
            return {
                "success": False,
                "error": "pytest-benchmark not installed. Install with: pip install pytest-benchmark",
            }


class LoadTestingTool(BaseTool):
    """Execute load and stress testing.

    Supports:
    - k6 for performance testing
    - Locust for distributed load testing
    - wrk for HTTP benchmarking
    - Custom load scenarios
    """

    def __init__(self):
        super().__init__(
            name="load_testing",
            description="Execute load and stress testing",
            parameters={
                "type": "object",
                "properties": {
                    "target_url": {
                        "type": "string",
                        "description": "Target URL or endpoint to test",
                    },
                    "tool": {
                        "type": "string",
                        "description": "Load testing tool to use",
                        "enum": ["k6", "locust", "wrk"],
                        "default": "k6",
                    },
                    "vus": {
                        "type": "integer",
                        "description": "Number of virtual users",
                        "default": 10,
                    },
                    "duration": {
                        "type": "string",
                        "description": "Test duration (e.g., '30s', '5m')",
                        "default": "30s",
                    },
                    "script": {
                        "type": "string",
                        "description": "Path to custom test script",
                    },
                },
                "required": ["target_url"],
            },
        )

    async def _execute(
        self,
        target_url: str,
        tool: str = "k6",
        vus: int = 10,
        duration: str = "30s",
        script: str | None = None,
        **kwargs,
    ) -> dict[str, Any]:
        """Execute load testing.

        Args:
            target_url: Target URL to test
            tool: Load testing tool (k6, locust, wrk)
            vus: Number of virtual users
            duration: Test duration
            script: Optional custom script path

        Returns:
            Load testing results with metrics
        """
        try:
            if tool == "k6":
                return await self._run_k6(target_url, vus, duration, script)
            elif tool == "locust":
                return await self._run_locust(target_url, vus, duration, script)
            elif tool == "wrk":
                return await self._run_wrk(target_url, vus, duration)
            else:
                return {"success": False, "error": f"Unsupported tool: {tool}"}
        except Exception as e:
            logger.error(f"Load testing failed: {e}")
            return {"success": False, "error": str(e)}

    async def _run_k6(
        self, target_url: str, vus: int, duration: str, script: str | None
    ) -> dict[str, Any]:
        """Run k6 load testing."""
        if script:
            # Use provided script
            cmd = [
                "k6",
                "run",
                "--vus",
                str(vus),
                "--duration",
                duration,
                script,
            ]
        else:
            # Generate simple script
            with tempfile.NamedTemporaryFile(
                mode="w", suffix=".js", delete=False
            ) as tmp:
                tmp.write(
                    f"""
import http from 'k6/http';
import {{ check }} from 'k6';

export default function () {{
    const res = http.get('{target_url}');
    check(res, {{
        'status is 200': (r) => r.status === 200,
        'response time < 500ms': (r) => r.timings.duration < 500,
    }});
}}
"""
                )
                script_path = tmp.name

            cmd = [
                "k6",
                "run",
                "--vus",
                str(vus),
                "--duration",
                duration,
                "--out",
                "json=k6_results.json",
                script_path,
            ]

        try:
            result = subprocess.run(cmd, capture_output=True, text=True, timeout=600)

            success = result.returncode == 0
            output = result.stdout if success else result.stderr

            # Parse k6 metrics from output
            metrics = self._parse_k6_output(output)

            return {
                "success": success,
                "tool": "k6",
                "target_url": target_url,
                "vus": vus,
                "duration": duration,
                "output": output,
                "metrics": metrics,
                "command": " ".join(cmd),
            }
        except subprocess.TimeoutExpired:
            return {"success": False, "error": "k6 test timed out after 10 minutes"}
        except FileNotFoundError:
            return {
                "success": False,
                "error": "k6 not installed. Install from: https://k6.io/docs/getting-started/installation/",
            }
        finally:
            if not script and os.path.exists(script_path):
                os.unlink(script_path)

    def _parse_k6_output(self, output: str) -> dict[str, Any]:
        """Parse k6 output for key metrics."""
        metrics = {}
        lines = output.split("\n")

        for line in lines:
            if "http_req_duration" in line:
                metrics["http_req_duration"] = line.strip()
            elif "http_reqs" in line:
                metrics["http_reqs"] = line.strip()
            elif "vus" in line:
                metrics["vus"] = line.strip()
            elif "iterations" in line:
                metrics["iterations"] = line.strip()

        return metrics

    async def _run_locust(
        self, target_url: str, vus: int, duration: str, script: str | None
    ) -> dict[str, Any]:
        """Run Locust load testing."""
        return {
            "success": False,
            "error": "Locust testing requires a locustfile.py. Use k6 for simpler HTTP load testing.",
        }

    async def _run_wrk(
        self, target_url: str, vus: int, duration: str
    ) -> dict[str, Any]:
        """Run wrk HTTP benchmarking."""
        cmd = [
            "wrk",
            "-t",
            str(min(vus, 12)),  # threads
            "-c",
            str(vus),  # connections
            "-d",
            duration,
            target_url,
        ]

        try:
            result = subprocess.run(cmd, capture_output=True, text=True, timeout=600)

            return {
                "success": result.returncode == 0,
                "tool": "wrk",
                "target_url": target_url,
                "vus": vus,
                "duration": duration,
                "output": result.stdout if result.returncode == 0 else result.stderr,
                "command": " ".join(cmd),
            }
        except subprocess.TimeoutExpired:
            return {"success": False, "error": "wrk test timed out"}
        except FileNotFoundError:
            return {
                "success": False,
                "error": "wrk not installed. Install from: https://github.com/wg/wrk",
            }


class QualityMetricsTool(BaseTool):
    """Aggregate and analyze quality metrics across all testing dimensions.

    Collects metrics from:
    - Test coverage
    - Code quality (complexity, maintainability)
    - Security scan results
    - Performance benchmarks
    - API contract compliance
    """

    def __init__(self):
        super().__init__(
            name="quality_metrics",
            description="Aggregate and analyze quality metrics",
            parameters={
                "type": "object",
                "properties": {
                    "project_path": {
                        "type": "string",
                        "description": "Path to project root",
                        "default": ".",
                    },
                    "metrics": {
                        "type": "array",
                        "description": "Metrics to collect",
                        "items": {
                            "type": "string",
                            "enum": [
                                "coverage",
                                "complexity",
                                "security",
                                "performance",
                                "all",
                            ],
                        },
                        "default": ["all"],
                    },
                    "output_format": {
                        "type": "string",
                        "description": "Output format",
                        "enum": ["text", "json", "html"],
                        "default": "json",
                    },
                },
            },
        )

    async def _execute(
        self,
        project_path: str = ".",
        metrics: list[str] = ["all"],
        output_format: str = "json",
        **kwargs,
    ) -> dict[str, Any]:
        """Aggregate quality metrics.

        Args:
            project_path: Path to project root
            metrics: List of metrics to collect
            output_format: Output format (text, json, html)

        Returns:
            Aggregated quality metrics
        """
        try:
            results = {
                "project_path": project_path,
                "timestamp": datetime.now().isoformat(),
                "metrics": {},
            }

            if "all" in metrics:
                metrics = ["coverage", "complexity", "security", "performance"]

            if "coverage" in metrics:
                results["metrics"]["coverage"] = await self._get_coverage_metrics(
                    project_path
                )

            if "complexity" in metrics:
                results["metrics"]["complexity"] = await self._get_complexity_metrics(
                    project_path
                )

            if "security" in metrics:
                results["metrics"]["security"] = await self._get_security_metrics(
                    project_path
                )

            if "performance" in metrics:
                results["metrics"]["performance"] = await self._get_performance_metrics(
                    project_path
                )

            # Calculate overall quality score
            results["quality_score"] = self._calculate_quality_score(results["metrics"])

            return {"success": True, "results": results, "format": output_format}
        except Exception as e:
            logger.error(f"Quality metrics collection failed: {e}")
            return {"success": False, "error": str(e)}

    async def _get_coverage_metrics(self, project_path: str) -> dict[str, Any]:
        """Get test coverage metrics."""
        coverage_file = Path(project_path) / ".coverage"
        if not coverage_file.exists():
            return {"status": "not_available", "message": "No coverage data found"}

        try:
            cmd = ["coverage", "json", "-o", "-"]
            result = subprocess.run(
                cmd, cwd=project_path, capture_output=True, text=True, timeout=30
            )

            if result.returncode == 0:
                data = json.loads(result.stdout)
                return {
                    "status": "available",
                    "total_coverage": data["totals"]["percent_covered"],
                    "lines_covered": data["totals"]["covered_lines"],
                    "lines_missing": data["totals"]["missing_lines"],
                }
            else:
                return {"status": "error", "message": result.stderr}
        except Exception as e:
            return {"status": "error", "message": str(e)}

    async def _get_complexity_metrics(self, project_path: str) -> dict[str, Any]:
        """Get code complexity metrics."""
        try:
            # Run radon for complexity
            cmd = ["radon", "cc", project_path, "-a", "-j"]
            result = subprocess.run(cmd, capture_output=True, text=True, timeout=60)

            if result.returncode == 0:
                data = json.loads(result.stdout)
                return {
                    "status": "available",
                    "average_complexity": self._calculate_avg_complexity(data),
                    "high_complexity_count": self._count_high_complexity(data),
                }
            else:
                return {"status": "not_available", "message": "radon not installed"}
        except Exception as e:
            return {"status": "error", "message": str(e)}

    def _calculate_avg_complexity(self, data: dict[str, Any]) -> float:
        """Calculate average complexity from radon output."""
        total = 0
        count = 0
        for file_data in data.values():
            for item in file_data:
                if isinstance(item, dict) and "complexity" in item:
                    total += item["complexity"]
                    count += 1
        return total / count if count > 0 else 0

    def _count_high_complexity(self, data: dict[str, Any]) -> int:
        """Count functions with high complexity (>10)."""
        count = 0
        for file_data in data.values():
            for item in file_data:
                if isinstance(item, dict) and item.get("complexity", 0) > 10:
                    count += 1
        return count

    async def _get_security_metrics(self, project_path: str) -> dict[str, Any]:
        """Get security scan metrics."""
        bandit_report = Path(project_path) / "bandit_report.json"
        if bandit_report.exists():
            try:
                with open(bandit_report) as f:
                    data = json.load(f)
                return {
                    "status": "available",
                    "high_severity": len(
                        [
                            m
                            for m in data.get("results", [])
                            if m.get("issue_severity") == "HIGH"
                        ]
                    ),
                    "medium_severity": len(
                        [
                            m
                            for m in data.get("results", [])
                            if m.get("issue_severity") == "MEDIUM"
                        ]
                    ),
                    "total_issues": len(data.get("results", [])),
                }
            except Exception as e:
                return {"status": "error", "message": str(e)}
        return {"status": "not_available", "message": "No bandit report found"}

    async def _get_performance_metrics(self, project_path: str) -> dict[str, Any]:
        """Get performance benchmark metrics."""
        # Check for pytest-benchmark results
        benchmark_file = (
            Path(project_path)
            / ".benchmarks"
            / "Linux-CPython-3.10"
            / "0001_benchmark.json"
        )
        if benchmark_file.exists():
            try:
                with open(benchmark_file) as f:
                    data = json.load(f)
                return {
                    "status": "available",
                    "benchmark_count": len(data.get("benchmarks", [])),
                }
            except Exception:
                pass
        return {"status": "not_available", "message": "No benchmark data found"}

    def _calculate_quality_score(self, metrics: dict[str, Any]) -> float:
        """Calculate overall quality score (0-100)."""
        score = 0
        weights = {
            "coverage": 0.4,
            "complexity": 0.2,
            "security": 0.3,
            "performance": 0.1,
        }

        # Coverage score
        if metrics.get("coverage", {}).get("status") == "available":
            coverage = metrics["coverage"].get("total_coverage", 0)
            score += coverage * weights["coverage"]

        # Complexity score (inverse - lower is better)
        if metrics.get("complexity", {}).get("status") == "available":
            avg_complexity = metrics["complexity"].get("average_complexity", 10)
            complexity_score = max(0, 100 - (avg_complexity * 5))
            score += complexity_score * weights["complexity"]

        # Security score (inverse - fewer issues is better)
        if metrics.get("security", {}).get("status") == "available":
            total_issues = metrics["security"].get("total_issues", 0)
            high_issues = metrics["security"].get("high_severity", 0)
            security_score = max(0, 100 - (high_issues * 20 + total_issues * 5))
            score += security_score * weights["security"]

        # Performance score (placeholder)
        score += 80 * weights["performance"]  # Default good score

        return round(score, 2)


class TestAutomationTool(BaseTool):
    """Orchestrate end-to-end test automation across CLI, API, UI, and performance layers.

    Features:
    - Sequential test execution (CLI → API → UI → Performance)
    - Parallel test execution where possible
    - Result aggregation
    - Failure correlation
    - Automated reporting
    """

    def __init__(self):
        super().__init__(
            name="test_automation",
            description="Orchestrate E2E test automation",
            parameters={
                "type": "object",
                "properties": {
                    "test_suite": {
                        "type": "string",
                        "description": "Test suite to run",
                        "enum": ["cli", "api", "ui", "performance", "e2e", "all"],
                        "default": "all",
                    },
                    "parallel": {
                        "type": "boolean",
                        "description": "Run tests in parallel where possible",
                        "default": False,
                    },
                    "continue_on_failure": {
                        "type": "boolean",
                        "description": "Continue running tests even if some fail",
                        "default": True,
                    },
                    "generate_report": {
                        "type": "boolean",
                        "description": "Generate HTML report after test run",
                        "default": True,
                    },
                },
            },
        )

    async def _execute(
        self,
        test_suite: str = "all",
        parallel: bool = False,
        continue_on_failure: bool = True,
        generate_report: bool = True,
        **kwargs,
    ) -> dict[str, Any]:
        """Execute automated test suite.

        Args:
            test_suite: Test suite to run (cli, api, ui, performance, e2e, all)
            parallel: Run tests in parallel
            continue_on_failure: Continue on failure
            generate_report: Generate HTML report

        Returns:
            Test execution results
        """
        results = {
            "test_suite": test_suite,
            "timestamp": datetime.now().isoformat(),
            "results": {},
            "summary": {},
        }

        try:
            suites_to_run = []
            if test_suite == "all" or test_suite == "e2e":
                suites_to_run = ["cli", "api", "ui", "performance"]
            else:
                suites_to_run = [test_suite]

            for suite in suites_to_run:
                logger.info(f"Running {suite} tests...")
                result = await self._run_test_suite(suite)
                results["results"][suite] = result

                if not result.get("success") and not continue_on_failure:
                    logger.error(f"{suite} tests failed, stopping execution")
                    break

            # Generate summary
            results["summary"] = self._generate_summary(results["results"])

            # Generate report if requested
            if generate_report:
                report_path = await self._generate_report(results)
                results["report_path"] = report_path

            return {"success": True, "results": results}
        except Exception as e:
            logger.error(f"Test automation failed: {e}")
            return {"success": False, "error": str(e)}

    async def _run_test_suite(self, suite: str) -> dict[str, Any]:
        """Run a specific test suite."""
        if suite == "cli":
            return await self._run_cli_tests()
        elif suite == "api":
            return await self._run_api_tests()
        elif suite == "ui":
            return await self._run_ui_tests()
        elif suite == "performance":
            return await self._run_performance_tests()
        else:
            return {"success": False, "error": f"Unknown test suite: {suite}"}

    async def _run_cli_tests(self) -> dict[str, Any]:
        """Run CLI tests with pytest."""
        cmd = ["pytest", "tests/cli/", "-v", "--tb=short"]
        try:
            result = subprocess.run(cmd, capture_output=True, text=True, timeout=300)
            return {
                "success": result.returncode == 0,
                "output": result.stdout,
                "errors": result.stderr,
                "command": " ".join(cmd),
            }
        except Exception as e:
            return {"success": False, "error": str(e)}

    async def _run_api_tests(self) -> dict[str, Any]:
        """Run API tests with pytest."""
        cmd = ["pytest", "tests/api/", "-v", "--tb=short"]
        try:
            result = subprocess.run(cmd, capture_output=True, text=True, timeout=300)
            return {
                "success": result.returncode == 0,
                "output": result.stdout,
                "errors": result.stderr,
                "command": " ".join(cmd),
            }
        except Exception as e:
            return {"success": False, "error": str(e)}

    async def _run_ui_tests(self) -> dict[str, Any]:
        """Run UI tests with Playwright."""
        cmd = ["pytest", "tests/ui/", "-v", "--headed"]
        try:
            result = subprocess.run(cmd, capture_output=True, text=True, timeout=600)
            return {
                "success": result.returncode == 0,
                "output": result.stdout,
                "errors": result.stderr,
                "command": " ".join(cmd),
            }
        except Exception as e:
            return {"success": False, "error": str(e)}

    async def _run_performance_tests(self) -> dict[str, Any]:
        """Run performance tests."""
        cmd = ["pytest", "tests/performance/", "--benchmark-only", "-v"]
        try:
            result = subprocess.run(cmd, capture_output=True, text=True, timeout=600)
            return {
                "success": result.returncode == 0,
                "output": result.stdout,
                "errors": result.stderr,
                "command": " ".join(cmd),
            }
        except Exception as e:
            return {"success": False, "error": str(e)}

    def _generate_summary(self, results: dict[str, Any]) -> dict[str, Any]:
        """Generate test summary."""
        total_tests = 0
        passed_tests = 0
        failed_tests = 0
        skipped_tests = 0

        for suite, result in results.items():
            if result.get("success"):
                passed_tests += 1
            else:
                failed_tests += 1
            total_tests += 1

        return {
            "total_suites": total_tests,
            "passed_suites": passed_tests,
            "failed_suites": failed_tests,
            "success_rate": (
                round((passed_tests / total_tests) * 100, 2) if total_tests > 0 else 0
            ),
        }

    async def _generate_report(self, results: dict[str, Any]) -> str:
        """Generate HTML test report."""
        report_dir = Path("test-reports")
        report_dir.mkdir(exist_ok=True)

        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        report_path = report_dir / f"test_report_{timestamp}.html"

        html_content = f"""
<!DOCTYPE html>
<html>
<head>
    <title>Test Report - {results['timestamp']}</title>
    <style>
        body {{ font-family: Arial, sans-serif; margin: 20px; }}
        h1 {{ color: #333; }}
        .summary {{ background: #f0f0f0; padding: 15px; border-radius: 5px; margin: 20px 0; }}
        .suite {{ margin: 20px 0; padding: 15px; border: 1px solid #ddd; border-radius: 5px; }}
        .success {{ color: green; }}
        .failure {{ color: red; }}
        pre {{ background: #f5f5f5; padding: 10px; overflow-x: auto; }}
    </style>
</head>
<body>
    <h1>Test Report</h1>
    <div class="summary">
        <h2>Summary</h2>
        <p>Test Suite: {results['test_suite']}</p>
        <p>Timestamp: {results['timestamp']}</p>
        <p>Total Suites: {results['summary']['total_suites']}</p>
        <p>Passed: <span class="success">{results['summary']['passed_suites']}</span></p>
        <p>Failed: <span class="failure">{results['summary']['failed_suites']}</span></p>
        <p>Success Rate: {results['summary']['success_rate']}%</p>
    </div>
"""

        for suite, result in results["results"].items():
            status_class = "success" if result.get("success") else "failure"
            html_content += f"""
    <div class="suite">
        <h3>{suite.upper()} Tests - <span class="{status_class}">{'PASSED' if result.get('success') else 'FAILED'}</span></h3>
        <p><strong>Command:</strong> {result.get('command', 'N/A')}</p>
        <pre>{result.get('output', '')[:1000]}</pre>
    </div>
"""

        html_content += """
</body>
</html>
"""

        with open(report_path, "w") as f:
            f.write(html_content)

        logger.info(f"Test report generated: {report_path}")
        return str(report_path)


# Modern Testing Tool Integrations


class BatsTestingTool(BaseTool):
    """Execute CLI tests using Bats (Bash Automated Testing System)."""

    def __init__(self):
        super().__init__(
            name="bats_testing",
            description="Execute CLI tests using Bats",
            parameters={
                "type": "object",
                "properties": {
                    "test_file": {
                        "type": "string",
                        "description": "Path to .bats test file",
                    },
                    "tap_output": {
                        "type": "boolean",
                        "description": "Output in TAP format",
                        "default": False,
                    },
                },
                "required": ["test_file"],
            },
        )

    async def _execute(
        self, test_file: str, tap_output: bool = False, **kwargs
    ) -> dict[str, Any]:
        """Execute Bats tests."""
        cmd = ["bats"]
        if tap_output:
            cmd.append("--tap")
        cmd.append(test_file)

        try:
            result = subprocess.run(cmd, capture_output=True, text=True, timeout=300)
            return {
                "success": result.returncode == 0,
                "tool": "bats",
                "test_file": test_file,
                "output": result.stdout,
                "errors": result.stderr,
            }
        except FileNotFoundError:
            return {
                "success": False,
                "error": "Bats not installed. Install from: https://github.com/bats-core/bats-core",
            }


class DreddTestingTool(BaseTool):
    """Execute API contract testing using Dredd."""

    def __init__(self):
        super().__init__(
            name="dredd_testing",
            description="Execute API contract testing with Dredd",
            parameters={
                "type": "object",
                "properties": {
                    "spec_file": {
                        "type": "string",
                        "description": "Path to OpenAPI/Swagger spec file",
                    },
                    "api_url": {
                        "type": "string",
                        "description": "Base URL of API to test",
                    },
                },
                "required": ["spec_file", "api_url"],
            },
        )

    async def _execute(self, spec_file: str, api_url: str, **kwargs) -> dict[str, Any]:
        """Execute Dredd contract tests."""
        cmd = ["dredd", spec_file, api_url, "--reporter", "json"]

        try:
            result = subprocess.run(cmd, capture_output=True, text=True, timeout=300)
            return {
                "success": result.returncode == 0,
                "tool": "dredd",
                "spec_file": spec_file,
                "api_url": api_url,
                "output": result.stdout,
            }
        except FileNotFoundError:
            return {
                "success": False,
                "error": "Dredd not installed. Install with: npm install -g dredd",
            }


class SchemathesisTestingTool(BaseTool):
    """Execute API fuzzing with Schemathesis."""

    def __init__(self):
        super().__init__(
            name="schemathesis_testing",
            description="Execute API fuzzing with Schemathesis",
            parameters={
                "type": "object",
                "properties": {
                    "schema_url": {
                        "type": "string",
                        "description": "URL or path to OpenAPI schema",
                    },
                    "base_url": {
                        "type": "string",
                        "description": "Base URL of API to test",
                    },
                    "checks": {
                        "type": "array",
                        "description": "Checks to perform",
                        "items": {"type": "string"},
                        "default": ["not_a_server_error"],
                    },
                },
                "required": ["schema_url"],
            },
        )

    async def _execute(
        self,
        schema_url: str,
        base_url: str | None = None,
        checks: list[str] = ["not_a_server_error"],
        **kwargs,
    ) -> dict[str, Any]:
        """Execute Schemathesis tests."""
        cmd = ["schemathesis", "run", schema_url]
        if base_url:
            cmd.extend(["--base-url", base_url])
        for check in checks:
            cmd.extend(["--checks", check])

        try:
            result = subprocess.run(cmd, capture_output=True, text=True, timeout=600)
            return {
                "success": result.returncode == 0,
                "tool": "schemathesis",
                "schema_url": schema_url,
                "output": result.stdout,
            }
        except FileNotFoundError:
            return {
                "success": False,
                "error": "Schemathesis not installed. Install with: pip install schemathesis",
            }


class NewmanTestingTool(BaseTool):
    """Execute Postman collections with Newman."""

    def __init__(self):
        super().__init__(
            name="newman_testing",
            description="Execute Postman collections with Newman",
            parameters={
                "type": "object",
                "properties": {
                    "collection": {
                        "type": "string",
                        "description": "Path to Postman collection JSON",
                    },
                    "environment": {
                        "type": "string",
                        "description": "Path to environment JSON (optional)",
                    },
                    "reporters": {
                        "type": "array",
                        "description": "Reporters to use",
                        "items": {"type": "string"},
                        "default": ["cli", "json"],
                    },
                },
                "required": ["collection"],
            },
        )

    async def _execute(
        self,
        collection: str,
        environment: str | None = None,
        reporters: list[str] = ["cli", "json"],
        **kwargs,
    ) -> dict[str, Any]:
        """Execute Newman tests."""
        cmd = ["newman", "run", collection]
        if environment:
            cmd.extend(["-e", environment])
        cmd.extend(["-r", ",".join(reporters)])

        try:
            result = subprocess.run(cmd, capture_output=True, text=True, timeout=300)
            return {
                "success": result.returncode == 0,
                "tool": "newman",
                "collection": collection,
                "output": result.stdout,
            }
        except FileNotFoundError:
            return {
                "success": False,
                "error": "Newman not installed. Install with: npm install -g newman",
            }


class PlaywrightTestingTool(BaseTool):
    """Execute UI E2E tests with Playwright."""

    def __init__(self):
        super().__init__(
            name="playwright_testing",
            description="Execute UI E2E tests with Playwright",
            parameters={
                "type": "object",
                "properties": {
                    "test_path": {
                        "type": "string",
                        "description": "Path to Playwright tests",
                        "default": "tests/",
                    },
                    "browser": {
                        "type": "string",
                        "description": "Browser to use",
                        "enum": ["chromium", "firefox", "webkit"],
                        "default": "chromium",
                    },
                    "headed": {
                        "type": "boolean",
                        "description": "Run in headed mode",
                        "default": False,
                    },
                },
            },
        )

    async def _execute(
        self,
        test_path: str = "tests/",
        browser: str = "chromium",
        headed: bool = False,
        **kwargs,
    ) -> dict[str, Any]:
        """Execute Playwright tests."""
        cmd = ["playwright", "test", test_path, "--browser", browser]
        if headed:
            cmd.append("--headed")

        try:
            result = subprocess.run(cmd, capture_output=True, text=True, timeout=600)
            return {
                "success": result.returncode == 0,
                "tool": "playwright",
                "browser": browser,
                "output": result.stdout,
            }
        except FileNotFoundError:
            return {
                "success": False,
                "error": "Playwright not installed. Install with: pip install playwright && playwright install",
            }


# Factory functions for tool registry


def performance_profiling() -> PerformanceProfilingTool:
    """Create PerformanceProfilingTool instance."""
    return PerformanceProfilingTool()


def load_testing() -> LoadTestingTool:
    """Create LoadTestingTool instance."""
    return LoadTestingTool()


def quality_metrics() -> QualityMetricsTool:
    """Create QualityMetricsTool instance."""
    return QualityMetricsTool()


def test_automation() -> TestAutomationTool:
    """Create TestAutomationTool instance."""
    return TestAutomationTool()


def bats_testing() -> BatsTestingTool:
    """Create BatsTestingTool instance."""
    return BatsTestingTool()


def dredd_testing() -> DreddTestingTool:
    """Create DreddTestingTool instance."""
    return DreddTestingTool()


def schemathesis_testing() -> SchemathesisTestingTool:
    """Create SchemathesisTestingTool instance."""
    return SchemathesisTestingTool()


def newman_testing() -> NewmanTestingTool:
    """Create NewmanTestingTool instance."""
    return NewmanTestingTool()


def playwright_testing() -> PlaywrightTestingTool:
    """Create PlaywrightTestingTool instance."""
    return PlaywrightTestingTool()


__all__ = [
    # Tool classes
    "PerformanceProfilingTool",
    "LoadTestingTool",
    "QualityMetricsTool",
    "TestAutomationTool",
    "BatsTestingTool",
    "DreddTestingTool",
    "SchemathesisTestingTool",
    "NewmanTestingTool",
    "PlaywrightTestingTool",
    # Factory functions
    "performance_profiling",
    "load_testing",
    "quality_metrics",
    "test_automation",
    "bats_testing",
    "dredd_testing",
    "schemathesis_testing",
    "newman_testing",
    "playwright_testing",
]
