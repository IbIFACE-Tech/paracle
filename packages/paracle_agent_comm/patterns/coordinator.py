"""Coordinator Communication Pattern.

All messages flow through a designated coordinator agent (hub-spoke).
"""

from typing import Any

from paracle_agent_comm.models import (
    AgentGroup,
    GroupMessage,
    GroupSession,
    MessageType,
)


class CoordinatorPattern:
    """Coordinator (hub-spoke) communication pattern.

    All messages flow through a designated coordinator:
    - Non-coordinator agents can only message the coordinator
    - Coordinator can message anyone and delegate tasks
    - Coordinator decides turn order and workflow
    """

    def __init__(self, group: AgentGroup):
        """Initialize the pattern.

        Args:
            group: The agent group configuration

        Raises:
            ValueError: If group has no coordinator set
        """
        if not group.coordinator:
            raise ValueError(
                f"Group {group.id} uses coordinator pattern but has no coordinator"
            )
        self.group = group
        self.coordinator_id = group.coordinator

    def can_send_to(self, sender: str, recipient: str) -> bool:
        """Check if sender can send a message to recipient.

        Non-coordinators can only message the coordinator.
        Coordinator can message anyone.
        """
        if sender == self.coordinator_id:
            return self.group.validate_member(recipient)
        else:
            return recipient == self.coordinator_id

    def route_message(
        self,
        message: GroupMessage,
    ) -> list[str]:
        """Route message based on coordinator pattern.

        Args:
            message: The message to route

        Returns:
            List of recipients (just coordinator for non-coordinators)
        """
        if message.sender == self.coordinator_id:
            # Coordinator can message anyone
            if message.recipients:
                return [r for r in message.recipients if self.group.validate_member(r)]
            else:
                # Broadcast from coordinator
                return [m for m in self.group.members if m != self.coordinator_id]
        else:
            # Non-coordinators can only message coordinator
            return [self.coordinator_id]

    def get_agent_context(
        self,
        session: GroupSession,
        agent_id: str,
    ) -> dict[str, Any]:
        """Build context for an agent in coordinator mode.

        Args:
            session: Current session
            agent_id: The agent receiving context

        Returns:
            Context dictionary for the agent
        """
        is_coordinator = agent_id == self.coordinator_id

        if is_coordinator:
            return {
                "pattern": "coordinator",
                "is_coordinator": True,
                "can_message": self.group.members,
                "can_delegate_to": [
                    m for m in self.group.members if m != self.coordinator_id
                ],
                "can_broadcast": True,
                "pending_requests": self._get_pending_requests(session),
            }
        else:
            return {
                "pattern": "coordinator",
                "is_coordinator": False,
                "can_message": [self.coordinator_id],
                "coordinator": self.coordinator_id,
                "can_broadcast": False,
                "my_assignments": self._get_agent_assignments(session, agent_id),
            }

    def _get_pending_requests(self, session: GroupSession) -> list[GroupMessage]:
        """Get pending requests for the coordinator to process."""
        # Find REQUEST messages not yet responded to
        requests = [
            m
            for m in session.messages
            if m.message_type == MessageType.REQUEST and m.sender != self.coordinator_id
        ]

        # Filter out those with responses
        responded_ids = {
            m.in_reply_to
            for m in session.messages
            if m.in_reply_to and m.sender == self.coordinator_id
        }

        return [r for r in requests if r.id not in responded_ids]

    def _get_agent_assignments(
        self,
        session: GroupSession,
        agent_id: str,
    ) -> list[GroupMessage]:
        """Get assignments/delegations to a specific agent."""
        return [
            m
            for m in session.messages
            if m.sender == self.coordinator_id
            and m.message_type == MessageType.DELEGATE
            and (m.recipients is None or agent_id in m.recipients)
        ]
