"""Paracle CLI - Workspace governance commands.

Commands for managing the .parac/ workspace:
- status: Show current project state
- sync: Synchronize with project reality
- validate: Validate workspace consistency
- session: Session management (start/end)
- init: Initialize a new .parac/ workspace

Architecture: CLI -> API -> Core (API-first design)
Falls back to direct core access if API is unavailable.
"""

import os
from pathlib import Path

import click
from paracle_core.parac.state import load_state, save_state
from rich.console import Console
from rich.panel import Panel
from rich.table import Table

from paracle_cli.api_client import APIClient, APIError, get_client
from paracle_cli.utils import get_parac_root_or_exit

console = Console()


def get_api_client() -> APIClient | None:
    """Get API client if API is available.

    Returns:
        APIClient if API responds, None otherwise
    """
    client = get_client()
    if client.is_available():
        return client
    return None


def use_api_or_fallback(api_func, fallback_func, *args, **kwargs):
    """Try API first, fall back to direct core access.

    Args:
        api_func: Function to call via API
        fallback_func: Function to call directly if API unavailable
        *args, **kwargs: Arguments to pass

    Returns:
        Result from either function
    """
    client = get_api_client()
    if client:
        try:
            return api_func(client, *args, **kwargs)
        except APIError as e:
            if e.status_code == 404:
                # .parac/ not found - let fallback handle gracefully
                pass
            else:
                console.print(f"[yellow]API error:[/yellow] {e.detail}")
                console.print("[dim]Falling back to direct access...[/dim]")
        except Exception as e:  # noqa: BLE001 - API fallback
            console.print(f"[yellow]API unavailable:[/yellow] {e}")
            console.print("[dim]Falling back to direct access...[/dim]")

    return fallback_func(*args, **kwargs)


# =============================================================================
# STATUS Command
# =============================================================================


def _status_via_api(client: APIClient, as_json: bool) -> None:
    """Get status via API."""
    result = client.parac_status()

    if as_json:
        import json

        console.print(json.dumps(result, indent=2))
        return

    # Rich formatted output
    phase = result["phase"]
    git = result["git"]

    # Header
    console.print()
    console.print(
        Panel(
            "[bold cyan]Project[/bold cyan]",
            title="Paracle Status",
            subtitle=f"Snapshot: {result['snapshot_date']}",
        )
    )

    # Phase info
    progress_color = "green" if phase["status"] == "completed" else "yellow"
    console.print(f"\n[bold]Phase:[/bold] {phase['id']} - {phase['name']}")
    console.print(
        f"[bold]Status:[/bold] "
        f"[{progress_color}]{phase['status']}[/{progress_color}]"
    )
    console.print(
        f"[bold]Progress:[/bold] "
        f"[{progress_color}]{phase['progress']}[/{progress_color}]"
    )

    # Git info
    console.print(f"\n[bold]Branch:[/bold] {git['branch']}")
    console.print(f"[bold]Last commit:[/bold] {git['last_commit'][:50]}...")
    if git["has_changes"]:
        console.print("[yellow]Has uncommitted changes[/yellow]")

    # Blockers and actions
    if result["blockers"] > 0:
        console.print(f"\n[bold red]Blockers:[/bold red] {result['blockers']}")
    if result["next_actions"] > 0:
        console.print(f"[bold]Next actions:[/bold] {result['next_actions']}")

    console.print()


def _status_direct(as_json: bool) -> None:
    """Get status via direct core access."""
    parac_root = get_parac_root_or_exit()
    state = load_state(parac_root)

    if state is None:
        console.print("[red]Error:[/red] Could not load state.")
        raise SystemExit(1)

    if as_json:
        import json

        from paracle_core.parac.sync import ParacSynchronizer

        synchronizer = ParacSynchronizer(parac_root)
        console.print(json.dumps(synchronizer.get_summary(), indent=2))
        return

    # Rich formatted output
    phase = state.current_phase

    # Header
    console.print()
    console.print(
        Panel(
            (
                f"[bold cyan]{state.project_name}[/bold cyan] "
                f"v{state.project_version}"
            ),
            title="Paracle Status",
            subtitle=f"Snapshot: {state.snapshot_date}",
        )
    )

    # Phase info
    progress_color = "green" if phase.status == "completed" else "yellow"
    console.print(f"\n[bold]Phase:[/bold] {phase.id} - {phase.name}")
    console.print(
        f"[bold]Status:[/bold] " f"[{progress_color}]{phase.status}[/{progress_color}]"
    )
    console.print(
        f"[bold]Progress:[/bold] "
        f"[{progress_color}]{phase.progress}[/{progress_color}]"
    )

    # Focus areas
    if phase.focus_areas:
        console.print("\n[bold]Focus Areas:[/bold]")
        for area in phase.focus_areas:
            console.print(f"  - {area}")

    # In progress
    if phase.in_progress:
        console.print("\n[bold yellow]In Progress:[/bold yellow]")
        for item in phase.in_progress:
            console.print(f"  -> {item}")

    # Pending
    if phase.pending:
        console.print("\n[bold]Pending:[/bold]")
        for item in phase.pending[:5]:  # Show max 5
            console.print(f"  - {item}")
        if len(phase.pending) > 5:
            console.print(f"  ... and {len(phase.pending) - 5} more")

    # Blockers
    if state.blockers:
        console.print("\n[bold red]Blockers:[/bold red]")
        for blocker in state.blockers:
            console.print(f"  ! {blocker.get('description', 'Unknown')}")

    # Next actions
    if state.next_actions:
        console.print("\n[bold]Next Actions:[/bold]")
        for action in state.next_actions[:3]:  # Show max 3
            console.print(f"  -> {action}")

    console.print()


@click.command()
@click.option("--json", "as_json", is_flag=True, help="Output as JSON")
def status(as_json: bool) -> None:
    """Show current project state from .parac/."""
    use_api_or_fallback(_status_via_api, _status_direct, as_json)


# =============================================================================
# SYNC Command
# =============================================================================


def _sync_via_api(
    client: APIClient,
    git: bool,
    metrics: bool,
    _manifest: bool,
) -> None:
    """Sync via API."""
    console.print("[bold]Synchronizing .parac/ state...[/bold]\n")

    result = client.parac_sync(update_git=git, update_metrics=metrics)

    if result.get("changes"):
        console.print("[green]Changes made:[/green]")
        for change in result["changes"]:
            desc = change.get("description", str(change))
            console.print(f"  [green]OK[/green] {desc}")
    else:
        console.print("[dim]No changes needed.[/dim]")

    if result.get("errors"):
        console.print("\n[red]Errors:[/red]")
        for error in result["errors"]:
            console.print(f"  [red]FAIL[/red] {error}")

    if result["success"]:
        console.print("\n[green]OK[/green] Synchronization complete.")
    else:
        console.print("\n[red]FAIL[/red] Synchronization failed.")
        raise SystemExit(1)


