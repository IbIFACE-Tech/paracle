"""Git integration CLI commands.

Commands for managing automatic commits and git integration.
"""

import click
from paracle_git import AutoCommitManager, CommitConfig, CommitType
from rich.console import Console
from rich.table import Table

console = Console()


@click.group()
def git():
    """Git integration and automatic commits."""
    pass


@git.command()
@click.option("--enable/--disable", default=True, help="Enable/disable auto-commit")
@click.option(
    "--approval/--no-approval", default=True, help="Require approval before commit"
)
@click.option(
    "--conventional/--simple", default=True, help="Use conventional commit format"
)
@click.option("--sign/--no-sign", default=False, help="Sign commits with GPG")
@click.option(
    "--prefix/--no-prefix", default=True, help="Prefix commits with agent name"
)
def config(enable: bool, approval: bool, conventional: bool, sign: bool, prefix: bool):
    """Configure automatic commit settings."""
    config = CommitConfig(
        enabled=enable,
        require_approval=approval,
        conventional_commits=conventional,
        sign_commits=sign,
        prefix_agent_name=prefix,
    )

    console.print("\n[bold]Auto-Commit Configuration:[/bold]")
    console.print(
        f"  Enabled: [{'green' if config.enabled else 'red'}]{config.enabled}[/]"
    )
    console.print(
        f"  Require approval: [{'green' if config.require_approval else 'red'}]{config.require_approval}[/]"
    )
    console.print(
        f"  Conventional commits: [{'green' if config.conventional_commits else 'red'}]{config.conventional_commits}[/]"
    )
    console.print(
        f"  Sign commits: [{'green' if config.sign_commits else 'red'}]{config.sign_commits}[/]"
    )
    console.print(
        f"  Prefix agent name: [{'green' if config.prefix_agent_name else 'red'}]{config.prefix_agent_name}[/]\n"
    )


@git.command()
@click.argument("repo_path", type=click.Path(exists=True), default=".")
def status(repo_path: str):
    """Show git repository status and changed files."""
    manager = AutoCommitManager(repo_path)

    if not manager.is_git_repo():
        console.print("[red]Not a git repository[/red]")
        return

    changes = manager.get_changed_files()

    if not changes:
        console.print("[green]No changes detected[/green]")
        return

    table = Table(title="Changed Files")
    table.add_column("File", style="cyan")
    table.add_column("Status", style="yellow")

    for change in changes:
        status_color = {
            "added": "green",
            "modified": "yellow",
            "deleted": "red",
        }.get(change.change_type, "white")

        table.add_row(change.file_path, f"[{status_color}]{change.change_type}[/]")

    console.print(table)


@git.command()
@click.argument("message")
@click.option(
    "--type",
    "-t",
    type=click.Choice([t.value for t in CommitType]),
    default="feat",
    help="Commit type",
)
@click.option("--scope", "-s", help="Commit scope")
@click.option("--body", "-b", help="Commit body")
@click.option("--agent", "-a", default="user", help="Agent name")
@click.option(
    "--repo", type=click.Path(exists=True), default=".", help="Repository path"
)
def commit(message: str, type: str, scope: str, body: str, agent: str, repo: str):
    """Create a commit with conventional format."""
    manager = AutoCommitManager(repo)

    if not manager.is_git_repo():
        console.print("[red]Not a git repository[/red]")
        return

    changes = manager.get_changed_files()
    if not changes:
        console.print("[yellow]No changes to commit[/yellow]")
        return

    console.print(f"\n[bold]Committing {len(changes)} file(s)...[/bold]")

    success = manager.commit_agent_changes(
        agent_name=agent,
        changes=changes,
        commit_type=CommitType(type),
        description=message,
        scope=scope,
        body=body,
    )

    if success:
        console.print("[green]Commit created successfully[/green]\n")
    else:
        console.print("[red]Failed to create commit[/red]\n")


