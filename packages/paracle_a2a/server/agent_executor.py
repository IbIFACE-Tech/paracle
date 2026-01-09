"""Agent Executor.

Bridges A2A protocol to Paracle agent execution.
"""

import asyncio
from pathlib import Path
from typing import Any

from paracle_a2a.exceptions import AgentNotFoundError
from paracle_a2a.models import Artifact, Message, Task, TaskState, TextPart
from paracle_a2a.server.event_queue import TaskEventQueue
from paracle_a2a.server.task_manager import TaskManager


class ParacleA2AExecutor:
    """Executes Paracle agents via A2A protocol.

    Bridges between A2A Tasks/Messages and Paracle's
    agent execution model.
    """

    def __init__(
        self,
        parac_root: Path,
        task_manager: TaskManager,
        event_queue: TaskEventQueue | None = None,
    ):
        """Initialize executor.

        Args:
            parac_root: Path to .parac directory
            task_manager: Task manager instance
            event_queue: Optional event queue for streaming
        """
        self.parac_root = Path(parac_root)
        self.task_manager = task_manager
        self.event_queue = event_queue

        # Cache of loaded agents
        self._agents: dict[str, Any] = {}
        self._lock = asyncio.Lock()

    async def get_agent(self, agent_id: str) -> Any:
        """Get or load an agent.

        Args:
            agent_id: Agent identifier

        Returns:
            Agent instance (placeholder for now)

        Raises:
            AgentNotFoundError: If agent not found
        """
        async with self._lock:
            if agent_id in self._agents:
                return self._agents[agent_id]

            # Check if agent spec exists
            spec_path = self.parac_root / "agents" / "specs" / f"{agent_id}.md"
            if not spec_path.exists():
                raise AgentNotFoundError(agent_id)

            # Placeholder - actual agent loading would integrate with
            # paracle_orchestration engine
            self._agents[agent_id] = {
                "id": agent_id,
                "spec_path": spec_path,
            }

            return self._agents[agent_id]

    async def execute_task(
        self,
        agent_id: str,
        task: Task,
        messages: list[Message],
    ) -> Task:
        """Execute a task with an agent.

        Args:
            agent_id: Target agent ID
            task: Task to execute
            messages: Task messages

        Returns:
            Updated Task with results
        """
        # Get agent
        agent = await self.get_agent(agent_id)

        # Update to working state
        await self.task_manager.update_status(
            task_id=task.id,
            state=TaskState.WORKING,
            message=f"Processing with agent {agent_id}",
        )

        try:
            # Extract text from messages
            prompt = self._extract_prompt(messages)

            # Execute agent (placeholder implementation)
            # In real implementation, this would call:
            # - paracle_orchestration.engine.execute()
            # - or the agent's specific provider
            result = await self._execute_agent(agent_id, agent, prompt, task)

            # Create artifact with result
            artifact = Artifact.from_text(
                text=result,
                name="response",
                artifact_type="text",
            )
            await self.task_manager.add_artifact(task.id, artifact)

            # Add agent response message
            response_message = Message(
                role="agent",
                parts=[TextPart(text=result)],
            )
            await self.task_manager.add_message(task.id, response_message)

            # Mark completed
            await self.task_manager.update_status(
                task_id=task.id,
                state=TaskState.COMPLETED,
                message="Task completed successfully",
            )

        except Exception as e:
            # Mark failed
            await self.task_manager.update_status(
                task_id=task.id,
                state=TaskState.FAILED,
                message=str(e),
                error={"type": type(e).__name__, "message": str(e)},
            )

        return await self.task_manager.get_task(task.id)

    async def execute_task_streaming(
        self,
        agent_id: str,
        task: Task,
        messages: list[Message],
    ) -> Task:
        """Execute a task with streaming.

        Args:
            agent_id: Target agent ID
            task: Task to execute
            messages: Task messages

        Returns:
            Updated Task
        """
        # Get agent
        agent = await self.get_agent(agent_id)

        # Update to working state
        await self.task_manager.update_status(
            task_id=task.id,
            state=TaskState.WORKING,
            message=f"Processing with agent {agent_id}",
        )

        try:
            prompt = self._extract_prompt(messages)

            # Execute with streaming
            full_response = ""
            chunk_index = 0

            async for chunk in self._execute_agent_streaming(
                agent_id, agent, prompt, task
            ):
                full_response += chunk

                # Create streaming artifact
                artifact = Artifact(
                    name="response",
                    artifact_type="text",
                    parts=[TextPart(text=chunk)],
                    index=chunk_index,
                    append=chunk_index > 0,
                    last_chunk=False,
                )
                await self.task_manager.add_artifact(task.id, artifact)
                chunk_index += 1

            # Final artifact
            artifact = Artifact(
                name="response",
                artifact_type="text",
                parts=[TextPart(text="")],
                index=chunk_index,
                append=True,
                last_chunk=True,
            )
            await self.task_manager.add_artifact(task.id, artifact)

            # Add complete response message
            response_message = Message(
                role="agent",
                parts=[TextPart(text=full_response)],
            )
            await self.task_manager.add_message(task.id, response_message)

            # Mark completed
            await self.task_manager.update_status(
                task_id=task.id,
                state=TaskState.COMPLETED,
                message="Task completed successfully",
            )

        except Exception as e:
            await self.task_manager.update_status(
                task_id=task.id,
                state=TaskState.FAILED,
                message=str(e),
                error={"type": type(e).__name__, "message": str(e)},
            )

        return await self.task_manager.get_task(task.id)

    def _extract_prompt(self, messages: list[Message]) -> str:
        """Extract prompt text from messages.

        Args:
            messages: List of messages

        Returns:
            Combined prompt text
        """
        texts = []
        for msg in messages:
            text = msg.get_text()
            if text:
                texts.append(f"[{msg.role}]: {text}")
        return "\n\n".join(texts)

    async def _execute_agent(
        self,
        agent_id: str,
        agent: dict[str, Any],
        prompt: str,
        task: Task,
    ) -> str:
        """Execute agent (placeholder).

        In real implementation, this would:
        1. Load agent spec
        2. Configure provider
        3. Execute with context
        4. Return result

        Args:
            agent_id: Agent identifier
            agent: Agent data
            prompt: User prompt
            task: Task object

        Returns:
            Agent response text
        """
        # Placeholder - simulates agent execution
        # Real implementation would integrate with paracle_orchestration

        # Simulate processing time
        await asyncio.sleep(0.5)

        return (
            f"[{agent_id}] Response to: {prompt[:100]}...\n\n"
            f"Task ID: {task.id}\n"
            f"Context ID: {task.context_id or 'none'}\n\n"
            "This is a placeholder response. "
            "Real implementation would execute the Paracle agent."
        )

    async def _execute_agent_streaming(
        self,
        agent_id: str,
        agent: dict[str, Any],
        prompt: str,
        task: Task,
    ) -> Any:
        """Execute agent with streaming (placeholder).

        Args:
            agent_id: Agent identifier
            agent: Agent data
            prompt: User prompt
            task: Task object

        Yields:
            Response chunks
        """
        # Placeholder - simulates streaming
        chunks = [
            f"[{agent_id}] ",
            "Processing ",
            "your request...\n\n",
            f"Task ID: {task.id}\n",
            f"Prompt: {prompt[:50]}...\n\n",
            "This is a ",
            "streaming ",
            "placeholder ",
            "response.",
        ]

        for chunk in chunks:
            await asyncio.sleep(0.1)
            yield chunk
