"""Streaming Handler.

Handles SSE (Server-Sent Events) streaming responses.
"""

import json
from collections.abc import AsyncIterator
from dataclasses import dataclass

import httpx

from paracle_a2a.config import A2AClientConfig
from paracle_a2a.exceptions import StreamingError
from paracle_a2a.models import (
    A2AEvent,
    Artifact,
    TaskArtifactUpdateEvent,
    TaskStatus,
    TaskStatusUpdateEvent,
)


@dataclass
class SSEEvent:
    """Parsed SSE event."""

    event: str
    data: str
    id: str | None = None
    retry: int | None = None


class StreamingHandler:
    """Handles SSE streaming from A2A servers."""

    def __init__(self, config: A2AClientConfig | None = None):
        """Initialize streaming handler.

        Args:
            config: Client configuration
        """
        self.config = config or A2AClientConfig()

    async def stream_events(
        self,
        url: str,
    ) -> AsyncIterator[A2AEvent]:
        """Stream events from SSE endpoint.

        Args:
            url: SSE endpoint URL

        Yields:
            A2AEvent instances
        """
        async with httpx.AsyncClient(
            timeout=httpx.Timeout(
                connect=self.config.connect_timeout_seconds,
                read=self.config.stream_timeout_seconds,
                write=self.config.timeout_seconds,
                pool=self.config.timeout_seconds,
            ),
            verify=self.config.verify_ssl,
            headers={
                "User-Agent": self.config.user_agent,
                "Accept": "text/event-stream",
                **self.config.get_auth_headers(),
            },
        ) as client:
            try:
                async with client.stream("GET", url) as response:
                    response.raise_for_status()

                    async for event in self._parse_sse_stream(response):
                        parsed = self._parse_event(event)
                        if parsed:
                            yield parsed

            except httpx.RequestError as e:
                raise StreamingError(
                    task_id="unknown",
                    reason=str(e),
                ) from e

    async def _parse_sse_stream(
        self,
        response: httpx.Response,
    ) -> AsyncIterator[SSEEvent]:
        """Parse SSE stream into events.

        Args:
            response: HTTP response with SSE stream

        Yields:
            SSEEvent instances
        """
        event_type = "message"
        data_lines: list[str] = []
        event_id: str | None = None
        retry: int | None = None

        async for line in response.aiter_lines():
            line = line.strip()

            if not line:
                # Empty line = dispatch event
                if data_lines:
                    yield SSEEvent(
                        event=event_type,
                        data="\n".join(data_lines),
                        id=event_id,
                        retry=retry,
                    )
                    # Reset
                    event_type = "message"
                    data_lines = []
                    event_id = None
                    retry = None
                continue

            if line.startswith(":"):
                # Comment, ignore
                continue

            if ":" in line:
                field, _, value = line.partition(":")
                value = value.lstrip(" ")
            else:
                field = line
                value = ""

            if field == "event":
                event_type = value
            elif field == "data":
                data_lines.append(value)
            elif field == "id":
                event_id = value
            elif field == "retry":
                try:
                    retry = int(value)
                except ValueError:
                    pass

        # Final event if pending
        if data_lines:
            yield SSEEvent(
                event=event_type,
                data="\n".join(data_lines),
                id=event_id,
                retry=retry,
            )

    def _parse_event(self, sse_event: SSEEvent) -> A2AEvent | None:
        """Parse SSE event into A2A event.

        Args:
            sse_event: Raw SSE event

        Returns:
            Parsed A2AEvent or None
        """
        from ulid import ULID

        from paracle_a2a.models import TaskState

        try:
            data = json.loads(sse_event.data)
        except json.JSONDecodeError:
            return None

        event_type = sse_event.event

        # SDK requires context_id, generate if missing
        context_id = data.get("contextId") or data.get("context_id") or str(ULID())

        if event_type == "task/status":
            # Parse status - SDK TaskStatus has state, message, timestamp
            status_data = data.get("status", {})
            status = TaskStatus(
                state=TaskState(status_data.get("state", "submitted")),
                message=status_data.get("message"),
                timestamp=status_data.get("timestamp"),
            )
            return TaskStatusUpdateEvent(
                task_id=data.get("taskId") or data.get("task_id", ""),
                context_id=context_id,
                status=status,
                final=data.get("final", False),
                metadata=data.get("metadata"),
            )
        elif event_type == "task/artifact":
            return TaskArtifactUpdateEvent(
                task_id=data.get("taskId") or data.get("task_id", ""),
                context_id=context_id,
                artifact=Artifact(**data.get("artifact", {})),
                metadata=data.get("metadata"),
            )

        return None


async def stream_task(
    stream_url: str,
    config: A2AClientConfig | None = None,
) -> AsyncIterator[A2AEvent]:
    """Convenience function to stream task events.

    Args:
        stream_url: SSE endpoint URL
        config: Optional client config

    Yields:
        A2AEvent instances
    """
    handler = StreamingHandler(config)
    async for event in handler.stream_events(stream_url):
        yield event
