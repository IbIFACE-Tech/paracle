"""Paracle Governance - Automatic .parac/ logging and tracking.

This module provides automatic governance logging that works regardless
of which AI assistant or IDE is being used. It integrates with the
framework to ensure all actions are logged to .parac/memory/logs/.

The key principle: "Declare once in .parac/, use everywhere."

Usage:
    from paracle_core.governance import governance_logger, log_action

    # Automatic logging for any action
    log_action("IMPLEMENTATION", "Added new feature X")

    # With specific agent context
    with governance_logger.agent_context("CoderAgent"):
        log_action("REFACTORING", "Improved error handling")

    # Automatic session tracking
    with governance_logger.session():
        # All actions within this session are logged
        ...
"""

from paracle_core.governance.context import (
    AgentContext,
    SessionContext,
    agent_context,
    session_context,
)
from paracle_core.governance.logger import (
    GovernanceLogger,
    get_governance_logger,
    log_action,
    log_decision,
)
from paracle_core.governance.types import (
    GovernanceActionType,
    GovernanceAgentType,
)

__all__ = [
    # Logger
    "GovernanceLogger",
    "get_governance_logger",
    "log_action",
    "log_decision",
    # Context
    "AgentContext",
    "SessionContext",
    "agent_context",
    "session_context",
    # Types
    "GovernanceActionType",
    "GovernanceAgentType",
]
