"""Agent Action Logger.

Centralized logging for agent and system actions in .parac/memory/logs/.
"""

from datetime import datetime
from enum import Enum
from pathlib import Path

from pydantic import BaseModel, Field


class ActionType(str, Enum):
    """Types of actions that can be logged."""

    IMPLEMENTATION = "IMPLEMENTATION"
    TEST = "TEST"
    REVIEW = "REVIEW"
    DOCUMENTATION = "DOCUMENTATION"
    DECISION = "DECISION"
    PLANNING = "PLANNING"
    REFACTORING = "REFACTORING"
    BUGFIX = "BUGFIX"
    UPDATE = "UPDATE"
    SESSION = "SESSION"
    SYNC = "SYNC"
    VALIDATION = "VALIDATION"
    INIT = "INIT"


class AgentType(str, Enum):
    """Types of agents that can perform actions."""

    PM = "PMAgent"
    ARCHITECT = "ArchitectAgent"
    CODER = "CoderAgent"
    TESTER = "TesterAgent"
    REVIEWER = "ReviewerAgent"
    DOCUMENTER = "DocumenterAgent"
    SYSTEM = "SystemAgent"


class LogEntry(BaseModel):
    """A single log entry."""

    timestamp: datetime = Field(default_factory=datetime.now)
    agent: AgentType
    action: ActionType
    description: str
    details: dict | None = None


class DecisionEntry(BaseModel):
    """A decision log entry."""

    timestamp: datetime = Field(default_factory=datetime.now)
    agent: AgentType
    decision: str
    rationale: str
    impact: str


class AgentLogger:
    """Logger for agent actions in .parac/memory/logs/."""

    def __init__(self, parac_root: Path | None = None):
        """Initialize the logger.

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
        raise FileNotFoundError("Cannot find .parac/ directory")

    def log(
        self,
        agent: AgentType,
        action: ActionType,
        description: str,
        details: dict | None = None,
    ) -> LogEntry:
        """Log an action.

        Args:
            agent: The agent performing the action.
            action: The type of action.
            description: A brief description of what happened.
            details: Optional additional details.

        Returns:
            The created log entry.
        """
        entry = LogEntry(
            agent=agent,
            action=action,
            description=description,
            details=details,
        )

        timestamp_str = entry.timestamp.strftime("%Y-%m-%d %H:%M:%S")
        log_line = f"[{timestamp_str}] [{entry.agent.value}] [{entry.action.value}] {description}\n"

        with open(self.actions_log, "a", encoding="utf-8") as f:
            f.write(log_line)

        return entry

    def log_decision(
        self,
        agent: AgentType,
        decision: str,
        rationale: str,
        impact: str,
    ) -> DecisionEntry:
        """Log an important decision.

        Args:
            agent: The agent making the decision.
            decision: What was decided.
            rationale: Why this decision was made.
            impact: Expected impact of the decision.

        Returns:
            The created decision entry.
        """
        entry = DecisionEntry(
            agent=agent,
            decision=decision,
            rationale=rationale,
            impact=impact,
        )

        timestamp_str = entry.timestamp.strftime("%Y-%m-%d %H:%M:%S")
        log_line = f"[{timestamp_str}] [{entry.agent.value}] [DECISION] {decision} | {rationale} | {impact}\n"

        with open(self.decisions_log, "a", encoding="utf-8") as f:
            f.write(log_line)

        # Also log to main actions log
        self.log(agent, ActionType.DECISION, decision)

        return entry

    def get_recent_actions(self, count: int = 10) -> list[str]:
        """Get the N most recent actions.

        Args:
            count: Number of actions to retrieve.

        Returns:
            List of log lines.
        """
        if not self.actions_log.exists():
            return []

        with open(self.actions_log, encoding="utf-8") as f:
            lines = f.readlines()

        return lines[-count:]

    def get_agent_actions(self, agent: AgentType) -> list[str]:
        """Get all actions by a specific agent.

        Args:
            agent: The agent to filter by.

        Returns:
            List of log lines for that agent.
        """
        if not self.actions_log.exists():
            return []

        with open(self.actions_log, encoding="utf-8") as f:
            lines = f.readlines()

        return [line for line in lines if f"[{agent.value}]" in line]

    def get_today_actions(self) -> list[str]:
        """Get all actions from today.

        Returns:
            List of log lines from today.
        """
        if not self.actions_log.exists():
            return []

        today = datetime.now().strftime("%Y-%m-%d")

        with open(self.actions_log, encoding="utf-8") as f:
            lines = f.readlines()

        return [line for line in lines if line.startswith(f"[{today}")]


# Singleton instance for easy access
_logger: AgentLogger | None = None


def get_logger(parac_root: Path | None = None) -> AgentLogger:
    """Get or create the global logger instance.

    Args:
        parac_root: Optional path to .parac/ directory.

    Returns:
        The AgentLogger instance.
    """
    global _logger
    if _logger is None:
        try:
            _logger = AgentLogger(parac_root)
        except FileNotFoundError:
            # Return a no-op logger if .parac/ not found
            return AgentLogger.__new__(AgentLogger)
    return _logger


def log_action(
    action: ActionType,
    description: str,
    agent: AgentType = AgentType.SYSTEM,
    details: dict | None = None,
) -> LogEntry | None:
    """Convenience function to log an action.

    Args:
        action: The type of action.
        description: A brief description.
        agent: The agent (defaults to SystemAgent).
        details: Optional additional details.

    Returns:
        The log entry, or None if logging failed.
    """
    try:
        logger = get_logger()
        return logger.log(agent, action, description, details)
    except (FileNotFoundError, AttributeError):
        # Silently fail if .parac/ not found
        return None
