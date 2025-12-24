"""Paracle CLI - Command Line Interface."""

import click
from rich.console import Console

console = Console()


@click.group()
@click.version_option(version="0.0.1")
def cli() -> None:
    """Paracle - User-driven multi-agent framework."""
    pass


@cli.command()
def hello() -> None:
    """Hello World command - Phase 0 validation."""
    console.print("[bold green]🎉 Paracle v0.0.1 - Hello World![/bold green]")
    console.print("\n[cyan]Framework successfully installed![/cyan]")
    console.print("\n[yellow]Phase 0: Foundation ✅[/yellow]")
    console.print("\nNext steps:")
    console.print("  • paracle agent create    - Create a new agent")
    console.print("  • paracle workflow run    - Run a workflow")
    console.print("  • paracle --help          - Show all commands")


@cli.group()
def agent() -> None:
    """Manage agents."""
    pass


@agent.command("create")
@click.argument("name")
def agent_create(name: str) -> None:
    """Create a new agent."""
    console.print(f"[green]Creating agent: {name}[/green]")
    console.print("[yellow]⚠️  Agent creation coming in Phase 1[/yellow]")


@cli.group()
def workflow() -> None:
    """Manage workflows."""
    pass


@workflow.command("run")
@click.argument("name")
def workflow_run(name: str) -> None:
    """Run a workflow."""
    console.print(f"[green]Running workflow: {name}[/green]")
    console.print("[yellow]⚠️  Workflow execution coming in Phase 3[/yellow]")


if __name__ == "__main__":
    cli()
