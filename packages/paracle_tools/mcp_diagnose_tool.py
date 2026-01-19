"""
MCP Diagnostics Tool - For Paracle Agents

Allows agents to diagnose and fix MCP/UV issues automatically.
"""

from typing import Literal

from paracle_tools.mcp_diagnostics import (
    MCPDiagnosticResult,
    diagnose_all,
    fix_all_issues,
    stop_mcp_processes,
    reinstall_paracle,
)


def mcp_diagnose(
    action: Literal["check", "fix", "stop_processes", "reinstall"] = "check",
    auto_fix: bool = False,
) -> dict[str, dict]:
    """
    Diagnose and fix MCP server and UV issues.

    This tool helps agents troubleshoot common problems:
    - MCP server won't start
    - UV commands failing
    - Process locks on paracle.exe
    - Missing virtual environment

    Args:
        action: Action to perform:
            - "check": Run all diagnostic checks (default)
            - "fix": Run diagnostics and attempt fixes
            - "stop_processes": Stop stuck MCP processes
            - "reinstall": Reinstall Paracle with UV
        auto_fix: If True, automatically apply fixes (use with caution)

    Returns:
        Dictionary with diagnostic results and recommendations

    Examples:
        >>> # Check for issues
        >>> result = mcp_diagnose(action="check")
        >>> if result["summary"]["has_errors"]:
        ...     print("Issues found:", result["issues"])

        >>> # Auto-fix issues
        >>> result = mcp_diagnose(action="fix", auto_fix=True)
        >>> if result["summary"]["fixed"]:
        ...     print("Issues fixed!")

        >>> # Just stop stuck processes
        >>> result = mcp_diagnose(action="stop_processes", auto_fix=True)
    """
    if action == "check":
        # Run diagnostics only
        results = diagnose_all()
        return _format_results(results, action="check")

    elif action == "fix":
        # Run diagnostics and fix issues
        results = fix_all_issues(auto_fix=auto_fix)
        return _format_results(results, action="fix")

    elif action == "stop_processes":
        # Stop stuck processes
        result = stop_mcp_processes(auto_fix=auto_fix)
        return _format_results({"stop_processes": result}, action="stop_processes")

    elif action == "reinstall":
        # Reinstall Paracle
        result = reinstall_paracle(auto_fix=auto_fix)
        return _format_results({"reinstall": result}, action="reinstall")

    return {"error": f"Unknown action: {action}"}


def _format_results(
    results: dict[str, MCPDiagnosticResult],
    action: str,
) -> dict[str, dict]:
    """Format diagnostic results for agent consumption."""
    formatted = {
        "action": action,
        "summary": {
            "total_checks": len(results),
            "healthy": 0,
            "warnings": 0,
            "errors": 0,
            "fixed": 0,
            "has_errors": False,
        },
        "results": {},
        "issues": [],
        "solutions": [],
        "next_steps": [],
    }

    for check_name, result in results.items():
        # Count statuses
        if result.status == "healthy":
            formatted["summary"]["healthy"] += 1
        elif result.status == "warning":
            formatted["summary"]["warnings"] += 1
        elif result.status == "error":
            formatted["summary"]["errors"] += 1
            formatted["summary"]["has_errors"] = True

        if result.fixed:
            formatted["summary"]["fixed"] += 1

        # Format result
        formatted["results"][check_name] = {
            "status": result.status,
            "issue": result.issue,
            "solution": result.solution,
            "fixed": result.fixed,
            "details": result.details,
        }

        # Collect issues and solutions
        if result.issue:
            formatted["issues"].append(f"{check_name}: {result.issue}")

        if result.solution:
            formatted["solutions"].append(f"{check_name}: {result.solution}")

    # Generate next steps
    if formatted["summary"]["has_errors"]:
        if action == "check":
            formatted["next_steps"].append(
                "Run with action='fix' and auto_fix=True to attempt repairs"
            )
        elif not any(r.fixed for r in results.values()):
            formatted["next_steps"].append(
                "Auto-fix was not enabled. Run with auto_fix=True or follow manual solutions"
            )

    if formatted["summary"]["warnings"] > 0:
        formatted["next_steps"].append(
            "Some warnings detected. Review results and take manual action if needed"
        )

    if formatted["summary"]["fixed"] > 0:
        formatted["next_steps"].append(
            "Issues were fixed. Restart VS Code to apply changes"
        )

    if not formatted["summary"]["has_errors"] and not formatted["summary"]["warnings"]:
        formatted["next_steps"].append("All checks passed! System is healthy.")

    return formatted


# Tool metadata for Paracle registration
TOOL_METADATA = {
    "name": "mcp_diagnose",
    "description": "Diagnose and fix MCP server and UV issues",
    "category": "diagnostics",
    "parameters": {
        "action": {
            "type": "string",
            "enum": ["check", "fix", "stop_processes", "reinstall"],
            "default": "check",
            "description": "Action to perform",
        },
        "auto_fix": {
            "type": "boolean",
            "default": False,
            "description": "Automatically apply fixes (use with caution)",
        },
    },
    "returns": {
        "type": "object",
        "description": "Diagnostic results with issues, solutions, and next steps",
    },
    "examples": [
        {
            "description": "Check for MCP/UV issues",
            "code": "mcp_diagnose(action='check')",
        },
        {
            "description": "Auto-fix all issues",
            "code": "mcp_diagnose(action='fix', auto_fix=True)",
        },
        {
            "description": "Stop stuck processes",
            "code": "mcp_diagnose(action='stop_processes', auto_fix=True)",
        },
    ],
}