def _sync_direct(
    git: bool,
    metrics: bool,
    manifest: bool,
    roadmap: bool,
    auto_fix: bool,
) -> None:
    """Sync via direct core access."""
    parac_root = get_parac_root_or_exit()

    console.print("[bold]Synchronizing .parac/ state...[/bold]\n")

    from paracle_core.parac.manifest_generator import write_manifest
    from paracle_core.parac.roadmap_sync import sync_roadmap_and_state
    from paracle_core.parac.sync import ParacSynchronizer

    synchronizer = ParacSynchronizer(parac_root)
    result = synchronizer.sync(update_git=git, update_metrics=metrics)

    # Check roadmap alignment if requested
    if roadmap:
        roadmap_result = sync_roadmap_and_state(
            parac_root, dry_run=not auto_fix, auto_fix=auto_fix
        )
        result.changes.extend(roadmap_result.changes)

        # Display warnings and suggestions
        if roadmap_result.warnings:
            console.print("\n[yellow]Roadmap Alignment Warnings:[/yellow]")
            for warning in roadmap_result.warnings:
                console.print(f"  [yellow]⚠[/yellow]  {warning}")

        if roadmap_result.suggestions:
            console.print("\n[cyan]Suggestions:[/cyan]")
            for suggestion in roadmap_result.suggestions:
                console.print(f"  [cyan]Help:[/cyan] {suggestion}")

        if roadmap_result.errors:
            result.errors.extend(roadmap_result.errors)

    # Also regenerate manifest if requested
    if manifest:
        try:
            manifest_path = write_manifest(parac_root)
            result.changes.append(f"Regenerated {manifest_path.name}")
        except Exception as e:  # noqa: BLE001
            result.errors.append(f"Failed to generate manifest: {e}")

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

    if result.success:
        console.print("\n[green]OK[/green] Synchronization complete.")
    else:
        console.print("\n[red]FAIL[/red] Synchronization failed.")
        raise SystemExit(1)


@click.command()
@click.option("--git/--no-git", default=True, help="Sync git information")
@click.option("--metrics/--no-metrics", default=True, help="Sync file metrics")
@click.option(
    "--manifest/--no-manifest", default=True, help="Regenerate agent manifest"
)
@click.option("--roadmap/--no-roadmap", default=True, help="Check roadmap alignment")
@click.option("--auto-fix", is_flag=True, help="Automatically fix safe mismatches")
def sync(
    git: bool, metrics: bool, manifest: bool, roadmap: bool, auto_fix: bool
) -> None:
    """Synchronize .parac/ state with project reality and roadmap."""
    use_api_or_fallback(
        _sync_via_api, _sync_direct, git, metrics, manifest, roadmap, auto_fix
    )


# =============================================================================
# VALIDATE Command
# =============================================================================


def _validate_via_api(client: APIClient, _fix: bool) -> None:
    """Validate via API."""
    console.print("[bold]Validating .parac/ workspace...[/bold]\n")

    result = client.parac_validate()

    # Create results table
    if result.get("issues"):
        table = Table(title="Validation Results")
        table.add_column("Level", style="bold")
        table.add_column("File")
        table.add_column("Message")

        for issue in result["issues"]:
            level_style = {
                "error": "red",
                "warning": "yellow",
                "info": "dim",
            }.get(issue["level"], "white")

            file_loc = issue["file"]
            if issue.get("line"):
                file_loc += f":{issue['line']}"

            table.add_row(
                f"[{level_style}]{issue['level'].upper()}[/{level_style}]",
                file_loc,
                issue["message"],
            )

        console.print(table)
    else:
        console.print("[green]No issues found.[/green]")

    console.print(f"\nFiles checked: {result['files_checked']}")
    console.print(f"Errors: {result['errors']}")
    console.print(f"Warnings: {result['warnings']}")

    if result["valid"]:
        console.print("\n[green]OK[/green] Validation passed.")
    else:
        console.print("\n[red]FAIL[/red] Validation failed.")
        raise SystemExit(1)


def _validate_direct(_fix: bool) -> None:
    """Validate via direct core access."""
    parac_root = get_parac_root_or_exit()

    console.print("[bold]Validating .parac/ workspace...[/bold]\n")

    from paracle_core.parac.validator import ParacValidator, ValidationLevel

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
        console.print("\n[green]OK[/green] Validation passed.")
    else:
        console.print("\n[red]FAIL[/red] Validation failed.")
        raise SystemExit(1)


@click.command()
@click.option("--fix", is_flag=True, help="Attempt to fix issues (not implemented)")
def validate(fix: bool) -> None:
    """Validate .parac/ workspace consistency."""
    use_api_or_fallback(_validate_via_api, _validate_direct, fix)


# =============================================================================
# SESSION Commands
# =============================================================================


@click.group()
def session() -> None:
    """Session management commands."""
    ...


def _session_start_via_api(client: APIClient) -> None:
    """Start session via API."""
    result = client.parac_session_start()

    phase = result["phase"]

    console.print()
    console.print(Panel("[bold green]SESSION START[/bold green]", expand=False))
    console.print()
    console.print("1. Reading .parac/memory/context/current_state.yaml")
    console.print("2. Checking .parac/roadmap/roadmap.yaml")
    console.print("3. Reviewing .parac/memory/context/open_questions.md")
    console.print()
    console.print(f"[bold]Phase:[/bold] {phase['id']} - {phase['name']}")
    console.print(f"[bold]Progress:[/bold] {phase['progress']}")

    if result.get("focus_areas"):
        console.print(f"[bold]Focus:[/bold] {', '.join(result['focus_areas'][:3])}")

    if result["blockers"] > 0:
        console.print(
            f"\n[yellow]Warning: {result['blockers']} " f"blocker(s) active[/yellow]"
        )

    console.print()
    console.print(f"[green]{result['message']}[/green]")
    console.print()


def _session_start_direct() -> None:
    """Start session via direct core access."""
    parac_root = get_parac_root_or_exit()
    state = load_state(parac_root)

    if state is None:
        console.print("[red]Error:[/red] Could not load state.")
        raise SystemExit(1)

    phase = state.current_phase

    console.print()
    console.print(Panel("[bold green]SESSION START[/bold green]", expand=False))
    console.print()
    console.print("1. Reading .parac/memory/context/current_state.yaml")
    console.print("2. Checking .parac/roadmap/roadmap.yaml")
    console.print("3. Reviewing .parac/memory/context/open_questions.md")
    console.print()
    console.print(f"[bold]Phase:[/bold] {phase.id} - {phase.name}")
    console.print(f"[bold]Progress:[/bold] {phase.progress}")

    if phase.focus_areas:
        console.print(f"[bold]Focus:[/bold] {', '.join(phase.focus_areas[:3])}")

    if state.blockers:
        console.print(
            f"\n[yellow]Warning: {len(state.blockers)} " f"blocker(s) active[/yellow]"
        )

    console.print()
    console.print("[green]Source of truth verified. Proceeding.[/green]")
    console.print()


@session.command("start")
def session_start() -> None:
    """Start a new work session.

    Reads .parac/ context and displays current state.
    """
    use_api_or_fallback(_session_start_via_api, _session_start_direct)


def _session_end_via_api(
    client: APIClient,
    progress: int | None,
    complete: tuple[str, ...],
    in_progress: tuple[str, ...],
    dry_run: bool,
) -> None:
    """End session via API."""
    result = client.parac_session_end(
        progress=progress,
        completed=list(complete),
        in_progress=list(in_progress),
        dry_run=dry_run,
    )

    # Display proposed changes
    console.print()
    console.print(
        Panel("[bold cyan]SESSION END - Proposed Updates[/bold cyan]", expand=False)
    )
    console.print()

    if result.get("changes"):
        console.print("[bold]Changes:[/bold]")
        for change in result["changes"]:
            field = change.get("field", "")
            desc = change.get("change", str(change))
            console.print(f"   - {field}: {desc}")
    else:
        console.print("[dim]No changes specified.[/dim]")

    console.print()

    if dry_run:
        console.print("[yellow]Dry run - no changes applied.[/yellow]")
    elif result["applied"]:
        console.print(f"[green]OK[/green] {result['message']}")
    else:
        console.print(f"[dim]{result['message']}[/dim]")

    console.print()


