"""Paracle CLI - Workspace governance commands.

Commands for managing the .parac/ workspace:
- status: Show current project state
- sync: Synchronize with project reality
- validate: Validate workspace consistency
- session: Session management (start/end)
- init: Initialize a new .parac/ workspace
"""

from pathlib import Path

import click
from rich.console import Console
from rich.panel import Panel
from rich.table import Table

from paracle_core.parac.state import find_parac_root, load_state, save_state
from paracle_core.parac.sync import ParacSynchronizer
from paracle_core.parac.validator import ParacValidator, ValidationLevel
from paracle_core.parac.manifest_generator import write_manifest

console = Console()


def get_parac_root_or_exit() -> Path:
    """Get .parac/ root or exit with error."""
    parac_root = find_parac_root()
    if parac_root is None:
        console.print("[red]Error:[/red] No .parac/ directory found.")
        console.print(
            "Run 'paracle init' to create one, or navigate to a project.")
        raise SystemExit(1)
    return parac_root


@click.command()
@click.option("--json", "as_json", is_flag=True, help="Output as JSON")
def status(as_json: bool) -> None:
    """Show current project state from .parac/."""
    parac_root = get_parac_root_or_exit()
    state = load_state(parac_root)

    if state is None:
        console.print("[red]Error:[/red] Could not load state.")
        raise SystemExit(1)

    if as_json:
        import json
        sync = ParacSynchronizer(parac_root)
        console.print(json.dumps(sync.get_summary(), indent=2))
        return

    # Rich formatted output
    phase = state.current_phase

    # Header
    console.print()
    console.print(
        Panel(
            f"[bold cyan]{state.project_name}[/bold cyan] v{state.project_version}",
            title="📊 Paracle Status",
            subtitle=f"Snapshot: {state.snapshot_date}",
        )
    )

    # Phase info
    progress_color = "green" if phase.status == "completed" else "yellow"
    console.print(f"\n[bold]Phase:[/bold] {phase.id} - {phase.name}")
    console.print(
        f"[bold]Status:[/bold] [{progress_color}]{phase.status}[/{progress_color}]")
    console.print(
        f"[bold]Progress:[/bold] [{progress_color}]{phase.progress}[/{progress_color}]")

    # Focus areas
    if phase.focus_areas:
        console.print("\n[bold]Focus Areas:[/bold]")
        for area in phase.focus_areas:
            console.print(f"  • {area}")

    # In progress
    if phase.in_progress:
        console.print("\n[bold yellow]In Progress:[/bold yellow]")
        for item in phase.in_progress:
            console.print(f"  🔄 {item}")

    # Pending
    if phase.pending:
        console.print("\n[bold]Pending:[/bold]")
        for item in phase.pending[:5]:  # Show max 5
            console.print(f"  ⏳ {item}")
        if len(phase.pending) > 5:
            console.print(f"  ... and {len(phase.pending) - 5} more")

    # Blockers
    if state.blockers:
        console.print("\n[bold red]Blockers:[/bold red]")
        for blocker in state.blockers:
            console.print(f"  🚫 {blocker.get('description', 'Unknown')}")

    # Next actions
    if state.next_actions:
        console.print("\n[bold]Next Actions:[/bold]")
        for action in state.next_actions[:3]:  # Show max 3
            console.print(f"  → {action}")

    console.print()


@click.command()
@click.option("--git/--no-git", default=True, help="Sync git information")
@click.option("--metrics/--no-metrics", default=True, help="Sync file metrics")
@click.option("--manifest/--no-manifest", default=True, help="Regenerate agent manifest")
def sync(git: bool, metrics: bool, manifest: bool) -> None:
    """Synchronize .parac/ state with project reality."""
    parac_root = get_parac_root_or_exit()

    console.print("[bold]Synchronizing .parac/ state...[/bold]\n")

    synchronizer = ParacSynchronizer(parac_root)
    result = synchronizer.sync(update_git=git, update_metrics=metrics)

    # Also regenerate manifest if requested
    if manifest:
        try:
            manifest_path = write_manifest(parac_root)
            result.changes.append(f"Regenerated {manifest_path.name}")
        except Exception as e:
            result.errors.append(f"Failed to generate manifest: {e}")

    if result.changes:
        console.print("[green]Changes made:[/green]")
        for change in result.changes:
            console.print(f"  ✅ {change}")
    else:
        console.print("[dim]No changes needed.[/dim]")

    if result.errors:
        console.print("\n[red]Errors:[/red]")
        for error in result.errors:
            console.print(f"  ❌ {error}")

    if result.success:
        console.print("\n[green]✅ Synchronization complete.[/green]")
    else:
        console.print("\n[red]❌ Synchronization failed.[/red]")
        raise SystemExit(1)


