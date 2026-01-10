"""CLI commands for error management and monitoring.

Provides access to the error registry for viewing and analyzing
errors across all Paracle components.
"""

import json

import click
from rich.console import Console
from rich.table import Table

console = Console()


@click.group()
def errors() -> None:
    """View and manage error registry."""
    pass


@errors.command("list")
@click.option("--component", "-c", help="Filter by component")
@click.option("--severity", "-s", help="Filter by severity")
@click.option("--limit", "-l", default=20, help="Number of errors to show")
@click.option("--json", "as_json", is_flag=True, help="Output as JSON")
def list_errors(
    component: str | None, severity: str | None, limit: int, as_json: bool
) -> None:
    """List recent errors from the error registry."""
    try:
        from paracle_observability import ErrorSeverityLevel, get_error_registry

        registry = get_error_registry()

        # Get errors with filters
        if component:
            errors_list = registry.get_errors_by_component(component)[:limit]
        elif severity:
            # Convert string to severity enum
            sev_map = {
                "debug": ErrorSeverityLevel.DEBUG,
                "info": ErrorSeverityLevel.INFO,
                "warning": ErrorSeverityLevel.WARNING,
                "error": ErrorSeverityLevel.ERROR,
                "critical": ErrorSeverityLevel.CRITICAL,
            }
            sev_enum = sev_map.get(severity.lower())
            if not sev_enum:
                console.print(f"[red]Invalid severity: {severity}[/red]")
                console.print("Valid: debug, info, warning, error, critical")
                return
            errors_list = registry.get_errors(severity=sev_enum, limit=limit)
        else:
            errors_list = registry.get_errors(limit=limit)

        if as_json:
            output = [e.to_dict() for e in errors_list]
            click.echo(json.dumps(output, indent=2, default=str))
            return

        if not errors_list:
            console.print("[yellow]No errors found[/yellow]")
            return

        table = Table(title=f"Recent Errors ({len(errors_list)} shown)")
        table.add_column("Time", style="cyan", no_wrap=True)
        table.add_column("Component", style="blue")
        table.add_column("Type", style="yellow")
        table.add_column("Severity", style="red")
        table.add_column("Message", style="white")
        table.add_column("Count", style="green")

        for error in errors_list:
            from datetime import datetime

            timestamp = datetime.fromtimestamp(error.timestamp)
            time_str = timestamp.strftime("%H:%M:%S")

            # Color severity
            severity_colors = {
                "debug": "dim",
                "info": "cyan",
                "warning": "yellow",
                "error": "red",
                "critical": "bold red",
            }
            severity_style = severity_colors.get(error.severity.value, "white")

            table.add_row(
                time_str,
                error.component,
                error.error_type,
                f"[{severity_style}]{error.severity.value}[/{severity_style}]",
                error.message[:50] +
                "..." if len(error.message) > 50 else error.message,
                str(error.count) if error.count > 1 else "-",
            )

        console.print(table)

    except ImportError:
        console.print(
            "[red]Error:[/red] paracle_observability not installed or available"
        )
    except Exception as e:
        console.print(f"[red]Error:[/red] {e}")


@errors.command("stats")
@click.option("--json", "as_json", is_flag=True, help="Output as JSON")
def error_stats(as_json: bool) -> None:
    """Show error statistics."""
    try:
        from paracle_observability import get_error_registry

        registry = get_error_registry()
        stats = registry.get_statistics()

        if as_json:
            click.echo(json.dumps(stats, indent=2, default=str))
            return

        console.print("\n[bold cyan]Error Registry Statistics[/bold cyan]\n")
        console.print(f"  Total errors: {stats['total_count']}")
        console.print(f"  Unique errors: {stats['unique_errors']}")
        console.print(
            f"  Error rate: {stats['error_rate_per_minute']:.2f} errors/min")
        console.print(
            f"  Recent (1h): {stats['recent_errors_1h']}"
        )
        console.print(f"  Uptime: {stats['uptime_seconds'] / 3600:.1f} hours")
        console.print(f"  Patterns detected: {stats['patterns_detected']}")

        if stats["severity_breakdown"]:
            console.print("\n[bold]Severity Breakdown:[/bold]")
            for severity, count in stats["severity_breakdown"].items():
                console.print(f"  • {severity}: {count}")

        if stats["top_error_types"]:
            console.print("\n[bold]Top Error Types:[/bold]")
            for item in stats["top_error_types"][:5]:
                console.print(f"  • {item['type']}: {item['count']}")

        if stats["top_components"]:
            console.print("\n[bold]Top Components:[/bold]")
            for item in stats["top_components"][:5]:
                console.print(f"  • {item['component']}: {item['count']}")

    except ImportError:
        console.print(
            "[red]Error:[/red] paracle_observability not installed or available"
        )
    except Exception as e:
        console.print(f"[red]Error:[/red] {e}")


@errors.command("clear")
@click.confirmation_option(prompt="Are you sure you want to clear all errors?")
def clear_errors() -> None:
    """Clear all errors from the registry."""
    try:
        from paracle_observability import get_error_registry

        registry = get_error_registry()
        count = len(registry.errors)
        registry.errors.clear()
        registry.error_counts.clear()
        registry.component_errors.clear()
        registry._error_index.clear()

        console.print(f"[green]✓[/green] Cleared {count} errors from registry")

    except ImportError:
        console.print(
            "[red]Error:[/red] paracle_observability not installed or available"
        )
    except Exception as e:
        console.print(f"[red]Error:[/red] {e}")


@errors.command("patterns")
@click.option("--json", "as_json", is_flag=True, help="Output as JSON")
def error_patterns(as_json: bool) -> None:
    """Detect and show error patterns."""
    try:
        from paracle_observability import get_error_registry

        registry = get_error_registry()
        patterns = registry.get_patterns()

        if as_json:
            click.echo(json.dumps(patterns, indent=2, default=str))
            return

        if not patterns:
            console.print("[yellow]No error patterns detected[/yellow]")
            return

        console.print("\n[bold cyan]Detected Error Patterns[/bold cyan]\n")

        for i, pattern in enumerate(patterns, 1):
            console.print(
                f"[bold]{i}. Pattern Type: {pattern['pattern_type']}[/bold]")

            if "error_type" in pattern:
                console.print(f"   Error type: {pattern['error_type']}")
            if "component" in pattern:
                console.print(f"   Component: {pattern['component']}")

            console.print(f"   Count: {pattern['count']}")

            if "time_window" in pattern:
                console.print(f"   Time window: {pattern['time_window']}")

            console.print()

    except ImportError:
        console.print(
            "[red]Error:[/red] paracle_observability not installed or available"
        )
    except Exception as e:
        console.print(f"[red]Error:[/red] {e}")
