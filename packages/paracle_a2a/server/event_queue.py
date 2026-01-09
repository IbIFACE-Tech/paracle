"""Event Queue for SSE Streaming.

Manages event queues for Server-Sent Events (SSE) streaming.
"""

import asyncio
from collections import defaultdict
from collections.abc import AsyncIterator

from paracle_a2a.models import A2AEvent, TaskArtifactUpdateEvent, TaskStatusUpdateEvent


class EventQueue:
    """Simple event queue for broadcasting events."""

    def __init__(self, max_size: int = 1000):
        """Initialize event queue.

        Args:
            max_size: Maximum queue size per subscriber
        """
        self.max_size = max_size
        self._subscribers: dict[str, asyncio.Queue[A2AEvent]] = {}
        self._lock = asyncio.Lock()

    async def subscribe(self, subscriber_id: str) -> AsyncIterator[A2AEvent]:
        """Subscribe to events.

        Args:
            subscriber_id: Unique subscriber identifier

        Yields:
            A2AEvent instances
        """
        queue: asyncio.Queue[A2AEvent] = asyncio.Queue(maxsize=self.max_size)

        async with self._lock:
            self._subscribers[subscriber_id] = queue

        try:
            while True:
                event = await queue.get()
                yield event
        finally:
            async with self._lock:
                self._subscribers.pop(subscriber_id, None)

    async def publish(self, event: A2AEvent) -> int:
        """Publish event to all subscribers.

        Args:
            event: Event to publish

        Returns:
            Number of subscribers that received the event
        """
        delivered = 0

        async with self._lock:
            for queue in self._subscribers.values():
                try:
                    queue.put_nowait(event)
                    delivered += 1
                except asyncio.QueueFull:
                    # Drop event for slow subscribers
                    pass

        return delivered

    async def close(self, subscriber_id: str) -> None:
        """Close subscription.

        Args:
            subscriber_id: Subscriber to close
        """
        async with self._lock:
            self._subscribers.pop(subscriber_id, None)

    @property
    def subscriber_count(self) -> int:
        """Get number of active subscribers."""
        return len(self._subscribers)


class TaskEventQueue:
    """Event queue for task-specific streaming.

    Each task can have multiple subscribers for real-time updates.
    """

    def __init__(self, max_size: int = 100):
        """Initialize task event queue.

        Args:
            max_size: Maximum queue size per subscriber
        """
        self.max_size = max_size
        # task_id -> subscriber_id -> queue
        self._queues: dict[str, dict[str, asyncio.Queue[A2AEvent]]] = defaultdict(dict)
        self._lock = asyncio.Lock()

    async def subscribe(
        self,
        task_id: str,
        subscriber_id: str,
    ) -> AsyncIterator[A2AEvent]:
        """Subscribe to task events.

        Args:
            task_id: Task to subscribe to
            subscriber_id: Unique subscriber identifier

        Yields:
            Task-related A2AEvent instances
        """
        queue: asyncio.Queue[A2AEvent] = asyncio.Queue(maxsize=self.max_size)

        async with self._lock:
            self._queues[task_id][subscriber_id] = queue

        try:
            while True:
                event = await queue.get()
                yield event

                # Check if this was a terminal event
                if isinstance(event, TaskStatusUpdateEvent) and event.final:
                    break
        finally:
            async with self._lock:
                if task_id in self._queues:
                    self._queues[task_id].pop(subscriber_id, None)
                    if not self._queues[task_id]:
                        del self._queues[task_id]

    async def publish(
        self,
        task_id: str,
        event: A2AEvent,
    ) -> int:
        """Publish event to task subscribers.

        Args:
            task_id: Target task
            event: Event to publish

        Returns:
            Number of subscribers that received the event
        """
        delivered = 0

        async with self._lock:
            if task_id in self._queues:
                for queue in self._queues[task_id].values():
                    try:
                        queue.put_nowait(event)
                        delivered += 1
                    except asyncio.QueueFull:
                        pass

        return delivered

    async def publish_status_update(
        self,
        event: TaskStatusUpdateEvent,
    ) -> int:
        """Publish status update event.

        Args:
            event: Status update event

        Returns:
            Number of subscribers that received the event
        """
        return await self.publish(event.task_id, event)

    async def publish_artifact_update(
        self,
        event: TaskArtifactUpdateEvent,
    ) -> int:
        """Publish artifact update event.

        Args:
            event: Artifact update event

        Returns:
            Number of subscribers that received the event
        """
        return await self.publish(event.task_id, event)

    async def close_task(self, task_id: str) -> None:
        """Close all subscriptions for a task.

        Args:
            task_id: Task to close
        """
        async with self._lock:
            self._queues.pop(task_id, None)

    def get_subscriber_count(self, task_id: str) -> int:
        """Get number of subscribers for a task.

        Args:
            task_id: Task identifier

        Returns:
            Number of active subscribers
        """
        return len(self._queues.get(task_id, {}))

    @property
    def total_subscribers(self) -> int:
        """Get total number of active subscribers across all tasks."""
        return sum(len(subs) for subs in self._queues.values())
