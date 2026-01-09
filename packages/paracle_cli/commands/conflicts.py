"""Conflict resolution CLI commands.

Commands for managing file locks and resolving conflicts
during concurrent agent execution.
"""

import click
from paracle_conflicts import (
    ConflictDetector,
    ConflictResolver,
    LockManager,
    ResolutionStrategy,
)
from rich.console import Console
from rich.table import Table

console = Console()


@click.group()
def conflicts():
    """Manage conflicts and file locks."""
    pass


@conflicts.command()
def locks():
    """Show all active file locks."""
    manager = LockManager()

    lock_files = list(manager.lock_dir.glob("*.lock"))

    if not lock_files:
        console.print("[green]No active locks[/green]")
        return

    table = Table(title="Active File Locks")
    table.add_column("File", style="cyan")
    table.add_column("Agent", style="yellow")
    table.add_column("Operation", style="blue")
    table.add_column("Expires", style="magenta")

    for lock_file in lock_files:
        try:
            import json

            with open(lock_file) as f:
                lock_data = json.load(f)

            table.add_row(
                lock_data.get("file_path", "unknown"),
                lock_data.get("agent_id", "unknown"),
                lock_data.get("operation", "write"),
                lock_data.get("expires_at", "unknown"),
            )
        except Exception:
            continue

    console.print(table)


@conflicts.command()
@click.argument("file_path")
@click.argument("agent_id")
@click.option("--timeout", "-t", default=300, help="Lock timeout in seconds")
def lock(file_path: str, agent_id: str, timeout: int):
    """Acquire a lock on a file."""
    manager = LockManager()

    success = manager.acquire_lock(file_path, agent_id, timeout=timeout)

    if success:
        console.print(f"[green]Lock acquired on {file_path} for {agent_id}[/green]")
    else:
        console.print(f"[red]Failed to acquire lock on {file_path}[/red]")

        # Show who holds the lock
        existing_lock = manager.get_lock(file_path)
        if existing_lock:
            console.print(f"  Lock held by: {existing_lock.agent_id}")
            console.print(f"  Expires: {existing_lock.expires_at}")


@conflicts.command()
@click.argument("file_path")
@click.argument("agent_id")
def unlock(file_path: str, agent_id: str):
    """Release a lock on a file."""
    manager = LockManager()

    success = manager.release_lock(file_path, agent_id)

    if success:
        console.print(f"[green]Lock released on {file_path}[/green]")
    else:
        console.print(f"[red]Failed to release lock on {file_path}[/red]")


@conflicts.command()
def cleanup():
    """Clear expired locks."""
    manager = LockManager()

    cleared = manager.clear_expired_locks()

    console.print(f"[green]Cleared {cleared} expired lock(s)[/green]")


@conflicts.command()
def detect():
    """Detect conflicts in recent modifications."""
    detector = ConflictDetector()

    # In a real implementation, this would scan recent agent runs
    conflicts = detector.get_conflicts(resolved=False)

    if not conflicts:
        console.print("[green]No conflicts detected[/green]")
        return

    table = Table(title="Detected Conflicts")
    table.add_column("File", style="cyan")
    table.add_column("Agent 1", style="yellow")
    table.add_column("Agent 2", style="red")
    table.add_column("Detected", style="magenta")

    for conflict in conflicts:
        table.add_row(
            conflict.file_path,
            conflict.agent1_id,
            conflict.agent2_id,
            conflict.detected_at.strftime("%Y-%m-%d %H:%M:%S"),
        )

    console.print(table)


@conflicts.command()
@click.option(
    "--strategy",
    "-s",
    type=click.Choice([s.value for s in ResolutionStrategy]),
    default="manual",
    help="Resolution strategy",
)
def resolve(strategy: str):
    """Resolve detected conflicts."""
    detector = ConflictDetector()
    resolver = ConflictResolver()

    conflicts = detector.get_conflicts(resolved=False)

    if not conflicts:
        console.print("[green]No conflicts to resolve[/green]")
        return

    console.print(
        f"\n[bold]Resolving {len(conflicts)} conflict(s) using {strategy}...[/bold]\n"
    )

    for conflict in conflicts:
        result = resolver.resolve(conflict, ResolutionStrategy(strategy))

        if result.success:
            console.print(f"[green]✓[/green] {conflict.file_path}: {result.message}")
            if result.backup_paths:
                for backup in result.backup_paths:
                    console.print(f"    Backup: {backup}")
            detector.mark_resolved(conflict)
        else:
            console.print(f"[red]✗[/red] {conflict.file_path}: {result.message}")

    console.print()


@conflicts.command()
def backups():
    """List all backup files."""
    resolver = ConflictResolver()

    backups = resolver.list_backups()

    if not backups:
        console.print("[yellow]No backups found[/yellow]")
        return

    table = Table(title="Backup Files")
    table.add_column("File", style="cyan")
    table.add_column("Size", style="yellow")
    table.add_column("Modified", style="magenta")

    for backup in backups:
        stat = backup.stat()
        from datetime import datetime

        table.add_row(
            backup.name,
            f"{stat.st_size:,} bytes",
            datetime.fromtimestamp(stat.st_mtime).strftime("%Y-%m-%d %H:%M:%S"),
        )

    console.print(table)
