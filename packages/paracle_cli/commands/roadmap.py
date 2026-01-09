"""Paracle CLI - Roadmap management commands.

Commands for managing multiple roadmaps:
- list: List all configured roadmaps
- show: Show a specific roadmap
- add: Add a new roadmap
- validate: Validate roadmap files
- sync: Synchronize roadmaps with state
- stats: Show roadmap statistics

Architecture: CLI -> Core (direct access for local file operations)
"""

import sys

import click
from rich.console import Console
from rich.panel import Panel
from rich.table import Table
from rich.tree import Tree

from paracle_cli.utils import get_parac_root_or_exit

console = Console()


def get_roadmap_manager():
    """Get RoadmapManager instance."""
    from paracle_core.parac.roadmap_manager import RoadmapManager

    parac_root = get_parac_root_or_exit()
    return RoadmapManager(parac_root)


@click.group(invoke_without_command=True)
@click.option(
    "--list",
    "-l",
    "list_flag",
    is_flag=True,
    help="List all roadmaps (shortcut for 'list')",
)
@click.pass_context
def roadmap(ctx: click.Context, list_flag: bool):
    """Manage project roadmaps.

    Examples:
        paracle roadmap -l      - List all roadmaps (shortcut)
        paracle roadmap list    - List all roadmaps
        paracle roadmap show    - Show current roadmap
    """
    if list_flag:
        ctx.invoke(list_roadmaps, as_json=False)
    elif ctx.invoked_subcommand is None:
        click.echo(ctx.get_help())


# =============================================================================
# LIST Command
# =============================================================================


@roadmap.command("list")
@click.option("--json", "as_json", is_flag=True, help="Output as JSON")
def list_roadmaps(as_json: bool):
    """List all configured roadmaps.

    Examples:
        paracle roadmap list
        paracle roadmap list --json
    """
    manager = get_roadmap_manager()
    roadmaps = manager.list_roadmaps()

    if not roadmaps:
        console.print("[yellow]No roadmaps configured.[/yellow]")
        return

    if as_json:
        import json

        data = [
            {
                "name": r.name,
                "path": str(r.path),
                "description": r.description,
                "exists": r.exists,
                "phase_count": r.phase_count,
                "current_phase": r.current_phase,
            }
            for r in roadmaps
        ]
        console.print(json.dumps(data, indent=2))
        return

    # Rich table output
    table = Table(title="Configured Roadmaps")
    table.add_column("Name", style="cyan")
    table.add_column("Description")
    table.add_column("Phases", justify="right")
    table.add_column("Current", style="green")
    table.add_column("Status")

    for r in roadmaps:
        if r.exists:
            status = "[green]OK[/green]"
        else:
            status = "[red]Missing[/red]"

        table.add_row(
            r.name,
            r.description,
            str(r.phase_count) if r.exists else "-",
            r.current_phase or "-",
            status,
        )

    console.print(table)


# =============================================================================
# SHOW Command
# =============================================================================


@roadmap.command("show")
@click.argument("name", default="primary")
@click.option("--json", "as_json", is_flag=True, help="Output as JSON")
def show_roadmap(name: str, as_json: bool):
    """Show a specific roadmap.

    NAME: Roadmap name (default: primary)

    Examples:
        paracle roadmap show
        paracle roadmap show primary
        paracle roadmap show tech-debt
    """
    manager = get_roadmap_manager()
    roadmap_obj = manager.get_roadmap(name)

    if roadmap_obj is None:
        console.print(f"[red]Error:[/red] Roadmap '{name}' not found.")
        available = [r.name for r in manager.list_roadmaps()]
        console.print(f"[dim]Available: {', '.join(available)}[/dim]")
        sys.exit(1)

    if as_json:
        import json

        data = {
            "name": roadmap_obj.name,
            "path": str(roadmap_obj.path),
            "description": roadmap_obj.description,
            "version": roadmap_obj.version,
            "phases": [
                {
                    "id": p.id,
                    "name": p.name,
                    "status": p.status,
                    "progress": p.progress,
                    "start_date": p.start_date.isoformat() if p.start_date else None,
                    "end_date": p.end_date.isoformat() if p.end_date else None,
                }
                for p in roadmap_obj.phases
            ],
        }
        console.print(json.dumps(data, indent=2))
        return

    # Rich formatted output
    console.print()
    console.print(
        Panel(
            f"[bold]{roadmap_obj.name}[/bold] Roadmap",
            subtitle=f"v{roadmap_obj.version}",
        )
    )

    if roadmap_obj.description:
        console.print(f"\n{roadmap_obj.description}")

    # Phases tree
    console.print("\n[bold]Phases:[/bold]")

    tree = Tree(f"[cyan]{roadmap_obj.name}[/cyan]")

    for phase in roadmap_obj.phases:
        status_style = {
            "pending": "dim",
            "in_progress": "yellow",
            "completed": "green",
            "blocked": "red",
        }.get(phase.status, "white")

        # Progress bar
        progress_filled = int(phase.progress / 100 * 10)
        progress_bar = "[" + "=" * progress_filled + "-" * (10 - progress_filled) + "]"

        phase_label = (
            f"[{status_style}]{phase.id}[/{status_style}]: {phase.name} "
            f"[dim]{progress_bar} {phase.progress:.0f}%[/dim]"
        )

        branch = tree.add(phase_label)

        # Add deliverables if any
        if phase.deliverables:
            for d in phase.deliverables[:3]:  # Show max 3
                d_name = d.get("name", str(d)) if isinstance(d, dict) else str(d)
                d_status = (
                    d.get("status", "pending") if isinstance(d, dict) else "pending"
                )
                d_style = "green" if d_status == "completed" else "dim"
                branch.add(f"[{d_style}]- {d_name}[/{d_style}]")
            if len(phase.deliverables) > 3:
                branch.add(f"[dim]... and {len(phase.deliverables) - 3} more[/dim]")

    console.print(tree)

    # Current phase highlight
    current = manager.get_current_phase(name)
    if current:
        console.print(f"\n[bold]Current:[/bold] {current.id} - {current.name}")
        console.print(f"[bold]Progress:[/bold] {current.progress:.0f}%")

    console.print(f"\n[dim]File: {roadmap_obj.path}[/dim]")
    console.print()


