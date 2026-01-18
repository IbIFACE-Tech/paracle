"""CLI commands for business metrics.

Provides high-level KPI tracking for cost, usage, performance, and quality.
"""

import click
from rich.console import Console
from rich.panel import Panel
from rich.table import Table
from rich.text import Text

console = Console()


# =============================================================================
# Metrics Fallback Functions
# =============================================================================


def _fallback_metrics_summary() -> dict:
    """Get metrics summary directly from core."""
    from paracle_observability import get_business_metrics

    metrics = get_business_metrics()
    summary = metrics.get_summary()
    return {
        "health_score": summary.health_score,
        "daily_cost": summary.cost.total_cost,  # Using total_cost as daily
        "weekly_cost": summary.cost.total_cost,  # Placeholder
        "monthly_cost": summary.cost.total_cost,  # Placeholder
        "budget_utilization": summary.cost.budget_usage_pct / 100.0,
        "total_tokens": summary.cost.total_tokens,
        "total_requests": summary.usage.total_requests,
        "success_rate": summary.quality.success_rate,
        "error_rate": summary.quality.error_rate,
        "avg_latency": summary.performance.avg_latency * 1000,  # Convert to ms
        "timestamp": summary.generated_at.isoformat(),
    }


def _fallback_metrics_cost() -> dict:
    """Get cost metrics directly from core."""
    from paracle_observability import get_business_metrics

    metrics = get_business_metrics()
    summary = metrics.get_summary()
    cost = summary.cost
    return {
        "daily_cost": cost.total_cost,
        "weekly_cost": cost.total_cost,  # Placeholder
        "monthly_cost": cost.total_cost,  # Placeholder
        "budget_utilization": cost.budget_usage_pct / 100.0,
        "estimated_monthly_cost": cost.total_cost * 30,  # Rough estimate
        "alerts": 0,  # Would need alert system integration
        "budget_status": cost.budget_status,
        "cost_per_request": cost.cost_per_request,
    }


def _fallback_metrics_usage() -> dict:
    """Get usage metrics directly from core."""
    from paracle_observability import get_business_metrics

    metrics = get_business_metrics()
    summary = metrics.get_summary()
    cost = summary.cost
    usage = summary.usage
    return {
        "total_tokens": cost.total_tokens,
        "prompt_tokens": cost.prompt_tokens,
        "completion_tokens": cost.completion_tokens,
        "total_requests": usage.total_requests,
        "active_agents": 0,  # Not tracked in current summary
        "avg_tokens_per_request": cost.tokens_per_request,
    }


def _fallback_metrics_performance() -> dict:
    """Get performance metrics directly from core."""
    from paracle_observability import get_business_metrics

    metrics = get_business_metrics()
    summary = metrics.get_summary()
    perf = summary.performance
    return {
        "avg_latency": perf.avg_latency * 1000,  # Convert to ms
        "p95_latency": perf.p95_latency * 1000,  # Convert to ms
        "p99_latency": perf.p99_latency * 1000,  # Convert to ms
        "requests_per_minute": perf.requests_per_minute,
        "tokens_per_second": perf.tokens_per_second,
        "active_connections": 0,  # Not tracked
        "queue_depth": 0,  # Not tracked
    }


def _fallback_metrics_quality() -> dict:
    """Get quality metrics directly from core."""
    from paracle_observability import get_business_metrics

    metrics = get_business_metrics()
    summary = metrics.get_summary()
    quality = summary.quality
    return {
        "success_rate": quality.success_rate,
        "error_rate": quality.error_rate,
        "timeout_rate": 0.0,  # Not tracked separately
        "total_successes": int(quality.success_rate * summary.usage.total_requests),
        "total_errors": quality.error_count,
        "total_timeouts": 0,  # Not tracked
    }


# =============================================================================
# Display Functions
# =============================================================================


