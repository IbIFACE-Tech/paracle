"""CLI commands for governance policy management and monitoring."""

import json
import sys
import time
from datetime import datetime
from pathlib import Path

import click
from rich.console import Console
from rich.live import Live
from rich.panel import Panel
from rich.table import Table

console = Console()


@click.group()
def governance() -> None:
    """Manage governance policies and risk scoring."""
    pass


@governance.command("list")
@click.option("--enabled/--all", default=True, help="Show only enabled policies")
@click.option("--type", "-t", "policy_type", help="Filter by policy type")
@click.option("--json", "as_json", is_flag=True, help="Output as JSON")
def list_policies(enabled: bool, policy_type: str | None, as_json: bool) -> None:
    """List all governance policies."""
    try:
        from paracle_governance import PolicyEngine

        engine = PolicyEngine()
        engine.load_default_policies()

        policies = engine.list_policies(enabled_only=enabled)

        if policy_type:
            policies = [p for p in policies if p.type.value == policy_type.upper()]

        if as_json:
            click.echo(
                json.dumps([p.model_dump() for p in policies], indent=2, default=str)
            )
        else:
            if not policies:
                console.print("[yellow]No policies found[/yellow]")
                return

            table = Table(title=f"Governance Policies ({len(policies)} total)")
            table.add_column("ID", style="cyan", no_wrap=True)
            table.add_column("Name", style="white")
            table.add_column("Type", style="blue")
            table.add_column("Actions", style="magenta")
            table.add_column("Risk", style="yellow")
            table.add_column("Status", style="green")

            for p in policies:
                actions = ", ".join(a.value for a in p.actions[:3])
                if len(p.actions) > 3:
                    actions += f" (+{len(p.actions) - 3})"

                status = (
                    "[green]Enabled[/green]" if p.enabled else "[dim]Disabled[/dim]"
                )
                risk = p.risk_level or "-"

                table.add_row(
                    p.id[:12],
                    p.name,
                    p.type.value,
                    actions,
                    risk,
                    status,
                )

            console.print(table)

    except ImportError:
        console.print("[red]Error: paracle_governance package not installed[/red]")
        raise SystemExit(1)
    except Exception as e:
        console.print(f"[red]Error: {e}[/red]")
        raise SystemExit(1)


@governance.command("show")
@click.argument("policy_id")
@click.option("--json", "as_json", is_flag=True, help="Output as JSON")
def show_policy(policy_id: str, as_json: bool) -> None:
    """Show details of a specific policy."""
    try:
        from paracle_governance import PolicyEngine

        engine = PolicyEngine()
        engine.load_default_policies()

        policy = engine.get_policy(policy_id)

        if not policy:
            # Try partial match
            for p in engine.list_policies(enabled_only=False):
                if p.id.startswith(policy_id) or p.name.lower() == policy_id.lower():
                    policy = p
                    break

        if not policy:
            console.print(f"[red]Error: Policy '{policy_id}' not found[/red]")
            raise SystemExit(1)

        if as_json:
            click.echo(policy.model_dump_json(indent=2))
        else:
            console.print(
                Panel(
                    f"[bold cyan]{policy.name}[/bold cyan]\n\n"
                    f"[dim]ID:[/dim] {policy.id}\n"
                    f"[dim]Type:[/dim] {policy.type.value}\n"
                    f"[dim]Description:[/dim] {policy.description or '(none)'}\n"
                    f"[dim]Version:[/dim] {policy.version}\n"
                    f"[dim]Priority:[/dim] {policy.priority}\n"
                    f"[dim]Risk Level:[/dim] {policy.risk_level or '(not set)'}\n"
                    f"[dim]ISO Control:[/dim] {policy.iso_control or '(none)'}\n"
                    f"[dim]Enabled:[/dim] {'Yes' if policy.enabled else 'No'}\n"
                    f"[dim]Approval Required:[/dim] "
                    f"{policy.approval_required_by or 'No'}",
                    title="Policy Details",
                )
            )

            if policy.actions:
                console.print("\n[bold]Actions Covered:[/bold]")
                for action in policy.actions:
                    console.print(f"  • {action.value}")

            if policy.conditions:
                console.print("\n[bold]Conditions:[/bold]")
                for cond in policy.conditions:
                    console.print(f"  • {cond.field} {cond.operator} {cond.value}")

            if policy.actors:
                console.print("\n[bold]Actors:[/bold]")
                for actor in policy.actors:
                    console.print(f"  • {actor}")

    except ImportError:
        console.print("[red]Error: paracle_governance package not installed[/red]")
        raise SystemExit(1)
    except Exception as e:
        console.print(f"[red]Error: {e}[/red]")
        raise SystemExit(1)