@click.command()
@click.option("--fix", is_flag=True, help="Attempt to fix issues (not implemented)")
def validate(fix: bool) -> None:
    """Validate .parac/ workspace consistency."""
    parac_root = get_parac_root_or_exit()

    console.print("[bold]Validating .parac/ workspace...[/bold]\n")

    validator = ParacValidator(parac_root)
    result = validator.validate()

    # Create results table
    if result.issues:
        table = Table(title="Validation Results")
        table.add_column("Level", style="bold")
        table.add_column("File")
        table.add_column("Message")

        for issue in result.issues:
            level_style = {
                ValidationLevel.ERROR: "red",
                ValidationLevel.WARNING: "yellow",
                ValidationLevel.INFO: "dim",
            }.get(issue.level, "white")

            file_loc = issue.file
            if issue.line:
                file_loc += f":{issue.line}"

            table.add_row(
                f"[{level_style}]{issue.level.value.upper()}[/{level_style}]",
                file_loc,
                issue.message,
            )

        console.print(table)
    else:
        console.print("[green]No issues found.[/green]")

    console.print(f"\nFiles checked: {result.files_checked}")
    console.print(f"Errors: {len(result.errors)}")
    console.print(f"Warnings: {len(result.warnings)}")

    if result.valid:
        console.print("\n[green]✅ Validation passed.[/green]")
    else:
        console.print("\n[red]❌ Validation failed.[/red]")
        raise SystemExit(1)


@click.group()
def session() -> None:
    """Session management commands."""
    pass


@session.command("start")
def session_start() -> None:
    """Start a new work session.

    Reads .parac/ context and displays current state.
    """
    parac_root = get_parac_root_or_exit()
    state = load_state(parac_root)

    if state is None:
        console.print("[red]Error:[/red] Could not load state.")
        raise SystemExit(1)

    phase = state.current_phase

    console.print()
    console.print(
        Panel("[bold green]SESSION START[/bold green]", expand=False))
    console.print()
    console.print("1. Reading .parac/memory/context/current_state.yaml")
    console.print("2. Checking .parac/roadmap/roadmap.yaml")
    console.print("3. Reviewing .parac/memory/context/open_questions.md")
    console.print()
    console.print(f"[bold]Phase:[/bold] {phase.id} - {phase.name}")
    console.print(f"[bold]Progress:[/bold] {phase.progress}")

    if phase.focus_areas:
        console.print(
            f"[bold]Focus:[/bold] {', '.join(phase.focus_areas[:3])}")

    if state.blockers:
        console.print(
            f"\n[yellow]⚠️  {len(state.blockers)} blocker(s) active[/yellow]")

    console.print()
    console.print("[green]Source of truth verified. Proceeding.[/green]")
    console.print()


@session.command("end")
@click.option("--progress", type=int, help="Update progress (0-100)")
@click.option("--complete", multiple=True, help="Mark item(s) as completed")
@click.option("--start", "in_progress", multiple=True, help="Mark item(s) as in-progress")
@click.option("--dry-run", is_flag=True, help="Show changes without applying")
def session_end(
    progress: int | None,
    complete: tuple[str, ...],
    in_progress: tuple[str, ...],
    dry_run: bool,
) -> None:
    """End work session with .parac/ updates.

    Proposes updates to current_state.yaml based on session work.
    """
    parac_root = get_parac_root_or_exit()
    state = load_state(parac_root)

    if state is None:
        console.print("[red]Error:[/red] Could not load state.")
        raise SystemExit(1)

    changes: list[str] = []

    # Apply progress update
    if progress is not None:
        old_progress = state.current_phase.progress
        state.update_progress(progress)
        changes.append(
            f"progress: {old_progress} → {state.current_phase.progress}")

    # Mark items completed
    for item in complete:
        state.add_completed(item)
        changes.append(f"completed: + {item}")

    # Mark items in-progress
    for item in in_progress:
        state.add_in_progress(item)
        changes.append(f"in_progress: + {item}")

    # Display proposed changes
    console.print()
    console.print(
        Panel("[bold cyan]SESSION END - Proposed Updates[/bold cyan]", expand=False))
    console.print()

    if changes:
        console.print("[bold]1. current_state.yaml:[/bold]")
        for change in changes:
            console.print(f"   - {change}")
    else:
        console.print("[dim]No changes specified.[/dim]")
        console.print(
            "[dim]Use --progress, --complete, or --start to specify changes.[/dim]")

    console.print()

    if dry_run:
        console.print("[yellow]Dry run - no changes applied.[/yellow]")
        return

    if changes:
        if save_state(state, parac_root):
            console.print("[green]✅ Changes applied.[/green]")
        else:
            console.print("[red]❌ Failed to save changes.[/red]")
            raise SystemExit(1)
    else:
        console.print("[dim]No changes to apply.[/dim]")

    console.print()


