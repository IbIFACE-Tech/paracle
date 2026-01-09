"""Cost management CLI commands.

Provides commands for viewing and managing LLM costs:
- paracle cost report: View cost reports
- paracle cost usage: View usage statistics
- paracle cost budget: View budget status
- paracle cost cleanup: Clean up old cost records
"""

from datetime import datetime, timedelta

import click
from rich.console import Console
from rich.panel import Panel
from rich.table import Table

console = Console()


@click.group()
def cost():
    """Cost tracking and budget management commands."""
    pass


@cost.command()
@click.option(
    "--period",
    type=click.Choice(["day", "week", "month", "all"]),
    default="month",
    help="Time period for report",
)
@click.option("--json", "as_json", is_flag=True, help="Output as JSON")
@click.option("--provider", help="Filter by provider")
@click.option("--model", help="Filter by model")
def report(period: str, as_json: bool, provider: str | None, model: str | None):
    """Generate cost report.

    Shows detailed breakdown of costs by provider, model, workflow, and agent.

    Examples:
        paracle cost report
        paracle cost report --period week
        paracle cost report --json
    """
    try:
        from paracle_core.cost import CostTracker
    except ImportError:
        console.print("[red]Cost tracking module not available[/red]")
        raise SystemExit(1)

    tracker = CostTracker()

    # Calculate time range
    now = datetime.utcnow()
    if period == "day":
        start = now - timedelta(days=1)
    elif period == "week":
        start = now - timedelta(weeks=1)
    elif period == "month":
        start = now - timedelta(days=30)
    else:
        start = None

    report_data = tracker.get_report(start=start, end=now)

    if as_json:
        import json

        console.print(json.dumps(report_data.to_dict(), indent=2))
        return

    # Display report
    console.print()
    console.print(
        Panel.fit(
            f"[bold]Cost Report[/bold]\n"
            f"Period: {period}\n"
            f"Generated: {report_data.generated_at.strftime('%Y-%m-%d %H:%M:%S')}",
            border_style="blue",
        )
    )

    # Summary table
    summary_table = Table(title="Summary", show_header=True, header_style="bold cyan")
    summary_table.add_column("Metric", style="dim")
    summary_table.add_column("Value", justify="right")

    usage = report_data.total_usage
    summary_table.add_row("Total Cost", f"${usage.total_cost:.4f}")
    summary_table.add_row("Total Tokens", f"{usage.total_tokens:,}")
    summary_table.add_row("Prompt Tokens", f"{usage.prompt_tokens:,}")
    summary_table.add_row("Completion Tokens", f"{usage.completion_tokens:,}")
    summary_table.add_row("Requests", f"{usage.request_count:,}")

    if usage.request_count > 0:
        avg_cost = usage.total_cost / usage.request_count
        avg_tokens = usage.total_tokens / usage.request_count
        summary_table.add_row("Avg Cost/Request", f"${avg_cost:.6f}")
        summary_table.add_row("Avg Tokens/Request", f"{avg_tokens:.1f}")

    console.print(summary_table)
    console.print()

    # By Provider
    if report_data.by_provider:
        provider_table = Table(
            title="By Provider", show_header=True, header_style="bold cyan"
        )
        provider_table.add_column("Provider")
        provider_table.add_column("Cost", justify="right")
        provider_table.add_column("Tokens", justify="right")
        provider_table.add_column("Requests", justify="right")

        for prov, prov_usage in sorted(
            report_data.by_provider.items(),
            key=lambda x: x[1].total_cost,
            reverse=True,
        ):
            provider_table.add_row(
                prov,
                f"${prov_usage.total_cost:.4f}",
                f"{prov_usage.total_tokens:,}",
                f"{prov_usage.request_count}",
            )

        console.print(provider_table)
        console.print()

    # By Model (top 10)
    if report_data.by_model:
        model_table = Table(
            title="Top Models by Cost", show_header=True, header_style="bold cyan"
        )
        model_table.add_column("Model")
        model_table.add_column("Cost", justify="right")
        model_table.add_column("Tokens", justify="right")
        model_table.add_column("Requests", justify="right")

        for mdl, mdl_usage in sorted(
            report_data.by_model.items(),
            key=lambda x: x[1].total_cost,
            reverse=True,
        )[:10]:
            model_table.add_row(
                mdl,
                f"${mdl_usage.total_cost:.4f}",
                f"{mdl_usage.total_tokens:,}",
                f"{mdl_usage.request_count}",
            )

        console.print(model_table)
        console.print()

    # Budget Status
    status = report_data.budget_status
    status_color = {
        "ok": "green",
        "warning": "yellow",
        "critical": "red",
        "exceeded": "red bold",
    }.get(status.value, "white")

    console.print(
        f"Budget Status: [{status_color}]{status.value.upper()}[/{status_color}]"
    )

    if report_data.budget_alerts:
        console.print()
        console.print("[yellow]Recent Alerts:[/yellow]")
        for alert in report_data.budget_alerts[-5:]:
            console.print(f"  - {alert['message']}")


