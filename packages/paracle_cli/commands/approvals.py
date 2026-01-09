"""Paracle CLI - Approval Commands.

Commands for managing Human-in-the-Loop approval requests (ISO 42001 compliance).
These commands allow reviewing and deciding on pending workflow approvals.
"""

import json

import click
from rich.console import Console
from rich.table import Table

from paracle_cli.api_client import APIError, get_client

console = Console()


@click.group(invoke_without_command=True)
@click.option(
    "--list",
    "-l",
    "list_flag",
    is_flag=True,
    help="List pending approvals (shortcut for 'list')",
)
@click.pass_context
def approvals(ctx: click.Context, list_flag: bool) -> None:
    """Manage approval requests (Human-in-the-Loop).

    Approval requests are created when workflows require human oversight.
    Use these commands to list, approve, or reject pending requests.

    Examples:
        # List pending approvals (shortcut)
        $ paracle approvals -l

        # List pending approvals
        $ paracle approvals list

        # Approve a request
        $ paracle approvals approve abc123 --approver user@example.com

        # Reject a request with reason
        $ paracle approvals reject abc123 --approver user@example.com --reason "Needs review"

        # View approval statistics
        $ paracle approvals stats
    """
    if list_flag:
        ctx.invoke(
            list_approvals,
            status="pending",
            workflow_id=None,
            priority=None,
            limit=100,
            output_json=False,
        )
    elif ctx.invoked_subcommand is None:
        click.echo(ctx.get_help())


@approvals.command("list")
@click.option(
    "--status",
    type=click.Choice(["pending", "decided"]),
    default="pending",
    help="Filter by status (pending or decided)",
)
@click.option("--workflow-id", help="Filter by workflow ID")
@click.option(
    "--priority",
    type=click.Choice(["low", "medium", "high", "critical"]),
    help="Filter by priority (for pending)",
)
@click.option("--limit", default=100, help="Maximum results (for decided)")
@click.option("--json", "output_json", is_flag=True, help="Output as JSON")
def list_approvals(
    status: str,
    workflow_id: str | None,
    priority: str | None,
    limit: int,
    output_json: bool,
) -> None:
    """List approval requests.

    By default shows pending approvals. Use --status decided to see history.

    Examples:
        $ paracle approvals list
        $ paracle approvals list --status decided --limit 20
        $ paracle approvals list --priority high
    """
    client = get_client()

    if not client.is_available():
        console.print("[red]API not available.[/red] Start with: paracle serve")
        raise click.Abort()

    try:
        if status == "pending":
            result = client.approvals_list_pending(
                workflow_id=workflow_id, priority=priority
            )
        else:
            result = client.approvals_list_decided(workflow_id=workflow_id, limit=limit)

        if output_json:
            console.print_json(json.dumps(result))
            return

        approvals_list = result.get("approvals", [])

        if not approvals_list:
            console.print(f"[dim]No {status} approvals found.[/dim]")
            return

        # Create table
        title = "Pending Approvals" if status == "pending" else "Decided Approvals"
        table = Table(title=title, show_header=True, header_style="bold cyan")
        table.add_column("ID", style="cyan", width=12)
        table.add_column("Workflow", width=15)
        table.add_column("Step", width=15)
        table.add_column("Agent", width=12)
        table.add_column("Priority", justify="center", width=10)
        table.add_column("Status", justify="center", width=10)
        table.add_column("Created", width=20)

        for approval in approvals_list:
            # Priority styling
            priority_val = approval.get("priority", "medium")
            if priority_val == "critical":
                priority_style = "[red bold]CRITICAL[/red bold]"
            elif priority_val == "high":
                priority_style = "[red]high[/red]"
            elif priority_val == "medium":
                priority_style = "[yellow]medium[/yellow]"
            else:
                priority_style = "[dim]low[/dim]"

            # Status styling
            status_val = approval.get("status", "pending")
            if status_val == "pending":
                status_style = "[yellow]pending[/yellow]"
            elif status_val == "approved":
                status_style = "[green]approved[/green]"
            elif status_val == "rejected":
                status_style = "[red]rejected[/red]"
            else:
                status_style = f"[dim]{status_val}[/dim]"

            table.add_row(
                approval.get("id", "")[:12],
                approval.get("workflow_id", "")[:15],
                approval.get("step_name", "")[:15],
                approval.get("agent_name", "")[:12],
                priority_style,
                status_style,
                approval.get("created_at", "")[:19],
            )

        console.print(table)
        console.print(f"\n[dim]Total: {result.get('total', len(approvals_list))}[/dim]")

    except APIError as e:
        console.print(f"[red]Error:[/red] {e.detail}")
        raise click.Abort()


