"""Peer-to-Peer Communication Pattern.

Agents can send messages directly to any other agent in the group.
"""

from typing import Any

from paracle_agent_comm.models import AgentGroup, GroupMessage, GroupSession


class PeerToPeerPattern:
    """Peer-to-peer communication pattern.

    Any agent can send messages to any other agent in the group.
    Messages can be targeted to specific recipients or broadcast.
    """

    def __init__(self, group: AgentGroup):
        """Initialize the pattern.

        Args:
            group: The agent group configuration
        """
        self.group = group

    def can_send_to(self, sender: str, recipient: str) -> bool:
        """Check if sender can send a message to recipient.

        In peer-to-peer, any member can send to any other member.
        """
        return self.group.validate_member(sender) and self.group.validate_member(
            recipient
        )

    def route_message(
        self,
        message: GroupMessage,
    ) -> list[str]:
        """Determine the actual recipients for a message.

        Args:
            message: The message to route

        Returns:
            List of agent IDs that should receive the message
        """
        if message.recipients:
            # Targeted message - validate recipients
            return [
                r
                for r in message.recipients
                if self.group.validate_member(r) and r != message.sender
            ]
        else:
            # Broadcast - all members except sender
            return [m for m in self.group.members if m != message.sender]

    def get_agent_context(
        self,
        session: GroupSession,
        agent_id: str,
    ) -> dict[str, Any]:
        """Build context for an agent in peer-to-peer mode.

        Args:
            session: Current session
            agent_id: The agent receiving context

        Returns:
            Context dictionary for the agent
        """
        # Get messages directed to this agent
        directed_messages = [
            m
            for m in session.messages
            if m.recipients is None or agent_id in m.recipients
        ]

        return {
            "pattern": "peer-to-peer",
            "can_message": [m for m in self.group.members if m != agent_id],
            "messages_to_me": directed_messages,
            "can_broadcast": True,
        }
