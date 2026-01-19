"""StreamingCapability - Real-time streaming for LLM responses.

This capability implements streaming patterns for real-time LLM responses:
- Server-Sent Events (SSE) for unidirectional streaming
- WebSocket for bidirectional streaming
- Chunk buffering and backpressure handling
- Stream lifecycle management

Integration Points:
- Uses paracle_core for utilities and logging
- Integrates with paracle_observability for metrics
- Async iterators for streaming

Example:
    >>> from paracle_meta.capabilities import StreamingCapability, StreamingConfig
    >>>
    >>> config = StreamingConfig(
    ...     protocol="sse",
    ...     buffer_size=10,
    ...     enable_compression=True
    ... )
    >>> streaming = StreamingCapability(config)
    >>>
    >>> # Stream LLM responses
    >>> async for chunk in streaming.stream_response(
    ...     operation=llm_completion,
    ...     operation_name="chat"
    ... ):
    ...     print(chunk.data)
"""

import asyncio
import json
import time
from collections import deque
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Any, AsyncIterator, Callable, Optional

from paracle_core.compat import UTC
from paracle_meta.capabilities.base import BaseCapability, CapabilityResult


class StreamProtocol(str, Enum):
    """Streaming protocols."""

    SSE = "sse"  # Server-Sent Events (unidirectional)
    WEBSOCKET = "websocket"  # WebSocket (bidirectional)
    RAW = "raw"  # Raw async iterator


class ChunkType(str, Enum):
    """Types of stream chunks."""

    DATA = "data"  # Data chunk
    METADATA = "metadata"  # Metadata chunk
    ERROR = "error"  # Error chunk
    DONE = "done"  # Stream complete


@dataclass
class StreamChunk:
    """A single chunk in a stream.

    Attributes:
        chunk_id: Unique chunk identifier.
        chunk_type: Type of chunk.
        data: Chunk data.
        timestamp: When chunk was created.
        metadata: Optional metadata.
    """

    chunk_id: int
    chunk_type: ChunkType
    data: Any
    timestamp: datetime = field(default_factory=lambda: datetime.now(UTC))
    metadata: dict[str, Any] = field(default_factory=dict)

    def to_sse(self) -> str:
        """Convert chunk to SSE format.

        Returns:
            SSE-formatted string.
        """
        lines = []
        lines.append(f"id: {self.chunk_id}")
        lines.append(f"event: {self.chunk_type.value}")

        # Serialize data
        if isinstance(self.data, (dict, list)):
            data_str = json.dumps(self.data)
        else:
            data_str = str(self.data)

        lines.append(f"data: {data_str}")
        lines.append("")  # Empty line terminates event
        return "\n".join(lines) + "\n"

    def to_websocket(self) -> str:
        """Convert chunk to WebSocket message format.

        Returns:
            JSON-formatted string.
        """
        return json.dumps(
            {
                "chunk_id": self.chunk_id,
                "type": self.chunk_type.value,
                "data": self.data,
                "timestamp": self.timestamp.isoformat(),
                "metadata": self.metadata,
            }
        )


@dataclass
class StreamingConfig:
    """Configuration for streaming capability.

    Attributes:
        protocol: Streaming protocol (sse, websocket, raw).
        buffer_size: Maximum chunks to buffer (default: 100).
        enable_compression: Enable compression for large chunks.
        chunk_timeout_seconds: Timeout for chunk processing.
        max_chunk_size_bytes: Maximum size per chunk.
        backpressure_threshold: Buffer % to trigger backpressure.
    """

    protocol: StreamProtocol = StreamProtocol.SSE
    buffer_size: int = 100
    enable_compression: bool = False
    chunk_timeout_seconds: float = 5.0
    max_chunk_size_bytes: int = 1024 * 1024  # 1MB
    backpressure_threshold: float = 0.8  # 80%


