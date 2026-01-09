"""Paracle CLI - Command Line Interface.

This package provides the Click-based CLI for Paracle:
- Project initialization and governance (init, status, sync, validate)
- Agent management (agents create, list, show)
- Workflow management (workflow list, run, status, cancel)
- Tool management (tools list, info, test, register)
- Provider management (providers list, add, test)
- API server (serve)
- IDE integration (ide generate, sync)
- Logging (logs recent, agent, clear)
- AI-powered generation (generate agent, skill, workflow, docs) - optional

Usage:
    paracle --help
    paracle init
    paracle agents list
    paracle workflow run my-workflow
    paracle generate agent "description"  # Requires AI provider
"""

from paracle_cli.main import cli

__version__ = "1.0.1"

__all__ = [
    "cli",
]
