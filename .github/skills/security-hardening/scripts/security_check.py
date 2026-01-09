#!/usr/bin/env python3
"""Run security checks on the codebase.

Usage:
    python security_check.py
    python security_check.py --verbose
"""

import re
import sys
from pathlib import Path


class SecurityIssue:
    def __init__(self, file: Path, line: int, severity: str, message: str):
        self.file = file
        self.line = line
        self.severity = severity
        self.message = message


def check_hardcoded_secrets(file_path: Path) -> list[SecurityIssue]:
    """Check for hardcoded secrets."""
    issues = []

    patterns = [
        (r'api[_-]?key\s*=\s*["\']([^"\']+)["\']', "API key"),
        (r'password\s*=\s*["\']([^"\']+)["\']', "Password"),
        (r'secret\s*=\s*["\']([^"\']+)["\']', "Secret"),
        (r'token\s*=\s*["\']([^"\']+)["\']', "Token"),
    ]

    try:
        content = file_path.read_text()
        for line_num, line in enumerate(content.split("\n"), 1):
            for pattern, secret_type in patterns:
                if re.search(pattern, line, re.IGNORECASE):
                    # Skip if using os.getenv or environment variable
                    if "os.getenv" in line or "${" in line or "env[" in line:
                        continue

                    issues.append(
                        SecurityIssue(
                            file=file_path,
                            line=line_num,
                            severity="HIGH",
                            message=f"Potential hardcoded {secret_type} found",
                        )
                    )
    except Exception:
        pass

    return issues


def check_sql_injection(file_path: Path) -> list[SecurityIssue]:
    """Check for SQL injection vulnerabilities."""
    issues = []

    try:
        content = file_path.read_text()
        for line_num, line in enumerate(content.split("\n"), 1):
            # Check for f-strings or format in SQL
            if any(
                sql_keyword in line.upper()
                for sql_keyword in ["SELECT", "INSERT", "UPDATE", "DELETE"]
            ):
                if 'f"' in line or "f'" in line or ".format(" in line:
                    issues.append(
                        SecurityIssue(
                            file=file_path,
                            line=line_num,
                            severity="CRITICAL",
                            message="Potential SQL injection: use parameterized queries",
                        )
                    )
    except Exception:
        pass

    return issues


def run_security_checks(directory: Path, verbose: bool = False) -> tuple[int, int]:
    """Run all security checks."""

    print("🔒 Running security checks...\n")

    all_issues = []

    # Check Python files
    for py_file in directory.rglob("*.py"):
        if ".venv" in str(py_file) or "node_modules" in str(py_file):
            continue

        issues = []
        issues.extend(check_hardcoded_secrets(py_file))
        issues.extend(check_sql_injection(py_file))

        all_issues.extend(issues)

        if verbose and issues:
            print(f"📁 {py_file.relative_to(directory)}")
            for issue in issues:
                print(f"  [{issue.severity}] Line {issue.line}: {issue.message}")

    # Summary
    critical = sum(1 for i in all_issues if i.severity == "CRITICAL")
    high = sum(1 for i in all_issues if i.severity == "HIGH")

    print("\n📊 Security Check Summary:")
    print(f"  Critical: {critical}")
    print(f"  High:     {high}")
    print(f"  Total:    {len(all_issues)}")

    if all_issues:
        print("\n⚠️  Security issues found!")
        return 1, len(all_issues)
    else:
        print("\n✅ No security issues found")
        return 0, 0


if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(description="Run security checks")
    parser.add_argument("--verbose", action="store_true", help="Show detailed output")
    parser.add_argument("--directory", default=".", help="Directory to check")

    args = parser.parse_args()

    directory = Path(args.directory)
    exit_code, _ = run_security_checks(directory, args.verbose)

    sys.exit(exit_code)