@git.command()
@click.option("--limit", "-n", default=10, help="Number of commits to show")
@click.option(
    "--repo", type=click.Path(exists=True), default=".", help="Repository path"
)
def log(limit: int, repo: str):
    """Show recent commit history."""
    manager = AutoCommitManager(repo)

    if not manager.is_git_repo():
        console.print("[red]Not a git repository[/red]")
        return

    commits = manager.get_commit_history(limit=limit)

    if not commits:
        console.print("[yellow]No commits found[/yellow]")
        return

    console.print(f"\n[bold]Recent Commits (last {limit}):[/bold]\n")
    for commit in commits:
        console.print(f"  {commit}")
    console.print()


# Git Workflow Management Commands (Phase 7)


@git.command()
@click.option(
    "--repo", type=click.Path(exists=True), default=".", help="Repository path"
)
def init_workflow(repo: str):
    """Initialize git workflow management for repository."""
    from pathlib import Path

    from paracle_git_workflows import BranchManager

    try:
        manager = BranchManager(Path(repo))
        current_branch = manager.get_current_branch()
        console.print("[green]✓[/green] Git workflow initialized")
        console.print(f"Current branch: {current_branch}")
    except ValueError as e:
        console.print(f"[red]Error: {e}[/red]")


@git.command()
@click.option(
    "--repo", type=click.Path(exists=True), default=".", help="Repository path"
)
def branches(repo: str):
    """List all execution branches."""
    from pathlib import Path

    from paracle_git_workflows import BranchManager

    manager = BranchManager(Path(repo))
    exec_branches = manager.list_execution_branches()

    if not exec_branches:
        console.print("[yellow]No execution branches found[/yellow]")
        return

    table = Table(title="Execution Branches")
    table.add_column("Branch Name", style="cyan")
    table.add_column("Execution ID", style="green")
    table.add_column("Created", style="yellow")
    table.add_column("Commits", style="blue")

    for branch in exec_branches:
        table.add_row(
            branch.name,
            branch.execution_id,
            branch.created_at,
            str(branch.commit_count),
        )

    console.print(table)
    console.print(f"\nTotal: {len(exec_branches)} execution branches")


@git.command()
@click.argument("branch_name")
@click.option("--target", default="main", help="Target branch to merge into")
@click.option(
    "--repo", type=click.Path(exists=True), default=".", help="Repository path"
)
def merge(branch_name: str, target: str, repo: str):
    """Merge an execution branch."""
    from pathlib import Path

    from paracle_git_workflows import BranchManager

    manager = BranchManager(Path(repo))

    try:
        manager.merge_execution_branch(branch_name, target)
        console.print(f"[green]✓[/green] Merged '{branch_name}' into '{target}'")
    except RuntimeError as e:
        console.print(f"[red]Error: {e}[/red]")


@git.command()
@click.argument("execution_id")
@click.argument("title")
@click.option("--body", default="", help="PR description")
@click.option(
    "--repo", type=click.Path(exists=True), default=".", help="Repository path"
)
def pr_create(execution_id: str, title: str, body: str, repo: str):
    """Create a pull request for an execution branch."""
    from pathlib import Path

    from paracle_git_workflows import BranchManager

    manager = BranchManager(Path(repo))
    exec_branches = manager.list_execution_branches()

    # Find branch for execution ID
    branch = next((b for b in exec_branches if b.execution_id == execution_id), None)

    if not branch:
        console.print(f"[red]No branch found for execution '{execution_id}'[/red]")
        return

    # Note: Actual PR creation requires GitHub CLI or API
    console.print(
        f"[yellow]To create PR, use GitHub CLI:[/yellow]\n"
        f"  gh pr create --head {branch.name} "
        f'--title "{title}" --body "{body}"'
    )


@git.command()
@click.option("--target", default="main", help="Target branch")
@click.option(
    "--repo", type=click.Path(exists=True), default=".", help="Repository path"
)
def cleanup(target: str, repo: str):
    """Cleanup merged execution branches."""
    from pathlib import Path

    from paracle_git_workflows import BranchManager

    manager = BranchManager(Path(repo))
    count = manager.cleanup_merged_branches(target)

    console.print(f"[green]✓[/green] Cleaned up {count} merged branches")
