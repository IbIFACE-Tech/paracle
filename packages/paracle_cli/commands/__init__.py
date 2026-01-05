"""Paracle CLI Commands.

This module contains all CLI command groups:
- agents: Agent management (create, list, show, delete)
- workflow: Workflow management (list, run, status, cancel)
- tools: Tool management (list, info, test, register)
- providers: Provider management (list, add, test, default)
- ide: IDE integration (generate, sync)
- logs: Logging commands (recent, agent, clear)
- parac: Governance commands (init, status, sync, validate, session)
- serve: API server command
"""

from paracle_cli.commands.agents import agents
from paracle_cli.commands.ide import ide
from paracle_cli.commands.logs import logs
from paracle_cli.commands.parac import init, parac, session, status, sync, validate
from paracle_cli.commands.providers import providers
from paracle_cli.commands.serve import serve
from paracle_cli.commands.tools import tools
from paracle_cli.commands.workflow import workflow

__all__ = [
    # Command groups
    "agents",
    "ide",
    "logs",
    "parac",
    "providers",
    "serve",
    "tools",
    "workflow",
    # Top-level governance commands
    "init",
    "session",
    "status",
    "sync",
    "validate",
]