class StreamBuffer:
    """Buffer for managing stream chunks with backpressure."""

    def __init__(self, max_size: int, backpressure_threshold: float):
        """Initialize stream buffer.

        Args:
            max_size: Maximum buffer size.
            backpressure_threshold: Threshold for backpressure (0.0-1.0).
        """
        self.max_size = max_size
        self.backpressure_threshold = backpressure_threshold
        self._buffer: deque[StreamChunk] = deque(maxlen=max_size)
        self._lock = asyncio.Lock()

    async def push(self, chunk: StreamChunk) -> bool:
        """Add chunk to buffer.

        Args:
            chunk: Chunk to add.

        Returns:
            True if added, False if buffer full.
        """
        async with self._lock:
            if len(self._buffer) >= self.max_size:
                return False
            self._buffer.append(chunk)
            return True

    async def pop(self) -> Optional[StreamChunk]:
        """Remove and return oldest chunk.

        Returns:
            Oldest chunk or None if buffer empty.
        """
        async with self._lock:
            if self._buffer:
                return self._buffer.popleft()
            return None

    def is_backpressure_active(self) -> bool:
        """Check if backpressure should be applied.

        Returns:
            True if buffer is above backpressure threshold.
        """
        utilization = len(self._buffer) / self.max_size
        return utilization >= self.backpressure_threshold

    def size(self) -> int:
        """Get current buffer size.

        Returns:
            Number of chunks in buffer.
        """
        return len(self._buffer)

    async def clear(self) -> int:
        """Clear all chunks from buffer.

        Returns:
            Number of chunks cleared.
        """
        async with self._lock:
            count = len(self._buffer)
            self._buffer.clear()
            return count


