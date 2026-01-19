"""System health check and diagnostics command.

Validates environment, dependencies, configuration, and system health.
"""

import platform
import sys
from typing import Any

import click
from paracle_core.parac import find_parac_root
from rich.console import Console
from rich.tree import Tree

console = Console()


@click.command()
@click.option(
    "--verbose", "-v", is_flag=True, help="Show detailed diagnostic information"
)
@click.option("--fix", is_flag=True, help="Attempt to auto-fix issues (where possible)")
def doctor(verbose: bool = False, fix: bool = False) -> None:
    """Run comprehensive system health check.

    Validates:
    - Python version and environment
    - Paracle installation and dependencies
    - .parac/ workspace structure
    - Configuration files
    - Optional dependencies (Docker, SSH, etc.)
    - System resources
    """
    console.print("\n[bold cyan]🏥 Paracle System Health Check[/bold cyan]\n")

    checks = [
        ("Python Environment", check_python_environment),
        ("Paracle Installation", check_paracle_installation),
        ("Workspace Structure", check_workspace_structure),
        ("Configuration", check_configuration),
        ("Dependencies", check_dependencies),
        ("Optional Features", check_optional_features),
        ("System Resources", check_system_resources),
    ]

    results = []
    total_issues = 0
    total_warnings = 0

    for name, check_func in checks:
        result = check_func(verbose=verbose)
        results.append((name, result))
        total_issues += result["errors"]
        total_warnings += result["warnings"]

    # Display results
    _display_results(results, verbose)

    # Summary
    console.print("\n" + "=" * 60)
    if total_issues == 0 and total_warnings == 0:
        console.print(
            "[bold green]✅ All checks passed! System is healthy.[/bold green]"
        )
    elif total_issues == 0:
        console.print(
            f"[bold yellow]⚠️  System functional with {total_warnings} warning(s)[/bold yellow]"
        )
    else:
        console.print(
            f"[bold red]❌ {total_issues} issue(s) found, {total_warnings} warning(s)[/bold red]"
        )

    # Auto-fix suggestion
    if total_issues > 0 and not fix:
        console.print(
            "\n[dim]💡 Tip: Run [bold]paracle doctor --fix[/bold] to auto-fix some issues[/dim]"
        )

    # Exit code
    if total_issues > 0:
        sys.exit(1)


def check_python_environment(verbose: bool = False) -> dict[str, Any]:
    """Check Python version and environment."""
    errors = []
    warnings = []
    info = {}

    # Python version
    py_version = sys.version_info
    info["Python Version"] = f"{py_version.major}.{py_version.minor}.{py_version.micro}"

    if py_version < (3, 10):
        errors.append(
            f"Python 3.10+ required, found {py_version.major}.{py_version.minor}"
        )
    elif py_version < (3, 11):
        warnings.append("Python 3.11+ recommended for best performance")

    # Platform
    info["Platform"] = platform.system()
    info["Architecture"] = platform.machine()

    # Virtual environment
    in_venv = hasattr(sys, "real_prefix") or (
        hasattr(sys, "base_prefix") and sys.base_prefix != sys.prefix
    )
    info["Virtual Environment"] = "Yes" if in_venv else "No"

    if not in_venv and platform.system() != "Windows":
        warnings.append("Not in virtual environment (recommended for isolation)")

    return {
        "status": "error" if errors else ("warning" if warnings else "ok"),
        "errors": len(errors),
        "warnings": len(warnings),
        "issues": errors + warnings,
        "info": info if verbose else {},
    }


def check_paracle_installation(verbose: bool = False) -> dict[str, Any]:
    """Check Paracle installation and core dependencies."""
    errors = []
    warnings = []
    info = {}

    try:
        import paracle

        info["Paracle Version"] = getattr(paracle, "__version__", "Unknown")
    except ImportError:
        errors.append("Paracle not properly installed")
        return {
            "status": "error",
            "errors": 1,
            "warnings": 0,
            "issues": errors,
            "info": {},
        }

    # Check core packages
    core_packages = [
        "paracle_core",
        "paracle_domain",
        "paracle_store",
        "paracle_providers",
        "paracle_orchestration",
        "paracle_api",
        "paracle_cli",
        "paracle_mcp",
    ]

    missing = []
    for pkg in core_packages:
        try:
            __import__(pkg)
        except ImportError:
            missing.append(pkg)

    if missing:
        errors.append(f"Missing core packages: {', '.join(missing)}")
        errors.append("Run: pip install --upgrade paracle")

    # Check critical dependencies
    critical_deps = [
        ("pydantic", "2.0", "Data validation"),
        ("fastapi", "0.100", "API server"),
        ("typer", "0.9", "CLI"),
        ("sqlalchemy", "2.0", "Database ORM"),
    ]

    for dep_name, min_version, purpose in critical_deps:
        try:
            mod = __import__(dep_name)
            version = getattr(mod, "__version__", "Unknown")
            info[f"{dep_name}"] = version
        except ImportError:
            errors.append(f"Missing {dep_name} ({purpose})")

    return {
        "status": "error" if errors else ("warning" if warnings else "ok"),
        "errors": len(errors),
        "warnings": len(warnings),
        "issues": errors + warnings,
        "info": info if verbose else {},
    }


