"""Agent Communication Models.

Defines the core data models for agent group collaboration,
combining A2A protocol concepts with ACP-inspired session management.

See ADR-025 for architectural details.
"""

from datetime import datetime
from enum import Enum
from typing import Any, Literal

from paracle_core.ids import generate_ulid
from pydantic import BaseModel, Field


class CommunicationPattern(str, Enum):
    """Communication patterns for agent groups."""

    PEER_TO_PEER = "peer-to-peer"  # Any agent can message any other
    BROADCAST = "broadcast"  # All messages go to all agents
    COORDINATOR = "coordinator"  # All messages go through coordinator


class MessageType(str, Enum):
    """Message types (FIPA-inspired performatives).

    These define the intent of a message in agent communication.
    """

    INFORM = "inform"  # Share information
    REQUEST = "request"  # Ask to perform action
    PROPOSE = "propose"  # Suggest approach
    ACCEPT = "accept"  # Accept proposal
    REJECT = "reject"  # Reject with reason
    QUERY = "query"  # Ask question
    DELEGATE = "delegate"  # Hand off to another agent
    CONFIRM = "confirm"  # Confirm understanding
    CANCEL = "cancel"  # Cancel previous request


class MessagePartType(str, Enum):
    """Types of content parts in a message."""

    TEXT = "text"
    CODE = "code"
    JSON = "json"
    IMAGE = "image"
    FILE = "file"


class MessagePart(BaseModel):
    """Single part of a message (ACP-inspired multimodal support).

    Allows messages to contain multiple content types like text,
    code snippets, JSON data, images, or file references.
    """

    type: MessagePartType = MessagePartType.TEXT
    content: str | dict | bytes = ""
    mime_type: str = "text/plain"
    metadata: dict[str, Any] = Field(default_factory=dict)

    # Optional metadata for specific types
    language: str | None = None  # For code parts
    filename: str | None = None  # For file parts

    @classmethod
    def text(cls, content: str) -> "MessagePart":
        """Create a text message part."""
        return cls(type=MessagePartType.TEXT, content=content)

    @classmethod
    def code(cls, content: str, language: str = "python") -> "MessagePart":
        """Create a code message part."""
        return cls(
            type=MessagePartType.CODE,
            content=content,
            language=language,
            mime_type=f"text/x-{language}",
        )

    @classmethod
    def json_data(cls, content: dict) -> "MessagePart":
        """Create a JSON data message part."""
        return cls(
            type=MessagePartType.JSON,
            content=content,
            mime_type="application/json",
        )


class GroupMessage(BaseModel):
    """Message exchanged within an agent group.

    Combines A2A message structure with FIPA-inspired performatives
    for rich agent-to-agent communication.
    """

    id: str = Field(default_factory=generate_ulid)
    group_id: str

    # Routing
    sender: str  # Agent ID or "system"
    recipients: list[str] | None = None  # None = broadcast to all

    # Content (ACP-inspired multimodal)
    content: list[MessagePart] = Field(default_factory=list)

    # Threading
    conversation_id: str = Field(default_factory=generate_ulid)
    in_reply_to: str | None = None

    # Message type (FIPA-inspired performatives)
    message_type: MessageType = MessageType.INFORM

    # Metadata
    priority: Literal["low", "normal", "high"] = "normal"
    timestamp: datetime = Field(default_factory=datetime.utcnow)
    metadata: dict[str, Any] = Field(default_factory=dict)

    # Execution hints
    expects_reply: bool = False
    timeout_seconds: float | None = None

    def get_text_content(self) -> str:
        """Get concatenated text content from all text parts."""
        texts = []
        for part in self.content:
            if part.type == MessagePartType.TEXT:
                texts.append(str(part.content))
        return "\n".join(texts)

    @classmethod
    def create(
        cls,
        group_id: str,
        sender: str,
        text: str,
        message_type: MessageType = MessageType.INFORM,
        recipients: list[str] | None = None,
        in_reply_to: str | None = None,
    ) -> "GroupMessage":
        """Create a simple text message."""
        return cls(
            group_id=group_id,
            sender=sender,
            recipients=recipients,
            content=[MessagePart.text(text)],
            message_type=message_type,
            in_reply_to=in_reply_to,
        )


class GroupSessionStatus(str, Enum):
    """Status of a group collaboration session."""

    ACTIVE = "active"
    PAUSED = "paused"
    COMPLETED = "completed"
    FAILED = "failed"
    TIMEOUT = "timeout"


