"""Agent Communication Exceptions.

Custom exceptions for the agent communication package.
"""


class AgentCommError(Exception):
    """Base exception for agent communication errors.

    Error codes: PARACLE-COMM-XXX
    """

    def __init__(
        self,
        message: str,
        code: str = "PARACLE-COMM-000",
        details: dict | None = None,
    ):
        super().__init__(message)
        self.code = code
        self.details = details or {}


class GroupNotFoundError(AgentCommError):
    """Raised when a group cannot be found."""

    def __init__(self, group_id: str):
        super().__init__(
            f"Group not found: {group_id}",
            code="PARACLE-COMM-001",
            details={"group_id": group_id},
        )
        self.group_id = group_id


class SessionNotFoundError(AgentCommError):
    """Raised when a session cannot be found."""

    def __init__(self, session_id: str):
        super().__init__(
            f"Session not found: {session_id}",
            code="PARACLE-COMM-002",
            details={"session_id": session_id},
        )
        self.session_id = session_id


class InvalidMessageError(AgentCommError):
    """Raised when a message is invalid."""

    def __init__(self, message: str, reason: str):
        super().__init__(
            f"Invalid message: {reason}",
            code="PARACLE-COMM-003",
            details={"message": message, "reason": reason},
        )
        self.reason = reason


class MaxRoundsExceededError(AgentCommError):
    """Raised when max rounds limit is exceeded."""

    def __init__(self, group_id: str, max_rounds: int, current_round: int):
        super().__init__(
            f"Max rounds exceeded for group {group_id}: {current_round}/{max_rounds}",
            code="PARACLE-COMM-004",
            details={
                "group_id": group_id,
                "max_rounds": max_rounds,
                "current_round": current_round,
            },
        )
        self.max_rounds = max_rounds
        self.current_round = current_round


class MaxMessagesExceededError(AgentCommError):
    """Raised when max messages limit is exceeded."""

    def __init__(self, session_id: str, max_messages: int):
        super().__init__(
            f"Max messages exceeded for session {session_id}: {max_messages}",
            code="PARACLE-COMM-005",
            details={"session_id": session_id, "max_messages": max_messages},
        )
        self.max_messages = max_messages


class SessionTimeoutError(AgentCommError):
    """Raised when a session times out."""

    def __init__(self, session_id: str, timeout_seconds: float):
        super().__init__(
            f"Session {session_id} timed out after {timeout_seconds}s",
            code="PARACLE-COMM-006",
            details={"session_id": session_id, "timeout_seconds": timeout_seconds},
        )
        self.timeout_seconds = timeout_seconds


class AgentNotInGroupError(AgentCommError):
    """Raised when an agent is not a member of the group."""

    def __init__(self, agent_id: str, group_id: str):
        super().__init__(
            f"Agent {agent_id} is not a member of group {group_id}",
            code="PARACLE-COMM-007",
            details={"agent_id": agent_id, "group_id": group_id},
        )
        self.agent_id = agent_id
        self.group_id = group_id


class CoordinatorRequiredError(AgentCommError):
    """Raised when a coordinator is required but not set."""

    def __init__(self, group_id: str):
        super().__init__(
            f"Group {group_id} uses coordinator pattern but no coordinator is set",
            code="PARACLE-COMM-008",
            details={"group_id": group_id},
        )
        self.group_id = group_id


class ExternalAgentError(AgentCommError):
    """Raised when communication with external agent fails."""

    def __init__(self, agent_url: str, reason: str):
        super().__init__(
            f"External agent communication failed: {reason}",
            code="PARACLE-COMM-009",
            details={"agent_url": agent_url, "reason": reason},
        )
        self.agent_url = agent_url
        self.reason = reason
