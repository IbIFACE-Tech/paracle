"""Paracle CLI - Logs commands.

Commands for viewing and managing logs.

Architecture: CLI -> API -> Core (API-first design)
Falls back to direct core access if API is unavailable.
"""

import json
import sys
from datetime import datetime
from pathlib import Path

import click
from rich.console import Console
from rich.table import Table
from rich.text import Text

from paracle_cli.api_client import APIClient, APIError, get_client
from paracle_cli.utils import get_parac_root_or_exit

console = Console()


def get_api_client() -> APIClient | None:
    """Get API client if API is available.

    Returns:
        APIClient if API responds, None otherwise
    """
    client = get_client()
    if client.is_available():
        return client
    return None


def use_api_or_fallback(api_func, fallback_func, *args, **kwargs):
    """Try API first, fall back to direct core access.

    Args:
        api_func: Function to call via API
        fallback_func: Function to call directly if API unavailable
        *args, **kwargs: Arguments to pass

    Returns:
        Result from either function
    """
    client = get_api_client()
    if client:
        try:
            return api_func(client, *args, **kwargs)
        except APIError as e:
            if e.status_code == 404:
                # .parac/ not found - let fallback handle gracefully
                pass
            else:
                console.print(f"[yellow]API error:[/yellow] {e.detail}")
                console.print("[dim]Falling back to direct access...[/dim]")
        except Exception as e:
            console.print(f"[yellow]API unavailable:[/yellow] {e}")
            console.print("[dim]Falling back to direct access...[/dim]")

    return fallback_func(*args, **kwargs)


def get_log_files(parac_root: Path) -> dict[str, Path]:
    """Get available log files.

    Args:
        parac_root: Path to .parac/ directory

    Returns:
        Dictionary of log name to path
    """
    logs_dir = parac_root / "memory" / "logs"
    log_files = {}

    if logs_dir.exists():
        # Governance logs
        if (logs_dir / "agent_actions.log").exists():
            log_files["actions"] = logs_dir / "agent_actions.log"
        if (logs_dir / "decisions.log").exists():
            log_files["decisions"] = logs_dir / "decisions.log"

        # Runtime logs
        runtime_dir = logs_dir / "runtime"
        if runtime_dir.exists():
            for log_file in runtime_dir.glob("**/*.log"):
                name = log_file.stem
                log_files[f"runtime/{name}"] = log_file

        # Audit logs
        audit_dir = logs_dir / "audit"
        if audit_dir.exists():
            for log_file in audit_dir.glob("*.log"):
                name = log_file.stem
                log_files[f"audit/{name}"] = log_file

    return log_files


def _print_log_line(line: str):
    """Print a log line with formatting."""
    # Parse timestamp
    if line.startswith("["):
        # Format: [2024-01-02 10:30:00] [AGENT] [ACTION] Message
        parts = line.split("]", 3)
        if len(parts) >= 3:
            timestamp = parts[0].strip("[")
            second = parts[1].strip().strip("[")
            third = parts[2].strip().strip("[")
            message = parts[3].strip() if len(parts) > 3 else ""

            text = Text()
            text.append(f"[{timestamp}] ", style="dim")

            # Color based on level/type
            style = "cyan"
            if "ERROR" in second or "FAILED" in second.upper():
                style = "red"
            elif "WARNING" in second:
                style = "yellow"
            elif "INFO" in second:
                style = "green"

            text.append(f"[{second}] ", style=style)
            text.append(f"[{third}] ", style="blue")
            text.append(message)

            console.print(text)
            return

    # Fallback: print as-is
    console.print(line)


@click.group(invoke_without_command=True)
@click.option(
    "--list",
    "-l",
    "list_flag",
    is_flag=True,
    help="List log files (shortcut for 'list')",
)
@click.pass_context
def logs(ctx: click.Context, list_flag: bool):
    """View and manage Paracle logs.

    Examples:
        paracle logs -l         - List log files (shortcut)
        paracle logs list       - List log files
        paracle logs show       - Show log content
    """
    if list_flag:
        ctx.invoke(list_logs)
    elif ctx.invoked_subcommand is None:
        click.echo(ctx.get_help())


# =============================================================================
# LIST Command
# =============================================================================