def check_workspace_structure(verbose: bool = False) -> dict[str, Any]:
    """Check .parac/ workspace structure."""
    errors = []
    warnings = []
    info = {}

    try:
        parac_root = find_parac_root()
        info["Workspace Root"] = str(parac_root)
    except Exception:
        errors.append(".parac/ workspace not found")
        errors.append("Run: paracle init to create workspace")
        return {
            "status": "error",
            "errors": 2,
            "warnings": 0,
            "issues": errors,
            "info": {},
        }

    # Required directories
    required_dirs = [
        "agents",
        "agents/specs",
        "agents/skills",
        "workflows",
        "memory",
        "memory/context",
        "memory/logs",
        "memory/data",
        "memory/knowledge",
        "roadmap",
        "policies",
    ]

    for dir_path in required_dirs:
        full_path = parac_root / dir_path
        if not full_path.exists():
            warnings.append(f"Missing directory: {dir_path}")

    # Required files
    required_files = [
        "project.yaml",
        "manifest.yaml",
        "GOVERNANCE.md",
        "memory/context/current_state.yaml",
        "roadmap/roadmap.yaml",
    ]

    for file_path in required_files:
        full_path = parac_root / file_path
        if not full_path.exists():
            if file_path == "manifest.yaml":
                warnings.append(f"Missing {file_path} (run: paracle sync)")
            else:
                errors.append(f"Missing critical file: {file_path}")

    # Check for misplaced files (anti-pattern)
    misplaced = []
    if (parac_root / "costs.db").exists():
        misplaced.append("costs.db → should be in memory/data/")
    if (parac_root / "logs").exists() and (parac_root / "logs").is_dir():
        if not (parac_root / "memory" / "logs").exists():
            misplaced.append("logs/ → should be memory/logs/")

    if misplaced:
        warnings.append(f"Misplaced files: {', '.join(misplaced)}")
        warnings.append("Run: paracle validate structure --fix")

    return {
        "status": "error" if errors else ("warning" if warnings else "ok"),
        "errors": len(errors),
        "warnings": len(warnings),
        "issues": errors + warnings,
        "info": info if verbose else {},
    }


def check_configuration(verbose: bool = False) -> dict[str, Any]:
    """Check configuration files."""
    errors = []
    warnings = []
    info = {}

    try:
        parac_root = find_parac_root()
    except Exception:
        return {"status": "skip", "errors": 0, "warnings": 0, "issues": [], "info": {}}

    # Check project.yaml
    project_yaml = parac_root / "project.yaml"
    if project_yaml.exists():
        try:
            import yaml

            with open(project_yaml) as f:
                config = yaml.safe_load(f)
                info["Project Name"] = config.get("project", {}).get("name", "Unknown")
                info["Project Version"] = config.get("project", {}).get(
                    "version", "Unknown"
                )
        except Exception as e:
            errors.append(f"project.yaml syntax error: {e}")
    else:
        warnings.append("project.yaml not found (using defaults)")

    # Check manifest.yaml
    manifest_yaml = parac_root / "manifest.yaml"
    if not manifest_yaml.exists():
        warnings.append("manifest.yaml not found (run: paracle sync)")

    # Check current_state.yaml
    current_state = parac_root / "memory" / "context" / "current_state.yaml"
    if current_state.exists():
        try:
            import yaml

            with open(current_state) as f:
                state = yaml.safe_load(f)
                phase = state.get("project", {}).get("phase", "Unknown")
                status = state.get("project", {}).get("status", "Unknown")
                info["Current Phase"] = f"{phase} ({status})"
        except Exception as e:
            errors.append(f"current_state.yaml syntax error: {e}")

    return {
        "status": "error" if errors else ("warning" if warnings else "ok"),
        "errors": len(errors),
        "warnings": len(warnings),
        "issues": errors + warnings,
        "info": info if verbose else {},
    }


def check_dependencies(verbose: bool = False) -> dict[str, Any]:
    """Check Python dependencies."""
    errors = []
    warnings = []
    info = {}

    # Check for dependency conflicts
    try:
        import importlib.metadata as metadata

        paracle_deps = metadata.distribution("paracle").requires or []
        info["Total Dependencies"] = len(paracle_deps)
    except Exception:
        warnings.append("Could not enumerate dependencies")

    return {
        "status": "error" if errors else ("warning" if warnings else "ok"),
        "errors": len(errors),
        "warnings": len(warnings),
        "issues": errors + warnings,
        "info": info if verbose else {},
    }