@approvals.command("get")
@click.argument("approval_id")
@click.option("--json", "output_json", is_flag=True, help="Output as JSON")
def get_approval(approval_id: str, output_json: bool) -> None:
    """Get details of a specific approval request.

    Args:
        approval_id: The approval request ID

    Examples:
        $ paracle approvals get abc123
        $ paracle approvals get abc123 --json
    """
    client = get_client()

    if not client.is_available():
        console.print("[red]API not available.[/red] Start with: paracle serve")
        raise click.Abort()

    try:
        result = client.approvals_get(approval_id)

        if output_json:
            console.print_json(json.dumps(result))
            return

        # Display detailed view
        console.print(
            f"\n[bold cyan]Approval Request: {result.get('id')}[/bold cyan]\n"
        )

        console.print(f"[bold]Workflow:[/bold] {result.get('workflow_id')}")
        console.print(f"[bold]Execution:[/bold] {result.get('execution_id')}")
        console.print(
            f"[bold]Step:[/bold] {result.get('step_name')} ({result.get('step_id')})"
        )
        console.print(f"[bold]Agent:[/bold] {result.get('agent_name')}")

        # Status with styling
        status_val = result.get("status", "pending")
        if status_val == "pending":
            status_display = "[yellow]PENDING[/yellow]"
        elif status_val == "approved":
            status_display = "[green]APPROVED[/green]"
        elif status_val == "rejected":
            status_display = "[red]REJECTED[/red]"
        else:
            status_display = status_val

        console.print(f"[bold]Status:[/bold] {status_display}")
        console.print(f"[bold]Priority:[/bold] {result.get('priority')}")
        console.print(f"[bold]Created:[/bold] {result.get('created_at')}")

        if result.get("expires_at"):
            console.print(f"[bold]Expires:[/bold] {result.get('expires_at')}")

        if result.get("decided_at"):
            console.print(f"\n[bold]Decided at:[/bold] {result.get('decided_at')}")
            console.print(f"[bold]Decided by:[/bold] {result.get('decided_by')}")
            if result.get("decision_reason"):
                console.print(f"[bold]Reason:[/bold] {result.get('decision_reason')}")

        # Context
        context = result.get("context", {})
        if context:
            console.print("\n[bold]Context:[/bold]")
            for key, value in context.items():
                console.print(f"  {key}: {value}")

    except APIError as e:
        console.print(f"[red]Error:[/red] {e.detail}")
        raise click.Abort()


@approvals.command("approve")
@click.argument("approval_id")
@click.option("--approver", "-a", required=True, help="Approver ID/email")
@click.option("--reason", "-r", help="Optional reason for approval")
def approve_request(approval_id: str, approver: str, reason: str | None) -> None:
    """Approve a pending request.

    Args:
        approval_id: The approval request ID

    Examples:
        $ paracle approvals approve abc123 --approver user@example.com
        $ paracle approvals approve abc123 -a admin -r "Looks good"
    """
    client = get_client()

    if not client.is_available():
        console.print("[red]API not available.[/red] Start with: paracle serve")
        raise click.Abort()

    try:
        result = client.approvals_approve(approval_id, approver, reason)

        console.print(f"[green]Approved[/green] request {result.get('id')}")
        console.print(f"  Workflow: {result.get('workflow_id')}")
        console.print(f"  Step: {result.get('step_name')}")
        console.print(f"  Approved by: {approver}")
        if reason:
            console.print(f"  Reason: {reason}")

    except APIError as e:
        if e.status_code == 404:
            console.print(f"[red]Approval not found:[/red] {approval_id}")
        elif e.status_code == 409:
            console.print(f"[yellow]Already decided:[/yellow] {e.detail}")
        elif e.status_code == 403:
            console.print(f"[red]Unauthorized:[/red] {e.detail}")
        else:
            console.print(f"[red]Error:[/red] {e.detail}")
        raise click.Abort()


