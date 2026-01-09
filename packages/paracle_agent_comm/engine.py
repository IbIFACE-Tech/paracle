"""Group Collaboration Engine.

Engine for running multi-agent group collaborations with
support for different communication patterns.

See ADR-025 for architectural details.
"""

import asyncio
from collections.abc import Callable
from datetime import datetime
from typing import Any, Protocol

from paracle_core.ids import generate_ulid

from paracle_agent_comm.exceptions import (
    AgentNotInGroupError,
    CoordinatorRequiredError,
    MaxMessagesExceededError,
    SessionTimeoutError,
)
from paracle_agent_comm.models import (
    AgentGroup,
    CommunicationPattern,
    GroupConfig,
    GroupMessage,
    GroupSession,
    GroupSessionStatus,
    GroupStatus,
    MessagePart,
    MessageType,
)


class AgentInterface(Protocol):
    """Protocol for agents that can participate in group collaboration."""

    @property
    def id(self) -> str:
        """Agent identifier."""
        ...

    async def respond_to_group(
        self,
        session: GroupSession,
        context: dict[str, Any],
    ) -> dict[str, Any]:
        """Generate a response in the context of a group collaboration.

        Args:
            session: Current group session with message history
            context: Additional context including goal, shared state

        Returns:
            Response dict with keys:
            - message: Optional[str] - Text response
            - message_type: Optional[MessageType] - Type of response
            - recipients: Optional[list[str]] - Target agents (None=broadcast)
            - update_context: Optional[dict] - Updates to shared context
            - artifacts: Optional[list[dict]] - Generated artifacts
        """
        ...


class AgentRegistryInterface(Protocol):
    """Protocol for agent registry."""

    async def get(self, agent_id: str) -> AgentInterface:
        """Get an agent by ID."""
        ...


class EventBusInterface(Protocol):
    """Protocol for event bus."""

    async def publish(self, event: dict[str, Any]) -> None:
        """Publish an event."""
        ...


