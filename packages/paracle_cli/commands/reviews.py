"""Paracle CLI - Review Commands.

Commands for managing artifact reviews in sandbox executions (Phase 5).
These commands allow reviewing agent-generated artifacts before deployment.
"""

import json

import click
from rich.console import Console
from rich.panel import Panel
from rich.table import Table

from paracle_cli.api_client import APIError, get_client

console = Console()


@click.group(invoke_without_command=True)
@click.option(
    "--list",
    "-l",
    "list_flag",
    is_flag=True,
    help="List artifact reviews (shortcut for 'list')",
)
@click.pass_context
def reviews(ctx: click.Context, list_flag: bool) -> None:
    """Manage artifact reviews (sandbox execution).

    Artifact reviews are created when agents generate changes in sandboxed
    environments. Use these commands to review, approve, or reject artifacts
    before they are applied.

    Examples:
        # List reviews (shortcut)
        $ paracle reviews -l

        # List pending reviews
        $ paracle reviews list

        # Approve a review
        $ paracle reviews approve abc123 --reviewer user@example.com

        # Reject a review with comment
        $ paracle reviews reject abc123 --reviewer user@example.com --comment "Needs changes"

        # View review statistics
        $ paracle reviews stats
    """
    if list_flag:
        ctx.invoke(list_reviews, status=None, sandbox_id=None, output_json=False)
    elif ctx.invoked_subcommand is None:
        click.echo(ctx.get_help())


@reviews.command("list")
@click.option(
    "--status",
    type=click.Choice(["pending", "approved", "rejected", "timeout"]),
    help="Filter by status",
)
@click.option("--sandbox-id", help="Filter by sandbox ID")
@click.option("--json", "output_json", is_flag=True, help="Output as JSON")
def list_reviews(
    status: str | None,
    sandbox_id: str | None,
    output_json: bool,
) -> None:
    """List artifact reviews.

    Shows reviews with optional filtering by status or sandbox.

    Examples:
        $ paracle reviews list
        $ paracle reviews list --status pending
        $ paracle reviews list --sandbox-id sandbox-abc123
    """
    client = get_client()

    if not client.is_available():
        console.print("[red]API not available.[/red] Start with: paracle serve")
        raise click.Abort()

    try:
        result = client.reviews_list(status=status, sandbox_id=sandbox_id)

        if output_json:
            console.print_json(json.dumps(result))
            return

        reviews_list = result.get("reviews", [])

        if not reviews_list:
            console.print("[dim]No reviews found.[/dim]")
            return

        # Create table
        table = Table(
            title="Artifact Reviews", show_header=True, header_style="bold cyan"
        )
        table.add_column("ID", style="cyan", width=12)
        table.add_column("Artifact", width=20)
        table.add_column("Type", width=12)
        table.add_column("Risk", justify="center", width=8)
        table.add_column("Status", justify="center", width=10)
        table.add_column("Approvals", justify="center", width=10)
        table.add_column("Created", width=20)

        for review in reviews_list:
            # Risk level styling
            risk_level = review.get("risk_level", "medium")
            if risk_level == "high":
                risk_style = "[red bold]HIGH[/red bold]"
            elif risk_level == "medium":
                risk_style = "[yellow]medium[/yellow]"
            else:
                risk_style = "[green]low[/green]"

            # Status styling
            status_val = review.get("status", "pending")
            if status_val == "pending":
                status_style = "[yellow]pending[/yellow]"
            elif status_val == "approved":
                status_style = "[green]approved[/green]"
            elif status_val == "rejected":
                status_style = "[red]rejected[/red]"
            elif status_val == "timeout":
                status_style = "[dim]timeout[/dim]"
            else:
                status_style = status_val

            # Approval progress
            approval_count = review.get("approval_count", 0)
            required = review.get("required_approvals", 1)
            approvals_display = f"{approval_count}/{required}"

            table.add_row(
                review.get("review_id", "")[:12],
                review.get("artifact_id", "")[:20],
                review.get("artifact_type", "")[:12],
                risk_style,
                status_style,
                approvals_display,
                review.get("created_at", "")[:19],
            )

        console.print(table)
        console.print(f"\n[dim]Total: {result.get('total', len(reviews_list))}[/dim]")

    except APIError as e:
        console.print(f"[red]Error:[/red] {e.detail}")
        raise click.Abort()


