"""Governance context management.

Provides context managers for tracking which agent is active
and session boundaries. This enables automatic logging of
actions to .parac/memory/logs/.
"""

from __future__ import annotations

import contextvars
from collections.abc import Generator
from contextlib import contextmanager
from datetime import datetime
from typing import Any
from uuid import uuid4

from paracle_core.governance.types import GovernanceAgentType

# Context variables for tracking current state
_current_agent: contextvars.ContextVar[GovernanceAgentType | None] = (
    contextvars.ContextVar("governance_agent", default=None)
)
_current_session: contextvars.ContextVar[str | None] = contextvars.ContextVar(
    "governance_session", default=None
)
_session_start: contextvars.ContextVar[datetime | None] = contextvars.ContextVar(
    "session_start", default=None
)


class AgentContext:
    """Context for agent-scoped operations.

    When entering an agent context, all logged actions will be
    attributed to that agent.

    Example:
        with AgentContext(GovernanceAgentType.CODER):
            log_action(GovernanceActionType.IMPLEMENTATION, "Added feature")
            # Logged as: [TIMESTAMP] [CoderAgent] [IMPLEMENTATION] Added feature
    """

    def __init__(self, agent: GovernanceAgentType | str):
        """Initialize agent context.

        Args:
            agent: Agent type or name string
        """
        if isinstance(agent, str):
            self.agent = GovernanceAgentType.from_string(agent)
        else:
            self.agent = agent
        self._token: contextvars.Token | None = None
        self._previous: GovernanceAgentType | None = None

    def __enter__(self) -> AgentContext:
        """Enter agent context."""
        self._previous = _current_agent.get()
        self._token = _current_agent.set(self.agent)
        return self

    def __exit__(self, exc_type: Any, exc_val: Any, exc_tb: Any) -> None:
        """Exit agent context."""
        if self._token is not None:
            _current_agent.reset(self._token)


class SessionContext:
    """Context for session-scoped operations.

    A session represents a unit of work (e.g., implementing a feature,
    fixing a bug). Sessions are logged in .parac/memory/logs/.

    Example:
        with SessionContext("Implementing user authentication"):
            # Session start logged
            log_action(GovernanceActionType.IMPLEMENTATION, "Added auth models")
            log_action(GovernanceActionType.TEST, "Added auth tests")
            # Session end logged on exit
    """

    def __init__(
        self,
        description: str = "",
        agent: GovernanceAgentType | str | None = None,
    ):
        """Initialize session context.

        Args:
            description: Session description
            agent: Optional agent for this session
        """
        self.description = description
        self.session_id = str(uuid4())[:8]
        self._agent_ctx: AgentContext | None = None
        self._session_token: contextvars.Token | None = None
        self._start_token: contextvars.Token | None = None
        self.start_time: datetime | None = None

        if agent is not None:
            if isinstance(agent, str):
                self._agent_ctx = AgentContext(GovernanceAgentType.from_string(agent))
            else:
                self._agent_ctx = AgentContext(agent)

    def __enter__(self) -> SessionContext:
        """Enter session context."""
        self.start_time = datetime.now()
        self._session_token = _current_session.set(self.session_id)
        self._start_token = _session_start.set(self.start_time)

        if self._agent_ctx:
            self._agent_ctx.__enter__()

        return self

    def __exit__(self, exc_type: Any, exc_val: Any, exc_tb: Any) -> None:
        """Exit session context."""
        if self._agent_ctx:
            self._agent_ctx.__exit__(exc_type, exc_val, exc_tb)

        if self._session_token is not None:
            _current_session.reset(self._session_token)
        if self._start_token is not None:
            _session_start.reset(self._start_token)

    @property
    def duration_seconds(self) -> float | None:
        """Get session duration in seconds."""
        if self.start_time is None:
            return None
        return (datetime.now() - self.start_time).total_seconds()


def get_current_agent() -> GovernanceAgentType:
    """Get the current agent from context, defaulting to SYSTEM."""
    return _current_agent.get() or GovernanceAgentType.SYSTEM


def get_current_session() -> str | None:
    """Get the current session ID from context."""
    return _current_session.get()


def get_session_start() -> datetime | None:
    """Get the current session start time."""
    return _session_start.get()


@contextmanager
def agent_context(
    agent: GovernanceAgentType | str,
) -> Generator[AgentContext, None, None]:
    """Context manager for setting the current agent.

    Args:
        agent: Agent type or name

    Yields:
        AgentContext instance

    Example:
        with agent_context("CoderAgent"):
            log_action(GovernanceActionType.IMPLEMENTATION, "Added feature")
    """
    ctx = AgentContext(agent)
    with ctx:
        yield ctx


@contextmanager
def session_context(
    description: str = "",
    agent: GovernanceAgentType | str | None = None,
) -> Generator[SessionContext, None, None]:
    """Context manager for session tracking.

    Args:
        description: Session description
        agent: Optional agent for this session

    Yields:
        SessionContext instance

    Example:
        with session_context("Bug fix session", agent="CoderAgent"):
            log_action(GovernanceActionType.BUGFIX, "Fixed null pointer")
    """
    ctx = SessionContext(description, agent)
    with ctx:
        yield ctx
