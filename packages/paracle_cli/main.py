"""Paracle CLI - Command Line Interface."""

import click
from rich.console import Console

from paracle_cli.commands.adr import adr
from paracle_cli.commands.agent_run import run as agent_run
from paracle_cli.commands.agents import agents
from paracle_cli.commands.cost import cost
from paracle_cli.commands.ide import ide
from paracle_cli.commands.logs import logs
from paracle_cli.commands.parac import (
    init,
    parac,
    session,
    status,
    sync,
)
from paracle_cli.commands.parac import validate as parac_validate
from paracle_cli.commands.providers import providers
from paracle_cli.commands.roadmap import roadmap
from paracle_cli.commands.serve import serve
from paracle_cli.commands.tools import tools
from paracle_cli.commands.validate import validate as governance_validate
from paracle_cli.commands.workflow import workflow

console = Console()


@click.group()
@click.version_option(version="0.0.1")
def cli() -> None:
    """Paracle - User-driven multi-agent framework."""
    pass


# Register top-level governance commands (new API)
cli.add_command(init)
cli.add_command(status)
cli.add_command(sync)
# Old: paracle parac validate
cli.add_command(parac_validate, name="parac-validate")
# New: paracle validate
cli.add_command(governance_validate, name="validate")
cli.add_command(session)

# Register server command (Priority 0 - Essential)
cli.add_command(serve)

# Register domain command groups
cli.add_command(agents)
cli.add_command(ide)
cli.add_command(logs)

# Priority 1 CLI commands - Phase 4
cli.add_command(workflow)   # Workflow management (list, run, status, cancel)
cli.add_command(tools)      # Tool management (list, info, test, register)
cli.add_command(providers)  # Provider management (list, add, test, default)
cli.add_command(cost)       # Cost tracking and budget management

# File management commands
# ADR management (list, create, get, status, migrate)
cli.add_command(adr)
# Roadmap management (list, show, add, validate, sync)
cli.add_command(roadmap)

# Legacy compatibility (hidden, deprecated)
cli.add_command(parac)


@cli.command()
def hello() -> None:
    """Hello World command - Phase 0 validation."""
    console.print("[bold green]Paracle v0.0.1 - Hello World![/bold green]")
    console.print("\n[cyan]Framework successfully installed![/cyan]")
    console.print("\n[yellow]Phase 0: Foundation - Complete[/yellow]")
    console.print("\nNext steps:")
    console.print("  - paracle agents create   - Create a new agent")
    console.print("  - paracle status          - View project state")
    console.print("  - paracle --help          - Show all commands")


@cli.group()
def agent() -> None:
    """Manage and run individual agents."""
    pass


# Add agent run command
agent.add_command(agent_run)


@agent.command("create")
@click.argument("name")
def agent_create(name: str) -> None:
    """Create a new agent."""
    console.print(f"[green]Creating agent: {name}[/green]")
    console.print("[yellow]⚠️  Use 'paracle agents create' instead[/yellow]")


if __name__ == "__main__":
    cli()