@reviews.command("get")
@click.argument("review_id")
@click.option("--json", "output_json", is_flag=True, help="Output as JSON")
@click.option("--show-content", is_flag=True, help="Show artifact content")
def get_review(review_id: str, output_json: bool, show_content: bool) -> None:
    """Get details of a specific review.

    Args:
        review_id: The review ID

    Examples:
        $ paracle reviews get abc123
        $ paracle reviews get abc123 --show-content
        $ paracle reviews get abc123 --json
    """
    client = get_client()

    if not client.is_available():
        console.print("[red]API not available.[/red] Start with: paracle serve")
        raise click.Abort()

    try:
        result = client.reviews_get(review_id)

        if output_json:
            console.print_json(json.dumps(result))
            return

        # Display detailed view
        console.print(
            f"\n[bold cyan]Artifact Review: {result.get('review_id')}[/bold cyan]\n"
        )

        console.print(f"[bold]Artifact ID:[/bold] {result.get('artifact_id')}")
        console.print(f"[bold]Type:[/bold] {result.get('artifact_type')}")
        console.print(f"[bold]Sandbox:[/bold] {result.get('sandbox_id')}")

        # Risk level with styling
        risk_level = result.get("risk_level", "medium")
        if risk_level == "high":
            risk_display = "[red bold]HIGH[/red bold]"
        elif risk_level == "medium":
            risk_display = "[yellow]MEDIUM[/yellow]"
        else:
            risk_display = "[green]LOW[/green]"
        console.print(f"[bold]Risk Level:[/bold] {risk_display}")

        # Status with styling
        status_val = result.get("status", "pending")
        if status_val == "pending":
            status_display = "[yellow]PENDING[/yellow]"
        elif status_val == "approved":
            status_display = "[green]APPROVED[/green]"
        elif status_val == "rejected":
            status_display = "[red]REJECTED[/red]"
        elif status_val == "timeout":
            status_display = "[dim]TIMEOUT[/dim]"
        else:
            status_display = status_val

        console.print(f"[bold]Status:[/bold] {status_display}")

        # Approvals
        approval_count = result.get("approval_count", 0)
        required = result.get("required_approvals", 1)
        console.print(f"[bold]Approvals:[/bold] {approval_count}/{required}")

        # Timestamps
        console.print(f"[bold]Created:[/bold] {result.get('created_at')}")
        console.print(f"[bold]Updated:[/bold] {result.get('updated_at')}")
        if result.get("expires_at"):
            console.print(f"[bold]Expires:[/bold] {result.get('expires_at')}")

        # Decisions
        decisions = result.get("decisions", [])
        if decisions:
            console.print("\n[bold]Decisions:[/bold]")
            for decision in decisions:
                decision_type = decision.get("decision", "unknown")
                if decision_type == "approve":
                    icon = "[green]approved[/green]"
                else:
                    icon = "[red]rejected[/red]"
                reviewer = decision.get("reviewer", "unknown")
                timestamp = decision.get("timestamp", "")[:19]
                comment = decision.get("comment", "")

                console.print(f"  {icon} by {reviewer} at {timestamp}")
                if comment:
                    console.print(f"    Comment: {comment}")

        # Artifact content
        if show_content and result.get("artifact_content"):
            console.print("\n[bold]Artifact Content:[/bold]")
            content = result.get("artifact_content", "")
            if len(content) > 2000:
                content = content[:2000] + "\n... (truncated)"
            console.print(Panel(content, title="Content", border_style="dim"))

    except APIError as e:
        console.print(f"[red]Error:[/red] {e.detail}")
        raise click.Abort()


@reviews.command("approve")
@click.argument("review_id")
@click.option("--reviewer", "-r", required=True, help="Reviewer ID/email")
@click.option("--comment", "-c", help="Optional comment")
def approve_review(review_id: str, reviewer: str, comment: str | None) -> None:
    """Approve an artifact review.

    Args:
        review_id: The review ID

    Examples:
        $ paracle reviews approve abc123 --reviewer user@example.com
        $ paracle reviews approve abc123 -r admin -c "LGTM"
    """
    client = get_client()

    if not client.is_available():
        console.print("[red]API not available.[/red] Start with: paracle serve")
        raise click.Abort()

    try:
        result = client.reviews_approve(review_id, reviewer, comment)

        status = result.get("status", "pending")
        approval_count = result.get("approval_count", 0)
        required = result.get("required_approvals", 1)

        if status == "approved":
            console.print(f"[green]Approved[/green] review {result.get('review_id')}")
            console.print("  All required approvals received.")
        else:
            console.print(
                f"[yellow]Approval recorded[/yellow] for review {result.get('review_id')}"
            )
            console.print(f"  Approvals: {approval_count}/{required}")

        console.print(f"  Artifact: {result.get('artifact_id')}")
        console.print(f"  Approved by: {reviewer}")
        if comment:
            console.print(f"  Comment: {comment}")

    except APIError as e:
        if e.status_code == 404:
            console.print(f"[red]Review not found:[/red] {review_id}")
        elif e.status_code == 409:
            console.print(f"[yellow]Already decided:[/yellow] {e.detail}")
        elif e.status_code == 410:
            console.print(f"[red]Expired:[/red] {e.detail}")
        else:
            console.print(f"[red]Error:[/red] {e.detail}")
        raise click.Abort()