class StreamingCapability(BaseCapability):
    """Streaming capability for real-time responses.

    Implements streaming patterns for LLM responses:
    - SSE for unidirectional streaming
    - WebSocket for bidirectional streaming
    - Buffering and backpressure handling

    Example:
        >>> config = StreamingConfig(protocol="sse", buffer_size=50)
        >>> streaming = StreamingCapability(config)
        >>>
        >>> # Stream responses
        >>> async for chunk in streaming.stream_response(
        ...     operation=llm_call,
        ...     operation_name="chat"
        ... ):
        ...     print(chunk.data)
    """

    name = "streaming"

    def __init__(self, config: StreamingConfig | None = None):
        """Initialize streaming capability.

        Args:
            config: Streaming configuration (uses defaults if None).
        """
        super().__init__(config or StreamingConfig())

        # Stream buffers per stream
        self._buffers: dict[str, StreamBuffer] = {}

        # Active streams
        self._active_streams: set[str] = set()

        # Metrics
        self._metrics = {
            "total_streams": 0,
            "active_streams": 0,
            "total_chunks": 0,
            "errors": 0,
            "backpressure_events": 0,
        }

        # Chunk ID counter
        self._chunk_id_counter = 0

    def _get_buffer(self, stream_id: str) -> StreamBuffer:
        """Get or create buffer for stream.

        Args:
            stream_id: Stream identifier.

        Returns:
            StreamBuffer instance.
        """
        if stream_id not in self._buffers:
            self._buffers[stream_id] = StreamBuffer(
                max_size=self.config.buffer_size,
                backpressure_threshold=self.config.backpressure_threshold,
            )
        return self._buffers[stream_id]

    def _next_chunk_id(self) -> int:
        """Get next chunk ID.

        Returns:
            Unique chunk ID.
        """
        self._chunk_id_counter += 1
        return self._chunk_id_counter

    async def stream_response(
        self,
        operation: Callable,
        operation_name: str,
        **operation_kwargs: Any,
    ) -> AsyncIterator[StreamChunk]:
        """Stream operation responses as chunks.

        Args:
            operation: Async generator operation to stream.
            operation_name: Name for stream identification.
            **operation_kwargs: Arguments for operation.

        Yields:
            StreamChunk instances.
        """
        stream_id = f"{operation_name}_{time.time()}"
        self._active_streams.add(stream_id)
        self._metrics["total_streams"] += 1
        self._metrics["active_streams"] = len(self._active_streams)

        buffer = self._get_buffer(stream_id)

        try:
            # Start operation
            async for item in operation(**operation_kwargs):
                # Check backpressure
                if buffer.is_backpressure_active():
                    self._metrics["backpressure_events"] += 1
                    # Slow down by waiting briefly
                    await asyncio.sleep(0.01)

                # Create chunk
                chunk = StreamChunk(
                    chunk_id=self._next_chunk_id(),
                    chunk_type=ChunkType.DATA,
                    data=item,
                )

                self._metrics["total_chunks"] += 1

                # Add to buffer
                await buffer.push(chunk)

                # Yield chunk
                yield chunk

            # Send completion chunk
            done_chunk = StreamChunk(
                chunk_id=self._next_chunk_id(),
                chunk_type=ChunkType.DONE,
                data={"status": "completed"},
            )
            yield done_chunk

        except Exception as e:
            self._metrics["errors"] += 1

            # Send error chunk
            error_chunk = StreamChunk(
                chunk_id=self._next_chunk_id(),
                chunk_type=ChunkType.ERROR,
                data={"error": str(e)},
            )
            yield error_chunk

        finally:
            # Cleanup
            self._active_streams.discard(stream_id)
            self._metrics["active_streams"] = len(self._active_streams)
            await buffer.clear()

    async def create_sse_stream(
        self,
        operation: Callable,
        operation_name: str,
        **operation_kwargs: Any,
    ) -> AsyncIterator[str]:
        """Create SSE-formatted stream.

        Args:
            operation: Async generator operation.
            operation_name: Stream name.
            **operation_kwargs: Operation arguments.

        Yields:
            SSE-formatted strings.
        """
        async for chunk in self.stream_response(
            operation, operation_name, **operation_kwargs
        ):
            yield chunk.to_sse()

    async def create_websocket_stream(
        self,
        operation: Callable,
        operation_name: str,
        **operation_kwargs: Any,
    ) -> AsyncIterator[str]:
        """Create WebSocket-formatted stream.

        Args:
            operation: Async generator operation.
            operation_name: Stream name.
            **operation_kwargs: Operation arguments.

        Yields:
            JSON-formatted WebSocket messages.
        """
        async for chunk in self.stream_response(
            operation, operation_name, **operation_kwargs
        ):
            yield chunk.to_websocket()

    async def get_active_streams(self) -> CapabilityResult:
        """Get list of active streams.

        Returns:
            CapabilityResult with active stream IDs.
        """
        start = datetime.now(UTC)

        duration = (datetime.now(UTC) - start).total_seconds() * 1000

        return CapabilityResult(
            capability=self.name,
            success=True,
            output={
                "active_streams": list(self._active_streams),
                "count": len(self._active_streams),
            },
            duration_ms=duration,
        )

    async def get_buffer_status(self, stream_id: str) -> CapabilityResult:
        """Get buffer status for stream.

        Args:
            stream_id: Stream identifier.

        Returns:
            CapabilityResult with buffer status.
        """
        start = datetime.now(UTC)

        if stream_id in self._buffers:
            buffer = self._buffers[stream_id]
            status = {
                "stream_id": stream_id,
                "buffer_size": buffer.size(),
                "max_size": buffer.max_size,
                "utilization": buffer.size() / buffer.max_size,
                "backpressure_active": buffer.is_backpressure_active(),
            }
        else:
            status = {"stream_id": stream_id, "exists": False}

        duration = (datetime.now(UTC) - start).total_seconds() * 1000

        return CapabilityResult(
            capability=self.name,
            success=True,
            output=status,
            duration_ms=duration,
        )

    async def get_metrics(self) -> CapabilityResult:
        """Get streaming metrics.

        Returns:
            CapabilityResult with metrics.
        """
        start = datetime.now(UTC)

        duration = (datetime.now(UTC) - start).total_seconds() * 1000

        return CapabilityResult(
            capability=self.name,
            success=True,
            output=self._metrics.copy(),
            duration_ms=duration,
        )

    async def reset_metrics(self) -> CapabilityResult:
        """Reset metrics (testing/admin).

        Returns:
            CapabilityResult indicating success.
        """
        start = datetime.now(UTC)

        self._metrics = {
            "total_streams": 0,
            "active_streams": len(self._active_streams),
            "total_chunks": 0,
            "errors": 0,
            "backpressure_events": 0,
        }

        duration = (datetime.now(UTC) - start).total_seconds() * 1000

        return CapabilityResult(
            capability=self.name,
            success=True,
            output={"metrics_reset": True},
            duration_ms=duration,
        )

    async def execute(self, **kwargs: Any) -> CapabilityResult:
        """Execute streaming operation with action routing.

        Args:
            **kwargs: Must include 'action' and action-specific parameters.

        Supported actions:
        - get_active_streams: Get active streams.
        - get_buffer_status: Get buffer status for stream.
        - get_metrics: Get streaming metrics.
        - reset_metrics: Reset metrics.

        Returns:
            CapabilityResult from the executed action.
        """
        action_param = kwargs.pop("action", "get_metrics")

        action_map = {
            "get_active_streams": self.get_active_streams,
            "get_buffer_status": self.get_buffer_status,
            "get_metrics": self.get_metrics,
            "reset_metrics": self.reset_metrics,
        }

        if action_param in action_map:
            return await action_map[action_param](**kwargs)

        return CapabilityResult(
            capability=self.name,
            success=False,
            output={"error": f"Unknown action: {action_param}"},
        )