@cost.command()
@click.option(
    "--period",
    type=click.Choice(["today", "week", "month"]),
    default="today",
    help="Time period",
)
def usage(period: str):
    """Show current usage statistics.

    Examples:
        paracle cost usage
        paracle cost usage --period week
    """
    try:
        from paracle_core.cost import CostTracker
    except ImportError:
        console.print("[red]Cost tracking module not available[/red]")
        raise SystemExit(1)

    tracker = CostTracker()

    if period == "today":
        usage_data = tracker.get_daily_usage()
        title = "Today's Usage"
    elif period == "week":
        now = datetime.utcnow()
        start = now - timedelta(weeks=1)
        usage_data = tracker._query_usage(start=start, end=now)
        title = "This Week's Usage"
    else:
        usage_data = tracker.get_monthly_usage()
        title = "This Month's Usage"

    console.print()
    console.print(Panel.fit(f"[bold]{title}[/bold]", border_style="blue"))

    table = Table(show_header=False)
    table.add_column("Metric", style="dim")
    table.add_column("Value", justify="right")

    table.add_row("Total Cost", f"${usage_data.total_cost:.4f}")
    table.add_row("Total Tokens", f"{usage_data.total_tokens:,}")
    table.add_row("Prompt Tokens", f"{usage_data.prompt_tokens:,}")
    table.add_row("Completion Tokens", f"{usage_data.completion_tokens:,}")
    table.add_row("Requests", f"{usage_data.request_count}")

    console.print(table)


@cost.command()
def budget():
    """Show budget status and limits.

    Displays current budget configuration and usage against limits.

    Examples:
        paracle cost budget
    """
    try:
        from paracle_core.cost import CostConfig, CostTracker
    except ImportError:
        console.print("[red]Cost tracking module not available[/red]")
        raise SystemExit(1)

    config = CostConfig.from_project_yaml()
    tracker = CostTracker(config)

    console.print()
    console.print(Panel.fit("[bold]Budget Configuration[/bold]", border_style="blue"))

    if not config.budget.enabled:
        console.print("[dim]Budget enforcement is disabled[/dim]")
        console.print(
            "\nTo enable budgets, add to .parac/project.yaml:\n"
            "[cyan]cost:\n"
            "  budget:\n"
            "    enabled: true\n"
            "    daily_limit: 10.0[/cyan]"
        )
        return

    table = Table(show_header=True, header_style="bold cyan")
    table.add_column("Budget Type")
    table.add_column("Limit", justify="right")
    table.add_column("Current", justify="right")
    table.add_column("Usage %", justify="right")
    table.add_column("Status")

    def add_budget_row(name: str, limit: float | None, current: float):
        if limit is None:
            return

        percent = (current / limit * 100) if limit > 0 else 0
        if percent >= 100:
            status = "[red bold]EXCEEDED[/red bold]"
        elif percent >= config.budget.critical_threshold * 100:
            status = "[red]CRITICAL[/red]"
        elif percent >= config.budget.warning_threshold * 100:
            status = "[yellow]WARNING[/yellow]"
        else:
            status = "[green]OK[/green]"

        table.add_row(
            name,
            f"${limit:.2f}",
            f"${current:.4f}",
            f"{percent:.1f}%",
            status,
        )

    # Daily budget
    daily = tracker.get_daily_usage()
    add_budget_row("Daily", config.budget.daily_limit, daily.total_cost)

    # Monthly budget
    monthly = tracker.get_monthly_usage()
    add_budget_row("Monthly", config.budget.monthly_limit, monthly.total_cost)

    # Total budget
    total = tracker.get_total_usage()
    add_budget_row("Total", config.budget.total_limit, total.total_cost)

    console.print(table)
    console.print()

    if config.budget.block_on_exceed:
        console.print(
            "[yellow]Note: Execution will be blocked when budget is exceeded[/yellow]"
        )
    else:
        console.print(
            "[dim]Note: Alerts only - execution not blocked on budget exceed[/dim]"
        )