def _display_summary(data: dict) -> None:
    """Display metrics summary."""
    health_score = data.get("health_score", 0)

    # Health score color coding
    if health_score >= 80:
        health_color = "green"
        health_icon = "✓"
    elif health_score >= 60:
        health_color = "yellow"
        health_icon = "⚠"
    else:
        health_color = "red"
        health_icon = "✗"

    # Create summary panel
    title = Text()
    title.append("Business Metrics Summary - ", style="bold")
    title.append(
        f"{health_icon} Health Score: {health_score:.1f}/100",
        style=f"bold {health_color}",
    )

    table = Table(show_header=False, box=None, padding=(0, 2))
    table.add_column("Metric", style="cyan")
    table.add_column("Value", style="white")

    # Cost section
    table.add_row("", "")
    table.add_row("[bold]💰 Cost Metrics[/bold]", "")
    table.add_row("Daily Cost", f"${data.get('daily_cost', 0):.4f}")
    table.add_row("Weekly Cost", f"${data.get('weekly_cost', 0):.4f}")
    table.add_row("Monthly Cost", f"${data.get('monthly_cost', 0):.4f}")
    table.add_row("Budget Used", f"{data.get('budget_utilization', 0):.1%}")

    # Usage section
    table.add_row("", "")
    table.add_row("[bold]📊 Usage Metrics[/bold]", "")
    table.add_row("Total Tokens", f"{data.get('total_tokens', 0):,}")
    table.add_row("Total Requests", f"{data.get('total_requests', 0):,}")

    # Performance section
    table.add_row("", "")
    table.add_row("[bold]⚡ Performance[/bold]", "")
    table.add_row("Avg Latency", f"{data.get('avg_latency', 0):.0f}ms")

    # Quality section
    table.add_row("", "")
    table.add_row("[bold]✨ Quality[/bold]", "")
    table.add_row("Success Rate", f"{data.get('success_rate', 0):.1%}")
    table.add_row("Error Rate", f"{data.get('error_rate', 0):.1%}")

    console.print(Panel(table, title=title, border_style=health_color))


def _display_cost(data: dict) -> None:
    """Display cost metrics."""
    table = Table(title="💰 Cost Metrics", show_header=True)
    table.add_column("Metric", style="cyan")
    table.add_column("Value", style="white", justify="right")

    table.add_row("Daily Cost", f"${data.get('daily_cost', 0):.4f}")
    table.add_row("Weekly Cost", f"${data.get('weekly_cost', 0):.4f}")
    table.add_row("Monthly Cost", f"${data.get('monthly_cost', 0):.4f}")
    table.add_row("Estimated Monthly", f"${data.get('estimated_monthly_cost', 0):.2f}")
    table.add_row("", "")

    budget_util = data.get("budget_utilization", 0)
    status = data.get("budget_status", "ok")

    status_colors = {"ok": "green", "warning": "yellow", "critical": "red"}
    status_icons = {"ok": "✓", "warning": "⚠", "critical": "✗"}

    table.add_row("Budget Utilization", f"{budget_util:.1%}")
    table.add_row(
        "Budget Status",
        f"[{status_colors.get(status, 'white')}]{status_icons.get(status, '•')} {status.upper()}[/]",
    )
    table.add_row("Cost per Request", f"${data.get('cost_per_request', 0):.6f}")

    alerts = data.get("alerts", 0)
    if alerts > 0:
        table.add_row("", "")
        table.add_row("[red bold]Active Alerts[/]", f"[red bold]{alerts}[/]")

    console.print(table)


def _display_usage(data: dict) -> None:
    """Display usage metrics."""
    table = Table(title="📊 Usage Metrics", show_header=True)
    table.add_column("Metric", style="cyan")
    table.add_column("Value", style="white", justify="right")

    table.add_row("Total Tokens", f"{data.get('total_tokens', 0):,}")
    table.add_row("  - Prompt Tokens", f"{data.get('prompt_tokens', 0):,}")
    table.add_row("  - Completion Tokens", f"{data.get('completion_tokens', 0):,}")
    table.add_row("", "")
    table.add_row("Total Requests", f"{data.get('total_requests', 0):,}")
    table.add_row("Active Agents", f"{data.get('active_agents', 0)}")
    table.add_row("", "")
    table.add_row("Avg Tokens/Request", f"{data.get('avg_tokens_per_request', 0):.1f}")

    console.print(table)


