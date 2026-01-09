"""Retry management CLI commands.

Provides commands for viewing retry statistics, managing retry contexts,
and configuring retry policies for workflow steps.
"""

import json

import click
from rich.console import Console
from rich.table import Table

console = Console()


@click.group()
def retry():
    """Manage workflow retry policies and statistics."""
    pass


@retry.command()
@click.option(
    "--format",
    type=click.Choice(["text", "json"]),
    default="text",
    help="Output format",
)
def stats(format: str):
    """Display retry statistics.

    Shows success rates, total retries, and average retries per context.

    Example:
        paracle retry stats
        paracle retry stats --format json
    """
    # Import here to avoid circular dependencies
    from paracle_orchestration import RetryManager

    manager = RetryManager()
    stats_data = manager.get_retry_stats()

    if format == "json":
        click.echo(json.dumps(stats_data, indent=2))
        return

    # Display as formatted text
    console.print("\n[bold cyan]Retry Statistics[/bold cyan]\n")

    table = Table(show_header=True, header_style="bold")
    table.add_column("Metric", style="cyan")
    table.add_column("Value", justify="right")

    table.add_row("Total Contexts", str(stats_data["total_contexts"]))
    table.add_row("Succeeded", f"[green]{stats_data['succeeded']}[/green]")
    table.add_row("Failed", f"[red]{stats_data['failed']}[/red]")
    table.add_row(
        "Success Rate",
        f"{stats_data['success_rate']:.1%}",
    )
    table.add_row("", "")  # Separator
    table.add_row("Total Attempts", str(stats_data["total_attempts"]))
    table.add_row("Total Retries", str(stats_data["total_retries"]))
    table.add_row(
        "Avg Retries/Context",
        f"{stats_data['avg_retries_per_context']:.2f}",
    )

    console.print(table)
    console.print()


@retry.command()
@click.option("--workflow-id", help="Filter by workflow ID")
@click.option("--execution-id", help="Filter by execution ID")
@click.option(
    "--status",
    type=click.Choice(["succeeded", "failed", "all"]),
    default="all",
    help="Filter by status",
)
@click.option(
    "--format",
    type=click.Choice(["text", "json"]),
    default="text",
    help="Output format",
)
def list(workflow_id: str | None, execution_id: str | None, status: str, format: str):
    """List retry contexts.

    Shows all retry contexts with their status, attempts, and policies.

    Example:
        paracle retry list
        paracle retry list --workflow-id wf_123
        paracle retry list --status failed
        paracle retry list --format json
    """
    from paracle_orchestration import RetryManager

    manager = RetryManager()

    # Get all contexts
    contexts = list(manager._retry_contexts.values())

    # Apply filters
    if workflow_id:
        contexts = [c for c in contexts if c.workflow_id == workflow_id]

    if execution_id:
        contexts = [c for c in contexts if c.execution_id == execution_id]

    if status != "all":
        if status == "succeeded":
            contexts = [c for c in contexts if c.succeeded]
        elif status == "failed":
            contexts = [c for c in contexts if not c.succeeded]

    if format == "json":
        data = [
            {
                "step_name": ctx.step_name,
                "workflow_id": ctx.workflow_id,
                "execution_id": ctx.execution_id,
                "total_retries": ctx.total_retries,
                "succeeded": ctx.succeeded,
                "max_attempts": ctx.policy.max_attempts,
                "backoff_strategy": ctx.policy.backoff_strategy.value,
            }
            for ctx in contexts
        ]
        click.echo(json.dumps(data, indent=2))
        return

    if not contexts:
        console.print("[yellow]No retry contexts found.[/yellow]")
        return

    # Display as table
    console.print(f"\n[bold cyan]Retry Contexts ({len(contexts)})[/bold cyan]\n")

    table = Table(show_header=True, header_style="bold")
    table.add_column("Step", style="cyan")
    table.add_column("Workflow ID", style="dim")
    table.add_column("Execution ID", style="dim")
    table.add_column("Retries", justify="right")
    table.add_column("Status")
    table.add_column("Strategy", style="dim")

    for ctx in contexts:
        status_display = (
            "[green]✓ Succeeded[/green]" if ctx.succeeded else "[red]✗ Failed[/red]"
        )

        table.add_row(
            ctx.step_name,
            (
                ctx.workflow_id[:12] + "..."
                if len(ctx.workflow_id) > 12
                else ctx.workflow_id
            ),
            (
                ctx.execution_id[:12] + "..."
                if len(ctx.execution_id) > 12
                else ctx.execution_id
            ),
            f"{ctx.total_retries}/{ctx.policy.max_attempts - 1}",
            status_display,
            ctx.policy.backoff_strategy.value,
        )

    console.print(table)
    console.print()