def check_optional_features(verbose: bool = False) -> dict[str, Any]:
    """Check optional feature dependencies."""
    errors = []
    warnings = []
    info = {}

    optional_features = [
        ("docker", "Docker SDK", "Sandbox features (paracle[sandbox])"),
        ("asyncssh", "AsyncSSH", "Remote execution (paracle[remote])"),
        ("openai", "OpenAI SDK", "OpenAI provider"),
        ("anthropic", "Anthropic SDK", "Claude provider"),
        ("sentence_transformers", "Sentence Transformers", "Vector embeddings"),
    ]

    available = []
    unavailable = []

    for module, name, purpose in optional_features:
        try:
            __import__(module)
            available.append(name)
            info[name] = "✅ Available"
        except ImportError:
            unavailable.append(f"{name} ({purpose})")
            info[name] = f"❌ Not installed - {purpose}"

    if verbose:
        if unavailable:
            warnings.append(
                f"Optional features not available: {', '.join(unavailable)}"
            )

    return {
        "status": "warning" if warnings else "ok",
        "errors": len(errors),
        "warnings": len(warnings),
        "issues": warnings,
        "info": info if verbose else {},
    }


def check_system_resources(verbose: bool = False) -> dict[str, Any]:
    """Check system resources."""
    errors = []
    warnings = []
    info = {}

    try:
        import psutil

        # Memory
        mem = psutil.virtual_memory()
        info["Total Memory"] = f"{mem.total / (1024**3):.1f} GB"
        info["Available Memory"] = f"{mem.available / (1024**3):.1f} GB"
        info["Memory Usage"] = f"{mem.percent}%"

        if mem.percent > 90:
            warnings.append(f"High memory usage: {mem.percent}%")
        elif mem.available < 1024**3:  # Less than 1GB
            warnings.append("Low available memory (< 1GB)")

        # Disk
        disk = psutil.disk_usage("/")
        info["Disk Total"] = f"{disk.total / (1024**3):.1f} GB"
        info["Disk Free"] = f"{disk.free / (1024**3):.1f} GB"
        info["Disk Usage"] = f"{disk.percent}%"

        if disk.percent > 90:
            warnings.append(f"High disk usage: {disk.percent}%")
        elif disk.free < 5 * 1024**3:  # Less than 5GB
            warnings.append("Low disk space (< 5GB)")

        # CPU
        cpu_count = psutil.cpu_count()
        info["CPU Cores"] = str(cpu_count)

    except ImportError:
        info["System Resources"] = "psutil not installed (optional)"

    return {
        "status": "warning" if warnings else "ok",
        "errors": len(errors),
        "warnings": len(warnings),
        "issues": warnings,
        "info": info if verbose else {},
    }


def _display_results(results: list, verbose: bool) -> None:
    """Display health check results."""
    for name, result in results:
        status = result["status"]

        # Status icon
        if status == "ok":
            icon = "✅"
            color = "green"
        elif status == "warning":
            icon = "⚠️"
            color = "yellow"
        elif status == "error":
            icon = "❌"
            color = "red"
        else:
            icon = "⏭️"
            color = "dim"

        console.print(f"{icon} [bold]{name}[/bold]", style=color)

        # Show issues
        for issue in result.get("issues", []):
            console.print(f"   • {issue}", style=color)

        # Show info in verbose mode
        if verbose and result.get("info"):
            for key, value in result["info"].items():
                console.print(f"   [dim]{key}: {value}[/dim]")

        console.print()


@click.command()
def info() -> None:
    """Display system information."""
    console.print("\n[bold cyan]📊 System Information[/bold cyan]\n")

    tree = Tree("🖥️  System")

    # Python
    py_branch = tree.add("🐍 Python")
    py_branch.add(f"Version: {sys.version.split()[0]}")
    py_branch.add(f"Executable: {sys.executable}")
    py_branch.add(f"Platform: {platform.platform()}")

    # Paracle
    try:
        import paracle

        p_branch = tree.add("⚡ Paracle")
        p_branch.add(f"Version: {getattr(paracle, '__version__', 'Unknown')}")

        try:
            parac_root = find_parac_root()
            p_branch.add(f"Workspace: {parac_root}")
        except Exception:
            p_branch.add("Workspace: Not found")
    except ImportError:
        tree.add("⚡ Paracle: Not installed")

    # System
    sys_branch = tree.add("💻 System")
    sys_branch.add(f"OS: {platform.system()} {platform.release()}")
    sys_branch.add(f"Architecture: {platform.machine()}")

    try:
        import psutil

        mem = psutil.virtual_memory()
        sys_branch.add(f"Memory: {mem.total / (1024**3):.1f} GB")
        sys_branch.add(f"CPU: {psutil.cpu_count()} cores")
    except ImportError:
        pass

    console.print(tree)
    console.print()


if __name__ == "__main__":
    doctor()
