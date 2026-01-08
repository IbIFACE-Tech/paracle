#!/usr/bin/env python3
"""Test runner script with coverage reporting.

Usage:
    python run_tests.py                    # Run all tests
    python run_tests.py --coverage         # Run with coverage
    python run_tests.py --markers unit     # Run only unit tests
    python run_tests.py --failed-first     # Run failed tests first
"""

import subprocess
import sys


def run_tests(coverage=False, markers=None, failed_first=False):
    """Run tests with optional coverage and filtering."""

    cmd = ["pytest"]

    if coverage:
        cmd.extend([
            "--cov=packages",
            "--cov-report=term-missing",
            "--cov-report=html",
            "--cov-fail-under=90",
        ])

    if markers:
        cmd.extend(["-m", markers])

    if failed_first:
        cmd.append("--failed-first")

    # Add standard options
    cmd.extend([
        "-v",
        "--tb=short",
        "--strict-markers",
        "tests/",
    ])

    print(f"Running: {' '.join(cmd)}")
    result = subprocess.run(cmd)

    return result.returncode


if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(description="Run Paracle tests")
    parser.add_argument("--coverage", action="store_true",
                        help="Run with coverage")
    parser.add_argument(
        "--markers", help="Run tests with specific marker (unit, integration, etc.)")
    parser.add_argument("--failed-first", action="store_true",
                        help="Run failed tests first")

    args = parser.parse_args()

    exit_code = run_tests(
        coverage=args.coverage,
        markers=args.markers,
        failed_first=args.failed_first,
    )

    sys.exit(exit_code)