def _session_end_direct(
    progress: int | None,
    complete: tuple[str, ...],
    in_progress: tuple[str, ...],
    dry_run: bool,
) -> None:
    """End session via direct core access."""
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
        changes.append(f"progress: {old_progress} -> {state.current_phase.progress}")

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
        Panel("[bold cyan]SESSION END - Proposed Updates[/bold cyan]", expand=False)
    )
    console.print()

    if changes:
        console.print("[bold]1. current_state.yaml:[/bold]")
        for change in changes:
            console.print(f"   - {change}")
    else:
        console.print("[dim]No changes specified.[/dim]")
        console.print(
            "[dim]Use --progress, --complete, or --start to " "specify changes.[/dim]"
        )

    console.print()

    if dry_run:
        console.print("[yellow]Dry run - no changes applied.[/yellow]")
        return

    if changes:
        if save_state(state, parac_root):
            console.print("[green]OK[/green] Changes applied.")
        else:
            console.print("[red]FAIL[/red] Failed to save changes.")
            raise SystemExit(1)
    else:
        console.print("[dim]No changes to apply.[/dim]")

    console.print()


@session.command("end")
@click.option("--progress", type=int, help="Update progress (0-100)")
@click.option("--complete", multiple=True, help="Mark item(s) as completed")
@click.option(
    "--start", "in_progress", multiple=True, help="Mark item(s) as in-progress"
)
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
    use_api_or_fallback(
        _session_end_via_api,
        _session_end_direct,
        progress,
        complete,
        in_progress,
        dry_run,
    )


# =============================================================================
# INIT Command
# =============================================================================


def _load_template_from_directory(
    template_name: str, parac_dir: Path, project_name: str
) -> bool:
    """Load template from content/templates/ directory.

    Args:
        template_name: Template to load (lite, standard, advanced)
        parac_dir: Target .parac/ directory
        project_name: Project name for substitution

    Returns:
        True if template was loaded successfully, False otherwise
    """
    import shutil
    from datetime import date

    # Find templates directory (relative to this file)
    # __file__ is packages/paracle_cli/commands/parac.py
    # parent = commands/,
    # parent.parent = paracle_cli/,
    # parent.parent.parent = packages/
    cli_dir = Path(__file__).parent.parent.parent  # packages/paracle_cli
    repo_root = cli_dir.parent  # repo root (packages -> root)
    templates_root = repo_root / "templates"

    # Map template names to directories
    template_map = {
        "lite": ".parac-template-lite",
        "standard": ".parac-template",
        "advanced": ".parac-template-advanced",
    }

    if template_name not in template_map:
        return False

    template_dir = templates_root / template_map[template_name]

    # Fallback if template doesn't exist yet
    if not template_dir.exists():
        console.print(f"[yellow]Template directory not found:[/yellow] {template_dir}")
        console.print("[dim]Falling back to programmatic creation...[/dim]")
        return False

    # Copy template directory
    try:
        shutil.copytree(template_dir, parac_dir, dirs_exist_ok=True)

        # Post-process files: substitute project name and dates
        for root, _, files in os.walk(parac_dir):
            for file in files:
                if file.endswith((".yaml", ".yml", ".md")):
                    filepath = Path(root) / file
                    try:
                        content = filepath.read_text(encoding="utf-8")
                        # Simple substitutions
                        content = content.replace("{{PROJECT_NAME}}", project_name)
                        content = content.replace("{{DATE}}", date.today().isoformat())
                        content = content.replace("my-project", project_name)
                        filepath.write_text(content, encoding="utf-8")
                    except Exception:  # noqa: BLE001
                        pass  # Skip files that can't be processed

        console.print(f"[dim]Loaded template:[/dim] {template_name}")
        return True

    except Exception as e:  # noqa: BLE001
        console.print(f"[yellow]Template loading failed:[/yellow] {e}")
        return False


def _interactive_init() -> tuple[str, str | None, str | None]:
    """
    Interactive prompts for workspace initialization.

    Returns:
        tuple[str, str | None, str | None]: (template, project_name, provider)
    """
    console.print("\n[bold cyan]Paracle Workspace Initialization[/bold cyan]\n")

    # Template selection
    console.print("[bold]Select a template:[/bold]")
    console.print("  [cyan]1[/cyan] - lite      (Learning & prototyping)")
    console.print("  [cyan]2[/cyan] - standard  (Production projects)")
    console.print("  [cyan]3[/cyan] - advanced  (Enterprise & complex)")

    template_choice = click.prompt(
        "\nTemplate",
        type=click.Choice(["1", "2", "3"], case_sensitive=False),
        default="2",
    )

    template_map = {"1": "lite", "2": "standard", "3": "advanced"}
    template = template_map[template_choice]

    # Project name
    console.print()
    project_name = click.prompt("[bold]Project name[/bold]", type=str, default=None)

    # LLM Provider
    console.print()
    console.print("[bold]Select LLM provider:[/bold]")
    console.print("  [cyan]1[/cyan] - openai")
    console.print("  [cyan]2[/cyan] - anthropic")
    console.print("  [cyan]3[/cyan] - google")
    console.print("  [cyan]4[/cyan] - groq")
    console.print("  [cyan]5[/cyan] - ollama (self-hosted)")

    provider_choice = click.prompt(
        "\nProvider",
        type=click.Choice(["1", "2", "3", "4", "5"], case_sensitive=False),
        default="1",
    )

    provider_map = {
        "1": "openai",
        "2": "anthropic",
        "3": "google",
        "4": "groq",
        "5": "ollama",
    }
    provider = provider_map[provider_choice]

    return template, project_name, provider


def _install_git_hooks(target: Path, parac_dir: Path, verbose: bool) -> None:
    """Install git hooks for governance enforcement.

    Args:
        target: Project root directory
        parac_dir: .parac/ directory
        verbose: Whether to show detailed output
    """
    import shutil
    import stat

    # Check if git repository exists
    git_dir = target / ".git"
    if not git_dir.exists():
        if verbose:
            console.print(
                "[dim]No git repository found, skipping hook " "installation[/dim]"
            )
        return

    # Create hooks directory if it doesn't exist
    hooks_dir = git_dir / "hooks"
    hooks_dir.mkdir(parents=True, exist_ok=True)

    # Source hook in .parac/tools/hooks/
    source_hook = parac_dir / "tools" / "hooks" / "validate-structure.py"
    target_hook = hooks_dir / "pre-commit"

    if not source_hook.exists():
        if verbose:
            console.print(
                f"[yellow]Warning:[/yellow] Hook source not found at " f"{source_hook}"
            )
        return

    try:
        # Copy hook to .git/hooks/pre-commit
        shutil.copy2(source_hook, target_hook)

        # Make executable (Unix/Mac)
        if hasattr(os, "chmod"):
            current_perms = stat.S_IMODE(os.lstat(target_hook).st_mode)
            os.chmod(
                target_hook, current_perms | stat.S_IXUSR | stat.S_IXGRP | stat.S_IXOTH
            )

        if verbose:
            console.print(f"[green]✓[/green] Installed pre-commit hook: {target_hook}")
        else:
            console.print("[dim]+ Git pre-commit hook installed[/dim]")

    except Exception as e:  # noqa: BLE001
        console.print(f"[yellow]Warning:[/yellow] Could not install git hook: {e}")
        if verbose:
            console.print("[dim]You can manually install it later with:[/dim]")
            console.print(f"[dim]  cp {source_hook} {target_hook}[/dim]")
            console.print(f"[dim]  chmod +x {target_hook}[/dim]")