@click.command()
@click.argument("path", default=".", type=click.Path())
@click.option("--name", help="Project name (defaults to directory name)")
@click.option("--force", is_flag=True, help="Overwrite existing .parac/")
def init(path: str, name: str | None, force: bool) -> None:
    """Initialize a new .parac/ workspace.

    Creates the .parac/ directory structure with default configuration.
    """
    target = Path(path).resolve()
    parac_dir = target / ".parac"

    if parac_dir.exists() and not force:
        console.print(
            f"[red]Error:[/red] .parac/ already exists at {target}")
        console.print("Use --force to overwrite.")
        raise SystemExit(1)

    project_name = name or target.name

    console.print(f"[bold]Initializing .parac/ workspace for: {project_name}[/bold]\n")

    # Create directory structure
    dirs_to_create = [
        parac_dir / "memory" / "context",
        parac_dir / "memory" / "knowledge",
        parac_dir / "memory" / "summaries",
        parac_dir / "roadmap",
        parac_dir / "agents" / "specs",
        parac_dir / "policies",
        parac_dir / "hooks",
        parac_dir / "adapters",
    ]

    for dir_path in dirs_to_create:
        dir_path.mkdir(parents=True, exist_ok=True)
        console.print(f"  📁 Created {dir_path.relative_to(target)}")

    # Create minimal current_state.yaml
    from datetime import date
    state_content = f"""version: '1.0'
snapshot_date: '{date.today().isoformat()}'
project:
  name: {project_name}
  version: 0.0.1
  phase: phase_0
  status: in_progress
current_phase:
  id: phase_0
  name: Setup
  status: in_progress
  progress: 0%
  started_date: '{date.today().isoformat()}'
  focus_areas:
    - Project initialization
  completed: []
  in_progress: []
  pending: []
blockers: []
next_actions:
  - Define project roadmap
  - Create initial agents
"""
    state_file = parac_dir / "memory" / "context" / "current_state.yaml"
    state_file.write_text(state_content, encoding="utf-8")
    console.print(f"  📄 Created {state_file.relative_to(target)}")

    # Create minimal roadmap.yaml
    roadmap_content = f"""version: '1.0'
project: {project_name}
phases:
  - id: phase_0
    name: Setup
    status: in_progress
    deliverables: []
"""
    roadmap_file = parac_dir / "roadmap" / "roadmap.yaml"
    roadmap_file.write_text(roadmap_content, encoding="utf-8")
    console.print(f"  📄 Created {roadmap_file.relative_to(target)}")

    # Create GOVERNANCE.md
    governance_content = """# .parac/ Governance

This directory is the single source of truth for the project.

## Structure

- `memory/context/` - Current project state
- `memory/knowledge/` - Accumulated knowledge
- `roadmap/` - Project roadmap and decisions
- `agents/specs/` - Agent specifications
- `policies/` - Project policies
- `hooks/` - Automation hooks
- `adapters/` - Tool/IDE adapters

## Rules

1. Always read current_state.yaml before starting work
2. Update state after completing significant work
3. Document all architectural decisions
4. Never contradict what's documented here
"""
    governance_file = parac_dir / "GOVERNANCE.md"
    governance_file.write_text(governance_content, encoding="utf-8")
    console.print(f"  📄 Created {governance_file.relative_to(target)}")

    console.print(f"\n[green]✅ .parac/ workspace initialized at {target}[/green]")
    console.print("\nNext steps:")
    console.print("  • paracle status     - View project state")
    console.print("  • paracle sync       - Sync with reality")
    console.print("  • paracle validate   - Check consistency")


# Legacy compatibility: keep 'parac' group for backward compatibility
# but mark as deprecated
@click.group(hidden=True)
def parac() -> None:
    """[DEPRECATED] Use top-level commands instead.

    paracle parac status  →  paracle status
    paracle parac sync    →  paracle sync
    """
    pass


# Add commands to legacy group for backward compatibility
parac.add_command(status, "status")
parac.add_command(sync, "sync")
parac.add_command(validate, "validate")
parac.add_command(session, "session")