class GroupCollaborationEngine:
    """Engine for running agent group collaborations.

    Supports three communication patterns:
    - Peer-to-peer: Any agent can message any other
    - Broadcast: All messages go to all agents
    - Coordinator: All messages go through a designated coordinator
    """

    def __init__(
        self,
        group: AgentGroup,
        agent_registry: AgentRegistryInterface,
        event_bus: EventBusInterface | None = None,
        config: GroupConfig | None = None,
    ):
        """Initialize the collaboration engine.

        Args:
            group: The agent group configuration
            agent_registry: Registry to fetch agent instances
            event_bus: Optional event bus for publishing events
            config: Optional collaboration configuration
        """
        self.group = group
        self.registry = agent_registry
        self.event_bus = event_bus
        self.config = config or GroupConfig()
        self._message_queue: asyncio.Queue[GroupMessage] = asyncio.Queue()

    async def collaborate(
        self,
        goal: str,
        initial_context: dict[str, Any] | None = None,
        termination_fn: Callable[[GroupSession], bool] | None = None,
    ) -> GroupSession:
        """Run a collaborative session until goal achieved or limits reached.

        Args:
            goal: The goal for the collaboration
            initial_context: Optional initial shared context
            termination_fn: Optional function to check if session should end

        Returns:
            GroupSession with full history and results

        Raises:
            MaxRoundsExceededError: If max rounds limit reached
            SessionTimeoutError: If session times out
            CoordinatorRequiredError: If coordinator pattern without coordinator
        """
        # Validate coordinator pattern
        if (
            self.group.communication_pattern == CommunicationPattern.COORDINATOR
            and not self.group.coordinator
        ):
            raise CoordinatorRequiredError(self.group.id)

        # Create session
        session = GroupSession(
            id=generate_ulid(),
            group_id=self.group.id,
            goal=goal,
            shared_context={
                **(self.group.default_context or {}),
                **(initial_context or {}),
            },
        )

        # Update group state
        self.group.status = GroupStatus.ACTIVE
        self.group.current_session_id = session.id

        # Emit start event
        await self._emit_event(
            "group.session.started",
            {
                "session_id": session.id,
                "group_id": self.group.id,
                "goal": goal,
            },
        )

        # Broadcast goal to all members
        await self._broadcast(
            session,
            text=f"Collaboration Goal: {goal}",
            message_type=MessageType.INFORM,
            sender="system",
        )

        try:
            # Run collaboration loop with timeout
            session = await asyncio.wait_for(
                self._run_collaboration_loop(session, termination_fn),
                timeout=self.group.timeout_seconds,
            )
        except asyncio.TimeoutError:
            session.status = GroupSessionStatus.TIMEOUT
            session.outcome = "Session timed out"
            raise SessionTimeoutError(session.id, self.group.timeout_seconds)
        finally:
            session.ended_at = datetime.utcnow()
            self.group.status = GroupStatus.IDLE
            self.group.current_session_id = None

            # Emit end event
            await self._emit_event(
                "group.session.ended",
                {
                    "session_id": session.id,
                    "group_id": self.group.id,
                    "status": session.status.value,
                    "rounds": session.round_count,
                    "messages": len(session.messages),
                },
            )

        return session

    async def _run_collaboration_loop(
        self,
        session: GroupSession,
        termination_fn: Callable[[GroupSession], bool] | None,
    ) -> GroupSession:
        """Run the main collaboration loop."""
        while session.round_count < self.group.max_rounds:
            session.round_count += 1

            # Emit round start event
            await self._emit_event(
                "group.round.started",
                {
                    "session_id": session.id,
                    "round": session.round_count,
                },
            )

            # Run agents based on communication pattern
            if self.group.communication_pattern == CommunicationPattern.COORDINATOR:
                await self._run_coordinator_round(session)
            else:
                await self._run_all_agents_round(session)

            # Check message limit
            if len(session.messages) >= self.group.max_messages:
                session.status = GroupSessionStatus.COMPLETED
                session.outcome = "Max messages reached"
                raise MaxMessagesExceededError(session.id, self.group.max_messages)

            # Check custom termination
            if termination_fn and termination_fn(session):
                session.status = GroupSessionStatus.COMPLETED
                session.outcome = "Termination condition met"
                break

            # Check for consensus (if configured)
            if self.config.require_consensus and session.has_consensus():
                session.status = GroupSessionStatus.COMPLETED
                session.outcome = "Consensus reached"
                break

        else:
            # Loop completed without early termination
            if session.status == GroupSessionStatus.ACTIVE:
                session.status = GroupSessionStatus.COMPLETED
                session.outcome = "Max rounds completed"

        return session

    async def _run_all_agents_round(self, session: GroupSession) -> None:
        """Run a round where all agents participate."""
        for agent_id in self.group.members:
            await self._agent_turn(session, agent_id)

    async def _run_coordinator_round(self, session: GroupSession) -> None:
        """Run a round managed by the coordinator."""
        coordinator_id = self.group.coordinator
        if not coordinator_id:
            return

        # Coordinator decides who speaks
        coordinator = await self.registry.get(coordinator_id)
        context = self._build_agent_context(session, coordinator_id)
        context["is_coordinator"] = True
        context["available_agents"] = [
            a for a in self.group.members if a != coordinator_id
        ]

        response = await coordinator.respond_to_group(session, context)

        # Process coordinator's response
        if response.get("message"):
            await self._add_message(
                session,
                sender=coordinator_id,
                text=response["message"],
                message_type=MessageType(response.get("type", "inform")),
                recipients=response.get("recipients"),
            )

        # Let coordinator-selected agent respond
        if response.get("delegate_to"):
            delegate_id = response["delegate_to"]
            if delegate_id in self.group.members:
                await self._agent_turn(session, delegate_id)

        # Update shared context
        if response.get("update_context"):
            session.shared_context.update(response["update_context"])

    async def _agent_turn(self, session: GroupSession, agent_id: str) -> None:
        """Give an agent a turn to respond."""
        if not self.group.validate_member(agent_id):
            raise AgentNotInGroupError(agent_id, self.group.id)

        agent = await self.registry.get(agent_id)
        context = self._build_agent_context(session, agent_id)

        # Get agent's response
        response = await agent.respond_to_group(session, context)

        # Process message
        if response.get("message"):
            await self._add_message(
                session,
                sender=agent_id,
                text=response["message"],
                message_type=MessageType(response.get("type", "inform")),
                recipients=response.get("recipients"),
            )

        # Process artifacts
        if response.get("artifacts"):
            session.artifacts.extend(response["artifacts"])

        # Update shared context
        if response.get("update_context"):
            session.shared_context.update(response["update_context"])

        # Emit turn event
        await self._emit_event(
            "group.agent.responded",
            {
                "session_id": session.id,
                "agent_id": agent_id,
                "message_type": response.get("type", "inform"),
            },
        )

    def _build_agent_context(
        self,
        session: GroupSession,
        agent_id: str,
    ) -> dict[str, Any]:
        """Build context for an agent's turn."""
        return {
            "goal": session.goal,
            "shared_context": session.shared_context,
            "recent_messages": session.get_recent_messages(10),
            "my_messages": session.get_messages_by_sender(agent_id),
            "round": session.round_count,
            "group_members": self.group.members,
            "communication_pattern": self.group.communication_pattern.value,
            "is_coordinator": self.group.is_coordinator(agent_id),
        }

    async def _broadcast(
        self,
        session: GroupSession,
        text: str,
        message_type: MessageType,
        sender: str,
    ) -> None:
        """Broadcast a message to all group members."""
        await self._add_message(
            session,
            sender=sender,
            text=text,
            message_type=message_type,
            recipients=None,  # Broadcast
        )

    async def _add_message(
        self,
        session: GroupSession,
        sender: str,
        text: str,
        message_type: MessageType,
        recipients: list[str] | None = None,
    ) -> GroupMessage:
        """Add a message to the session."""
        message = GroupMessage(
            group_id=self.group.id,
            sender=sender,
            recipients=recipients,
            content=[MessagePart.text(text)],
            message_type=message_type,
        )
        session.add_message(message)

        # Emit message event
        await self._emit_event(
            "group.message.sent",
            {
                "session_id": session.id,
                "message_id": message.id,
                "sender": sender,
                "type": message_type.value,
                "recipients": recipients,
            },
        )

        return message

    async def _emit_event(self, event_type: str, data: dict[str, Any]) -> None:
        """Emit an event to the event bus."""
        if self.event_bus:
            await self.event_bus.publish(
                {
                    "type": event_type,
                    "timestamp": datetime.utcnow().isoformat(),
                    **data,
                }
            )

    async def inject_human_message(
        self,
        session: GroupSession,
        text: str,
        message_type: MessageType = MessageType.INFORM,
    ) -> GroupMessage:
        """Inject a human message into an active session.

        Args:
            session: The active session
            text: Message text from human
            message_type: Type of message

        Returns:
            The created message
        """
        if not self.config.allow_human_injection:
            raise ValueError("Human message injection is not allowed")

        return await self._add_message(
            session,
            sender="human",
            text=text,
            message_type=message_type,
        )
