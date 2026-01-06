#!/usr/bin/env python3
"""Direct git automation script for releasemanager agent.

This script allows the releasemanager agent to execute git operations
directly without going through the full agent framework.
"""

from rich.table import Table
from rich.panel import Panel
from rich.console import Console
from paracle_tools.git_tools import git_add, git_commit, git_status
import asyncio
import sys
from pathlib import Path

# Add packages to path
sys.path.insert(0, str(Path(__file__).parent.parent / "packages"))


console = Console()


async def git_commit_all(message: str, cwd: str = ".") -> dict:
    """Execute full git commit workflow.

    Args:
        message: Commit message
        cwd: Working directory

    Returns:
        Results dictionary
    """
    console.print(
        Panel(
            "[bold cyan]🔧 ReleaseManager Git Automation[/bold cyan]",
            border_style="cyan",
        )
    )

    results = {}

    # Step 1: Check status
    console.print("\n[bold]Step 1: Checking git status...[/bold]")
    status_result = await git_status.execute(cwd=cwd)

    if not status_result.success:
        console.print(
            f"[red]❌ Failed to check status: {status_result.error}[/red]")
        return {"success": False, "error": "Status check failed"}

    results["status"] = status_result.output

    # Display status
    table = Table(title="Git Status")
    table.add_column("Type", style="cyan")
    table.add_column("Count", style="yellow")

    table.add_row("Modified", str(
        len(status_result.output.get("modified", []))))
    table.add_row("Added", str(len(status_result.output.get("added", []))))
    table.add_row("Deleted", str(len(status_result.output.get("deleted", []))))
    table.add_row("Untracked", str(
        len(status_result.output.get("untracked", []))))
    table.add_row("TOTAL", str(status_result.output.get("total_changes", 0)))

    console.print(table)

    total_changes = status_result.output.get("total_changes", 0)
    if total_changes == 0:
        console.print("\n[yellow]ℹ️  No changes to commit[/yellow]")
        return {"success": True, "message": "No changes"}

    # Step 2: Stage all files
    console.print(f"\n[bold]Step 2: Staging {total_changes} files...[/bold]")
    add_result = await git_add.execute(files="-A", cwd=cwd)

    if not add_result.success:
        console.print(
            f"[red]❌ Failed to stage files: {add_result.error}[/red]")
        return {"success": False, "error": "Stage failed"}

    results["add"] = add_result.output
    console.print("[green]✅ Files staged successfully[/green]")

    # Step 3: Create commit
    console.print("\n[bold]Step 3: Creating commit...[/bold]")
    console.print(f"[dim]Message: {message}[/dim]")

    commit_result = await git_commit.execute(message=message, cwd=cwd)

    if not commit_result.success:
        console.print(f"[red]❌ Failed to commit: {commit_result.error}[/red]")
        return {"success": False, "error": "Commit failed"}

    results["commit"] = commit_result.output
    console.print("[green]✅ Commit created successfully[/green]")

    if commit_result.output.get("stdout"):
        console.print(f"\n[dim]{commit_result.output['stdout']}[/dim]")

    # Success summary
    console.print(
        Panel(
            "[bold green]✅ Git commit workflow completed successfully![/bold green]\n\n"
            f"Files changed: {total_changes}\n"
            f"Commit created: ✓",
            border_style="green",
        )
    )

    return {
        "success": True,
        "results": results,
        "files_changed": total_changes,
    }


async def main():
    """Main entry point."""
    if len(sys.argv) < 2:
        console.print("[red]❌ Error: Commit message required[/red]")
        console.print("\nUsage:")
        console.print(
            "  python scripts/git_commit_automation.py \"commit message\"")
        console.print("\nExample:")
        console.print(
            "  python scripts/git_commit_automation.py \"docs: add git tools\"")
        sys.exit(1)

    message = sys.argv[1]
    cwd = sys.argv[2] if len(sys.argv) > 2 else "."

    try:
        result = await git_commit_all(message, cwd)

        if result["success"]:
            sys.exit(0)
        else:
            console.print(
                f"\n[red]❌ Workflow failed: {result.get('error')}[/red]")
            sys.exit(1)

    except KeyboardInterrupt:
        console.print("\n[yellow]⚠️  Cancelled by user[/yellow]")
        sys.exit(130)
    except Exception as e:
        console.print(f"\n[red]❌ Unexpected error: {e}[/red]")
        console.print_exception()
        sys.exit(1)


if __name__ == "__main__":
    asyncio.run(main())
