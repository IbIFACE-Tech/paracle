"""
MCP & UV Troubleshooting Tool for Paracle Agents

This tool allows agents to diagnose and fix common MCP server and UV issues.
"""

import subprocess
import sys
from pathlib import Path
from typing import Literal

from pydantic import BaseModel, Field


class MCPDiagnosticResult(BaseModel):
    """Result of MCP/UV diagnostic check."""

    status: Literal["healthy", "warning", "error"]
    issue: str | None = None
    solution: str | None = None
    fixed: bool = False
    details: dict[str, str] = Field(default_factory=dict)


def find_project_root() -> Path:
    """Find the project root directory (where pyproject.toml is)."""
    current = Path.cwd()
    for parent in [current, *current.parents]:
        if (parent / "pyproject.toml").exists():
            return parent
    return current


def check_uv_available() -> MCPDiagnosticResult:
    """Check if UV is installed and available."""
    try:
        result = subprocess.run(
            ["uv", "--version"],
            capture_output=True,
            text=True,
            timeout=5,
        )
        if result.returncode == 0:
            return MCPDiagnosticResult(
                status="healthy",
                details={"uv_version": result.stdout.strip()},
            )
        return MCPDiagnosticResult(
            status="error",
            issue="UV command failed",
            solution="Reinstall UV: pip install uv",
            details={"error": result.stderr},
        )
    except FileNotFoundError:
        return MCPDiagnosticResult(
            status="error",
            issue="UV not installed",
            solution="Install UV: pip install uv or curl -LsSf https://astral.sh/uv/install.sh | sh",
        )
    except Exception as e:
        return MCPDiagnosticResult(
            status="error",
            issue=f"UV check failed: {e}",
            solution="Check UV installation",
        )


def check_venv_exists() -> MCPDiagnosticResult:
    """Check if virtual environment exists."""
    project_root = find_project_root()
    venv_paths = [
        project_root / ".venv",
        project_root / "venv",
    ]

    for venv_path in venv_paths:
        if venv_path.exists():
            python_paths = [
                venv_path / "Scripts" / "python.exe",  # Windows
                venv_path / "bin" / "python",  # Unix
            ]
            for python_path in python_paths:
                if python_path.exists():
                    return MCPDiagnosticResult(
                        status="healthy",
                        details={
                            "venv_path": str(venv_path),
                            "python_path": str(python_path),
                        },
                    )

    return MCPDiagnosticResult(
        status="error",
        issue="Virtual environment not found",
        solution="Run: uv sync",
        details={"searched_paths": [str(p) for p in venv_paths]},
    )


def check_mcp_server_processes() -> MCPDiagnosticResult:
    """Check for stuck MCP server processes."""
    project_root = find_project_root()

    try:
        if sys.platform == "win32":
            # Windows: PowerShell command
            cmd = [
                "powershell",
                "-Command",
                f"Get-Process | Where-Object {{$_.ProcessName -like '*python*' -and $_.Path -like '{project_root}*'}} | Select-Object ProcessName, Id",
            ]
        else:
            # Unix: ps command
            cmd = ["ps", "aux"]

        result = subprocess.run(cmd, capture_output=True, text=True, timeout=10)

        if result.returncode == 0:
            output = result.stdout.strip()
            if output and ("python" in output.lower() or "paracle" in output.lower()):
                process_count = len(
                    [line for line in output.split("\n") if "python" in line.lower()]
                )
                return MCPDiagnosticResult(
                    status="warning",
                    issue=f"Found {process_count} potentially stuck processes",
                    solution="Run stop-mcp-processes script",
                    details={"processes": output[:500]},  # Limit output
                )
            return MCPDiagnosticResult(
                status="healthy",
                details={"message": "No stuck processes found"},
            )

        return MCPDiagnosticResult(
            status="warning",
            issue="Could not check processes",
            solution="Manually check with Task Manager (Windows) or ps (Unix)",
        )

    except Exception as e:
        return MCPDiagnosticResult(
            status="warning",
            issue=f"Process check failed: {e}",
            solution="Try manual process check",
        )


def check_paracle_exe_locked() -> MCPDiagnosticResult:
    """Check if paracle.exe is locked (Windows only)."""
    if sys.platform != "win32":
        return MCPDiagnosticResult(
            status="healthy",
            details={"message": "Not applicable on non-Windows systems"},
        )

    project_root = find_project_root()
    paracle_exe = project_root / ".venv" / "Scripts" / "paracle.exe"

    if not paracle_exe.exists():
        return MCPDiagnosticResult(
            status="warning",
            issue="paracle.exe not found",
            solution="Run: uv sync",
        )

    # Try to open file exclusively
    try:
        with paracle_exe.open("rb"):
            return MCPDiagnosticResult(
                status="healthy",
                details={"paracle_exe": str(paracle_exe)},
            )
    except PermissionError:
        return MCPDiagnosticResult(
            status="error",
            issue="paracle.exe is locked by another process",
            solution="Stop MCP processes or run: .\\scripts\\stop-mcp-processes.ps1",
            details={"file": str(paracle_exe)},
        )
    except Exception as e:
        return MCPDiagnosticResult(
            status="warning",
            issue=f"Could not check file lock: {e}",
        )


