"""A2A Client.

Client for invoking external A2A-compatible agents.
"""

from collections.abc import AsyncIterator
from typing import Any

import httpx

from paracle_a2a.client.discovery import AgentDiscovery
from paracle_a2a.client.streaming import StreamingHandler
from paracle_a2a.config import A2AClientConfig
from paracle_a2a.exceptions import (
    A2AError,
    AgentNotFoundError,
    InvalidRequestError,
    TaskNotFoundError,
)
from paracle_a2a.models import (
    A2AEvent,
    AgentCard,
    Message,
    Task,
    TaskState,
    TaskStatus,
    create_message,
    is_task_terminal,
)


class ParacleA2AClient:
    """Client for calling external A2A agents.

    Supports both sync (JSON-RPC) and streaming (SSE) modes.
    """

    def __init__(
        self,
        url: str | None = None,
        config: A2AClientConfig | None = None,
    ):
        """Initialize A2A client.

        Args:
            url: Agent endpoint URL (optional, can be set per call)
            config: Client configuration
        """
        self.url = url
        self.config = config or A2AClientConfig()
        self._discovery = AgentDiscovery(self.config)
        self._streaming = StreamingHandler(self.config)
        self._agent_card: AgentCard | None = None

    async def discover(
        self,
        url: str | None = None,
        *,
        force_refresh: bool = False,
    ) -> AgentCard:
        """Discover agent capabilities.

        Args:
            url: Agent URL (uses instance URL if not provided)
            force_refresh: Force cache refresh

        Returns:
            AgentCard describing the agent
        """
        target_url = url or self.url
        if not target_url:
            raise ValueError("No URL provided")

        card = await self._discovery.discover(target_url, force_refresh=force_refresh)
        if not url and self.url:
            self._agent_card = card
        return card

    async def invoke(
        self,
        message: str | Message,
        *,
        url: str | None = None,
        context_id: str | None = None,
        task_id: str | None = None,
        metadata: dict[str, Any] | None = None,
        wait: bool = True,
        poll_interval: float = 0.5,
    ) -> Task:
        """Invoke agent with a message.

        Args:
            message: Text or Message to send
            url: Agent URL (uses instance URL if not provided)
            context_id: Optional context ID for conversation continuity
            task_id: Optional task ID (for continuing a task)
            metadata: Optional metadata
            wait: Wait for task completion
            poll_interval: Polling interval when waiting

        Returns:
            Task with results
        """
        target_url = url or self.url
        if not target_url:
            raise ValueError("No URL provided")

        # Convert string to Message
        if isinstance(message, str):
            msg = create_message(message, role="user")
        else:
            msg = message

        # Send task
        task = await self._send_task(
            url=target_url,
            message=msg,
            context_id=context_id,
            task_id=task_id,
            metadata=metadata,
        )

        if not wait:
            return task

        # Poll until complete
        while not is_task_terminal(task):
            import asyncio

            await asyncio.sleep(poll_interval)
            task = await self.get_task(task.id, url=target_url)

        return task

    async def invoke_streaming(
        self,
        message: str | Message,
        *,
        url: str | None = None,
        context_id: str | None = None,
        task_id: str | None = None,
        metadata: dict[str, Any] | None = None,
    ) -> AsyncIterator[A2AEvent]:
        """Invoke agent with streaming response.

        Args:
            message: Text or Message to send
            url: Agent URL
            context_id: Optional context ID
            task_id: Optional task ID
            metadata: Optional metadata

        Yields:
            A2AEvent instances (status updates and artifacts)
        """
        target_url = url or self.url
        if not target_url:
            raise ValueError("No URL provided")

        # Convert string to Message
        if isinstance(message, str):
            msg = create_message(message, role="user")
        else:
            msg = message

        # Send task
        task = await self._send_task(
            url=target_url,
            message=msg,
            context_id=context_id,
            task_id=task_id,
            metadata=metadata,
        )

        # Build stream URL
        stream_url = self._build_stream_url(target_url, task.id)

        # Stream events
        async for event in self._streaming.stream_events(stream_url):
            yield event

    async def get_task(
        self,
        task_id: str,
        *,
        url: str | None = None,
    ) -> Task:
        """Get task by ID.

        Args:
            task_id: Task identifier
            url: Agent URL

        Returns:
            Task with current status
        """
        target_url = url or self.url
        if not target_url:
            raise ValueError("No URL provided")

        result = await self._jsonrpc_call(
            url=target_url,
            method="tasks/get",
            params={"id": task_id},
        )

        return self._parse_task(result)

    async def list_tasks(
        self,
        *,
        url: str | None = None,
        context_id: str | None = None,
        states: list[TaskState] | None = None,
        limit: int = 100,
        offset: int = 0,
    ) -> list[Task]:
        """List tasks.

        Args:
            url: Agent URL
            context_id: Filter by context ID
            states: Filter by states
            limit: Maximum results
            offset: Results offset

        Returns:
            List of tasks
        """
        target_url = url or self.url
        if not target_url:
            raise ValueError("No URL provided")

        params: dict[str, Any] = {
            "limit": limit,
            "offset": offset,
        }
        if context_id:
            params["contextId"] = context_id
        if states:
            params["states"] = [s.value for s in states]

        result = await self._jsonrpc_call(
            url=target_url,
            method="tasks/list",
            params=params,
        )

        return [self._parse_task(t) for t in result.get("tasks", [])]

    async def cancel_task(
        self,
        task_id: str,
        *,
        url: str | None = None,
    ) -> Task:
        """Cancel a task.

        Args:
            task_id: Task identifier
            url: Agent URL

        Returns:
            Cancelled task
        """
        target_url = url or self.url
        if not target_url:
            raise ValueError("No URL provided")

        result = await self._jsonrpc_call(
            url=target_url,
            method="tasks/cancel",
            params={"id": task_id},
        )

        return self._parse_task(result)

    async def _send_task(
        self,
        url: str,
        message: Message,
        context_id: str | None = None,
        task_id: str | None = None,
        metadata: dict[str, Any] | None = None,
    ) -> Task:
        """Send task to agent.

        Args:
            url: Agent endpoint URL
            message: Message to send
            context_id: Optional context ID
            task_id: Optional task ID
            metadata: Optional metadata

        Returns:
            Created Task
        """
        params: dict[str, Any] = {
            "message": message.model_dump(by_alias=True, exclude_none=True),
        }
        if context_id:
            params["contextId"] = context_id
        if task_id:
            params["id"] = task_id
        if metadata:
            params["metadata"] = metadata

        result = await self._jsonrpc_call(
            url=url,
            method="tasks/send",
            params=params,
        )

        return self._parse_task(result)

    async def _jsonrpc_call(
        self,
        url: str,
        method: str,
        params: dict[str, Any],
    ) -> dict[str, Any]:
        """Make JSON-RPC 2.0 call.

        Args:
            url: Endpoint URL
            method: RPC method name
            params: Method parameters

        Returns:
            Result from RPC call

        Raises:
            A2AError: On RPC error
        """
        import uuid

        request_id = str(uuid.uuid4())

        body = {
            "jsonrpc": "2.0",
            "id": request_id,
            "method": method,
            "params": params,
        }

        try:
            async with httpx.AsyncClient(
                timeout=self.config.timeout_seconds,
                verify=self.config.verify_ssl,
                headers={
                    "User-Agent": self.config.user_agent,
                    "Content-Type": "application/json",
                    **self.config.get_auth_headers(),
                },
            ) as client:
                response = await client.post(url, json=body)

                if response.status_code == 404:
                    raise AgentNotFoundError(url)

                data = response.json()

        except httpx.HTTPStatusError as e:
            raise A2AError(f"HTTP error: {e}") from e
        except httpx.RequestError as e:
            raise A2AError(f"Request failed: {e}") from e

        # Check for JSON-RPC error
        if "error" in data:
            error = data["error"]
            code = error.get("code", -32000)
            message = error.get("message", "Unknown error")
            error_data = error.get("data", {})

            if code == -32001:
                raise TaskNotFoundError(error_data.get("task_id", ""))
            elif code == -32003:
                raise AgentNotFoundError(error_data.get("agent_id", url))
            elif code == -32600:
                raise InvalidRequestError(message)
            else:
                raise A2AError(message, code=code, data=error_data)

        return data.get("result", {})

    def _build_stream_url(self, base_url: str, task_id: str) -> str:
        """Build SSE stream URL.

        Args:
            base_url: Agent base URL
            task_id: Task identifier

        Returns:
            Stream URL
        """
        # Parse URL to extract agent path
        # Assuming URL is like: http://host/a2a/agents/{agent_id}
        if "/agents/" in base_url:
            return f"{base_url}/stream/{task_id}"
        else:
            return f"{base_url}/stream/{task_id}"

    def _parse_task(self, data: dict[str, Any]) -> Task:
        """Parse task from response data.

        Args:
            data: Task data dictionary

        Returns:
            Task instance
        """
        from ulid import ULID

        # Handle status - SDK TaskStatus has state, message, timestamp
        status_data = data.get("status", {})
        status = TaskStatus(
            state=TaskState(status_data.get("state", "submitted")),
            message=status_data.get("message"),
            timestamp=status_data.get("timestamp"),
        )

        # SDK Task requires context_id, generate if not present
        context_id = data.get("contextId") or data.get("context_id") or str(ULID())

        return Task(
            id=data.get("id", ""),
            context_id=context_id,
            status=status,
            metadata=data.get("metadata", {}),
        )


async def invoke_agent(
    url: str,
    message: str,
    *,
    config: A2AClientConfig | None = None,
    wait: bool = True,
) -> Task:
    """Convenience function to invoke an A2A agent.

    Args:
        url: Agent endpoint URL
        message: Message to send
        config: Optional client config
        wait: Wait for completion

    Returns:
        Task with results
    """
    client = ParacleA2AClient(url, config)
    return await client.invoke(message, wait=wait)