@retry.command()
@click.argument("workflow_id")
@click.argument("execution_id")
@click.argument("step_name")
@click.option(
    "--format",
    type=click.Choice(["text", "json"]),
    default="text",
    help="Output format",
)
def get(workflow_id: str, execution_id: str, step_name: str, format: str):
    """Get detailed retry context for a specific step.

    Shows all retry attempts, errors, delays, and accumulated context.

    Example:
        paracle retry get wf_123 exec_456 api_call
        paracle retry get wf_123 exec_456 api_call --format json
    """
    from paracle_orchestration import RetryManager

    manager = RetryManager()
    ctx = manager.get_retry_context(workflow_id, execution_id, step_name)

    if not ctx:
        console.print(
            f"[red]Retry context not found for:[/red] {workflow_id}/{execution_id}/{step_name}"
        )
        raise click.Abort()

    if format == "json":
        data = {
            "step_name": ctx.step_name,
            "workflow_id": ctx.workflow_id,
            "execution_id": ctx.execution_id,
            "succeeded": ctx.succeeded,
            "total_retries": ctx.total_retries,
            "policy": {
                "max_attempts": ctx.policy.max_attempts,
                "backoff_strategy": ctx.policy.backoff_strategy.value,
                "initial_delay": ctx.policy.initial_delay,
                "max_delay": ctx.policy.max_delay,
                "backoff_factor": ctx.policy.backoff_factor,
            },
            "attempts": [
                {
                    "attempt_number": att.attempt_number,
                    "started_at": att.started_at.isoformat(),
                    "ended_at": att.ended_at.isoformat() if att.ended_at else None,
                    "error": att.error,
                    "error_type": att.error_type,
                    "error_category": att.error_category.value,
                    "delay_before": att.delay_before,
                }
                for att in ctx.attempts
            ],
            "accumulated_context": ctx.accumulated_context,
        }
        click.echo(json.dumps(data, indent=2))
        return

    # Display as formatted text
    console.print(f"\n[bold cyan]Retry Context: {step_name}[/bold cyan]\n")

    console.print(f"[bold]Workflow ID:[/bold] {ctx.workflow_id}")
    console.print(f"[bold]Execution ID:[/bold] {ctx.execution_id}")
    console.print(
        f"[bold]Status:[/bold] {'[green]✓ Succeeded[/green]' if ctx.succeeded else '[red]✗ Failed[/red]'}"
    )
    console.print(f"[bold]Total Retries:[/bold] {ctx.total_retries}")

    console.print("\n[bold]Policy:[/bold]")
    console.print(f"  Max Attempts: {ctx.policy.max_attempts}")
    console.print(f"  Strategy: {ctx.policy.backoff_strategy.value}")
    console.print(f"  Initial Delay: {ctx.policy.initial_delay}s")
    console.print(f"  Max Delay: {ctx.policy.max_delay}s")
    console.print(f"  Backoff Factor: {ctx.policy.backoff_factor}")

    console.print("\n[bold]Attempts:[/bold]")
    table = Table(show_header=True, header_style="bold")
    table.add_column("#", justify="right")
    table.add_column("Started", style="dim")
    table.add_column("Delay", justify="right")
    table.add_column("Error Category", style="dim")
    table.add_column("Error", style="red")

    for att in ctx.attempts:
        table.add_row(
            str(att.attempt_number),
            att.started_at.strftime("%H:%M:%S"),
            f"{att.delay_before:.1f}s" if att.delay_before > 0 else "-",
            att.error_category.value if att.error else "[green]success[/green]",
            (
                att.error[:60] + "..."
                if att.error and len(att.error) > 60
                else att.error or "[green]✓[/green]"
            ),
        )

    console.print(table)

    if ctx.accumulated_context:
        console.print("\n[bold]Accumulated Context:[/bold]")
        for key, value in ctx.accumulated_context.items():
            console.print(f"  {key}: {value}")

    console.print()