@cost.command()
@click.option("--format", "fmt", type=click.Choice(["table", "yaml"]), default="table")
def pricing(fmt: str):
    """Show configured model pricing.

    Examples:
        paracle cost pricing
        paracle cost pricing --format yaml
    """
    try:
        from paracle_core.cost import CostConfig
    except ImportError:
        console.print("[red]Cost tracking module not available[/red]")
        raise SystemExit(1)

    config = CostConfig.from_project_yaml()

    if fmt == "yaml":
        import yaml

        console.print(yaml.dump({"default_pricing": config.default_pricing}))
        return

    console.print()
    console.print(
        Panel.fit(
            "[bold]Model Pricing[/bold] (per million tokens)", border_style="blue"
        )
    )

    for provider, models in sorted(config.default_pricing.items()):
        table = Table(
            title=provider.upper(), show_header=True, header_style="bold cyan"
        )
        table.add_column("Model")
        table.add_column("Input $/M", justify="right")
        table.add_column("Output $/M", justify="right")

        for model, prices in sorted(models.items()):
            table.add_row(
                model,
                f"${prices['input']:.2f}",
                f"${prices['output']:.2f}",
            )

        console.print(table)
        console.print()


@cost.command()
@click.option(
    "--provider", required=True, help="Provider name (e.g., openai, anthropic)"
)
@click.option("--model", required=True, help="Model name")
@click.option(
    "--prompt-tokens", type=int, required=True, help="Estimated prompt tokens"
)
@click.option(
    "--completion-tokens", type=int, required=True, help="Estimated completion tokens"
)
def estimate(provider: str, model: str, prompt_tokens: int, completion_tokens: int):
    """Estimate cost for a request.

    Examples:
        paracle cost estimate --provider openai --model gpt-4 \\
            --prompt-tokens 1000 --completion-tokens 500
    """
    try:
        from paracle_core.cost import CostTracker
    except ImportError:
        console.print("[red]Cost tracking module not available[/red]")
        raise SystemExit(1)

    tracker = CostTracker()
    prompt_cost, completion_cost, total_cost = tracker.calculate_cost(
        provider, model, prompt_tokens, completion_tokens
    )

    console.print()
    console.print(Panel.fit("[bold]Cost Estimate[/bold]", border_style="blue"))

    table = Table(show_header=False)
    table.add_column("", style="dim")
    table.add_column("", justify="right")

    table.add_row("Provider", provider)
    table.add_row("Model", model)
    table.add_row("Prompt Tokens", f"{prompt_tokens:,}")
    table.add_row("Completion Tokens", f"{completion_tokens:,}")
    table.add_row("Total Tokens", f"{prompt_tokens + completion_tokens:,}")
    table.add_row("", "")
    table.add_row("Prompt Cost", f"${prompt_cost:.6f}")
    table.add_row("Completion Cost", f"${completion_cost:.6f}")
    table.add_row("[bold]Total Cost[/bold]", f"[bold]${total_cost:.6f}[/bold]")

    console.print(table)


@cost.command()
@click.option("--dry-run", is_flag=True, help="Show what would be deleted")
@click.option("--force", is_flag=True, help="Skip confirmation")
def cleanup(dry_run: bool, force: bool):
    """Clean up old cost records.

    Removes records older than the retention period (default: 90 days).

    Examples:
        paracle cost cleanup --dry-run
        paracle cost cleanup --force
    """
    try:
        from paracle_core.cost import CostTracker
    except ImportError:
        console.print("[red]Cost tracking module not available[/red]")
        raise SystemExit(1)

    tracker = CostTracker()

    count = tracker.cleanup_old_records(dry_run=True)

    if count == 0:
        console.print("[green]No records to clean up[/green]")
        return

    console.print(f"Found {count} records older than retention period")

    if dry_run:
        console.print("[dim]Dry run - no records deleted[/dim]")
        return

    if not force:
        if not click.confirm(f"Delete {count} records?"):
            console.print("Cancelled")
            return

    deleted = tracker.cleanup_old_records(dry_run=False)
    console.print(f"[green]Deleted {deleted} records[/green]")


# Register the cost command group
def register_cost_commands(cli):
    """Register cost commands with the main CLI."""
    cli.add_command(cost)