# =============================================================================
# ADD Command
# =============================================================================


@roadmap.command("add")
@click.argument("name")
@click.argument("path")
@click.option("--description", "-d", default="", help="Roadmap description")
@click.option("--no-create", is_flag=True, help="Don't create the file")
def add_roadmap(name: str, path: str, description: str, no_create: bool):
    """Add a new roadmap.

    NAME: Unique name for the roadmap
    PATH: Relative path within roadmap directory

    Examples:
        paracle roadmap add tech-debt tech-debt-roadmap.yaml -d "Technical debt"
        paracle roadmap add research research/r-and-d.yaml
    """
    manager = get_roadmap_manager()

    # Check if name already exists
    existing = [r.name for r in manager.list_roadmaps()]
    if name in existing:
        console.print(f"[red]Error:[/red] Roadmap '{name}' already exists.")
        sys.exit(1)

    # Add roadmap
    if manager.add_roadmap(name, path, description, create_file=not no_create):
        console.print(f"[green]OK[/green] Added roadmap: {name}")
        full_path = manager.roadmap_dir / path
        console.print(f"[dim]Path: {full_path}[/dim]")

        if not no_create:
            console.print("[dim]Created template file.[/dim]")

        console.print(
            "\n[yellow]Note:[/yellow] To persist this addition, update project.yaml:"
        )
        console.print(
            f"""
  file_management:
    roadmap:
      additional:
        - name: {name}
          path: {path}
          description: "{description or name}"
"""
        )
    else:
        console.print("[red]Error:[/red] Failed to add roadmap.")
        sys.exit(1)


# =============================================================================
# VALIDATE Command
# =============================================================================


@roadmap.command("validate")
@click.argument("name", required=False)
@click.option("--json", "as_json", is_flag=True, help="Output as JSON")
def validate_roadmaps(name: str | None, as_json: bool):
    """Validate roadmap files.

    NAME: Specific roadmap to validate (optional)

    Examples:
        paracle roadmap validate           # Validate all
        paracle roadmap validate primary   # Validate specific
    """
    manager = get_roadmap_manager()
    results = manager.validate(name)

    if as_json:
        import json

        data = [
            {
                "roadmap": r.roadmap_name,
                "valid": r.is_valid,
                "errors": r.errors,
                "warnings": r.warnings,
            }
            for r in results
        ]
        console.print(json.dumps(data, indent=2))
        return

    all_valid = True

    for result in results:
        if result.is_valid:
            console.print(f"[green]OK[/green] {result.roadmap_name}")
        else:
            console.print(f"[red]FAIL[/red] {result.roadmap_name}")
            all_valid = False

        for error in result.errors:
            console.print(f"  [red]ERROR:[/red] {error}")

        for warning in result.warnings:
            console.print(f"  [yellow]WARN:[/yellow] {warning}")

    console.print()
    if all_valid:
        console.print("[green]All roadmaps valid.[/green]")
    else:
        console.print("[red]Validation failed.[/red]")
        sys.exit(1)


# =============================================================================
# SYNC Command
# =============================================================================


