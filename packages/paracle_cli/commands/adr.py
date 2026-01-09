"""Paracle CLI - ADR (Architecture Decision Records) commands.

Commands for managing ADRs:
- list: List all ADRs
- create: Create a new ADR
- get: View a specific ADR
- status: Update ADR status
- migrate: Migrate from legacy decisions.md
- search: Search ADRs by keyword

Architecture: CLI -> Core (direct access for local file operations)
"""

import sys
from datetime import date

import click
from rich.console import Console
from rich.panel import Panel
from rich.table import Table

from paracle_cli.utils import get_parac_root_or_exit

console = Console()


def get_adr_manager():
    """Get ADRManager instance."""
    from paracle_core.parac.adr_manager import ADRManager

    parac_root = get_parac_root_or_exit()
    return ADRManager(parac_root)


@click.group(invoke_without_command=True)
@click.option(
    "--list",
    "-l",
    "list_flag",
    is_flag=True,
    help="List all ADRs (shortcut for 'list')",
)
@click.pass_context
def adr(ctx: click.Context, list_flag: bool):
    """Manage Architecture Decision Records (ADRs).

    Examples:
        paracle adr -l              - List all ADRs (shortcut)
        paracle adr list            - List all ADRs
        paracle adr create "Title"  - Create new ADR
    """
    if list_flag:
        ctx.invoke(list_adrs, status=None, since=None, as_json=False)
    elif ctx.invoked_subcommand is None:
        click.echo(ctx.get_help())


# =============================================================================
# LIST Command
# =============================================================================


@adr.command("list")
@click.option(
    "--status", "-s", help="Filter by status (Proposed, Accepted, Deprecated)"
)
@click.option("--since", help="Filter by date (YYYY-MM-DD)")
@click.option("--json", "as_json", is_flag=True, help="Output as JSON")
def list_adrs(status: str | None, since: str | None, as_json: bool):
    """List all ADRs.

    Examples:
        paracle adr list                    # List all ADRs
        paracle adr list -s Accepted        # List accepted ADRs
        paracle adr list --since 2024-01-01 # ADRs since date
    """
    manager = get_adr_manager()

    # Parse since date
    since_date = None
    if since:
        try:
            since_date = date.fromisoformat(since)
        except ValueError:
            console.print(f"[red]Error:[/red] Invalid date format: {since}")
            console.print("Use YYYY-MM-DD format.")
            sys.exit(1)

    adrs = manager.list(status=status, since=since_date)

    if not adrs:
        console.print("[yellow]No ADRs found.[/yellow]")
        if status:
            console.print(f"[dim]Filter: status={status}[/dim]")
        return

    if as_json:
        import json

        data = [
            {
                "id": adr.id,
                "title": adr.title,
                "status": adr.status,
                "date": adr.date.isoformat(),
                "deciders": adr.deciders,
            }
            for adr in adrs
        ]
        console.print(json.dumps(data, indent=2))
        return

    # Rich table output
    table = Table(title="Architecture Decision Records")
    table.add_column("ID", style="cyan")
    table.add_column("Title")
    table.add_column("Status")
    table.add_column("Date", style="dim")
    table.add_column("Deciders")

    for adr_meta in adrs:
        status_style = {
            "Proposed": "yellow",
            "Accepted": "green",
            "Deprecated": "dim",
            "Superseded": "red",
        }.get(adr_meta.status, "white")

        table.add_row(
            adr_meta.id,
            adr_meta.title,
            f"[{status_style}]{adr_meta.status}[/{status_style}]",
            str(adr_meta.date),
            adr_meta.deciders,
        )

    console.print(table)

    # Show summary
    counts = manager.count_by_status()
    summary = ", ".join(f"{k}: {v}" for k, v in counts.items())
    console.print(f"\n[dim]Total: {len(adrs)} | {summary}[/dim]")


# =============================================================================
# GET Command
# =============================================================================