@governance.command("evaluate")
@click.argument("actor")
@click.argument("action")
@click.option("--target", "-t", help="Target resource")
@click.option("--context", "-c", multiple=True, help="Context key=value pairs")
@click.option("--json", "as_json", is_flag=True, help="Output as JSON")
def evaluate_action(
    actor: str,
    action: str,
    target: str | None,
    context: tuple[str, ...],
    as_json: bool,
) -> None:
    """Evaluate an action against governance policies.

    Example: paracle governance evaluate coder file_write --target /app/main.py
    """
    try:
        from paracle_governance import PolicyAction, PolicyEngine

        engine = PolicyEngine()
        engine.load_default_policies()

        # Parse context
        ctx = {}
        for item in context:
            if "=" in item:
                key, value = item.split("=", 1)
                ctx[key] = value

        # Try to convert action to PolicyAction
        try:
            policy_action = PolicyAction(action.upper())
        except ValueError:
            policy_action = PolicyAction(action)

        result = engine.evaluate(
            actor=actor,
            action=policy_action,
            target=target,
            context=ctx,
        )

        if as_json:
            click.echo(result.model_dump_json(indent=2))
        else:
            if result.allowed:
                status = "[green]✓ ALLOWED[/green]"
            else:
                status = "[red]✗ DENIED[/red]"

            console.print(f"\n{status}")
            console.print(f"[dim]Actor:[/dim] {actor}")
            console.print(f"[dim]Action:[/dim] {action}")
            console.print(f"[dim]Target:[/dim] {target or '(none)'}")

            if result.applied_policies:
                console.print("\n[bold]Applied Policies:[/bold]")
                for pid in result.applied_policies:
                    policy = engine.get_policy(pid)
                    if policy:
                        console.print(f"  • {policy.name} ({policy.type.value})")

            if result.reason:
                console.print(f"\n[dim]Reason:[/dim] {result.reason}")

            if result.requires_approval:
                console.print(
                    f"\n[yellow]⚠ Requires approval from: {result.approval_required_by}[/yellow]"
                )

    except ImportError:
        console.print("[red]Error: paracle_governance package not installed[/red]")
        raise SystemExit(1)
    except Exception as e:
        console.print(f"[red]Error: {e}[/red]")
        raise SystemExit(1)


@governance.command("risk")
@click.argument("actor")
@click.argument("action")
@click.option("--target", "-t", help="Target resource")
@click.option(
    "--data-sensitivity",
    "-d",
    default="internal",
    type=click.Choice(["public", "internal", "confidential", "restricted"]),
    help="Data sensitivity level",
)
@click.option("--json", "as_json", is_flag=True, help="Output as JSON")
def calculate_risk(
    actor: str,
    action: str,
    target: str | None,
    data_sensitivity: str,
    as_json: bool,
) -> None:
    """Calculate risk score for an action.

    Example: paracle governance risk coder file_delete --target /app/config.py -d confidential
    """
    try:
        from paracle_governance import PolicyAction, RiskScorer  # noqa: F401
        from paracle_governance.risk.factors import DataSensitivity

        scorer = RiskScorer()

        # Build context
        context = {
            "actor": actor,
            "action": action,
            "target": target,
            "data_sensitivity": DataSensitivity(data_sensitivity.upper()),
        }

        result = scorer.calculate(context)

        if as_json:
            click.echo(result.model_dump_json(indent=2))
        else:
            # Color based on risk level
            level_colors = {
                "LOW": "green",
                "MEDIUM": "yellow",
                "HIGH": "red",
                "CRITICAL": "red bold",
            }
            color = level_colors.get(result.level.value, "white")

            console.print("\n[bold]Risk Assessment[/bold]")
            console.print(
                f"Score: [{color}]{result.score:.1f}[/{color}] ({result.level.value})"
            )
            console.print(f"Action Required: {result.action.value}")

            console.print("\n[bold]Factor Contributions:[/bold]")
            for factor, contribution in sorted(
                result.factor_contributions.items(), key=lambda x: x[1], reverse=True
            ):
                bar_len = int(contribution / 5)
                bar = "█" * bar_len + "░" * (20 - bar_len)
                console.print(f"  {factor:20} [{bar}] {contribution:.1f}")

            if result.action.value != "ALLOW":
                console.print(
                    f"\n[yellow]⚠ Recommended: {result.action.value}[/yellow]"
                )

    except ImportError:
        console.print("[red]Error: paracle_governance package not installed[/red]")
        raise SystemExit(1)
    except Exception as e:
        console.print(f"[red]Error: {e}[/red]")
        raise SystemExit(1)