@roadmap.command("sync")
@click.option("--dry-run", is_flag=True, help="Show what would change")
def sync_roadmaps(dry_run: bool):
    """Synchronize roadmaps with current state.

    Updates current_state.yaml based on roadmap changes.

    Examples:
        paracle roadmap sync --dry-run
        paracle roadmap sync
    """
    manager = get_roadmap_manager()

    console.print("[bold]Synchronizing roadmaps with state...[/bold]\n")

    # Validate first
    results = manager.validate()
    for result in results:
        if not result.is_valid:
            console.print(
                f"[red]Error:[/red] {result.roadmap_name} has validation errors."
            )
            for error in result.errors:
                console.print(f"  - {error}")
            console.print("\nFix validation errors before syncing.")
            sys.exit(1)

    if dry_run:
        # Just show what would change
        console.print("[yellow]Dry run - no changes made.[/yellow]")
        console.print("\nWould sync the following:")

        for roadmap_meta in manager.list_roadmaps():
            if roadmap_meta.exists:
                current = manager.get_current_phase(roadmap_meta.name)
                if current:
                    console.print(
                        f"  - {roadmap_meta.name}: {current.id} ({current.progress:.0f}%)"
                    )
        return

    # Perform sync
    result = manager.sync_with_state()

    if result.changes:
        console.print("[green]Changes made:[/green]")
        for change in result.changes:
            console.print(f"  [green]OK[/green] {change}")
    else:
        console.print("[dim]No changes needed.[/dim]")

    if result.errors:
        console.print("\n[red]Errors:[/red]")
        for error in result.errors:
            console.print(f"  [red]FAIL[/red] {error}")
        sys.exit(1)

    if result.synced_roadmaps:
        console.print(
            f"\n[green]OK[/green] Synced: {', '.join(result.synced_roadmaps)}"
        )


# =============================================================================
# STATS Command
# =============================================================================


@roadmap.command("stats")
def show_stats():
    """Show roadmap statistics.

    Displays phase counts and progress across all roadmaps.
    """
    manager = get_roadmap_manager()
    stats = manager.get_stats()

    if stats["total_roadmaps"] == 0:
        console.print("[yellow]No roadmaps configured.[/yellow]")
        return

    console.print()
    console.print(Panel("[bold]Roadmap Statistics[/bold]", expand=False))

    # Overview
    console.print(f"\n[bold]Roadmaps:[/bold] {stats['total_roadmaps']}")
    console.print(f"[bold]Total Phases:[/bold] {stats['total_phases']}")
    console.print(f"[bold]Average Progress:[/bold] {stats['average_progress']:.1f}%")

    # Phases by status
    console.print("\n[bold]Phases by Status:[/bold]")
    table = Table(show_header=False)
    table.add_column("Status")
    table.add_column("Count", justify="right")

    status_styles = {
        "pending": "dim",
        "in_progress": "yellow",
        "completed": "green",
        "blocked": "red",
    }

    for status, count in stats["phases_by_status"].items():
        style = status_styles.get(status, "white")
        table.add_row(f"[{style}]{status}[/{style}]", str(count))

    console.print(table)

    # Per-roadmap breakdown
    console.print("\n[bold]Per Roadmap:[/bold]")
    for name, roadmap_stats in stats["roadmaps"].items():
        current = roadmap_stats.get("current_phase", "-")
        progress = roadmap_stats.get("progress", 0)
        phases = roadmap_stats.get("phases", 0)

        console.print(
            f"  [cyan]{name}[/cyan]: {phases} phases, "
            f"current: {current}, progress: {progress:.0f}%"
        )

    console.print()


# =============================================================================
# PHASE Command
# =============================================================================


@roadmap.command("phase")
@click.argument("action", type=click.Choice(["next", "complete", "block"]))
@click.option("--roadmap", "-r", default="primary", help="Roadmap name")
def manage_phase(action: str, roadmap_name: str):
    """Manage roadmap phases.

    ACTION: Phase action (next, complete, block)

    Examples:
        paracle roadmap phase next         # Show next pending phase
        paracle roadmap phase complete     # Mark current as completed
        paracle roadmap phase block        # Mark current as blocked
    """
    manager = get_roadmap_manager()

    current = manager.get_current_phase(roadmap_name)

    if action == "next":
        next_phase = manager.get_next_phase(roadmap_name)
        if next_phase:
            console.print(
                f"[bold]Next phase:[/bold] {next_phase.id} - {next_phase.name}"
            )
        else:
            console.print("[dim]No pending phases.[/dim]")
        return

    if current is None:
        console.print("[yellow]No current phase in progress.[/yellow]")
        return

    if action == "complete":
        if manager.update_phase_status(roadmap_name, current.id, "completed"):
            console.print(f"[green]OK[/green] Marked {current.id} as completed.")

            # Start next phase if available
            next_phase = manager.get_next_phase(roadmap_name)
            if next_phase:
                if click.confirm(f"Start next phase ({next_phase.id})?"):
                    manager.update_phase_status(
                        roadmap_name, next_phase.id, "in_progress"
                    )
                    console.print(f"[green]OK[/green] Started {next_phase.id}.")
        else:
            console.print("[red]Error:[/red] Failed to update status.")
            sys.exit(1)

    elif action == "block":
        if manager.update_phase_status(roadmap_name, current.id, "blocked"):
            console.print(f"[yellow]OK[/yellow] Marked {current.id} as blocked.")
        else:
            console.print("[red]Error:[/red] Failed to update status.")
            sys.exit(1)