@adr.command("get")
@click.argument("adr_id")
@click.option("--json", "as_json", is_flag=True, help="Output as JSON")
def get_adr(adr_id: str, as_json: bool):
    """View a specific ADR.

    ADR_ID: The ADR identifier (e.g., ADR-001)

    Examples:
        paracle adr get ADR-001
        paracle adr get ADR-001 --json
    """
    manager = get_adr_manager()

    # Normalize ID
    if not adr_id.upper().startswith("ADR-"):
        adr_id = f"ADR-{adr_id.zfill(3)}"
    else:
        adr_id = adr_id.upper()

    adr_obj = manager.get(adr_id)

    if adr_obj is None:
        console.print(f"[red]Error:[/red] ADR '{adr_id}' not found.")
        sys.exit(1)

    if as_json:
        import json

        data = {
            "id": adr_obj.id,
            "title": adr_obj.title,
            "date": adr_obj.date.isoformat(),
            "status": adr_obj.status,
            "deciders": adr_obj.deciders,
            "context": adr_obj.context,
            "decision": adr_obj.decision,
            "consequences": adr_obj.consequences,
            "implementation": adr_obj.implementation,
            "related": adr_obj.related,
        }
        console.print(json.dumps(data, indent=2))
        return

    # Rich formatted output
    status_style = {
        "Proposed": "yellow",
        "Accepted": "green",
        "Deprecated": "dim",
        "Superseded": "red",
    }.get(adr_obj.status, "white")

    console.print()
    console.print(
        Panel(
            f"[bold]{adr_obj.id}: {adr_obj.title}[/bold]",
            subtitle=f"[{status_style}]{adr_obj.status}[/{status_style}] | {adr_obj.date}",
        )
    )

    console.print(f"\n[bold]Deciders:[/bold] {adr_obj.deciders}")

    if adr_obj.context:
        console.print("\n[bold cyan]Context[/bold cyan]")
        console.print(adr_obj.context)

    if adr_obj.decision:
        console.print("\n[bold green]Decision[/bold green]")
        console.print(adr_obj.decision)

    if adr_obj.consequences:
        console.print("\n[bold yellow]Consequences[/bold yellow]")
        console.print(adr_obj.consequences)

    if adr_obj.implementation and adr_obj.implementation != "TBD":
        console.print("\n[bold]Implementation[/bold]")
        console.print(adr_obj.implementation)

    if adr_obj.related and adr_obj.related != "None":
        console.print("\n[bold dim]Related Decisions[/bold dim]")
        console.print(adr_obj.related)

    if adr_obj.file_path:
        console.print(f"\n[dim]File: {adr_obj.file_path}[/dim]")

    console.print()


# =============================================================================
# CREATE Command
# =============================================================================


@adr.command("create")
@click.option("--title", "-t", required=True, help="ADR title")
@click.option("--context", "-c", help="Context/background")
@click.option("--decision", "-d", help="The decision made")
@click.option("--consequences", help="Consequences of the decision")
@click.option(
    "--status",
    "-s",
    default="Proposed",
    type=click.Choice(["Proposed", "Accepted", "Deprecated", "Superseded"]),
)
@click.option("--deciders", default="Core Team", help="Who made the decision")
@click.option("--interactive", "-i", is_flag=True, help="Interactive mode")
def create_adr(
    title: str,
    context: str | None,
    decision: str | None,
    consequences: str | None,
    status: str,
    deciders: str,
    interactive: bool,
):
    """Create a new ADR.

    Examples:
        paracle adr create -t "Use PostgreSQL for persistence"
        paracle adr create -t "API versioning" -i   # Interactive mode
        paracle adr create -t "Auth strategy" -c "Need auth" -d "Use OAuth2"
    """
    manager = get_adr_manager()

    if interactive:
        # Interactive prompts
        if not context:
            console.print("\n[bold]Context[/bold] (why was this decision needed?):")
            context = click.prompt("", default="", show_default=False)

        if not decision:
            console.print("\n[bold]Decision[/bold] (what was decided?):")
            decision = click.prompt("", default="", show_default=False)

        if not consequences:
            console.print("\n[bold]Consequences[/bold] (impact of the decision):")
            consequences = click.prompt("", default="", show_default=False)

    # Validate required fields
    if not context:
        context = "TBD"
    if not decision:
        decision = "TBD"
    if not consequences:
        consequences = "TBD"

    # Create ADR
    adr_id = manager.create(
        title=title,
        context=context,
        decision=decision,
        consequences=consequences,
        status=status,
        deciders=deciders,
    )

    console.print(f"\n[green]OK[/green] Created {adr_id}: {title}")
    console.print(f"[dim]File: {manager.adr_dir / f'{adr_id}.md'}[/dim]")

    if status == "Proposed":
        console.print(
            "\n[dim]Tip: Use 'paracle adr status {adr_id} Accepted' to approve.[/dim]"
        )