def _list_via_api(client: APIClient) -> None:
    """List logs via API."""
    result = client.logs_list()
    log_files = result.get("logs", [])

    if not log_files:
        console.print("[yellow]No log files found.[/yellow]")
        return

    table = Table(title="Available Log Files")
    table.add_column("Name", style="cyan")
    table.add_column("Path", style="dim")
    table.add_column("Size", justify="right")
    table.add_column("Modified", style="green")

    for log_info in log_files:
        table.add_row(
            log_info.get("name", ""),
            log_info.get("path", ""),
            log_info.get("size", ""),
            log_info.get("modified", ""),
        )

    console.print(table)


def _list_direct() -> None:
    """List logs via direct file access."""
    parac_root = get_parac_root_or_exit()
    log_files = get_log_files(parac_root)

    if not log_files:
        console.print("[yellow]No log files found.[/yellow]")
        return

    table = Table(title="Available Log Files")
    table.add_column("Name", style="cyan")
    table.add_column("Path", style="dim")
    table.add_column("Size", justify="right")
    table.add_column("Modified", style="green")

    for name, path in sorted(log_files.items()):
        stat = path.stat()
        size = f"{stat.st_size:,} bytes"
        modified = datetime.fromtimestamp(stat.st_mtime).strftime("%Y-%m-%d %H:%M")
        table.add_row(name, str(path.relative_to(parac_root)), size, modified)

    console.print(table)


@logs.command("list")
def list_logs():
    """List available log files."""
    use_api_or_fallback(_list_via_api, _list_direct)


# =============================================================================
# SHOW Command
# =============================================================================


def _show_via_api(
    client: APIClient,
    log_name: str,
    tail: int,
    follow: bool,
    as_json: bool,
    grep_pattern: str | None,
) -> None:
    """Show logs via API."""
    if follow:
        console.print("[yellow]Warning:[/yellow] Follow mode not supported via API.")
        console.print("[dim]Falling back to direct access...[/dim]")
        _show_direct(log_name, tail, follow, as_json, grep_pattern)
        return

    result = client.logs_show(log_name=log_name, tail=tail, pattern=grep_pattern)
    lines = result.get("lines", [])

    if not lines:
        console.print("[yellow]No matching log entries.[/yellow]")
        return

    if as_json:
        # Try to parse as structured logs
        entries = []
        for line in lines:
            try:
                entry = json.loads(line)
                entries.append(entry)
            except json.JSONDecodeError:
                entries.append({"raw": line.strip()})
        console.print(json.dumps(entries, indent=2))
    else:
        # Pretty print with formatting
        for line in lines:
            _print_log_line(line.strip() if isinstance(line, str) else str(line))


def _show_direct(
    log_name: str,
    tail: int,
    follow: bool,
    as_json: bool,
    grep_pattern: str | None,
) -> None:
    """Show logs via direct file access."""
    parac_root = get_parac_root_or_exit()
    log_files = get_log_files(parac_root)

    # Find matching log file
    log_path = None
    for name, path in log_files.items():
        if name == log_name or name.endswith(log_name):
            log_path = path
            break

    if not log_path:
        console.print(f"[red]Error:[/red] Log file '{log_name}' not found.")
        console.print("Available logs:", ", ".join(log_files.keys()))
        sys.exit(1)

    if not log_path.exists():
        console.print(f"[yellow]Log file is empty: {log_path}[/yellow]")
        return

    if follow:
        _follow_log(log_path, grep_pattern)
    else:
        _show_log_tail(log_path, tail, as_json, grep_pattern)


def _show_log_tail(
    log_path: Path,
    count: int,
    as_json: bool,
    pattern: str | None,
):
    """Show last N lines of log file."""
    with open(log_path, encoding="utf-8") as f:
        lines = f.readlines()

    # Filter if pattern provided
    if pattern:
        lines = [line for line in lines if pattern.lower() in line.lower()]

    # Get last N lines
    lines = lines[-count:]

    if not lines:
        console.print("[yellow]No matching log entries.[/yellow]")
        return

    if as_json:
        # Try to parse as structured logs
        entries = []
        for line in lines:
            try:
                entry = json.loads(line)
                entries.append(entry)
            except json.JSONDecodeError:
                entries.append({"raw": line.strip()})
        console.print(json.dumps(entries, indent=2))
    else:
        # Pretty print with formatting
        for line in lines:
            _print_log_line(line.strip())


