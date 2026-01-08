"""Paracle Agent Communication Package.

This package provides multi-agent group collaboration capabilities,
combining A2A protocol concepts with ACP-inspired session management.

Features:
- Agent Groups: Define teams of agents that collaborate
- Communication Patterns: Peer-to-peer, broadcast, coordinator
- Session Management: Stateful conversations with history
- Message Types: FIPA-inspired performatives (inform, request, propose, etc.)
- Multimodal Content: Text, code, JSON, images, files
- External Integration: A2A bridge for external agents

Usage:
    from paracle_agent_comm import AgentGroup, GroupSession, GroupMessage
    from paracle_agent_comm.engine import GroupCollaborationEngine

    # Define a group
    group = AgentGroup(
        id="feature-team",
        name="Feature Development Team",
        members=["architect", "coder", "tester"],
        coordinator="architect",
        communication_pattern="coordinator",
    )

    # Run collaboration
    engine = GroupCollaborationEngine(group, agent_registry, event_bus)
    session = await engine.collaborate(goal="Design authentication system")

See ADR-025 for architectural details and protocol comparison.
"""

from paracle_agent_comm.exceptions import (
    AgentCommError,
    GroupNotFoundError,
    InvalidMessageError,
    MaxRoundsExceededError,
    SessionNotFoundError,
)
from paracle_agent_comm.models import (
    AgentGroup,
    CommunicationPattern,
    GroupMessage,
    GroupSession,
    MessagePart,
    MessageType,
)

__all__ = [
    # Models
    "AgentGroup",
    "GroupMessage",
    "GroupSession",
    "MessagePart",
    "MessageType",
    "CommunicationPattern",
    # Exceptions
    "AgentCommError",
    "GroupNotFoundError",
    "SessionNotFoundError",
    "InvalidMessageError",
    "MaxRoundsExceededError",
]