@reviews.command("reject")
@click.argument("review_id")
@click.option("--reviewer", "-r", required=True, help="Reviewer ID/email")
@click.option("--comment", "-c", help="Optional comment explaining rejection")
def reject_review(review_id: str, reviewer: str, comment: str | None) -> None:
    """Reject an artifact review.

    Args:
        review_id: The review ID

    Examples:
        $ paracle reviews reject abc123 --reviewer user@example.com
        $ paracle reviews reject abc123 -r admin -c "Security issue found"
    """
    client = get_client()

    if not client.is_available():
        console.print("[red]API not available.[/red] Start with: paracle serve")
        raise click.Abort()

    try:
        result = client.reviews_reject(review_id, reviewer, comment)

        console.print(f"[red]Rejected[/red] review {result.get('review_id')}")
        console.print(f"  Artifact: {result.get('artifact_id')}")
        console.print(f"  Rejected by: {reviewer}")
        if comment:
            console.print(f"  Comment: {comment}")

    except APIError as e:
        if e.status_code == 404:
            console.print(f"[red]Review not found:[/red] {review_id}")
        elif e.status_code == 409:
            console.print(f"[yellow]Already decided:[/yellow] {e.detail}")
        else:
            console.print(f"[red]Error:[/red] {e.detail}")
        raise click.Abort()


@reviews.command("cancel")
@click.argument("review_id")
def cancel_review(review_id: str) -> None:
    """Cancel a pending review.

    This removes the review without approval or rejection.

    Args:
        review_id: The review ID

    Examples:
        $ paracle reviews cancel abc123
    """
    client = get_client()

    if not client.is_available():
        console.print("[red]API not available.[/red] Start with: paracle serve")
        raise click.Abort()

    try:
        client.reviews_cancel(review_id)
        console.print(f"[yellow]Cancelled[/yellow] review {review_id}")

    except APIError as e:
        if e.status_code == 404:
            console.print(f"[red]Review not found:[/red] {review_id}")
        else:
            console.print(f"[red]Error:[/red] {e.detail}")
        raise click.Abort()


@reviews.command("stats")
@click.option("--json", "output_json", is_flag=True, help="Output as JSON")
def review_stats(output_json: bool) -> None:
    """Show review statistics.

    Displays counts by status and risk level.

    Examples:
        $ paracle reviews stats
        $ paracle reviews stats --json
    """
    client = get_client()

    if not client.is_available():
        console.print("[red]API not available.[/red] Start with: paracle serve")
        raise click.Abort()

    try:
        result = client.reviews_stats()

        if output_json:
            console.print_json(json.dumps(result))
            return

        console.print("\n[bold cyan]Review Statistics[/bold cyan]\n")

        # Status table
        table = Table(title="By Status", show_header=True, header_style="bold")
        table.add_column("Status", style="cyan")
        table.add_column("Count", justify="right")

        table.add_row("Pending", f"[yellow]{result.get('pending', 0)}[/yellow]")
        table.add_row("Approved", f"[green]{result.get('approved', 0)}[/green]")
        table.add_row("Rejected", f"[red]{result.get('rejected', 0)}[/red]")
        table.add_row("Timeout", f"[dim]{result.get('timeout', 0)}[/dim]")
        table.add_row("", "")
        table.add_row("[bold]Total[/bold]", f"[bold]{result.get('total', 0)}[/bold]")

        console.print(table)

        # Risk level table
        by_risk = result.get("by_risk_level", {})
        if by_risk:
            console.print()
            risk_table = Table(
                title="By Risk Level", show_header=True, header_style="bold"
            )
            risk_table.add_column("Risk Level", style="cyan")
            risk_table.add_column("Count", justify="right")

            risk_table.add_row("Low", f"[green]{by_risk.get('low', 0)}[/green]")
            risk_table.add_row("Medium", f"[yellow]{by_risk.get('medium', 0)}[/yellow]")
            risk_table.add_row("High", f"[red]{by_risk.get('high', 0)}[/red]")

            console.print(risk_table)

    except APIError as e:
        console.print(f"[red]Error:[/red] {e.detail}")
        raise click.Abort()
