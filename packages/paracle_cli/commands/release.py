"""CLI commands for ReleaseManager agent operations."""

import asyncio

import click
from rich.console import Console
from rich.panel import Panel

console = Console()


@click.group("release")
def release():
    """ReleaseManager agent operations (git, versioning, releases)."""
    pass


@release.command("commit")
@click.argument("message")
@click.option(
    "--push",
    is_flag=True,
    help="Push after committing",
)
def commit(message: str, push: bool):
    """Commit changes using ReleaseManager agent.

    Examples:
        paracle release commit "feat: add new feature"
        paracle release commit "fix: resolve bug" --push
    """
    asyncio.run(_commit_async(message, push))


async def _commit_async(message: str, push: bool):
    """Async commit implementation."""
    try:
        from paracle_orchestration.tool_executor import ToolEnabledAgentExecutor

        console.print(
            Panel(
                "[bold cyan]🚀 ReleaseManager Agent - Git Commit[/bold cyan]",
                border_style="cyan",
            )
        )

        executor = ToolEnabledAgentExecutor()

        # Step 1: Check status
        console.print("\n[bold]Step 1: Checking git status...[/bold]")
        status_result = await executor.execute_tool("git_status", cwd=".")

        if not status_result.success:
            console.print(f"[red]❌ Status check failed: {status_result.error}[/red]")
            raise click.Abort()

        output = status_result.output
        total = output.get("total_changes", 0)

        console.print(f"[green]✅ Found {total} changes[/green]")
        console.print(f"[dim]  Modified: {len(output.get('modified', []))}[/dim]")
        console.print(f"[dim]  Added: {len(output.get('added', []))}[/dim]")
        console.print(f"[dim]  Deleted: {len(output.get('deleted', []))}[/dim]")
        console.print(f"[dim]  Untracked: {len(output.get('untracked', []))}[/dim]")

        if total == 0:
            console.print("\n[yellow]ℹ️  No changes to commit[/yellow]")
            return

        # Step 2: Stage files
        console.print("\n[bold]Step 2: Staging files...[/bold]")
        add_result = await executor.execute_tool("git_add", files="-A", cwd=".")

        if not add_result.success:
            console.print(f"[red]❌ Staging failed: {add_result.error}[/red]")
            raise click.Abort()

        console.print("[green]✅ Files staged successfully[/green]")

        # Step 3: Create commit
        console.print("\n[bold]Step 3: Creating commit...[/bold]")
        console.print(f"[dim]Message: {message}[/dim]")

        commit_result = await executor.execute_tool(
            "git_commit", message=message, cwd="."
        )

        if not commit_result.success:
            console.print(f"[red]❌ Commit failed: {commit_result.error}[/red]")
            raise click.Abort()

        console.print("[green]✅ Commit created successfully![/green]")

        if commit_result.output.get("stdout"):
            console.print(f"\n[dim]{commit_result.output['stdout']}[/dim]")

        # Step 4: Push if requested
        if push:
            console.print("\n[bold]Step 4: Pushing to remote...[/bold]")
            push_result = await executor.execute_tool("git_push", cwd=".")

            if not push_result.success:
                console.print(f"[red]❌ Push failed: {push_result.error}[/red]")
                console.print("[yellow]⚠️  Commit was created but not pushed[/yellow]")
                raise click.Abort()

            console.print("[green]✅ Pushed to remote successfully![/green]")

        # Success summary
        console.print(
            Panel(
                f"[bold green]✅ ReleaseManager completed successfully![/bold green]\n\n"
                f"Files changed: {total}\n"
                f"Commit created: ✓\n" + ("Pushed to remote: ✓" if push else ""),
                border_style="green",
            )
        )

    except ImportError as e:
        console.print(f"[red]❌ Error: {e}[/red]")
        console.print("[yellow]Make sure paracle_orchestration is installed[/yellow]")
        raise click.Abort()
    except Exception as e:
        console.print(f"[red]❌ Unexpected error: {e}[/red]")
        raise click.Abort()


