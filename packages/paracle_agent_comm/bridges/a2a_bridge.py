"""A2A Protocol Bridge.

Bridge for integrating external A2A-compatible agents into group collaborations.
Uses the existing paracle_a2a package for protocol handling.
"""

from typing import Any

from paracle_agent_comm.exceptions import ExternalAgentError
from paracle_agent_comm.models import (
    GroupMessage,
    GroupSession,
    MessagePart,
    MessagePartType,
    MessageType,
)


class A2ABridge:
    """Bridge between Paracle Agent Groups and A2A protocol.

    Enables external A2A-compatible agents to participate in
    group collaborations by translating between internal messages
    and A2A tasks.
    """

    def __init__(self, agent_url: str, api_key: str | None = None):
        """Initialize the A2A bridge.

        Args:
            agent_url: URL of the external A2A agent
            api_key: Optional API key for authentication
        """
        self.agent_url = agent_url
        self.api_key = api_key
        self._client: Any = None
        self._agent_card: Any = None

    async def initialize(self) -> None:
        """Initialize the bridge and discover agent capabilities."""
        try:
            from paracle_a2a.client import ParacleA2AClient
            from paracle_a2a.config import A2AClientConfig

            config = A2AClientConfig()
            if self.api_key:
                config.api_key = self.api_key

            self._client = ParacleA2AClient(self.agent_url, config)
            self._agent_card = await self._client.discover()

        except ImportError:
            raise ExternalAgentError(
                self.agent_url, "paracle_a2a package not installed"
            )
        except Exception as e:
            raise ExternalAgentError(self.agent_url, f"Failed to discover agent: {e}")

    @property
    def agent_id(self) -> str:
        """Get the external agent's ID (from Agent Card)."""
        if self._agent_card:
            return f"external:{self._agent_card.name}"
        return f"external:{self.agent_url}"

    @property
    def capabilities(self) -> dict[str, Any]:
        """Get the agent's capabilities from its Agent Card."""
        if not self._agent_card:
            return {}
        return {
            "name": self._agent_card.name,
            "description": self._agent_card.description,
            "skills": [s.name for s in (self._agent_card.skills or [])],
            "streaming": (
                self._agent_card.capabilities.streaming
                if self._agent_card.capabilities
                else False
            ),
        }

    async def send_message(
        self,
        session: GroupSession,
        message: GroupMessage,
    ) -> GroupMessage | None:
        """Send a message to the external agent and get response.

        Args:
            session: Current group session for context
            message: The message to send

        Returns:
            Response message from the external agent, or None

        Raises:
            ExternalAgentError: If communication fails
        """
        if not self._client:
            await self.initialize()

        try:
            # Convert GroupMessage to A2A format
            a2a_message = self._to_a2a_message(message, session)

            # Send via A2A client
            task = await self._client.invoke(
                a2a_message,
                context_id=session.id,
                wait=True,
            )

            # Convert response back to GroupMessage
            return self._from_a2a_task(task, session)

        except Exception as e:
            raise ExternalAgentError(self.agent_url, f"Failed to communicate: {e}")

    def _to_a2a_message(
        self,
        message: GroupMessage,
        session: GroupSession,
    ) -> str:
        """Convert GroupMessage to A2A message format.

        Args:
            message: The internal group message
            session: Current session for context

        Returns:
            Message string for A2A protocol
        """
        # Build context-rich message for the external agent
        parts = []

        # Add session context
        parts.append(f"[Group Collaboration: {session.goal}]")
        parts.append(f"[Round: {session.round_count}]")
        parts.append("")

        # Add recent conversation context
        recent = session.get_recent_messages(5)
        if recent:
            parts.append("Recent conversation:")
            for msg in recent:
                parts.append(f"  {msg.sender}: {msg.get_text_content()[:100]}")
            parts.append("")

        # Add the actual message
        parts.append(f"Message from {message.sender} ({message.message_type.value}):")
        parts.append(message.get_text_content())

        return "\n".join(parts)

    def _from_a2a_task(
        self,
        task: Any,
        session: GroupSession,
    ) -> GroupMessage | None:
        """Convert A2A task response to GroupMessage.

        Args:
            task: A2A Task response
            session: Current session

        Returns:
            GroupMessage or None if no response
        """
        from paracle_a2a.models import get_artifact_text

        # Check if task has artifacts (response content)
        if not task.artifacts:
            return None

        # Extract text from artifacts
        response_text = ""
        for artifact in task.artifacts:
            text = get_artifact_text(artifact)
            if text:
                response_text += text + "\n"

        if not response_text.strip():
            return None

        # Create GroupMessage from response
        return GroupMessage(
            group_id=session.group_id,
            sender=self.agent_id,
            content=[
                MessagePart(
                    type=MessagePartType.TEXT,
                    content=response_text.strip(),
                )
            ],
            message_type=MessageType.INFORM,  # Default to inform
            metadata={
                "source": "a2a",
                "task_id": task.id,
                "agent_url": self.agent_url,
            },
        )

    async def close(self) -> None:
        """Close the bridge connection."""
        self._client = None
        self._agent_card = None


class A2AAgentAdapter:
    """Adapter to make an A2ABridge work like a local agent.

    This allows external A2A agents to participate in group
    collaborations using the same interface as local agents.
    """

    def __init__(self, bridge: A2ABridge):
        """Initialize the adapter.

        Args:
            bridge: The A2A bridge to wrap
        """
        self.bridge = bridge

    @property
    def id(self) -> str:
        """Get the agent ID."""
        return self.bridge.agent_id

    async def respond_to_group(
        self,
        session: GroupSession,
        context: dict[str, Any],
    ) -> dict[str, Any]:
        """Generate a response as part of group collaboration.

        Args:
            session: Current group session
            context: Collaboration context

        Returns:
            Response dictionary with message and optional updates
        """
        # Create a message representing the current context
        context_message = GroupMessage.create(
            group_id=session.group_id,
            sender="system",
            text=f"Please respond to the group goal: {session.goal}",
            message_type=MessageType.REQUEST,
        )

        # Send to external agent
        response = await self.bridge.send_message(session, context_message)

        if response:
            return {
                "message": response.get_text_content(),
                "type": response.message_type.value,
                "metadata": response.metadata,
            }
        else:
            return {
                "message": None,
            }