def stop_mcp_processes(auto_fix: bool = False) -> MCPDiagnosticResult:
    """Stop stuck MCP processes."""
    project_root = find_project_root()

    if not auto_fix:
        return MCPDiagnosticResult(
            status="warning",
            issue="Auto-fix not enabled",
            solution="Run with auto_fix=True or manually: .\\scripts\\stop-mcp-processes.ps1",
        )

    try:
        if sys.platform == "win32":
            script = project_root / "scripts" / "stop-mcp-processes.ps1"
            if script.exists():
                result = subprocess.run(
                    ["powershell", "-ExecutionPolicy", "Bypass", "-File", str(script)],
                    capture_output=True,
                    text=True,
                    timeout=30,
                )
            else:
                # Fallback: Direct PowerShell command
                cmd = f"Get-Process | Where-Object {{$_.ProcessName -like '*python*' -and $_.Path -like '{project_root}*'}} | Stop-Process -Force"
                result = subprocess.run(
                    ["powershell", "-Command", cmd],
                    capture_output=True,
                    text=True,
                    timeout=30,
                )
        else:
            script = project_root / "scripts" / "stop-mcp-processes.sh"
            if script.exists():
                result = subprocess.run(
                    ["bash", str(script)],
                    capture_output=True,
                    text=True,
                    timeout=30,
                )
            else:
                # Fallback: Direct kill command
                result = subprocess.run(
                    ["pkill", "-f", f"{project_root}.*python"],
                    capture_output=True,
                    text=True,
                    timeout=30,
                )

        if result.returncode == 0:
            return MCPDiagnosticResult(
                status="healthy",
                issue="Stuck processes found and stopped",
                fixed=True,
                details={"output": result.stdout[:500]},
            )

        return MCPDiagnosticResult(
            status="warning",
            issue="Could not stop all processes",
            solution="Try manually or restart VS Code",
            details={"error": result.stderr[:500]},
        )

    except Exception as e:
        return MCPDiagnosticResult(
            status="error",
            issue=f"Failed to stop processes: {e}",
            solution="Manually stop processes or restart system",
        )


def reinstall_paracle(auto_fix: bool = False) -> MCPDiagnosticResult:
    """Reinstall Paracle with UV."""
    if not auto_fix:
        return MCPDiagnosticResult(
            status="warning",
            issue="Auto-fix not enabled",
            solution="Run with auto_fix=True or manually: uv sync --reinstall",
        )

    try:
        # First, stop processes
        stop_result = stop_mcp_processes(auto_fix=True)

        # Then reinstall
        result = subprocess.run(
            ["uv", "sync", "--reinstall"],
            capture_output=True,
            text=True,
            timeout=300,  # 5 minutes
            cwd=find_project_root(),
        )

        if result.returncode == 0:
            return MCPDiagnosticResult(
                status="healthy",
                issue="Paracle reinstalled successfully",
                fixed=True,
                details={
                    "output": result.stdout[-500:],  # Last 500 chars
                    "processes_stopped": stop_result.fixed,
                },
            )

        return MCPDiagnosticResult(
            status="error",
            issue="Reinstallation failed",
            solution="Check UV output and try manually",
            details={"error": result.stderr[-500:]},
        )

    except Exception as e:
        return MCPDiagnosticResult(
            status="error",
            issue=f"Reinstallation error: {e}",
            solution="Run manually: uv sync --reinstall",
        )


def diagnose_all() -> dict[str, MCPDiagnosticResult]:
    """Run all diagnostic checks."""
    return {
        "uv_available": check_uv_available(),
        "venv_exists": check_venv_exists(),
        "stuck_processes": check_mcp_server_processes(),
        "paracle_locked": check_paracle_exe_locked(),
    }


def fix_all_issues(auto_fix: bool = False) -> dict[str, MCPDiagnosticResult]:
    """Diagnose and attempt to fix all issues."""
    results = diagnose_all()

    # If processes stuck, stop them
    if results["stuck_processes"].status in ("warning", "error"):
        results["fix_processes"] = stop_mcp_processes(auto_fix=auto_fix)

    # If paracle locked, try reinstall
    if results["paracle_locked"].status == "error":
        results["fix_reinstall"] = reinstall_paracle(auto_fix=auto_fix)

    # If venv missing, create it
    if results["venv_exists"].status == "error" and auto_fix:
        try:
            subprocess.run(
                ["uv", "sync"],
                capture_output=True,
                text=True,
                timeout=300,
                cwd=find_project_root(),
            )
            results["fix_venv"] = MCPDiagnosticResult(
                status="healthy",
                issue="Virtual environment created",
                fixed=True,
            )
        except Exception as e:
            results["fix_venv"] = MCPDiagnosticResult(
                status="error",
                issue=f"Could not create venv: {e}",
            )

    return results