@release.command("tag")
@click.argument("tag")
@click.option(
    "--message",
    "-m",
    required=True,
    help="Tag message",
)
@click.option(
    "--push",
    is_flag=True,
    help="Push tag after creating",
)
def tag(tag: str, message: str, push: bool):
    """Create an annotated git tag using ReleaseManager agent.

    Examples:
        paracle release tag v1.0.0 -m "Release v1.0.0"
        paracle release tag v1.0.1 -m "Patch release" --push
    """
    asyncio.run(_tag_async(tag, message, push))


async def _tag_async(tag_name: str, message: str, push: bool):
    """Async tag implementation."""
    try:
        from paracle_orchestration.tool_executor import ToolEnabledAgentExecutor

        console.print(
            Panel(
                "[bold cyan]🏷️  ReleaseManager Agent - Create Tag[/bold cyan]",
                border_style="cyan",
            )
        )

        executor = ToolEnabledAgentExecutor()

        # Create tag
        console.print(f"\n[bold]Creating tag '{tag_name}'...[/bold]")
        tag_result = await executor.execute_tool(
            "git_tag", tag=tag_name, message=message, cwd="."
        )

        if not tag_result.success:
            console.print(f"[red]❌ Tag creation failed: {tag_result.error}[/red]")
            raise click.Abort()

        console.print(f"[green]✅ Tag '{tag_name}' created successfully![/green]")

        # Push if requested
        if push:
            console.print("\n[bold]Pushing tag to remote...[/bold]")
            push_result = await executor.execute_tool("git_push", tags=True, cwd=".")

            if not push_result.success:
                console.print(f"[red]❌ Push failed: {push_result.error}[/red]")
                console.print("[yellow]⚠️  Tag was created but not pushed[/yellow]")
                raise click.Abort()

            console.print("[green]✅ Tag pushed to remote![/green]")

        console.print(
            Panel(
                f"[bold green]✅ ReleaseManager completed![/bold green]\n\n"
                f"Tag: {tag_name}\n" + ("Pushed: ✓" if push else ""),
                border_style="green",
            )
        )

    except Exception as e:
        console.print(f"[red]❌ Error: {e}[/red]")
        raise click.Abort()


@release.command("status")
def status():
    """Check git repository status using ReleaseManager agent.

    Example:
        paracle release status
    """
    asyncio.run(_status_async())


async def _status_async():
    """Async status implementation."""
    try:
        from paracle_orchestration.tool_executor import ToolEnabledAgentExecutor
        from rich.table import Table

        console.print(
            Panel(
                "[bold cyan]📊 ReleaseManager Agent - Git Status[/bold cyan]",
                border_style="cyan",
            )
        )

        executor = ToolEnabledAgentExecutor()

        console.print("\n[bold]Checking repository status...[/bold]")
        status_result = await executor.execute_tool("git_status", cwd=".")

        if not status_result.success:
            console.print(f"[red]❌ Status check failed: {status_result.error}[/red]")
            raise click.Abort()

        output = status_result.output

        # Display status table
        table = Table(title="Git Repository Status")
        table.add_column("Type", style="cyan")
        table.add_column("Count", style="yellow")
        table.add_column("Files", style="dim")

        modified = output.get("modified", [])
        added = output.get("added", [])
        deleted = output.get("deleted", [])
        untracked = output.get("untracked", [])

        table.add_row(
            "Modified",
            str(len(modified)),
            ", ".join(modified[:3]) + ("..." if len(modified) > 3 else ""),
        )
        table.add_row(
            "Added",
            str(len(added)),
            ", ".join(added[:3]) + ("..." if len(added) > 3 else ""),
        )
        table.add_row(
            "Deleted",
            str(len(deleted)),
            ", ".join(deleted[:3]) + ("..." if len(deleted) > 3 else ""),
        )
        table.add_row(
            "Untracked",
            str(len(untracked)),
            ", ".join(untracked[:3]) + ("..." if len(untracked) > 3 else ""),
        )
        table.add_row(
            "[bold]TOTAL[/bold]", f"[bold]{output.get('total_changes', 0)}[/bold]", ""
        )

        console.print(table)

        if output.get("total_changes", 0) == 0:
            console.print("\n[green]✅ Working directory clean[/green]")
        else:
            console.print(
                f"\n[yellow]ℹ️  {output['total_changes']} changes pending[/yellow]"
            )

    except Exception as e:
        console.print(f"[red]❌ Error: {e}[/red]")
        raise click.Abort()
