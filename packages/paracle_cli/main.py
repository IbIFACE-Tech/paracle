"""Paracle CLI - Command Line Interface."""

import click
from rich.console import Console

from paracle_cli.commands.adr import adr
from paracle_cli.commands.agents import agents
from paracle_cli.commands.approvals import approvals
from paracle_cli.commands.cost import cost
from paracle_cli.commands.ide import ide
from paracle_cli.commands.logs import logs
from paracle_cli.commands.mcp import mcp
from paracle_cli.commands.parac import (
    init,
    parac,
    session,
    status,
    sync,
)
from paracle_cli.commands.parac import validate as parac_validate
from paracle_cli.commands.providers import providers
from paracle_cli.commands.release import release
from paracle_cli.commands.reviews import reviews
from paracle_cli.commands.roadmap import roadmap
from paracle_cli.commands.serve import serve
from paracle_cli.commands.tools import tools
from paracle_cli.commands.validate import validate as governance_validate
from paracle_cli.commands.workflow import workflow

console = Console()


@click.group()
@click.version_option(version="0.0.1")
def cli() -> None:
    """Paracle - User-driven multi-agent framework.

    Run AI-powered agents for code review, testing, documentation, and more.

    Quick start:
        paracle init              - Initialize a new project
        paracle agents list       - List available agents
        paracle agents run coder -t "Fix bug"  - Run an agent

    For more help: paracle <command> --help
    """
    pass


# Project governance commands
cli.add_command(init)
cli.add_command(status)
cli.add_command(sync)
cli.add_command(parac_validate, name="parac-validate")
cli.add_command(governance_validate, name="validate")
cli.add_command(session)

# API server
cli.add_command(serve)

# Agent management (includes run command)
cli.add_command(agents)

# IDE and MCP integration
cli.add_command(ide)
cli.add_command(mcp)

# Workflow and tool management
cli.add_command(workflow)
cli.add_command(tools)
cli.add_command(providers)

# Cost tracking
cli.add_command(cost)

# Release management
cli.add_command(release)

# Human-in-the-loop approvals and reviews
cli.add_command(approvals)
cli.add_command(reviews)

# Project documentation
cli.add_command(adr)
cli.add_command(roadmap)
cli.add_command(logs)

# Legacy commands (hidden)
cli.add_command(parac)


@cli.command()
def hello() -> None:
    """Verify Paracle installation."""
    console.print("[bold green]Paracle v0.0.1[/bold green]")
    console.print("\n[cyan]Framework successfully installed![/cyan]")
    console.print("\nGet started:")
    console.print("  paracle init              - Initialize a project")
    console.print("  paracle agents list       - List available agents")
    console.print("  paracle agents run coder -t 'Fix bug'  - Run an agent")
    console.print("  paracle --help            - Show all commands")


if __name__ == "__main__":
    cli()