def _create_lite_workspace(parac_dir: Path, _target: Path, project_name: str) -> None:
    """Create lite .parac/ workspace with complete structure.

    Lite mode creates all essential folders and files for Paracle to function:
    - agents/ with specs, skills, and manifest
    - memory/ with context, logs
    - roadmap/ with roadmap, decisions, constraints
    - tools/ with custom and builtin folders
    - integrations/ with IDE support

    Perfect for:
    - Quick prototyping with full structure
    - Learning Paracle
    - Single-agent projects ready to grow
    - Experimenting with ideas

    Can be upgraded to full mode later with: paracle init --all --force
    """
    from datetime import date

    # Complete directory structure for lite mode
    dirs_to_create = [
        parac_dir / "agents" / "specs",
        parac_dir / "agents" / "skills" / "my-first-skill",
        parac_dir / "memory" / "context",
        parac_dir / "memory" / "logs",
        parac_dir / "roadmap",
        parac_dir / "tools" / "custom",
        parac_dir / "tools" / "builtin",
        parac_dir / "integrations" / "ide",
    ]

    for dir_path in dirs_to_create:
        dir_path.mkdir(parents=True, exist_ok=True)

    console.print("  [dim]Created directory structure[/dim]")

    # =========================================================================
    # Root files
    # =========================================================================

    # .gitignore
    gitignore_content = """# Paracle workspace ignores
memory/logs/*.log
*.pyc
__pycache__/
.env
.env.local
"""
    (parac_dir / ".gitignore").write_text(gitignore_content, encoding="utf-8")

    # project.yaml - Project configuration
    project_content = f"""# Paracle Project (Lite Mode)
# Upgrade to full mode: paracle init --all --force

name: {project_name}
version: 0.0.1

# Default LLM settings
defaults:
  model: gpt-4o-mini
  provider: openai
  temperature: 0.7
"""
    (parac_dir / "project.yaml").write_text(project_content, encoding="utf-8")

    # changelog.md
    changelog_content = f"""# Changelog - {project_name}

All notable changes to this project will be documented in this file.

## [0.0.1] - {date.today().isoformat()}

### Added
- Initial project setup with Paracle lite mode
"""
    (parac_dir / "changelog.md").write_text(changelog_content, encoding="utf-8")

    console.print(
        "  [dim]Created[/dim] root files " "(.gitignore, project.yaml, changelog.md)"
    )

    # =========================================================================
    # Agents files
    # =========================================================================

    # agents/manifest.yaml
    manifest_content = f"""# Agent Manifest
# AUTO-GENERATED - Regenerate with: paracle sync

generated_at: '{date.today().isoformat()}'
agents:
  - id: myagent
    name: My Agent
    spec_file: agents/specs/myagent.md
"""
    (parac_dir / "agents" / "manifest.yaml").write_text(
        manifest_content, encoding="utf-8"
    )

    # agents/SKILL_ASSIGNMENTS.md
    skill_assignments = """# Skill Assignments

Maps skills to agents in this project.

## Assignments

| Agent | Skills |
|-------|--------|
| myagent | my-first-skill |

## How to Assign Skills

1. Create a skill in `skills/` directory
2. Reference it in the agent's spec file
3. Update this table for documentation
"""
    (parac_dir / "agents" / "SKILL_ASSIGNMENTS.md").write_text(
        skill_assignments, encoding="utf-8"
    )

    # agents/specs/myagent.md
    agent_spec = """# My Agent

A simple agent to get you started.

## Role

Describe what this agent does.

## Capabilities

- Answer questions
- Help with tasks

## Guidelines

1. Be helpful and concise
2. Ask for clarification when needed

## Skills

- my-first-skill

## Model

Uses the default model from project.yaml.
"""
    (parac_dir / "agents" / "specs" / "myagent.md").write_text(
        agent_spec, encoding="utf-8"
    )

    # agents/skills/README.md
    skills_readme = """# Agent Skills

Reusable skills that can be assigned to agents.

## What are Skills?

Skills are reusable capabilities that can be shared across multiple agents.
They define specific behaviors, prompts, or tool configurations.

## Structure

Each skill is a folder with its definition:

```
skills/
└── my-first-skill/
    └── skill.yaml  (or README.md)
```

## Using Skills

Assign skills to agents in their spec files:

```markdown
## Skills

- my-first-skill
- another-skill
```
"""
    (parac_dir / "agents" / "skills" / "README.md").write_text(
        skills_readme, encoding="utf-8"
    )

    console.print("  [dim]Created[/dim] agents/* files")

    # =========================================================================
    # Memory files
    # =========================================================================

    # memory/index.yaml
    memory_index = f"""# Memory Index
created: '{date.today().isoformat()}'
entries: []
"""
    (parac_dir / "memory" / "index.yaml").write_text(memory_index, encoding="utf-8")

    # memory/context/current_state.yaml
    state_content = f"""# Project State (Lite Mode)
version: '1.0'
snapshot_date: '{date.today().isoformat()}'
project:
  name: {project_name}
  version: 0.0.1
  phase: phase_0
  status: in_progress
  mode: lite
current_phase:
  id: phase_0
  name: Setup
  status: in_progress
  progress: 0%
"""
    (parac_dir / "memory" / "context" / "current_state.yaml").write_text(
        state_content, encoding="utf-8"
    )

    # memory/context/open_questions.md
    questions_content = """# Open Questions

Track unresolved questions and decisions here.

## Questions

(No open questions yet)
"""
    (parac_dir / "memory" / "context" / "open_questions.md").write_text(
        questions_content, encoding="utf-8"
    )

    # memory/logs/README.md
    logs_readme = """# Logging System

## Files

- `agent_actions.log` - Agent action history
- `decisions.log` - Important decisions

## Format

```
[TIMESTAMP] [AGENT] [ACTION] Description
```

## Example

```
[2026-01-06 10:00:00] [myagent] [TASK] Completed initial setup
```
"""
    (parac_dir / "memory" / "logs" / "README.md").write_text(
        logs_readme, encoding="utf-8"
    )

    # memory/logs/agent_actions.log
    actions_log = (
        f"# Agent Actions Log - {project_name}\n"
        "# Format: [TIMESTAMP] [AGENT] [ACTION] Description\n\n"
    )
    (parac_dir / "memory" / "logs" / "agent_actions.log").write_text(
        actions_log, encoding="utf-8"
    )

    # memory/logs/decisions.log
    decisions_log = (
        f"# Decisions Log - {project_name}\n"
        "# Format: [TIMESTAMP] [DECISION] Description\n\n"
    )
    (parac_dir / "memory" / "logs" / "decisions.log").write_text(
        decisions_log, encoding="utf-8"
    )

    console.print("  [dim]Created[/dim] memory/* files")

    # =========================================================================
    # Roadmap files
    # =========================================================================

    # roadmap/roadmap.yaml
    roadmap_content = f"""# Project Roadmap
version: '1.0'
project: {project_name}

phases:
  - id: phase_0
    name: Setup
    status: in_progress
    description: Initial project setup
    deliverables:
      - name: .parac/ workspace
        status: completed
"""
    (parac_dir / "roadmap" / "roadmap.yaml").write_text(
        roadmap_content, encoding="utf-8"
    )

    # roadmap/decisions.md
    decisions_content = """# Architecture Decision Records

## Index

| ADR | Title | Status | Date |
|-----|-------|--------|------|
| - | - | - | - |

## Records

(No ADRs yet)
"""
    (parac_dir / "roadmap" / "decisions.md").write_text(
        decisions_content, encoding="utf-8"
    )

    # roadmap/constraints.yaml
    constraints_content = """# Project Constraints

# Define project constraints and boundaries

constraints:
  - name: budget
    type: resource
    description: Project budget constraints
    value: TBD

  - name: timeline
    type: time
    description: Project timeline
    value: TBD
"""
    (parac_dir / "roadmap" / "constraints.yaml").write_text(
        constraints_content, encoding="utf-8"
    )

    console.print("  [dim]Created[/dim] roadmap/* files")

    # =========================================================================
    # Tools files
    # =========================================================================

    # tools/README.md
    tools_readme = """# Tools

Tool definitions and hooks for Paracle.

## Structure

- `custom/` - Custom tools you create
- `builtin/` - Built-in Paracle tools
- `registry.yaml` - Tool registry

## Creating Custom Tools

Create a YAML file in `custom/`:

```yaml
name: my_tool
description: What this tool does
parameters:
  - name: param1
    type: string
    required: true
```
"""
    (parac_dir / "tools" / "README.md").write_text(tools_readme, encoding="utf-8")

    # tools/registry.yaml
    (parac_dir / "tools" / "registry.yaml").write_text(
        "# Tool Registry\ntools: []\n", encoding="utf-8"
    )

    # tools/custom/.gitkeep
    (parac_dir / "tools" / "custom" / ".gitkeep").write_text("", encoding="utf-8")

    console.print("  [dim]Created[/dim] tools/* files")

    # =========================================================================
    # Integrations files
    # =========================================================================

    # integrations/README.md
    integrations_readme = """# Integrations

External tool and IDE integrations.

## IDE Support

Run `paracle ide sync --copy` to generate IDE-specific configs:

- `.cursorrules` - Cursor AI
- `.claude/CLAUDE.md` - Claude Code
- `.github/copilot-instructions.md` - GitHub Copilot
- `.windsurfrules` - Windsurf
- `.clinerules` - Cline
"""
    (parac_dir / "integrations" / "README.md").write_text(
        integrations_readme, encoding="utf-8"
    )

    # integrations/ide/_manifest.yaml
    ide_manifest = f"""# IDE Integration Manifest
generated_at: '{date.today().isoformat()}'
supported_ides:
  - cursor
  - claude
  - copilot
  - windsurf
  - cline
"""
    (parac_dir / "integrations" / "ide" / "_manifest.yaml").write_text(
        ide_manifest, encoding="utf-8"
    )