@approvals.command("reject")
@click.argument("approval_id")
@click.option("--approver", "-a", required=True, help="Approver ID/email")
@click.option("--reason", "-r", help="Optional reason for rejection")
def reject_request(approval_id: str, approver: str, reason: str | None) -> None:
    """Reject a pending request.

    Args:
        approval_id: The approval request ID

    Examples:
        $ paracle approvals reject abc123 --approver user@example.com
        $ paracle approvals reject abc123 -a admin -r "Security concern"
    """
    client = get_client()

    if not client.is_available():
        console.print("[red]API not available.[/red] Start with: paracle serve")
        raise click.Abort()

    try:
        result = client.approvals_reject(approval_id, approver, reason)

        console.print(f"[red]Rejected[/red] request {result.get('id')}")
        console.print(f"  Workflow: {result.get('workflow_id')}")
        console.print(f"  Step: {result.get('step_name')}")
        console.print(f"  Rejected by: {approver}")
        if reason:
            console.print(f"  Reason: {reason}")

    except APIError as e:
        if e.status_code == 404:
            console.print(f"[red]Approval not found:[/red] {approval_id}")
        elif e.status_code == 409:
            console.print(f"[yellow]Already decided:[/yellow] {e.detail}")
        elif e.status_code == 403:
            console.print(f"[red]Unauthorized:[/red] {e.detail}")
        else:
            console.print(f"[red]Error:[/red] {e.detail}")
        raise click.Abort()


@approvals.command("cancel")
@click.argument("approval_id")
def cancel_request(approval_id: str) -> None:
    """Cancel a pending request.

    This is typically used when the parent workflow is cancelled.

    Args:
        approval_id: The approval request ID

    Examples:
        $ paracle approvals cancel abc123
    """
    client = get_client()

    if not client.is_available():
        console.print("[red]API not available.[/red] Start with: paracle serve")
        raise click.Abort()

    try:
        result = client.approvals_cancel(approval_id)

        console.print(f"[yellow]Cancelled[/yellow] request {result.get('id')}")

    except APIError as e:
        if e.status_code == 404:
            console.print(f"[red]Approval not found:[/red] {approval_id}")
        elif e.status_code == 409:
            console.print(f"[yellow]Already decided:[/yellow] {e.detail}")
        else:
            console.print(f"[red]Error:[/red] {e.detail}")
        raise click.Abort()


@approvals.command("stats")
@click.option("--json", "output_json", is_flag=True, help="Output as JSON")
def approval_stats(output_json: bool) -> None:
    """Show approval statistics.

    Displays counts of pending, approved, rejected, expired, and cancelled requests.

    Examples:
        $ paracle approvals stats
        $ paracle approvals stats --json
    """
    client = get_client()

    if not client.is_available():
        console.print("[red]API not available.[/red] Start with: paracle serve")
        raise click.Abort()

    try:
        result = client.approvals_stats()

        if output_json:
            console.print_json(json.dumps(result))
            return

        console.print("\n[bold cyan]Approval Statistics[/bold cyan]\n")

        table = Table(show_header=True, header_style="bold")
        table.add_column("Status", style="cyan")
        table.add_column("Count", justify="right")

        table.add_row("Pending", f"[yellow]{result.get('pending_count', 0)}[/yellow]")
        table.add_row("Approved", f"[green]{result.get('approved_count', 0)}[/green]")
        table.add_row("Rejected", f"[red]{result.get('rejected_count', 0)}[/red]")
        table.add_row("Expired", f"[dim]{result.get('expired_count', 0)}[/dim]")
        table.add_row("Cancelled", f"[dim]{result.get('cancelled_count', 0)}[/dim]")
        table.add_row("", "")
        table.add_row(
            "[bold]Total Decided[/bold]",
            f"[bold]{result.get('decided_count', 0)}[/bold]",
        )

        console.print(table)

    except APIError as e:
        console.print(f"[red]Error:[/red] {e.detail}")
        raise click.Abort()