def _follow_log(log_path: Path, pattern: str | None):
    """Follow log file in real-time."""
    import time

    console.print(f"[cyan]Following {log_path.name}... (Ctrl+C to stop)[/cyan]")
    console.print()

    # Get current file size
    last_size = log_path.stat().st_size if log_path.exists() else 0

    try:
        while True:
            if log_path.exists():
                current_size = log_path.stat().st_size

                if current_size > last_size:
                    with open(log_path, encoding="utf-8") as f:
                        f.seek(last_size)
                        new_lines = f.readlines()

                    for line in new_lines:
                        line = line.strip()
                        if pattern and pattern.lower() not in line.lower():
                            continue
                        _print_log_line(line)

                    last_size = current_size

            time.sleep(0.5)

    except KeyboardInterrupt:
        console.print("\n[yellow]Stopped following log.[/yellow]")


@logs.command("show")
@click.argument("log_name", default="actions")
@click.option("--tail", "-n", default=50, help="Number of lines to show")
@click.option("--follow", "-f", is_flag=True, help="Follow log output")
@click.option("--json", "as_json", is_flag=True, help="Output as JSON")
@click.option("--filter", "-g", "grep_pattern", help="Filter lines by pattern")
def show_logs(
    log_name: str,
    tail: int,
    follow: bool,
    as_json: bool,
    grep_pattern: str | None,
):
    """Show log contents.

    LOG_NAME: Name of log file (default: actions)

    Examples:
        paracle logs show              # Show last 50 lines of actions log
        paracle logs show -n 100       # Show last 100 lines
        paracle logs show -f           # Follow log in real-time
        paracle logs show decisions    # Show decisions log
        paracle logs show -g "ERROR"   # Filter for ERROR
    """
    use_api_or_fallback(
        _show_via_api,
        _show_direct,
        log_name,
        tail,
        follow,
        as_json,
        grep_pattern,
    )


# =============================================================================
# CLEAR Command
# =============================================================================


def _clear_direct(log_name: str, force: bool) -> None:
    """Clear log via direct file access."""
    parac_root = get_parac_root_or_exit()
    log_files = get_log_files(parac_root)

    # Find matching log file
    log_path = None
    for name, path in log_files.items():
        if name == log_name or name.endswith(log_name):
            log_path = path
            break

    if not log_path:
        console.print(f"[red]Error:[/red] Log file '{log_name}' not found.")
        sys.exit(1)

    if not force:
        if not click.confirm(f"Clear {log_path.name}? This cannot be undone."):
            console.print("[yellow]Cancelled.[/yellow]")
            return

    # Clear the file
    log_path.write_text("")
    console.print(f"[green]OK[/green] Cleared {log_path.name}")


@logs.command("clear")
@click.argument("log_name", default="actions")
@click.option("--force", "-f", is_flag=True, help="Skip confirmation")
def clear_log(log_name: str, force: bool):
    """Clear a log file.

    LOG_NAME: Name of log file to clear

    Note: This command always runs locally (destructive operation).
    """
    _clear_direct(log_name, force)


# =============================================================================
# EXPORT Command
# =============================================================================


def _export_direct(
    log_name: str,
    output: str | None,
    fmt: str,
    from_date: str | None,
    to_date: str | None,
) -> None:
    """Export logs via direct file access."""
    parac_root = get_parac_root_or_exit()
    log_files = get_log_files(parac_root)

    # Find matching log file
    log_path = None
    for name, path in log_files.items():
        if name == log_name or name.endswith(log_name):
            log_path = path
            break

    if not log_path:
        console.print(f"[red]Error:[/red] Log file '{log_name}' not found.")
        sys.exit(1)

    with open(log_path, encoding="utf-8") as f:
        lines = f.readlines()

    # Parse and filter
    entries = []
    for line in lines:
        line = line.strip()
        if not line:
            continue

        entry = {"raw": line}

        # Try to parse timestamp
        if line.startswith("["):
            try:
                timestamp_end = line.index("]")
                timestamp_str = line[1:timestamp_end]
                entry["timestamp"] = timestamp_str

                # Date filter
                if from_date and timestamp_str[:10] < from_date:
                    continue
                if to_date and timestamp_str[:10] > to_date:
                    continue
            except (ValueError, IndexError):
                pass

        entries.append(entry)

    # Export based on format
    if output:
        output_path = Path(output)
    else:
        ext = {"json": ".json", "csv": ".csv", "ndjson": ".ndjson"}[fmt]
        output_path = Path(f"{log_name}_export{ext}")

    if fmt == "json":
        with open(output_path, "w", encoding="utf-8") as f:
            json.dump(entries, f, indent=2)
    elif fmt == "ndjson":
        with open(output_path, "w", encoding="utf-8") as f:
            for entry in entries:
                f.write(json.dumps(entry) + "\n")
    elif fmt == "csv":
        import csv

        with open(output_path, "w", encoding="utf-8", newline="") as f:
            if entries:
                writer = csv.DictWriter(f, fieldnames=entries[0].keys())
                writer.writeheader()
                writer.writerows(entries)

    console.print(f"[green]OK[/green] Exported {len(entries)} entries to {output_path}")


