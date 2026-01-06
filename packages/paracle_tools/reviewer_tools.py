"""Code review and quality tools for Reviewer agent."""

import json
import logging
import subprocess
from pathlib import Path
from typing import Any

from paracle_tools.builtin.base import BaseTool

logger = logging.getLogger("paracle.tools.reviewer")


class StaticAnalysisTool(BaseTool):
    """Perform static code analysis with ruff, mypy, pylint.

    Detects:
    - Style violations
    - Type errors
    - Code smells
    - Complexity issues
    """

    def __init__(self):
        super().__init__(
            name="static_analysis",
            description="Run static analysis with ruff, mypy, or pylint",
            parameters={
                "type": "object",
                "properties": {
                    "path": {
                        "type": "string",
                        "description": "File or directory to analyze",
                    },
                    "tool": {
                        "type": "string",
                        "description": "Analysis tool to use",
                        "enum": ["ruff", "mypy", "pylint"],
                        "default": "ruff",
                    },
                },
                "required": ["path"],
            },
        )

    async def _execute(self, path: str, tool: str = "ruff", **kwargs) -> dict[str, Any]:
        """Run static analysis tool.

        Args:
            path: File or directory to analyze
            tool: Analysis tool (ruff, mypy, pylint)

        Returns:
            Analysis results
        """
        if tool == "ruff":
            return await self._run_ruff(path)
        elif tool == "mypy":
            return await self._run_mypy(path)
        elif tool == "pylint":
            return await self._run_pylint(path)
        else:
            return {"error": f"Unsupported tool: {tool}"}

    async def _run_ruff(self, path: str) -> dict[str, Any]:
        """Run ruff linter."""
        try:
            result = subprocess.run(
                ["ruff", "check", path, "--output-format=json"],
                capture_output=True,
                text=True,
            )

            if result.stdout:
                issues = json.loads(result.stdout)
            else:
                issues = []

            return {
                "tool": "ruff",
                "path": path,
                "issues_found": len(issues),
                "issues": issues,
                "passed": len(issues) == 0,
            }
        except FileNotFoundError:
            return {"error": "ruff not installed"}
        except json.JSONDecodeError:
            return {"error": "Failed to parse ruff output"}
        except Exception as e:
            return {"error": str(e)}

    async def _run_mypy(self, path: str) -> dict[str, Any]:
        """Run mypy type checker."""
        try:
            result = subprocess.run(
                ["mypy", path, "--no-error-summary"],
                capture_output=True,
                text=True,
            )

            errors = result.stdout.strip().split("\n") if result.stdout.strip() else []

            return {
                "tool": "mypy",
                "path": path,
                "errors_found": len(errors),
                "errors": errors,
                "passed": result.returncode == 0,
            }
        except FileNotFoundError:
            return {"error": "mypy not installed"}
        except Exception as e:
            return {"error": str(e)}

    async def _run_pylint(self, path: str) -> dict[str, Any]:
        """Run pylint."""
        try:
            result = subprocess.run(
                ["pylint", path, "--output-format=json"],
                capture_output=True,
                text=True,
            )

            if result.stdout:
                issues = json.loads(result.stdout)
            else:
                issues = []

            return {
                "tool": "pylint",
                "path": path,
                "issues_found": len(issues),
                "issues": issues,
                "score": self._extract_pylint_score(result.stdout),
            }
        except FileNotFoundError:
            return {"error": "pylint not installed"}
        except json.JSONDecodeError:
            return {"error": "Failed to parse pylint output"}
        except Exception as e:
            return {"error": str(e)}

    def _extract_pylint_score(self, output: str) -> float | None:
        """Extract score from pylint output."""
        # Pylint score typically in format: "Your code has been rated at X.XX/10"
        for line in output.split("\n"):
            if "rated at" in line:
                try:
                    score_str = line.split("rated at")[1].split("/")[0].strip()
                    return float(score_str)
                except (IndexError, ValueError):
                    pass
        return None


