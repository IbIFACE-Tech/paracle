"""ReleaseManager agent with git tools integration."""

import asyncio
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent / "packages"))

from paracle_domain.models import AgentSpec
from paracle_orchestration.tool_executor import ToolEnabledAgentExecutor
from rich.console import Console
from rich.panel import Panel

console = Console()


async def run_releasemanager_commit(message: str) -> None:
    """Run releasemanager agent to commit changes.
    
    Args:
        message: Commit message
    """
    console.print(
        Panel(
            "[bold cyan]🚀 ReleaseManager Agent - Git Commit[/bold cyan]",
            border_style="cyan",
        )
    )
    
    # Create tool-enabled executor
    executor = ToolEnabledAgentExecutor()
    
    # Execute git status
    console.print("\n[bold]Step 1: Checking status...[/bold]")
    status_result = await executor.execute_tool("git_status", cwd=".")
    
    if not status_result.success:
        console.print(f"[red]❌ Status check failed: {status_result.error}[/red]")
        return
    
    output = status_result.output
    total = output.get("total_changes", 0)
    
    console.print(f"[green]✅ Found {total} changes[/green]")
    
    if total == 0:
        console.print("[yellow]ℹ️  No changes to commit[/yellow]")
        return
    
    # Stage all files
    console.print("\n[bold]Step 2: Staging files...[/bold]")
    add_result = await executor.execute_tool("git_add", files="-A", cwd=".")
    
    if not add_result.success:
        console.print(f"[red]❌ Staging failed: {add_result.error}[/red]")
        return
    
    console.print("[green]✅ Files staged[/green]")
    
    # Create commit
    console.print("\n[bold]Step 3: Creating commit...[/bold]")
    commit_result = await executor.execute_tool("git_commit", message=message, cwd=".")
    
    if not commit_result.success:
        console.print(f"[red]❌ Commit failed: {commit_result.error}[/red]")
        return
    
    console.print("[green]✅ Commit created successfully![/green]")
    
    if commit_result.output.get("stdout"):
        console.print(f"\n[dim]{commit_result.output['stdout']}[/dim]")
    
    console.print(
        Panel(
            f"[bold green]✅ ReleaseManager completed successfully![/bold green]\n\n"
            f"Files changed: {total}\n"
            f"Commit: ✓",
            border_style="green",
        )
    )


async def main():
    """Main entry point."""
    if len(sys.argv) < 2:
        console.print("[red]❌ Error: Commit message required[/red]")
        console.print("\nUsage:")
        console.print('  python scripts/releasemanager_commit.py "commit message"')
        sys.exit(1)
    
    message = sys.argv[1]
    
    try:
        await run_releasemanager_commit(message)
    except KeyboardInterrupt:
        console.print("\n[yellow]⚠️  Cancelled[/yellow]")
        sys.exit(130)
    except Exception as e:
        console.print(f"\n[red]❌ Error: {e}[/red]")
        console.print_exception()
        sys.exit(1)


if __name__ == "__main__":
    asyncio.run(main())