@retry.command()
@click.option("--workflow-id", help="Clear only this workflow's contexts")
@click.option("--execution-id", help="Clear only this execution's contexts")
@click.confirmation_option(
    prompt="Are you sure you want to clear retry contexts?",
)
def clear(workflow_id: str | None, execution_id: str | None):
    """Clear retry contexts.

    Removes retry contexts from memory. This does not affect retry policies.

    Example:
        paracle retry clear
        paracle retry clear --workflow-id wf_123
        paracle retry clear --execution-id exec_456
    """
    from paracle_orchestration import RetryManager

    manager = RetryManager()

    if workflow_id and execution_id:
        manager.clear_context(workflow_id, execution_id)
        console.print(
            f"[green]✓[/green] Cleared retry contexts for {workflow_id}/{execution_id}"
        )
    elif workflow_id or execution_id:
        console.print(
            "[red]Error:[/red] Both --workflow-id and --execution-id required for targeted clear"
        )
        raise click.Abort()
    else:
        # Clear all
        count = len(manager._retry_contexts)
        manager._retry_contexts.clear()
        console.print(f"[green]✓[/green] Cleared {count} retry contexts")


@retry.command()
@click.option(
    "--max-attempts",
    type=int,
    help="Maximum retry attempts (1-10)",
)
@click.option(
    "--strategy",
    type=click.Choice(["constant", "linear", "exponential", "fibonacci"]),
    help="Backoff strategy",
)
@click.option(
    "--initial-delay",
    type=float,
    help="Initial delay in seconds",
)
@click.option(
    "--max-delay",
    type=float,
    help="Maximum delay in seconds",
)
def policy(
    max_attempts: int | None,
    strategy: str | None,
    initial_delay: float | None,
    max_delay: float | None,
):
    """Display or configure default retry policy.

    Shows the current default retry policy or sets new values.

    Example:
        paracle retry policy                           # Show current policy
        paracle retry policy --max-attempts 5          # Set max attempts
        paracle retry policy --strategy exponential    # Set strategy
    """
    from paracle_domain.models import BackoffStrategy, RetryPolicy
    from paracle_orchestration import DEFAULT_RETRY_POLICY

    # If no options provided, display current policy
    if not any([max_attempts, strategy, initial_delay, max_delay]):
        console.print("\n[bold cyan]Default Retry Policy[/bold cyan]\n")
        console.print(f"[bold]Enabled:[/bold] {DEFAULT_RETRY_POLICY.enabled}")
        console.print(f"[bold]Max Attempts:[/bold] {DEFAULT_RETRY_POLICY.max_attempts}")
        console.print(
            f"[bold]Strategy:[/bold] {DEFAULT_RETRY_POLICY.backoff_strategy.value}"
        )
        console.print(
            f"[bold]Initial Delay:[/bold] {DEFAULT_RETRY_POLICY.initial_delay}s"
        )
        console.print(f"[bold]Max Delay:[/bold] {DEFAULT_RETRY_POLICY.max_delay}s")
        console.print(
            f"[bold]Backoff Factor:[/bold] {DEFAULT_RETRY_POLICY.backoff_factor}"
        )
        console.print()
        return

    # Create new policy (note: this doesn't persist, just shows what it would be)
    policy_dict = {
        "enabled": True,
        "max_attempts": max_attempts or DEFAULT_RETRY_POLICY.max_attempts,
        "backoff_strategy": (
            BackoffStrategy(strategy)
            if strategy
            else DEFAULT_RETRY_POLICY.backoff_strategy
        ),
        "initial_delay": initial_delay or DEFAULT_RETRY_POLICY.initial_delay,
        "max_delay": max_delay or DEFAULT_RETRY_POLICY.max_delay,
        "backoff_factor": DEFAULT_RETRY_POLICY.backoff_factor,
    }

    new_policy = RetryPolicy(**policy_dict)

    console.print("\n[bold cyan]Updated Retry Policy[/bold cyan]\n")
    console.print(f"[bold]Max Attempts:[/bold] {new_policy.max_attempts}")
    console.print(f"[bold]Strategy:[/bold] {new_policy.backoff_strategy.value}")
    console.print(f"[bold]Initial Delay:[/bold] {new_policy.initial_delay}s")
    console.print(f"[bold]Max Delay:[/bold] {new_policy.max_delay}s")
    console.print()

    console.print(
        "[yellow]Note:[/yellow] Policy changes are shown but not persisted. "
        "Configure policies in your workflow YAML files."
    )