@governance.command("load")
@click.argument("policy_file", type=click.Path(exists=True))
@click.option("--validate-only", is_flag=True, help="Only validate, don't load")
def load_policies(policy_file: str, validate_only: bool) -> None:
    """Load policies from a YAML file.

    Example: paracle governance load ./policies/custom.yaml
    """
    try:
        from paracle_governance import PolicyLoader

        loader = PolicyLoader()
        policies = loader.load_from_file(Path(policy_file))

        if validate_only:
            msg = f"Validated {len(policies)} policies from {policy_file}"
            console.print(f"[green]✓[/green] {msg}")
            for p in policies:
                console.print(f"  • {p.name} ({p.type.value})")
        else:
            msg = f"Loaded {len(policies)} policies from {policy_file}"
            console.print(f"[green]✓[/green] {msg}")
            for p in policies:
                console.print(f"  • {p.name} ({p.type.value})")

    except ImportError:
        console.print("[red]Error: paracle_governance package not installed[/red]")
        raise SystemExit(1)
    except Exception as e:
        console.print(f"[red]Error loading policies: {e}[/red]")
        raise SystemExit(1)


@governance.command("defaults")
@click.option("--json", "as_json", is_flag=True, help="Output as JSON")
def show_defaults(as_json: bool) -> None:
    """Show default built-in policies."""
    try:
        from paracle_governance.policies import DEFAULT_POLICIES

        if as_json:
            click.echo(
                json.dumps(
                    {k: v.model_dump() for k, v in DEFAULT_POLICIES.items()},
                    indent=2,
                    default=str,
                )
            )
        else:
            console.print("[bold]Default Policies[/bold]\n")
            for policy_id, policy in DEFAULT_POLICIES.items():
                content = (
                    f"[dim]Type:[/dim] {policy.type.value}\n"
                    f"[dim]Description:[/dim] {policy.description}\n"
                    f"[dim]Risk Level:[/dim] {policy.risk_level or 'N/A'}\n"
                    f"[dim]ISO Control:[/dim] {policy.iso_control or 'N/A'}"
                )
                console.print(
                    Panel(
                        content,
                        title=f"[cyan]{policy.name}[/cyan]",
                        subtitle=f"ID: {policy_id}",
                    )
                )

    except ImportError:
        console.print("[red]Error: paracle_governance package not installed[/red]")
        raise SystemExit(1)
    except Exception as e:
        console.print(f"[red]Error: {e}[/red]")
        raise SystemExit(1)


# ============================================================================
# Layer 5: Continuous Monitoring Commands
# ============================================================================


@governance.command()
@click.option(
    "--auto-repair",
    is_flag=True,
    help="Enable automatic violation repair",
)
@click.option(
    "--repair-delay",
    type=float,
    default=5.0,
    help="Delay in seconds before auto-repair (default: 5.0)",
)
@click.option(
    "--daemon",
    is_flag=True,
    help="Run as background daemon",
)
def monitor(auto_repair: bool, repair_delay: float, daemon: bool):
    """Start continuous .parac/ structure monitoring.

    Monitors .parac/ directory for structure violations in real-time.
    When violations are detected, they are logged and optionally
    auto-repaired based on severity.

    Examples:
        # Monitor with auto-repair
        paracle governance monitor --auto-repair

        # Run as daemon
        paracle governance monitor --daemon

        # Custom repair delay
        paracle governance monitor --auto-repair --repair-delay 10
    """
    try:
        from paracle_core.governance import get_monitor

        # Get monitor instance
        monitor_instance = get_monitor(
            auto_repair=auto_repair,
            repair_delay=repair_delay,
        )

        # Display startup banner
        console.print("\n[bold cyan]🛡️  Paracle Governance Monitor[/bold cyan]")
        console.print("=" * 60)
        console.print(f"Monitoring: {monitor_instance.parac_root}")
        console.print(f"Auto-repair: {'✅ Enabled' if auto_repair else '❌ Disabled'}")
        if auto_repair:
            console.print(f"Repair delay: {repair_delay}s")
        console.print("=" * 60)
        console.print("\n[yellow]Press Ctrl+C to stop monitoring[/yellow]\n")

        # Start monitoring
        monitor_instance.start()

        if daemon:
            console.print("[green]Monitor running in daemon mode[/green]")
            # Keep running indefinitely
            while True:
                time.sleep(60)
        else:
            # Interactive mode with live dashboard
            _display_live_dashboard(monitor_instance)

    except KeyboardInterrupt:
        console.print("\n\n[yellow]Stopping monitor...[/yellow]")
        monitor_instance.stop()
        console.print("[green]Monitor stopped successfully[/green]\n")
        sys.exit(0)
    except Exception as e:
        console.print(f"\n[red]Error: {e}[/red]\n")
        sys.exit(1)


