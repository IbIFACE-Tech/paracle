"""Broadcast Communication Pattern.

All messages are sent to all agents in the group.
"""

from typing import Any

from paracle_agent_comm.models import AgentGroup, GroupMessage, GroupSession


class BroadcastPattern:
    """Broadcast communication pattern.

    All messages are automatically sent to all group members.
    No direct messaging - everything is public to the group.
    """

    def __init__(self, group: AgentGroup):
        """Initialize the pattern.

        Args:
            group: The agent group configuration
        """
        self.group = group

    def route_message(
        self,
        message: GroupMessage,
    ) -> list[str]:
        """Route message to all group members.

        In broadcast mode, all messages go to everyone (except sender).

        Args:
            message: The message to route

        Returns:
            List of all members except sender
        """
        return [m for m in self.group.members if m != message.sender]

    def get_agent_context(
        self,
        session: GroupSession,
        agent_id: str,
    ) -> dict[str, Any]:
        """Build context for an agent in broadcast mode.

        Args:
            session: Current session
            agent_id: The agent receiving context

        Returns:
            Context dictionary for the agent
        """
        return {
            "pattern": "broadcast",
            "all_messages_visible": True,
            "can_message": None,  # Cannot direct message
            "can_broadcast": True,
        }