# =============================================================================
# STATUS Command
# =============================================================================


@adr.command("status")
@click.argument("adr_id")
@click.argument(
    "new_status",
    type=click.Choice(["Proposed", "Accepted", "Deprecated", "Superseded"]),
)
def update_status(adr_id: str, new_status: str):
    """Update ADR status.

    ADR_ID: The ADR identifier (e.g., ADR-001)
    NEW_STATUS: New status (Proposed, Accepted, Deprecated, Superseded)

    Examples:
        paracle adr status ADR-001 Accepted
        paracle adr status 1 Deprecated
    """
    manager = get_adr_manager()

    # Normalize ID
    if not adr_id.upper().startswith("ADR-"):
        adr_id = f"ADR-{adr_id.zfill(3)}"
    else:
        adr_id = adr_id.upper()

    # Get current status
    adr_obj = manager.get(adr_id)
    if adr_obj is None:
        console.print(f"[red]Error:[/red] ADR '{adr_id}' not found.")
        sys.exit(1)

    old_status = adr_obj.status

    if old_status == new_status:
        console.print(f"[yellow]ADR already has status: {new_status}[/yellow]")
        return

    # Update status
    if manager.update_status(adr_id, new_status):
        console.print(f"[green]OK[/green] {adr_id}: {old_status} -> {new_status}")
    else:
        console.print("[red]Error:[/red] Failed to update status.")
        sys.exit(1)


# =============================================================================
# MIGRATE Command
# =============================================================================


@adr.command("migrate")
@click.option("--dry-run", is_flag=True, help="Show what would be migrated")
def migrate_legacy(dry_run: bool):
    """Migrate from legacy decisions.md format.

    Parses the legacy single-file decisions.md and creates
    individual ADR files for each decision found.

    Examples:
        paracle adr migrate --dry-run   # Preview migration
        paracle adr migrate             # Perform migration
    """
    manager = get_adr_manager()

    # Check if legacy file exists
    if manager.legacy_file is None or not manager.legacy_file.exists():
        console.print("[yellow]No legacy decisions.md found.[/yellow]")
        console.print(f"[dim]Expected at: {manager.config.legacy_file}[/dim]")
        return

    console.print(f"[bold]Migrating from:[/bold] {manager.legacy_file}\n")

    if dry_run:
        # Read and parse to show what would be migrated
        import re

        content = manager.legacy_file.read_text(encoding="utf-8")
        pattern = r"## (ADR-\d+):\s*(.+?)(?=\n## ADR-|\Z)"
        matches = re.findall(pattern, content, re.DOTALL)

        if not matches:
            console.print("[yellow]No ADRs found in legacy file.[/yellow]")
            return

        console.print(f"[cyan]Found {len(matches)} ADR(s) to migrate:[/cyan]")
        for adr_id, _ in matches:
            # Check if already exists
            exists = (manager.adr_dir / f"{adr_id}.md").exists()
            status = (
                "[dim]exists, will skip[/dim]"
                if exists
                else "[green]will create[/green]"
            )
            console.print(f"  - {adr_id}: {status}")

        console.print("\n[yellow]Dry run - no changes made.[/yellow]")
        console.print("Run without --dry-run to perform migration.")
        return

    # Perform actual migration
    migrated = manager.migrate_legacy()

    if migrated > 0:
        console.print(f"[green]OK[/green] Migrated {migrated} ADR(s).")
        console.print(f"[dim]ADR directory: {manager.adr_dir}[/dim]")
    else:
        console.print("[yellow]No new ADRs migrated.[/yellow]")
        console.print("[dim]ADRs may already exist or none found in legacy file.[/dim]")