def _display_performance(data: dict) -> None:
    """Display performance metrics."""
    table = Table(title="⚡ Performance Metrics", show_header=True)
    table.add_column("Metric", style="cyan")
    table.add_column("Value", style="white", justify="right")

    avg_latency = data.get("avg_latency", 0)
    p95_latency = data.get("p95_latency", 0)
    p99_latency = data.get("p99_latency", 0)

    # Latency color coding
    def latency_color(ms: float) -> str:
        if ms < 100:
            return "green"
        elif ms < 500:
            return "yellow"
        else:
            return "red"

    table.add_row(
        "Average Latency", f"[{latency_color(avg_latency)}]{avg_latency:.0f}ms[/]"
    )
    table.add_row(
        "P95 Latency", f"[{latency_color(p95_latency)}]{p95_latency:.0f}ms[/]"
    )
    table.add_row(
        "P99 Latency", f"[{latency_color(p99_latency)}]{p99_latency:.0f}ms[/]"
    )
    table.add_row("", "")
    table.add_row("Requests/Minute", f"{data.get('requests_per_minute', 0):.1f}")
    table.add_row("Tokens/Second", f"{data.get('tokens_per_second', 0):.1f}")
    table.add_row("", "")
    table.add_row("Active Connections", f"{data.get('active_connections', 0)}")
    table.add_row("Queue Depth", f"{data.get('queue_depth', 0)}")

    console.print(table)


def _display_quality(data: dict) -> None:
    """Display quality metrics."""
    table = Table(title="✨ Quality Metrics", show_header=True)
    table.add_column("Metric", style="cyan")
    table.add_column("Value", style="white", justify="right")

    success_rate = data.get("success_rate", 0)
    error_rate = data.get("error_rate", 0)
    timeout_rate = data.get("timeout_rate", 0)

    # Quality color coding
    def quality_color(rate: float, inverse: bool = False) -> str:
        if inverse:  # For error/timeout rates
            if rate < 0.01:
                return "green"
            elif rate < 0.05:
                return "yellow"
            else:
                return "red"
        else:  # For success rate
            if rate > 0.99:
                return "green"
            elif rate > 0.95:
                return "yellow"
            else:
                return "red"

    table.add_row(
        "Success Rate", f"[{quality_color(success_rate)}]{success_rate:.1%}[/]"
    )
    table.add_row(
        "Error Rate", f"[{quality_color(error_rate, True)}]{error_rate:.1%}[/]"
    )
    table.add_row(
        "Timeout Rate", f"[{quality_color(timeout_rate, True)}]{timeout_rate:.1%}[/]"
    )
    table.add_row("", "")
    table.add_row("Total Successes", f"{data.get('total_successes', 0):,}")
    table.add_row("Total Errors", f"{data.get('total_errors', 0):,}")
    table.add_row("Total Timeouts", f"{data.get('total_timeouts', 0):,}")

    console.print(table)


# =============================================================================
# CLI Commands
# =============================================================================


@click.group()
def metrics() -> None:
    """Business metrics and KPIs.

    Track cost, usage, performance, and quality metrics for your Paracle workspace.
    Provides high-level insights into system health and resource utilization.
    """
    pass


@metrics.command()
def summary() -> None:
    """Display comprehensive metrics summary with health score."""
    try:
        data = _fallback_metrics_summary()
        _display_summary(data)
    except Exception as e:
        console.print(f"[red]Error getting metrics summary: {e}[/]")
        raise click.Abort()


@metrics.command()
def cost() -> None:
    """Display cost metrics and budget status."""
    try:
        data = _fallback_metrics_cost()
        _display_cost(data)
    except Exception as e:
        console.print(f"[red]Error getting cost metrics: {e}[/]")
        raise click.Abort()


@metrics.command()
def usage() -> None:
    """Display usage metrics (tokens, requests, agents)."""
    try:
        data = _fallback_metrics_usage()
        _display_usage(data)
    except Exception as e:
        console.print(f"[red]Error getting usage metrics: {e}[/]")
        raise click.Abort()


@metrics.command()
def performance() -> None:
    """Display performance metrics (latency, throughput)."""
    try:
        data = _fallback_metrics_performance()
        _display_performance(data)
    except Exception as e:
        console.print(f"[red]Error getting performance metrics: {e}[/]")
        raise click.Abort()


@metrics.command()
def quality() -> None:
    """Display quality metrics (success rate, errors)."""
    try:
        data = _fallback_metrics_quality()
        _display_quality(data)
    except Exception as e:
        console.print(f"[red]Error getting quality metrics: {e}[/]")
        raise click.Abort()