def _create_minimal_workspace(parac_dir: Path, target: Path, project_name: str) -> None:
    """Create minimal .parac/ workspace structure."""
    from datetime import date

    # Create directory structure
    dirs_to_create = [
        parac_dir / "memory" / "context",
        parac_dir / "memory" / "knowledge",
        parac_dir / "memory" / "summaries",
        parac_dir / "memory" / "logs",
        parac_dir / "roadmap",
        parac_dir / "agents" / "specs",
        parac_dir / "agents" / "skills",
        parac_dir / "policies",
        parac_dir / "tools" / "hooks",
        parac_dir / "adapters",
        parac_dir / "integrations" / "ide",
    ]

    for dir_path in dirs_to_create:
        dir_path.mkdir(parents=True, exist_ok=True)
        console.print(f"  [dim]Created[/dim] {dir_path.relative_to(target)}")

    # Create minimal current_state.yaml
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
    console.print(f"  [dim]Created[/dim] {state_file.relative_to(target)}")

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
    console.print(f"  [dim]Created[/dim] {roadmap_file.relative_to(target)}")

    # Create skills README
    skills_readme = """# Agent Skills

Reusable skills that can be assigned to agents.

## What are Skills?

Skills are reusable capabilities that can be shared across multiple agents.
They define specific behaviors, prompts, or tool configurations.

## Structure

Each skill is defined as a YAML file:

```yaml
name: code-review
description: Review code for quality and best practices
prompts:
  system: "You are a code reviewer..."
tools:
  - read_file
  - search_code
```

## Using Skills

Assign skills to agents in their spec files:

```yaml
# In agents/specs/reviewer.md
skills:
  - code-review
  - security-audit
```

## Creating Skills

1. Create a YAML file in this directory
2. Define the skill name, description, and capabilities
3. Reference it in agent specifications
"""
    skills_file = parac_dir / "agents" / "skills" / "README.md"
    skills_file.write_text(skills_readme, encoding="utf-8")
    console.print(f"  [dim]Created[/dim] {skills_file.relative_to(target)}")

    # Create GOVERNANCE.md
    governance_content = """# .parac/ Governance

This directory is the single source of truth for the project.

## Structure

- `memory/context/` - Current project state
- `memory/knowledge/` - Accumulated knowledge
- `memory/logs/` - Action logs
- `roadmap/` - Project roadmap and decisions
- `agents/specs/` - Agent specifications
- `agents/skills/` - Reusable agent skills
- `policies/` - Project policies
- `tools/hooks/` - Automation hooks
- `adapters/` - Framework adapters
- `integrations/ide/` - IDE configurations
- `workflows/` - Workflow definitions

## Rules

1. Always read current_state.yaml before starting work
2. Update state after completing significant work
3. Document all architectural decisions
4. Never contradict what's documented here
"""
    governance_file = parac_dir / "GOVERNANCE.md"
    governance_file.write_text(governance_content, encoding="utf-8")
    console.print(f"  [dim]Created[/dim] {governance_file.relative_to(target)}")


def _create_full_workspace(parac_dir: Path, _target: Path, project_name: str) -> None:
    """Create complete .parac/ workspace with all files and templates."""
    from datetime import date

    # Full directory structure
    dirs_to_create = [
        # Memory
        parac_dir / "memory" / "context",
        parac_dir / "memory" / "knowledge",
        parac_dir / "memory" / "summaries",
        parac_dir / "memory" / "logs" / "runtime" / "agents",
        parac_dir / "memory" / "logs" / "runtime" / "errors",
        parac_dir / "memory" / "logs" / "runtime" / "workflows",
        parac_dir / "memory" / "logs" / "sessions",
        parac_dir / "memory" / "data",
        # Roadmap
        parac_dir / "roadmap" / "adr",
        # Agents
        parac_dir / "agents" / "specs",
        parac_dir / "agents" / "skills",
        # Policies
        parac_dir / "policies",
        # Tools
        parac_dir / "tools" / "hooks",
        parac_dir / "tools" / "custom",
        # Adapters
        parac_dir / "adapters",
        # Integrations
        parac_dir / "integrations" / "ide",
        # Workflows
        parac_dir / "workflows" / "definitions",
        parac_dir / "workflows" / "templates",
    ]

    for dir_path in dirs_to_create:
        dir_path.mkdir(parents=True, exist_ok=True)

    console.print("  [dim]Created directory structure[/dim]")

    # =========================================================================
    # Core Configuration Files
    # =========================================================================

    # .gitignore
    gitignore_content = """# Paracle workspace ignores
memory/data/*.db
memory/logs/runtime/**/*.log
*.pyc
__pycache__/
.env
.env.local
"""
    (parac_dir / ".gitignore").write_text(gitignore_content, encoding="utf-8")

    # project.yaml
    project_content = f"""# Project Configuration
# This file is manually edited - defines project settings

name: {project_name}
version: 0.0.1
description: A Paracle-managed project

# Default LLM settings
defaults:
  model: gpt-4o-mini
  provider: openai
  temperature: 0.7

# Feature flags
features:
  cost_tracking: true
  auto_logging: true
  require_approvals: false
"""
    (parac_dir / "project.yaml").write_text(project_content, encoding="utf-8")
    console.print(f"  [dim]Created[/dim] {parac_dir.name}/project.yaml")

    # =========================================================================
    # Memory Files
    # =========================================================================

    # current_state.yaml
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
    - Define roadmap
    - Setup development environment
  completed: []
  in_progress:
    - Initialize .parac/ workspace
  pending:
    - Create initial agents
    - Define workflows
blockers: []
next_actions:
  - Review GOVERNANCE.md
  - Define project roadmap in roadmap/roadmap.yaml
  - Create agent specifications in agents/specs/
"""
    (parac_dir / "memory" / "context" / "current_state.yaml").write_text(
        state_content, encoding="utf-8"
    )
    console.print("  [dim]Created[/dim] memory/context/current_state.yaml")

    # open_questions.md
    questions_content = """# Open Questions

Track unresolved questions and decisions here.

## Format