# =============================================================================
# SEARCH Command
# =============================================================================


@adr.command("search")
@click.argument("query")
@click.option("--json", "as_json", is_flag=True, help="Output as JSON")
def search_adrs(query: str, as_json: bool):
    """Search ADRs by keyword.

    QUERY: Search term (case-insensitive)

    Examples:
        paracle adr search database
        paracle adr search "api versioning"
    """
    manager = get_adr_manager()

    results = manager.search(query)

    if not results:
        console.print(f"[yellow]No ADRs found matching: {query}[/yellow]")
        return

    if as_json:
        import json

        data = [
            {
                "id": adr.id,
                "title": adr.title,
                "status": adr.status,
                "date": adr.date.isoformat(),
            }
            for adr in results
        ]
        console.print(json.dumps(data, indent=2))
        return

    # Rich table output
    table = Table(title=f"Search Results: '{query}'")
    table.add_column("ID", style="cyan")
    table.add_column("Title")
    table.add_column("Status")
    table.add_column("Date", style="dim")

    for adr_meta in results:
        status_style = {
            "Proposed": "yellow",
            "Accepted": "green",
            "Deprecated": "dim",
            "Superseded": "red",
        }.get(adr_meta.status, "white")

        table.add_row(
            adr_meta.id,
            adr_meta.title,
            f"[{status_style}]{adr_meta.status}[/{status_style}]",
            str(adr_meta.date),
        )

    console.print(table)
    console.print(f"\n[dim]Found {len(results)} matching ADR(s)[/dim]")


# =============================================================================
# STATS Command
# =============================================================================


@adr.command("stats")
def show_stats():
    """Show ADR statistics.

    Displays counts by status and recent activity.
    """
    manager = get_adr_manager()

    counts = manager.count_by_status()
    total = sum(counts.values())

    if total == 0:
        console.print("[yellow]No ADRs found.[/yellow]")
        console.print("Create your first ADR with: paracle adr create -t 'Title'")
        return

    console.print()
    console.print(Panel("[bold]ADR Statistics[/bold]", expand=False))

    # Status breakdown
    table = Table(show_header=False)
    table.add_column("Status")
    table.add_column("Count", justify="right")
    table.add_column("Bar")

    for status in ["Proposed", "Accepted", "Deprecated", "Superseded"]:
        count = counts.get(status, 0)
        if count > 0:
            bar_len = int((count / total) * 30)
            bar = "[" + "=" * bar_len + " " * (30 - bar_len) + "]"

            style = {
                "Proposed": "yellow",
                "Accepted": "green",
                "Deprecated": "dim",
                "Superseded": "red",
            }.get(status, "white")

            table.add_row(
                f"[{style}]{status}[/{style}]",
                str(count),
                f"[{style}]{bar}[/{style}]",
            )

    console.print(table)
    console.print(f"\n[bold]Total:[/bold] {total} ADR(s)")

    # Recent ADRs
    adrs = manager.list()
    if adrs:
        recent = sorted(adrs, key=lambda a: a.date, reverse=True)[:3]
        console.print("\n[bold]Recent:[/bold]")
        for adr_meta in recent:
            console.print(f"  - {adr_meta.id}: {adr_meta.title} ({adr_meta.date})")

    console.print()
