"""Paracle CLI - Command Line Interface."""

import click
from rich.console import Console

from paracle_cli.commands.a2a import a2a
from paracle_cli.commands.adr import adr
from paracle_cli.commands.agents import agents
from paracle_cli.commands.approvals import approvals
from paracle_cli.commands.audit import audit
from paracle_cli.commands.benchmark import benchmark
from paracle_cli.commands.board import board
from paracle_cli.commands.cache import cache
from paracle_cli.commands.compliance import compliance
from paracle_cli.commands.config import config
from paracle_cli.commands.conflicts import conflicts
from paracle_cli.commands.cost import cost
from paracle_cli.commands.errors import errors
from paracle_cli.commands.git import git
from paracle_cli.commands.governance import governance
from paracle_cli.commands.groups import groups
from paracle_cli.commands.ide import ide
from paracle_cli.commands.inventory import inventory
from paracle_cli.commands.logs import logs
from paracle_cli.commands.mcp import mcp
from paracle_cli.commands.meta import meta
from paracle_cli.commands.parac import init, parac, session, status, sync
from paracle_cli.commands.parac import validate as parac_validate
from paracle_cli.commands.pool import pool
from paracle_cli.commands.providers import providers
from paracle_cli.commands.release import release
from paracle_cli.commands.remote import remote
from paracle_cli.commands.retry import retry
from paracle_cli.commands.reviews import reviews
from paracle_cli.commands.roadmap import roadmap
from paracle_cli.commands.runs import runs_group
from paracle_cli.commands.sandbox import sandbox_group
from paracle_cli.commands.serve import serve
from paracle_cli.commands.task import task
from paracle_cli.commands.tools import tools
from paracle_cli.commands.tutorial import tutorial
from paracle_cli.commands.validate import validate as governance_validate
from paracle_cli.commands.workflow import workflow

console = Console()


@click.group()
@click.version_option(version="1.0.0")
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

# Interactive tutorial
cli.add_command(tutorial)

# API server
cli.add_command(serve)

# Agent management (includes run command)
cli.add_command(agents)

# Agent groups for multi-agent collaboration
cli.add_command(groups)

# IDE, MCP, and A2A integration
cli.add_command(ide)
cli.add_command(mcp)
cli.add_command(a2a)

# Paracle Meta AI Engine (system-level)
cli.add_command(meta)

# Workflow and tool management
cli.add_command(workflow)
cli.add_command(runs_group, name="runs")
cli.add_command(tools)
cli.add_command(providers)

# Cost tracking
cli.add_command(cost)

# Error management and monitoring
cli.add_command(errors)

# Cache management
cli.add_command(cache)

# Performance benchmarking
cli.add_command(benchmark)

# Connection pool management
cli.add_command(pool)

# Configuration management
cli.add_command(config)

# Remote development
cli.add_command(remote)

# Release management
cli.add_command(release)

# Human-in-the-loop approvals and reviews
cli.add_command(approvals)
cli.add_command(reviews)

# Retry management
cli.add_command(retry)

# Kanban task management
cli.add_command(task)
cli.add_command(board)

# Git integration and automatic commits
cli.add_command(git)

# Conflict resolution and file locking
cli.add_command(conflicts)

# Governance, Audit, and Compliance (ISO 42001)
cli.add_command(governance)
cli.add_command(audit)
cli.add_command(compliance)

# Project documentation
cli.add_command(adr)
cli.add_command(roadmap)
cli.add_command(logs)

# Services inventory management
cli.add_command(inventory)

# Sandbox management
cli.add_command(sandbox_group, name="sandbox")

# Legacy commands (hidden)
cli.add_command(parac)


@cli.command()
def hello() -> None:
    """Verify Paracle installation."""
    console.print("[bold green]Paracle v1.0.0[/bold green]")
    console.print("\n[cyan]Framework successfully installed![/cyan]")
    console.print("\nGet started:")
    console.print("  paracle init              - Initialize a project")
    console.print("  paracle agents list       - List available agents")
    console.print("  paracle agents run coder -t 'Fix bug'  - Run an agent")
    console.print("  paracle governance list   - List policies")
    console.print("  paracle compliance status - Check compliance")
    console.print("  paracle --help            - Show all commands")


if __name__ == "__main__":
    cli()