```markdown
### Q[N]: [Title]

**Status:** Open | Resolved | Deferred
**Priority:** High | Medium | Low
**Owner:** [Who decides]
**Deadline:** [When to decide]

**Context:**
[Background information]

**Options:**
1. [Option A]
2. [Option B]

**Resolution:** (when resolved)
[What was decided and why]
```

## Questions

(No open questions yet)
"""
    (parac_dir / "memory" / "context" / "open_questions.md").write_text(
        questions_content, encoding="utf-8"
    )

    # memory/knowledge/architecture.md
    arch_content = f"""# Architecture Knowledge

## Project: {project_name}

### Overview

(Document your architecture here)

### Key Components

- Component A: (description)
- Component B: (description)

### Design Decisions

See `roadmap/adr/` for Architecture Decision Records.
"""
    (parac_dir / "memory" / "knowledge" / "architecture.md").write_text(
        arch_content, encoding="utf-8"
    )

    # memory/knowledge/glossary.md
    glossary_content = """# Project Glossary

Define project-specific terms here.

| Term | Definition |
|------|------------|
| Agent | An AI-powered entity that performs tasks |
| Workflow | A sequence of steps executed by agents |
| Adapter | Integration layer for external frameworks |
"""
    (parac_dir / "memory" / "knowledge" / "glossary.md").write_text(
        glossary_content, encoding="utf-8"
    )

    # memory/logs files
    (parac_dir / "memory" / "logs" / "agent_actions.log").write_text(
        (
            f"# Agent Actions Log - {project_name}\n"
            "# Format: [TIMESTAMP] [AGENT] [ACTION] Description\n\n"
        ),
        encoding="utf-8",
    )
    (parac_dir / "memory" / "logs" / "decisions.log").write_text(
        (
            f"# Decisions Log - {project_name}\n"
            "# Format: [TIMESTAMP] [DECISION] Description\n\n"
        ),
        encoding="utf-8",
    )

    # memory/index.yaml
    (parac_dir / "memory" / "index.yaml").write_text(
        (f"# Memory Index\ncreated: '{date.today().isoformat()}'\n" "entries: []\n"),
        encoding="utf-8",
    )

    console.print("  [dim]Created[/dim] memory/* files")

    # =========================================================================
    # Roadmap Files
    # =========================================================================

    # roadmap.yaml
    roadmap_content = f"""version: '1.0'
project: {project_name}
phases:
  - id: phase_0
    name: Setup
    status: in_progress
    description: Initial project setup and configuration
    deliverables:
      - name: .parac/ workspace
        status: completed
      - name: Project roadmap
        status: pending
      - name: Initial agents
        status: pending

  - id: phase_1
    name: Development
    status: pending
    description: Core development phase
    deliverables: []
"""
    (parac_dir / "roadmap" / "roadmap.yaml").write_text(
        roadmap_content, encoding="utf-8"
    )
    console.print("  [dim]Created[/dim] roadmap/roadmap.yaml")

    # decisions.md
    decisions_content = """# Architecture Decision Records

## Index

| ADR | Title | Status | Date |
|-----|-------|--------|------|
| ADR-001 | Use Paracle for project governance | Accepted | (today) |

## Records

See `adr/` directory for full ADR documents.
"""
    (parac_dir / "roadmap" / "decisions.md").write_text(
        decisions_content, encoding="utf-8"
    )

    # ADR template
    adr_index = """# ADR Index

Architecture Decision Records for this project.

## Template

Copy `ADR-TEMPLATE.md` to create new ADRs.

## Records

- [ADR-001](ADR-001.md): Use Paracle for project governance
"""
    (parac_dir / "roadmap" / "adr" / "index.md").write_text(adr_index, encoding="utf-8")

    adr_template = """# ADR-XXX: [Title]

## Status

Proposed | Accepted | Deprecated | Superseded

## Context