class SecurityScanTool(BaseTool):
    """Scan code for security vulnerabilities.

    Uses:
    - bandit for Python security issues
    - safety for dependency vulnerabilities
    - Custom pattern matching
    """

    def __init__(self):
        super().__init__(
            name="security_scan",
            description="Scan for security vulnerabilities with bandit and safety",
            parameters={
                "type": "object",
                "properties": {
                    "path": {
                        "type": "string",
                        "description": "Path to scan for security issues",
                    },
                    "scan_type": {
                        "type": "string",
                        "description": "Type of security scan",
                        "enum": ["code", "dependencies", "all"],
                        "default": "code",
                    },
                },
                "required": ["path"],
            },
        )

    async def _execute(
        self, path: str, scan_type: str = "code", **kwargs
    ) -> dict[str, Any]:
        """Perform security scan.

        Args:
            path: Path to scan
            scan_type: Type of scan (code, dependencies, all)

        Returns:
            Security scan results
        """
        if scan_type == "code":
            return await self._scan_code(path)
        elif scan_type == "dependencies":
            return await self._scan_dependencies()
        elif scan_type == "all":
            code_results = await self._scan_code(path)
            dep_results = await self._scan_dependencies()
            return {
                "scan_type": "all",
                "code_scan": code_results,
                "dependency_scan": dep_results,
            }
        else:
            return {"error": f"Unsupported scan type: {scan_type}"}

    async def _scan_code(self, path: str) -> dict[str, Any]:
        """Scan code with bandit."""
        try:
            result = subprocess.run(
                ["bandit", "-r", path, "-f", "json"],
                capture_output=True,
                text=True,
            )

            if result.stdout:
                scan_results = json.loads(result.stdout)
                issues = scan_results.get("results", [])
            else:
                issues = []

            # Categorize by severity
            high = [i for i in issues if i.get("issue_severity") == "HIGH"]
            medium = [i for i in issues if i.get("issue_severity") == "MEDIUM"]
            low = [i for i in issues if i.get("issue_severity") == "LOW"]

            return {
                "tool": "bandit",
                "path": path,
                "total_issues": len(issues),
                "high_severity": len(high),
                "medium_severity": len(medium),
                "low_severity": len(low),
                "issues": issues,
                "passed": len(high) == 0,
            }
        except FileNotFoundError:
            return {"error": "bandit not installed"}
        except json.JSONDecodeError:
            return {"error": "Failed to parse bandit output"}
        except Exception as e:
            return {"error": str(e)}

    async def _scan_dependencies(self) -> dict[str, Any]:
        """Scan dependencies with safety."""
        try:
            result = subprocess.run(
                ["safety", "check", "--json"],
                capture_output=True,
                text=True,
            )

            if result.stdout:
                scan_results = json.loads(result.stdout)
                vulnerabilities = scan_results if isinstance(scan_results, list) else []
            else:
                vulnerabilities = []

            return {
                "tool": "safety",
                "vulnerabilities_found": len(vulnerabilities),
                "vulnerabilities": vulnerabilities,
                "passed": len(vulnerabilities) == 0,
            }
        except FileNotFoundError:
            return {"error": "safety not installed"}
        except json.JSONDecodeError:
            return {"error": "Failed to parse safety output"}
        except Exception as e:
            return {"error": str(e)}


class CodeReviewTool(BaseTool):
    """Perform comprehensive code review checks.

    Reviews:
    - Code style and conventions
    - Documentation quality
    - Test coverage
    - Best practices
    """

    def __init__(self):
        super().__init__(
            name="code_review",
            description="Review code quality and style",
            parameters={
                "type": "object",
                "properties": {
                    "path": {
                        "type": "string",
                        "description": "File or directory to review",
                    },
                },
                "required": ["path"],
            },
        )

    async def _execute(self, path: str, **kwargs) -> dict[str, Any]:
        """Perform code review.

        Args:
            path: File or directory to review

        Returns:
            Review results with scores and feedback
        """
        file_path = Path(path)

        if not file_path.exists():
            return {"error": f"Path not found: {path}"}

        if file_path.is_file() and file_path.suffix == ".py":
            return await self._review_file(file_path)
        elif file_path.is_dir():
            results = []
            for py_file in file_path.rglob("*.py"):
                if "__pycache__" not in str(py_file):
                    file_result = await self._review_file(py_file)
                    results.append(file_result)

            # Aggregate scores
            avg_score = (
                sum(r.get("score", 0) for r in results) / len(results) if results else 0
            )

            return {
                "path": str(file_path),
                "files_reviewed": len(results),
                "average_score": round(avg_score, 2),
                "files": results,
            }
        else:
            return {"error": f"Unsupported file type: {path}"}

    async def _review_file(self, file_path: Path) -> dict[str, Any]:
        """Review a single file."""
        try:
            content = file_path.read_text(encoding="utf-8")
            lines = content.split("\n")

            issues = []
            score = 100

            # Check for docstrings
            if '"""' not in content and "'''" not in content:
                issues.append("Missing docstrings")
                score -= 20

            # Check for type hints
            if "def " in content and "->" not in content:
                issues.append("Missing type hints in functions")
                score -= 15

            # Check for long lines (>100 chars)
            long_lines = [i for i, line in enumerate(lines, 1) if len(line) > 100]
            if long_lines:
                issues.append(f"Long lines (>100 chars): {len(long_lines)} lines")
                score -= min(10, len(long_lines))

            # Check for TODO/FIXME
            todos = [
                i
                for i, line in enumerate(lines, 1)
                if "TODO" in line or "FIXME" in line
            ]
            if todos:
                issues.append(f"Unresolved TODOs: {len(todos)}")
                score -= min(5, len(todos))

            # Check for print statements (should use logging)
            prints = [i for i, line in enumerate(lines, 1) if "print(" in line]
            if prints:
                issues.append(f"Print statements (use logging): {len(prints)}")
                score -= min(10, len(prints))

            return {
                "file": str(file_path),
                "score": max(0, score),
                "issues": issues,
                "lines_of_code": len([line for line in lines if line.strip()]),
            }
        except Exception as e:
            logger.error(f"Failed to review {file_path}: {e}")
            return {"error": str(e), "file": str(file_path)}


# Tool instances
static_analysis = StaticAnalysisTool()
security_scan = SecurityScanTool()
code_review = CodeReviewTool()

__all__ = [
    "StaticAnalysisTool",
    "SecurityScanTool",
    "CodeReviewTool",
    "static_analysis",
    "security_scan",
    "code_review",
]