def _display_live_dashboard(monitor_instance):
    """Display live monitoring dashboard."""

    def generate_table() -> Table:
        """Generate dashboard table."""
        health = monitor_instance.get_health()

        # Create main table
        table = Table(title="Governance Monitor Dashboard", show_header=True)
        table.add_column("Metric", style="cyan", width=25)
        table.add_column("Value", style="yellow", width=30)

        # Status
        status_color = {
            "healthy": "green",
            "warning": "yellow",
            "critical": "red",
        }.get(health.status, "white")
        table.add_row(
            "Status", f"[{status_color}]{health.status.upper()}[/{status_color}]"
        )

        # Health percentage
        health_pct = health.health_percentage
        health_color = (
            "green" if health_pct >= 95 else "yellow" if health_pct >= 80 else "red"
        )
        table.add_row("Health", f"[{health_color}]{health_pct:.1f}%[/{health_color}]")

        # Files
        table.add_row("Total Files", f"{health.total_files}")
        table.add_row("Valid Files", f"[green]{health.valid_files}[/green]")
        table.add_row("Violations", f"[red]{health.violations}[/red]")
        table.add_row("Repaired", f"[blue]{health.repaired}[/blue]")

        # Auto-repair
        auto_repair_status = (
            "✅ Enabled" if health.auto_repair_enabled else "❌ Disabled"
        )
        table.add_row("Auto-Repair", auto_repair_status)

        # Uptime
        uptime_str = _format_duration(health.uptime_seconds)
        table.add_row("Uptime", uptime_str)

        # Last check
        last_check_str = health.last_check.strftime("%H:%M:%S")
        table.add_row("Last Check", last_check_str)

        # Violation rate
        table.add_row("Violation Rate", f"{health.violation_rate:.2f}/hour")

        return table

    # Live updating dashboard
    with Live(generate_table(), refresh_per_second=1) as live:
        try:
            while True:
                time.sleep(1)
                live.update(generate_table())
        except KeyboardInterrupt:
            pass


@governance.command()
@click.option(
    "--verbose",
    "-v",
    is_flag=True,
    help="Show detailed information",
)
def health(verbose: bool):
    """Check governance health status.

    Displays current governance health including:
    - Overall status
    - File statistics
    - Violation count
    - Repair statistics

    Examples:
        paracle governance health
        paracle governance health -v
    """
    try:
        from paracle_core.governance import get_monitor

        # Get monitor (don't start it)
        monitor_instance = get_monitor()

        # Perform scan
        console.print("\n[cyan]Scanning .parac/ structure...[/cyan]")
        monitor_instance._scan_all_files()

        # Get health
        health = monitor_instance.get_health()

        # Display health panel
        _display_health_panel(health, verbose, monitor_instance)

    except Exception as e:
        console.print(f"\n[red]Error: {e}[/red]\n")
        sys.exit(1)


def _display_health_panel(health, verbose: bool, monitor_instance):
    """Display health information panel."""
    # Status emoji and color
    status_info = {
        "healthy": ("✅", "green"),
        "warning": ("⚠️", "yellow"),
        "critical": ("❌", "red"),
    }
    emoji, color = status_info.get(health.status, ("❓", "white"))

    # Build content
    content = []
    content.append(
        f"[bold {color}]{emoji} Status: " f"{health.status.upper()}[/bold {color}]"
    )
    content.append("")
    content.append(f"Health: [{color}]{health.health_percentage:.1f}%[/{color}]")
    content.append(f"Total Files: {health.total_files}")
    content.append(f"Valid Files: [green]{health.valid_files}[/green]")
    content.append(f"Violations: [red]{health.violations}[/red]")
    content.append(f"Repaired: [blue]{health.repaired}[/blue]")

    # Create panel
    panel = Panel(
        "\n".join(content),
        title="[bold cyan]Governance Health[/bold cyan]",
        border_style=color,
    )
    console.print(panel)

    # Show violations if any
    if health.violations > 0:
        console.print("\n[bold red]Active Violations:[/bold red]")

        violations = monitor_instance.get_violations()
        for v in violations:
            console.print(f"\n  📁 {v.path}")
            console.print(f"     Category: {v.category.value}")
            console.print(f"     Severity: {v.severity.value}")
            console.print(f"     Issue: {v.error}")
            console.print(f"     Fix: Move to {v.suggested_path}")

        console.print(
            "\n[yellow]Run 'paracle governance repair' " "to fix violations[/yellow]"
        )
    else:
        console.print(
            "\n[green]✅ No violations found - " "governance is healthy![/green]"
        )

    # Verbose information
    if verbose and health.repaired > 0:
        console.print("\n[bold blue]Recently Repaired:[/bold blue]")

        repaired = monitor_instance.get_repaired_violations()[-5:]  # Last 5
        for v in repaired:
            repaired_ago = _format_duration(
                (datetime.now() - v.repaired_at).total_seconds()
            )
            console.print(f"  ✅ {v.path} → {v.suggested_path} ({repaired_ago} ago)")

    console.print()


