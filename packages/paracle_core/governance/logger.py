"""Governance Logger - Automatic logging to .parac/memory/logs/.

This module provides the core logging functionality for governance actions.
It writes to .parac/memory/logs/agent_actions.log and decisions.log.

The logger works automatically regardless of which AI assistant or IDE
is being used - it's built into the Paracle framework itself.

Key principle: Framework-level automatic logging, not AI-dependent.
"""

from __future__ import annotations

from datetime import datetime
from pathlib import Path
from typing import Any

from pydantic import BaseModel, Field

from paracle_core.governance.context import (
    AgentContext,
    SessionContext,
    get_current_agent,
    get_current_session,
)
from paracle_core.governance.types import GovernanceActionType, GovernanceAgentType


class GovernanceLogEntry(BaseModel):
    """A governance log entry."""

    timestamp: datetime = Field(default_factory=datetime.now)
    agent: GovernanceAgentType
    action: GovernanceActionType
    description: str
    session_id: str | None = None
    details: dict[str, Any] | None = None


class GovernanceDecisionEntry(BaseModel):
    """A governance decision entry."""

    timestamp: datetime = Field(default_factory=datetime.now)
    agent: GovernanceAgentType
    decision: str
    rationale: str
    impact: str
    session_id: str | None = None


class GovernanceLogger:
    """Logger for governance actions in .parac/memory/logs/.

    This logger is designed to work automatically within the Paracle
    framework, regardless of which AI assistant is being used.

    Log locations:
        - .parac/memory/logs/agent_actions.log - All actions
        - .parac/memory/logs/decisions.log - Important decisions

    Example:
        logger = get_governance_logger()

        # Simple logging
        logger.log(
            GovernanceActionType.IMPLEMENTATION,
            "Added user authentication"
        )

        # With agent context
        with logger.agent_context("CoderAgent"):
            logger.log(
                GovernanceActionType.TEST,
                "Added auth tests"
            )
    """

    _instance: GovernanceLogger | None = None

    def __init__(self, parac_root: Path | None = None):
        """Initialize the governance logger.

        Args:
            parac_root: Path to .parac/ directory. If None, searches from cwd.
        """
        if parac_root is None:
            parac_root = self._find_parac_root()

        self.parac_root = parac_root
        self.logs_dir = parac_root / "memory" / "logs"
        self.actions_log = self.logs_dir / "agent_actions.log"
        self.decisions_log = self.logs_dir / "decisions.log"

        # Ensure logs directory exists
        self.logs_dir.mkdir(parents=True, exist_ok=True)

    def _find_parac_root(self) -> Path:
        """Find .parac/ directory from current working directory."""
        current = Path.cwd()
        while current != current.parent:
            parac_dir = current / ".parac"
            if parac_dir.exists():
                return parac_dir
            current = current.parent
        raise FileNotFoundError(
            "Cannot find .parac/ directory. " "Run 'paracle init' to create one."
        )

    def log(
        self,
        action: GovernanceActionType | str,
        description: str,
        agent: GovernanceAgentType | str | None = None,
        details: dict[str, Any] | None = None,
    ) -> GovernanceLogEntry:
        """Log a governance action.

        Args:
            action: Type of action being logged
            description: Human-readable description
            agent: Agent performing the action (uses context if not provided)
            details: Optional additional details

        Returns:
            The created log entry
        """
        # Resolve action type
        if isinstance(action, str):
            action = GovernanceActionType(action)

        # Resolve agent (from param, context, or default)
        if agent is None:
            resolved_agent = get_current_agent()
        elif isinstance(agent, str):
            resolved_agent = GovernanceAgentType.from_string(agent)
        else:
            resolved_agent = agent

        # Create entry
        entry = GovernanceLogEntry(
            agent=resolved_agent,
            action=action,
            description=description,
            session_id=get_current_session(),
            details=details,
        )

        # Format log line
        timestamp_str = entry.timestamp.strftime("%Y-%m-%d %H:%M:%S")
        log_line = (
            f"[{timestamp_str}] [{entry.agent.value}] "
            f"[{entry.action.value}] {description}\n"
        )

        # Write to file
        with open(self.actions_log, "a", encoding="utf-8") as f:
            f.write(log_line)

        return entry

    def log_decision(
        self,
        decision: str,
        rationale: str,
        impact: str,
        agent: GovernanceAgentType | str | None = None,
    ) -> GovernanceDecisionEntry:
        """Log an important architectural or technical decision.

        Decisions are logged both to decisions.log and agent_actions.log.

        Args:
            decision: What was decided
            rationale: Why this decision was made
            impact: Expected impact of the decision
            agent: Agent making the decision

        Returns:
            The created decision entry
        """
        # Resolve agent
        if agent is None:
            resolved_agent = get_current_agent()
        elif isinstance(agent, str):
            resolved_agent = GovernanceAgentType.from_string(agent)
        else:
            resolved_agent = agent

        # Create entry
        entry = GovernanceDecisionEntry(
            agent=resolved_agent,
            decision=decision,
            rationale=rationale,
            impact=impact,
            session_id=get_current_session(),
        )

        # Format decision log line
        timestamp_str = entry.timestamp.strftime("%Y-%m-%d %H:%M:%S")
        decision_line = (
            f"[{timestamp_str}] [{entry.agent.value}] [DECISION] "
            f"{decision} | {rationale} | {impact}\n"
        )

        # Write to decisions log
        with open(self.decisions_log, "a", encoding="utf-8") as f:
            f.write(decision_line)

        # Also log to main actions log
        self.log(
            GovernanceActionType.DECISION,
            decision,
            agent=resolved_agent,
        )

        return entry

    def agent_context(self, agent: GovernanceAgentType | str) -> AgentContext:
        """Create an agent context for scoped logging.

        Args:
            agent: Agent type or name

        Returns:
            AgentContext for use with 'with' statement

        Example:
            with logger.agent_context("CoderAgent"):
                logger.log(GovernanceActionType.IMPLEMENTATION, "Added feature")
        """
        return AgentContext(agent)

    def session(
        self,
        description: str = "",
        agent: GovernanceAgentType | str | None = None,
    ) -> SessionContext:
        """Create a session context for scoped logging.

        Args:
            description: Session description
            agent: Optional agent for this session

        Returns:
            SessionContext for use with 'with' statement

        Example:
            with logger.session("Bug fix session"):
                logger.log(GovernanceActionType.BUGFIX, "Fixed issue")
        """
        return SessionContext(description, agent)

    def get_recent_actions(self, count: int = 10) -> list[str]:
        """Get the N most recent actions.

        Args:
            count: Number of actions to retrieve

        Returns:
            List of log lines
        """
        if not self.actions_log.exists():
            return []

        with open(self.actions_log, encoding="utf-8") as f:
            lines = f.readlines()

        return lines[-count:]

    def get_agent_actions(self, agent: GovernanceAgentType | str) -> list[str]:
        """Get all actions by a specific agent.

        Args:
            agent: Agent to filter by

        Returns:
            List of log lines for that agent
        """
        if not self.actions_log.exists():
            return []

        if isinstance(agent, str):
            agent = GovernanceAgentType.from_string(agent)

        with open(self.actions_log, encoding="utf-8") as f:
            lines = f.readlines()

        return [line for line in lines if f"[{agent.value}]" in line]

    def get_today_actions(self) -> list[str]:
        """Get all actions from today.

        Returns:
            List of log lines from today
        """
        if not self.actions_log.exists():
            return []

        today = datetime.now().strftime("%Y-%m-%d")

        with open(self.actions_log, encoding="utf-8") as f:
            lines = f.readlines()

        return [line for line in lines if line.startswith(f"[{today}")]