@logs.command("export")
@click.argument("log_name", default="actions")
@click.option("--output", "-o", help="Output file path")
@click.option(
    "--format",
    "-f",
    "fmt",
    type=click.Choice(["json", "csv", "ndjson"]),
    default="json",
)
@click.option("--from-date", help="Filter from date (YYYY-MM-DD)")
@click.option("--to-date", help="Filter to date (YYYY-MM-DD)")
def export_logs(
    log_name: str,
    output: str | None,
    fmt: str,
    from_date: str | None,
    to_date: str | None,
):
    """Export logs to file.

    LOG_NAME: Name of log file to export

    Note: This command always runs locally (file operation).
    """
    _export_direct(log_name, output, fmt, from_date, to_date)


# =============================================================================
# AUDIT Command
# =============================================================================


def _audit_direct(
    tail: int,
    category: str | None,
    severity: str | None,
) -> None:
    """Show audit log via direct file access."""
    parac_root = get_parac_root_or_exit()
    audit_dir = parac_root / "memory" / "logs" / "audit"

    if not audit_dir.exists():
        console.print(
            "[yellow]No audit logs found. Audit logging may not be configured.[/yellow]"
        )
        console.print("\nTo enable audit logging, configure it at startup:")
        console.print("  from paracle_core.logging import configure_logging")
        console.print("  configure_logging(audit_enabled=True)")
        return

    # Find all audit log files
    audit_files = sorted(audit_dir.glob("*.log"), reverse=True)

    if not audit_files:
        console.print("[yellow]No audit log files found.[/yellow]")
        return

    # Read entries from files
    entries = []
    for audit_file in audit_files:
        with open(audit_file, encoding="utf-8") as f:
            for line in f:
                line = line.strip()
                if not line or line.startswith("#"):
                    continue

                # Filter by category
                if category and f"[{category}" not in line.lower():
                    continue

                # Filter by severity
                if severity and f"[{severity.upper()}]" not in line:
                    continue

                entries.append(line)

                if len(entries) >= tail:
                    break

        if len(entries) >= tail:
            break

    if not entries:
        console.print("[yellow]No matching audit entries.[/yellow]")
        return

    # Display with table
    table = Table(title=f"Audit Log (last {len(entries)} entries)")
    table.add_column("Timestamp", style="dim")
    table.add_column("Severity")
    table.add_column("Category", style="cyan")
    table.add_column("Actor")
    table.add_column("Resource")
    table.add_column("Action")
    table.add_column("Outcome")

    for entry in entries[-tail:]:
        # Parse entry
        parts = entry.split(" ")
        if len(parts) < 5:
            continue

        timestamp = parts[0]
        severity_val = parts[1].strip("[]") if len(parts) > 1 else ""
        cat = parts[2].strip("[]") if len(parts) > 2 else ""

        # Parse key=value pairs
        actor = resource = action = outcome = ""
        for part in parts[3:]:
            if "=" in part:
                key, val = part.split("=", 1)
                if key == "actor":
                    actor = val
                elif key == "resource":
                    resource = val
                elif key == "action":
                    action = val
                elif key == "outcome":
                    outcome = val

        # Color severity
        sev_style = {
            "INFO": "green",
            "LOW": "blue",
            "MEDIUM": "yellow",
            "HIGH": "red",
            "CRITICAL": "bold red",
        }.get(severity_val.upper(), "white")

        table.add_row(
            timestamp,
            Text(severity_val, style=sev_style),
            cat,
            actor,
            resource,
            action,
            outcome,
        )

    console.print(table)


@logs.command("audit")
@click.option("--tail", "-n", default=50, help="Number of entries to show")
@click.option("--category", "-c", help="Filter by category (e.g., agent, workflow)")
@click.option(
    "--severity", "-s", help="Filter by severity (info, low, medium, high, critical)"
)
def show_audit(tail: int, category: str | None, severity: str | None):
    """Show audit log (ISO 42001 compliance trail).

    Note: This command always runs locally (audit logs are sensitive).
    """
    _audit_direct(tail, category, severity)
