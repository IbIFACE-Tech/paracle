"""Agent Action Logger.

Centralized logging for agent and system actions in .parac/memory/logs/.
Supports configurable log files via project.yaml file_management section.
"""

from datetime import datetime
from enum import Enum
from pathlib import Path
from typing import TYPE_CHECKING

from pydantic import BaseModel, Field

if TYPE_CHECKING:
    from paracle_core.parac.file_config import FileManagementConfig


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
    """Logger for agent actions in .parac/memory/logs/.

    Supports configurable log files via project.yaml file_management section.
    Backward compatible with hardcoded paths when no config is available.

    Example:
        >>> logger = AgentLogger()
        >>> logger.log(AgentType.CODER, ActionType.IMPLEMENTATION, "Added feature X")

        # With explicit config
        >>> config = FileManagementConfig.from_project_yaml(parac_root)
        >>> logger = AgentLogger(parac_root, config=config)

        # Log to custom log file
        >>> logger.log_to("security", "User authenticated", level="INFO")
    """

    def __init__(
        self,
        parac_root: Path | None = None,
        config: "FileManagementConfig | None" = None,
    ):
        """Initialize the logger.

        Args:
            parac_root: Path to .parac/ directory. If None, searches from cwd.
            config: Optional FileManagementConfig. If None, loads from project.yaml.
        """
        if parac_root is None:
            parac_root = self._find_parac_root()

        self.parac_root = parac_root

        # Load configuration
        if config is None:
            config = self._load_config()
        self.config = config

        # Initialize log file paths
        self.log_files: dict[str, Path] = {}
        self._init_log_files()

        # Legacy compatibility: keep direct references
        self.logs_dir = parac_root / (
            config.logs.base_path if config else "memory/logs"
        )
        self.actions_log = self.log_files.get(
            "actions", self.logs_dir / "agent_actions.log"
        )
        self.decisions_log = self.log_files.get(
            "decisions", self.logs_dir / "decisions.log"
        )

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

    def _load_config(self) -> "FileManagementConfig | None":
        """Load configuration from project.yaml."""
        try:
            from paracle_core.parac.file_config import FileManagementConfig

            return FileManagementConfig.from_project_yaml(self.parac_root)
        except (ImportError, FileNotFoundError):
            return None

    def _init_log_files(self) -> None:
        """Initialize all configured log files."""
        if self.config is None:
            # Fallback to hardcoded paths
            base = self.parac_root / "memory" / "logs"
            self.log_files = {
                "actions": base / "agent_actions.log",
                "decisions": base / "decisions.log",
            }
            return

        # Use configuration
        self.log_files = self.config.get_enabled_logs(self.parac_root)

    def _ensure_log_dir(self, log_path: Path) -> None:
        """Ensure parent directory exists for a log file."""
        log_path.parent.mkdir(parents=True, exist_ok=True)

    def log(
        self,
        agent: AgentType,
        action: ActionType,
        description: str,
        details: dict | None = None,
    ) -> LogEntry:
        """Log an action to the actions log.

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

        self._ensure_log_dir(self.actions_log)
        with open(self.actions_log, "a", encoding="utf-8") as f:
            f.write(log_line)

        return entry

    def log_to(
        self,
        log_name: str,
        message: str,
        level: str = "INFO",
        **kwargs,
    ) -> None:
        """Log to a specific log file by name.

        Args:
            log_name: Name of the log file (e.g., 'security', 'performance', 'risk').
            message: The message to log.
            level: Log level (INFO, WARNING, ERROR, etc.).
            **kwargs: Additional fields to include in structured logs.

        Raises:
            ValueError: If log_name is not configured or disabled.
        """
        if log_name not in self.log_files:
            available = list(self.log_files.keys())
            raise ValueError(
                f"Unknown or disabled log: '{log_name}'. "
                f"Available logs: {available}"
            )

        log_path = self.log_files[log_name]
        self._ensure_log_dir(log_path)

        # Get format from config
        format_str = "[{timestamp}] [{level}] {message}"
        if self.config:
            predefined = self.config.logs.predefined
            config_map = {
                "actions": predefined.actions,
                "decisions": predefined.decisions,
                "security": predefined.security,
                "performance": predefined.performance,
                "risk": predefined.risk,
            }
            if log_name in config_map:
                format_str = config_map[log_name].format or format_str
            else:
                # Check custom logs
                for custom in self.config.logs.custom:
                    if custom.name == log_name:
                        format_str = custom.format or format_str
                        break

        # Format the log line
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

        if format_str == "structured_json":
            import json

            log_data = {
                "timestamp": timestamp,
                "level": level,
                "message": message,
                **kwargs,
            }
            log_line = json.dumps(log_data) + "\n"
        else:
            # Simple format substitution
            log_line = format_str.format(
                timestamp=timestamp,
                level=level,
                message=message,
                **kwargs,
            )
            if not log_line.endswith("\n"):
                log_line += "\n"

        with open(log_path, "a", encoding="utf-8") as f:
            f.write(log_line)

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

        self._ensure_log_dir(self.decisions_log)
        with open(self.decisions_log, "a", encoding="utf-8") as f:
            f.write(log_line)

        # Also log to main actions log
        self.log(agent, ActionType.DECISION, decision)

        return entry

    def get_available_logs(self) -> list[str]:
        """Get list of available log file names.

        Returns:
            List of log names that can be used with log_to().
        """
        return list(self.log_files.keys())

    def get_log_path(self, log_name: str) -> Path | None:
        """Get the full path to a log file.

        Args:
            log_name: Name of the log file.

        Returns:
            Full path to the log file, or None if not found.
        """
        return self.log_files.get(log_name)

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

    def get_log_entries(
        self,
        log_name: str,
        count: int | None = None,
        since: datetime | None = None,
    ) -> list[str]:
        """Get entries from a specific log file.

        Args:
            log_name: Name of the log file.
            count: Optional limit on number of entries (from end).
            since: Optional datetime to filter entries after.

        Returns:
            List of log lines.
        """
        log_path = self.log_files.get(log_name)
        if log_path is None or not log_path.exists():
            return []

        with open(log_path, encoding="utf-8") as f:
            lines = f.readlines()

        # Filter by date if specified
        if since:
            since_str = since.strftime("%Y-%m-%d")
            lines = [line for line in lines if line >= f"[{since_str}"]

        # Limit count if specified
        if count:
            lines = lines[-count:]

        return lines


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


def log_to_custom(
    log_name: str,
    message: str,
    level: str = "INFO",
    **kwargs,
) -> None:
    """Convenience function to log to a custom log file.

    Args:
        log_name: Name of the log file (e.g., 'security', 'performance').
        message: The message to log.
        level: Log level (INFO, WARNING, ERROR, etc.).
        **kwargs: Additional fields for structured logs.
    """
    try:
        logger = get_logger()
        logger.log_to(log_name, message, level, **kwargs)
    except (FileNotFoundError, AttributeError, ValueError):
        # Silently fail if .parac/ not found or log not configured
        pass
