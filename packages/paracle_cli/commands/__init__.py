"""Paracle CLI Commands.

This module contains all CLI command groups:
- agents: Agent management (create, list, show, delete)
- groups: Agent group management (multi-agent collaboration)
- workflow: Workflow management (list, run, status, cancel)
- runs: Execution run management (list, get, replay, cleanup)
- tools: Tool management (list, info, test, register)
- providers: Provider management (list, add, test, default)
- ide: IDE integration (generate, sync)
- logs: Logging commands (recent, agent, clear)
- parac: Governance commands (init, status, sync, validate, session)
- governance: Policy management and risk scoring
- audit: Audit trail management and integrity verification
- compliance: ISO 42001 compliance reporting
- serve: API server command
"""

from paracle_cli.commands.agents import agents
from paracle_cli.commands.audit import audit
from paracle_cli.commands.cache import cache
from paracle_cli.commands.compliance import compliance
from paracle_cli.commands.governance import governance
from paracle_cli.commands.groups import groups
from paracle_cli.commands.ide import ide
from paracle_cli.commands.logs import logs
from paracle_cli.commands.meta import meta
from paracle_cli.commands.parac import init, parac, session, status, sync, validate
from paracle_cli.commands.pool import pool
from paracle_cli.commands.providers import providers
from paracle_cli.commands.runs import runs_group
from paracle_cli.commands.serve import serve
from paracle_cli.commands.tools import tools
from paracle_cli.commands.workflow import workflow

__all__ = [
    # Command groups
    "agents",
    "audit",
    "cache",
    "compliance",
    "governance",
    "groups",
    "ide",
    "logs",
    "meta",
    "parac",
    "pool",
    "providers",
    "runs_group",
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