@governance.command()
@click.option(
    "--dry-run",
    is_flag=True,
    help="Show what would be repaired without actually repairing",
)
@click.option(
    "--force",
    is_flag=True,
    help="Skip confirmation prompt",
)
def repair(dry_run: bool, force: bool):
    """Manually repair all violations.

    Scans .parac/ structure and repairs all detected violations
    by moving files to their correct locations.

    Examples:
        # Preview repairs
        paracle governance repair --dry-run

        # Repair without confirmation
        paracle governance repair --force
    """
    try:
        from paracle_core.governance import get_monitor

        # Get monitor
        monitor_instance = get_monitor()

        # Scan for violations
        console.print("\n[cyan]Scanning for violations...[/cyan]")
        monitor_instance._scan_all_files()

        violations = monitor_instance.get_violations()

        if not violations:
            console.print(
                "[green]✅ No violations found - nothing to repair![/green]\n"
            )
            return

        # Display violations
        console.print(f"\n[yellow]Found {len(violations)} violation(s):[/yellow]\n")

        for i, v in enumerate(violations, 1):
            console.print(f"{i}. {v.path}")
            console.print(f"   → {v.suggested_path}")
            console.print(f"   Issue: {v.error}\n")

        if dry_run:
            console.print("[yellow]Dry run - no repairs performed[/yellow]\n")
            return

        # Confirm
        if not force:
            confirm = click.confirm("\nProceed with repairs?", default=True)
            if not confirm:
                console.print("[yellow]Repair cancelled[/yellow]\n")
                return

        # Repair
        console.print("\n[cyan]Repairing violations...[/cyan]\n")

        repaired = monitor_instance.repair_all()

        console.print(
            f"\n[green]✅ Successfully repaired "
            f"{repaired}/{len(violations)} violation(s)[/green]\n"
        )

    except Exception as e:
        console.print(f"\n[red]Error: {e}[/red]\n")
        sys.exit(1)


@governance.command()
@click.option(
    "--limit",
    type=int,
    default=20,
    help="Maximum number of entries to show (default: 20)",
)
def history(limit: int):
    """View violation repair history.

    Displays history of repaired violations with timestamps.

    Examples:
        paracle governance history
        paracle governance history --limit 50
    """
    try:
        from paracle_core.governance import get_monitor

        # Get monitor
        monitor_instance = get_monitor()

        repaired = monitor_instance.get_repaired_violations()

        if not repaired:
            console.print("\n[yellow]No repair history found[/yellow]\n")
            return

        # Display history
        console.print(f"\n[bold cyan]Repair History (last {limit}):[/bold cyan]\n")

        for v in repaired[-limit:]:
            if v.repaired_at:
                timestamp = v.repaired_at.strftime("%Y-%m-%d %H:%M:%S")
                console.print(f"[dim]{timestamp}[/dim]")
                console.print(f"  {v.path} → {v.suggested_path}")
                action_str = v.repair_action.value if v.repair_action else "unknown"
                console.print(f"  Action: {action_str}\n")

        console.print(f"[green]Total repairs: {len(repaired)}[/green]\n")

    except Exception as e:
        console.print(f"\n[red]Error: {e}[/red]\n")
        sys.exit(1)


def _format_duration(seconds: float) -> str:
    """Format duration in seconds to human-readable string."""
    if seconds < 60:
        return f"{seconds:.0f}s"
    elif seconds < 3600:
        minutes = seconds / 60
        return f"{minutes:.1f}m"
    elif seconds < 86400:
        hours = seconds / 3600
        return f"{hours:.1f}h"
    else:
        days = seconds / 86400
        return f"{days:.1f}d"