class GroupSession(BaseModel):
    """Stateful session for group collaboration (ACP-inspired).

    Maintains the full context of a collaborative session including
    message history, shared state, and results.
    """

    id: str = Field(default_factory=generate_ulid)
    group_id: str
    goal: str

    # Message history
    messages: list[GroupMessage] = Field(default_factory=list)

    # State
    status: GroupSessionStatus = GroupSessionStatus.ACTIVE
    round_count: int = 0

    # Shared context across all agents
    shared_context: dict[str, Any] = Field(default_factory=dict)

    # Results
    outcome: str | None = None
    artifacts: list[dict[str, Any]] = Field(default_factory=list)

    # Timestamps
    started_at: datetime = Field(default_factory=datetime.utcnow)
    ended_at: datetime | None = None

    # Metrics
    total_tokens: int = 0
    estimated_cost: float = 0.0

    def add_message(self, message: GroupMessage) -> None:
        """Add a message to the session history."""
        self.messages.append(message)

    def get_recent_messages(self, count: int = 10) -> list[GroupMessage]:
        """Get the most recent messages."""
        return self.messages[-count:] if self.messages else []

    def get_messages_by_sender(self, sender: str) -> list[GroupMessage]:
        """Get all messages from a specific sender."""
        return [m for m in self.messages if m.sender == sender]

    def get_messages_by_type(self, message_type: MessageType) -> list[GroupMessage]:
        """Get all messages of a specific type."""
        return [m for m in self.messages if m.message_type == message_type]

    def has_consensus(self) -> bool:
        """Check if all agents have accepted (simple consensus check).

        Consensus is reached when:
        1. There is at least one proposal
        2. All participants (except the proposer) have accepted after the proposal
        """
        if not self.messages:
            return False

        # Get unique participants (excluding system)
        participants = {m.sender for m in self.messages if m.sender != "system"}

        # Check if there's a recent proposal and all accepted
        proposals = self.get_messages_by_type(MessageType.PROPOSE)
        if not proposals:
            return False

        last_proposal = proposals[-1]
        proposer = last_proposal.sender

        # Get accepts after the last proposal
        accepts_after = [
            m
            for m in self.messages
            if m.message_type == MessageType.ACCEPT
            and m.timestamp >= last_proposal.timestamp
        ]

        acceptors = {m.sender for m in accepts_after}

        # All participants except the proposer must have accepted
        required_acceptors = participants - {proposer}
        return required_acceptors <= acceptors


class GroupStatus(str, Enum):
    """Status of an agent group."""

    IDLE = "idle"
    ACTIVE = "active"
    COMPLETED = "completed"
    FAILED = "failed"


class AgentGroup(BaseModel):
    """A group of agents that collaborate on a shared goal.

    Defines the team composition and communication rules for
    multi-agent collaboration sessions.
    """

    id: str = Field(default_factory=generate_ulid)
    name: str
    description: str | None = None

    # Members
    members: list[str]  # Agent IDs
    coordinator: str | None = None  # Optional coordinator agent

    # Communication settings
    communication_pattern: CommunicationPattern = CommunicationPattern.PEER_TO_PEER

    # Session limits (prevent runaway costs)
    max_rounds: int = 10
    max_messages: int = 100
    timeout_seconds: float = 300.0  # 5 minutes default

    # State
    status: GroupStatus = GroupStatus.IDLE
    current_session_id: str | None = None

    # Shared context template (initial context for sessions)
    default_context: dict[str, Any] = Field(default_factory=dict)

    # Timestamps
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)

    # External agent integration (A2A)
    external_members: list[dict[str, str]] = Field(default_factory=list)

    def validate_member(self, agent_id: str) -> bool:
        """Check if an agent is a member of this group."""
        return agent_id in self.members or agent_id == "system"

    def is_coordinator(self, agent_id: str) -> bool:
        """Check if an agent is the coordinator."""
        return self.coordinator == agent_id

    def get_member_count(self) -> int:
        """Get the total number of members including external."""
        return len(self.members) + len(self.external_members)


class GroupConfig(BaseModel):
    """Configuration for group collaboration behavior."""

    # Termination conditions
    require_consensus: bool = False
    require_all_participants: bool = True
    min_rounds: int = 1

    # Cost control
    max_tokens_per_round: int = 10000
    max_cost_per_session: float = 10.0  # USD

    # Behavior
    allow_delegation: bool = True
    allow_human_injection: bool = True
    record_reasoning: bool = True

    # Retry settings
    retry_on_failure: bool = True
    max_retries: int = 3