[What is the issue that we're seeing that is motivating this decision?]

## Decision

[What is the change that we're proposing and/or doing?]

## Consequences

### Positive
- [Benefit 1]

### Negative
- [Drawback 1]

### Neutral
- [Side effect 1]
"""
    (parac_dir / "roadmap" / "adr" / "ADR-TEMPLATE.md").write_text(
        adr_template, encoding="utf-8"
    )

    adr_001 = """# ADR-001: Use Paracle for Project Governance

## Status

Accepted

## Context

We need a consistent way to manage project state, track decisions,
and coordinate AI agent activities across the development lifecycle.

## Decision

Use Paracle's .parac/ workspace as the single source of truth for:
- Project state and progress
- Agent specifications and configurations
- Workflow definitions
- Architecture decisions

## Consequences

### Positive
- Single source of truth for all project governance
- AI assistants can understand project context
- Consistent patterns across IDE integrations

### Negative
- Learning curve for .parac/ structure
- Additional files to maintain

### Neutral
- All team members need to follow .parac/ conventions
"""
    (parac_dir / "roadmap" / "adr" / "ADR-001.md").write_text(adr_001, encoding="utf-8")

    console.print("  [dim]Created[/dim] roadmap/* files")

    # =========================================================================
    # Agent Files
    # =========================================================================

    # agents/manifest.yaml (auto-generated marker)
    manifest_content = f"""# Agent Manifest
# AUTO-GENERATED - Do not edit manually
# Regenerate with: paracle sync

generated_at: '{date.today().isoformat()}'
agents: []
"""
    (parac_dir / "agents" / "manifest.yaml").write_text(
        manifest_content, encoding="utf-8"
    )

    # Default coder agent
    coder_agent = """# Coder Agent

An agent specialized in writing and modifying code.

## Role

Implementation of features, writing production-quality code
following project standards and best practices.

## Capabilities

- Code implementation
- Bug fixing
- Code refactoring
- Unit test creation

## Guidelines

1. Follow project code style (see policies/CODE_STYLE.md)
2. Write tests for new functionality
3. Document complex logic
4. Keep changes focused and minimal

## Tools

- read_file
- write_file
- run_tests
"""
    (parac_dir / "agents" / "specs" / "coder.md").write_text(
        coder_agent, encoding="utf-8"
    )

    # Default reviewer agent
    reviewer_agent = """# Reviewer Agent

An agent specialized in code review and quality assurance.

## Role

Review code changes for quality, correctness, and adherence
to project standards.

## Capabilities

- Code review
- Security analysis
- Performance review
- Best practices enforcement

## Guidelines

1. Check for security vulnerabilities
2. Verify test coverage
3. Ensure code follows project standards
4. Provide constructive feedback

## Tools

- read_file
- search_code
"""
    (parac_dir / "agents" / "specs" / "reviewer.md").write_text(
        reviewer_agent, encoding="utf-8"
    )

    console.print("  [dim]Created[/dim] agents/* files")

    # =========================================================================
    # Policy Files
    # =========================================================================

    # CODE_STYLE.md
    code_style = """# Code Style Policy

## General

- Use consistent formatting (run linter before commit)
- Keep functions focused and small
- Use meaningful variable names
- Add type hints where applicable

## Python

- Follow PEP 8
- Use Black for formatting
- Use ruff for linting
- Maximum line length: 88 characters

## Documentation

- Document public APIs
- Use docstrings for functions
- Keep comments up to date
"""
    (parac_dir / "policies" / "CODE_STYLE.md").write_text(code_style, encoding="utf-8")

    # TESTING.md
    testing_policy = """# Testing Policy

## Requirements

- All new features require tests
- Bug fixes should include regression tests
- Maintain minimum 80% coverage

## Test Types

1. **Unit Tests**: Test individual functions
2. **Integration Tests**: Test component interactions
3. **E2E Tests**: Test full workflows

## Running Tests

```bash
pytest tests/
pytest --cov=src tests/
```
"""
    (parac_dir / "policies" / "TESTING.md").write_text(testing_policy, encoding="utf-8")

    # SECURITY.md
    security_policy = """# Security Policy

## API Keys

- Never commit API keys to git
- Use environment variables or .env files
- Rotate keys regularly

## Code Security

- Validate all inputs
- Use parameterized queries
- Sanitize outputs
- Follow OWASP guidelines

## Agent Security

- Review agent actions before execution
- Use minimum required permissions
- Log all agent activities
"""
    (parac_dir / "policies" / "SECURITY.md").write_text(
        security_policy, encoding="utf-8"
    )

    console.print("  [dim]Created[/dim] policies/* files")

    # =========================================================================
    # Tools Files
    # =========================================================================

    # tools/README.md
    tools_readme = """# Tools Directory

## Structure

- `hooks/` - Git and automation hooks
- `custom/` - Custom tool definitions

## Adding Custom Tools

Create a YAML file in `custom/` with tool definition:

```yaml
name: my_tool
description: What this tool does
parameters:
  - name: param1
    type: string
    required: true
```
"""
    (parac_dir / "tools" / "README.md").write_text(tools_readme, encoding="utf-8")

    # tools/registry.yaml
    (parac_dir / "tools" / "registry.yaml").write_text(
        "# Tool Registry\ntools: []\n", encoding="utf-8"
    )

    # tools/hooks/README.md
    hooks_readme = """# Hooks

Automation hooks for Paracle workflows.

## Available Hooks

- `pre-commit` - Run before git commits
- `validate.py` - Validate .parac/ structure

## Creating Hooks

1. Create a Python file in this directory
2. Register in registry.yaml
3. Configure trigger conditions
"""
    (parac_dir / "tools" / "hooks" / "README.md").write_text(
        hooks_readme, encoding="utf-8"
    )

    console.print("  [dim]Created[/dim] tools/* files")

    # =========================================================================
    # Workflow Files
    # =========================================================================

    # workflows/README.md
    workflows_readme = """# Workflows

Define multi-agent workflows here.

## Structure

- `definitions/` - Workflow YAML files
- `content/templates/` - Reusable workflow templates

## Creating Workflows

```yaml
name: my-workflow
description: What this workflow does
steps:
  - id: step1
    agent: coder
    task: "Do something"
  - id: step2
    agent: reviewer
    depends_on: [step1]
    task: "Review step1 output"
```
"""
    (parac_dir / "workflows" / "README.md").write_text(
        workflows_readme, encoding="utf-8"
    )

    # workflows/catalog.yaml
    (parac_dir / "workflows" / "catalog.yaml").write_text(
        "# Workflow Catalog\nworkflows: []\n", encoding="utf-8"
    )

    # Sample workflow template
    hello_workflow = """# Hello World Workflow
name: hello-world
description: A simple example workflow

steps:
  - id: greet
    agent: coder
    task: "Generate a hello world greeting"
    outputs:
      - greeting

  - id: review
    agent: reviewer
    depends_on: [greet]
    task: "Review the greeting for appropriateness"
"""
    (parac_dir / "workflows" / "templates" / "hello_world.yaml").write_text(
        hello_workflow, encoding="utf-8"
    )

    console.print("  [dim]Created[/dim] workflows/* files")

    # =========================================================================
    # Integration Files
    # =========================================================================

    # integrations/README.md
    integrations_readme = """# Integrations

External tool and IDE integrations.

## IDE Configurations

Run `paracle ide sync --copy` to generate IDE-specific configs:

- `.cursorrules` - Cursor AI
- `.claude/CLAUDE.md` - Claude Code
- `.github/copilot-instructions.md` - GitHub Copilot
- `.windsurfrules` - Windsurf
- `.clinerules` - Cline

## Adding Integrations

Custom integrations can be added to the `ide/` directory.
"""
    (parac_dir / "integrations" / "README.md").write_text(
        integrations_readme, encoding="utf-8"
    )

    console.print("  [dim]Created[/dim] integrations/* files")

    # =========================================================================
    # GOVERNANCE.md
    # =========================================================================

    governance_content = f"""# .parac/ Governance

## Project: {project_name}

This directory is the **single source of truth** for the project.

## Structure

```
.parac/
├── project.yaml           # Project configuration (edit this)
├── manifest.yaml          # Auto-generated workspace state
├── GOVERNANCE.md          # This file
│
├── memory/                # Project memory
│   ├── context/           # Current state
│   ├── knowledge/         # Accumulated knowledge
│   ├── logs/              # Action and decision logs
│   └── summaries/         # Session summaries
│
├── roadmap/               # Project roadmap
│   ├── roadmap.yaml       # Phases and deliverables
│   ├── decisions.md       # Decision index
│   └── adr/               # Architecture Decision Records
│
├── agents/                # Agent definitions
│   ├── specs/             # Agent specifications
│   └── skills/            # Reusable skills
│
├── policies/              # Project policies
│   ├── CODE_STYLE.md
│   ├── TESTING.md
│   └── SECURITY.md
│
├── tools/                 # Tools and hooks
│   ├── hooks/             # Automation hooks
│   └── custom/            # Custom tools
│
├── workflows/             # Workflow definitions
│   ├── definitions/       # Workflow YAML files
│   └── content/templates/         # Workflow templates
│
└── integrations/          # External integrations
    └── ide/               # IDE configurations
```

## Rules

1. **Read First**: Always read `memory/context/current_state.yaml` before work
2. **Log Actions**: Log significant actions to `memory/logs/agent_actions.log`
3. **Document Decisions**: Add ADRs for architectural decisions
4. **Never Contradict**: .parac/ is the source of truth

## Commands

```bash
paracle status      # View current state
paracle sync        # Sync with reality
paracle validate    # Check consistency
paracle ide sync    # Generate IDE configs
```
"""
    (parac_dir / "GOVERNANCE.md").write_text(governance_content, encoding="utf-8")
    console.print("  [dim]Created[/dim] GOVERNANCE.md")


@click.command()
@click.argument("path", default=".", type=click.Path())
@click.option("--name", help="Project name (defaults to directory name)")
@click.option("--force", is_flag=True, help="Overwrite existing .parac/")
@click.option(
    "--template",
    "-t",
    type=click.Choice(["lite", "standard", "advanced"], case_sensitive=False),
    help=("Project template: lite (minimal), standard (balanced), " "advanced (full)"),
)
@click.option(
    "-i",
    "--interactive",
    is_flag=True,
    help="Interactive mode with prompts for template, name, and provider",
)
@click.option(
    "-v", "--verbose", is_flag=True, help="Verbose output with detailed information"
)
@click.option(
    "--all",
    "full_init",
    is_flag=True,
    help="[DEPRECATED] Use --template advanced instead",
)
@click.option(
    "--lite", "lite_init", is_flag=True, help="[DEPRECATED] Use --template lite instead"
)
def init(
    path: str,
    name: str | None,
    force: bool,
    template: str | None,
    interactive: bool,
    verbose: bool,
    full_init: bool,
    lite_init: bool,
) -> None:
    """Initialize a new .parac/ workspace.

    Creates the .parac/ directory structure with configuration.

    \b
    Quick Start:
      paracle init                  # Standard template
      paracle init -i               # Interactive mode with prompts
      paracle init -t lite          # Lite template (learning)
      paracle init -t advanced -v   # Advanced with verbose output

    \b
    Interactive Mode (-i):
      Prompts for:
      - Template choice (lite/standard/advanced)
      - Project name
      - Default LLM provider (optional)

    \b
    Template Tiers:
      lite      Minimal setup - No Docker, no DB, single agent
                Perfect for: Learning, prototyping, quick experiments
                Time to first agent: < 2 minutes

      standard  Balanced setup - Optional Docker, SQLite, multiple agents
                Perfect for: Small teams, side projects, MVPs
                Production-ready with growth path

      advanced  Full enterprise - Docker Compose, PostgreSQL, all 8 agents
                Perfect for: Production, teams, complex workflows
                Complete observability and compliance

    \b
    Examples:
      paracle init -i                           # Interactive prompts
      paracle init my-project -t lite           # Named lite project
      paracle init --template advanced -v       # Advanced with details
      paracle init --name my-bot -t standard    # Named standard project
      paracle init -i -v                        # Interactive + verbose

    \b
    Flags:
      -i, --interactive    Prompt for all options
      -v, --verbose        Show detailed progress
      -t, --template       Choose template (lite/standard/advanced)
      --force              Overwrite existing .parac/

    \b
    What's Created (lite):
      + Single agent definition
      + File-based persistence only
      + Zero external dependencies
      + Upgrade path to standard/advanced

    \b
    What's Created (standard):
      + Multiple agent templates
      + SQLite + file persistence
      + Basic policies and workflows
      + IDE integration support

    \b
    What's Created (advanced):
      + All 8 agent types (architect, coder, tester, reviewer, pm,
        documenter, release manager, security)
      + PostgreSQL + Redis/Valkey
      + Complete policy pack
      + Docker Compose setup
      + CI/CD templates

    \b
    Upgrade Later:
      paracle init --template advanced --force  # Upgrade lite → advanced

    Note: This command always runs locally (no API call) as it creates
    the workspace that the API would operate on.
    """
    # Interactive mode: explicit -i flag OR auto-detect
    # (no template, default path, no name)
    is_interactive = interactive or (
        template is None
        and not lite_init
        and not full_init
        and path == "."
        and name is None
        and not interactive  # Prevent double prompt
    )

    if is_interactive:
        if verbose:
            console.print("[dim]Running in interactive mode...[/dim]\n")
        # Run interactive prompts
        template, name, _provider = _interactive_init()
        # Provider is captured but will be used in future enhancement
        # For now, we just use the template and name

    # Handle backward compatibility
    if lite_init:
        console.print(
            "[yellow]Note:[/yellow] --lite is deprecated, " "use --template lite"
        )
        template = "lite"
    elif full_init:
        console.print(
            "[yellow]Note:[/yellow] --all is deprecated, " "use --template advanced"
        )
        template = "advanced"
    elif template is None:
        template = "standard"  # Default for non-interactive mode

    # Validate mutually exclusive options
    if lite_init and full_init:
        console.print("[red]Error:[/red] --all and --lite are mutually exclusive")
        raise SystemExit(1)

    target = Path(path).resolve()

    # Create target directory if it doesn't exist
    if not target.exists():
        target.mkdir(parents=True)
        if verbose:
            console.print(f"[dim]+ Created project directory:[/dim] {target}")
        else:
            console.print(f"[dim]Created project directory:[/dim] {target}")

    parac_dir = target / ".parac"

    if parac_dir.exists() and not force:
        console.print(f"[red]Error:[/red] .parac/ already exists at {target}")
        console.print("Use --force to overwrite.")
        raise SystemExit(1)

    project_name = name or target.name

    if verbose:
        console.print(f"[dim]Project name: {project_name}[/dim]")
        console.print(f"[dim]Template: {template}[/dim]")
        console.print(f"[dim]Target: {target}[/dim]\n")

    # Template descriptions
    template_info = {
        "lite": {
            "name": "Lite Mode",
            "emoji": "🚀",
            "tagline": "Zero config, maximum speed",
            "features": [
                "Single agent (myagent)",
                "File-based only (no DB)",
                "Zero dependencies",
                "< 2 minute setup",
            ],
            "upgrade": "paracle init --template standard --force",
        },
        "standard": {
            "name": "Standard Mode",
            "emoji": "⚡",
            "tagline": "Balanced power and simplicity",
            "features": [
                "Multiple agents (coder, reviewer)",
                "SQLite persistence",
                "Basic policies",
                "Production-ready",
            ],
            "upgrade": "paracle init --template advanced --force",
        },
        "advanced": {
            "name": "Advanced Mode",
            "emoji": "🏢",
            "tagline": "Enterprise-grade, full stack",
            "features": [
                (
                    "All 8 agents (architect, coder, tester, reviewer, "
                    "pm, documenter, releasemanager, security)"
                ),
                "PostgreSQL + Redis",
                "Docker Compose",
                "Complete CI/CD",
            ],
            "upgrade": None,
        },
    }

    info = template_info[template]
    console.print(f"\n[bold cyan]{info['name']}:[/bold cyan] {info['tagline']}")
    console.print(f"[dim]Project:[/dim] {project_name}\n")

    if verbose:
        console.print("[bold]Template Details:[/bold]")
        for feature in info["features"]:
            console.print(f"  • {feature}")
        console.print()

    # Try loading from template directory first
    if verbose:
        console.print(
            f"[dim]Loading template from content/templates/{template}..." "[/dim]"
        )

    template_loaded = _load_template_from_directory(template, parac_dir, project_name)

    if not template_loaded:
        # Fallback to programmatic creation
        if verbose:
            console.print(
                "[yellow]Template files not found, generating "
                "programmatically...[/yellow]\n"
            )
        else:
            console.print("[dim]Using programmatic template generation...[/dim]\n")

        if template == "lite":
            _create_lite_workspace(parac_dir, target, project_name)
        elif template == "advanced":
            _create_full_workspace(parac_dir, target, project_name)
        else:  # standard
            _create_minimal_workspace(parac_dir, target, project_name)

    # Install git hooks for governance enforcement
    _install_git_hooks(target, parac_dir, verbose)

    # Success message
    console.print(f"\n[green]+ {info['name']} initialized[/green] at {target}")
    console.print("\n[bold]Features:[/bold]")
    for feature in info["features"]:
        console.print(f"  + {feature}")

    console.print("\n[bold]Next steps:[/bold]")
    if template == "lite":
        console.print("  1. Edit [cyan].parac/agents/specs/myagent.md[/cyan]")
        console.print("  2. [cyan]paracle agents list[/cyan] - View your agent")
        console.print("  3. [cyan]paracle agents run myagent --task 'hello'[/cyan]")
        console.print("  4. [cyan]paracle ide sync[/cyan] - Generate IDE configs")
    elif template == "standard":
        console.print("  1. [cyan]paracle status[/cyan] - View project state")
        console.print("  2. [cyan]paracle agents list[/cyan] - View available agents")
        console.print("  3. [cyan]paracle sync[/cyan] - Sync workspace")
        console.print("  4. [cyan]paracle ide sync[/cyan] - Generate IDE configs")
    else:  # advanced
        console.print("  1. [cyan]paracle status[/cyan] - View project state")
        console.print("  2. [cyan]paracle agents list[/cyan] - View all 8 agents")
        console.print("  3. [cyan]docker compose up -d[/cyan] - Start services")
        console.print("  4. [cyan]paracle workflows list[/cyan] - Explore workflows")

    if info["upgrade"]:
        console.print(f"\n[dim]Upgrade later:[/dim] [cyan]{info['upgrade']}[/cyan]")

    console.print(f"\n[dim]Docs: Docs:[/dim] https://paracle.dev/templates/{template}")
    console.print("[dim]Help: Help:[/dim] [cyan]paracle --help[/cyan]\n")


# Legacy compatibility: keep 'parac' group for backward compatibility
# but mark as deprecated
@click.group(hidden=True)
def parac() -> None:
    """[DEPRECATED] Use top-level commands instead.

    paracle parac status  ->  paracle status
    paracle parac sync    ->  paracle sync
    """
    ...


# Add commands to legacy group for backward compatibility
parac.add_command(status, "status")
parac.add_command(sync, "sync")
parac.add_command(validate, "validate")
parac.add_command(session, "session")