# Singleton instance
_governance_logger: GovernanceLogger | None = None


def get_governance_logger(parac_root: Path | None = None) -> GovernanceLogger:
    """Get or create the global governance logger instance.

    Args:
        parac_root: Optional path to .parac/ directory

    Returns:
        GovernanceLogger instance
    """
    global _governance_logger
    if _governance_logger is None:
        try:
            _governance_logger = GovernanceLogger(parac_root)
        except FileNotFoundError:
            # Return a no-op logger if .parac/ not found
            # This prevents errors when running outside a Paracle project
            return _create_noop_logger()
    return _governance_logger


def _create_noop_logger() -> GovernanceLogger:
    """Create a no-op logger when .parac/ doesn't exist."""
    logger = object.__new__(GovernanceLogger)
    logger.parac_root = None
    logger.logs_dir = None
    logger.actions_log = None
    logger.decisions_log = None
    return logger


def reset_governance_logger() -> None:
    """Reset global governance logger instance.

    Useful for testing to ensure clean state between tests.
    """
    global _governance_logger
    _governance_logger = None


def log_action(
    action: GovernanceActionType | str,
    description: str,
    agent: GovernanceAgentType | str | None = None,
    details: dict[str, Any] | None = None,
) -> GovernanceLogEntry | None:
    """Convenience function to log a governance action.

    This function automatically logs to .parac/memory/logs/agent_actions.log.
    It uses the current agent context if no agent is specified.

    Args:
        action: Type of action
        description: Human-readable description
        agent: Optional agent (uses context if not provided)
        details: Optional additional details

    Returns:
        Log entry, or None if logging failed

    Example:
        # Simple usage
        log_action("IMPLEMENTATION", "Added user model")

        # With agent context
        with agent_context("CoderAgent"):
            log_action("TEST", "Added user model tests")
    """
    try:
        logger = get_governance_logger()
        if logger.actions_log is None:
            return None
        return logger.log(action, description, agent, details)
    except (FileNotFoundError, AttributeError):
        return None


def log_decision(
    decision: str,
    rationale: str,
    impact: str,
    agent: GovernanceAgentType | str | None = None,
) -> GovernanceDecisionEntry | None:
    """Convenience function to log a governance decision.

    This function logs to both .parac/memory/logs/decisions.log and
    agent_actions.log.

    Args:
        decision: What was decided
        rationale: Why this decision was made
        impact: Expected impact
        agent: Optional agent

    Returns:
        Decision entry, or None if logging failed

    Example:
        log_decision(
            "Use PostgreSQL for production",
            "Better scalability than SQLite",
            "Requires Docker setup for development"
        )
    """
    try:
        logger = get_governance_logger()
        if logger.decisions_log is None:
            return None
        return logger.log_decision(decision, rationale, impact, agent)
    except (FileNotFoundError, AttributeError):
        return None
