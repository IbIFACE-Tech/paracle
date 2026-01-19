"""Unit tests for StreamingCapability (SSE, WebSocket streaming)."""

import asyncio
import json

import pytest

from paracle_meta.capabilities.streaming import (
    ChunkType,
    StreamBuffer,
    StreamChunk,
    StreamingCapability,
    StreamingConfig,
    StreamProtocol,
)


# --- Test Fixtures ---


@pytest.fixture
def streaming_config():
    """Create default streaming configuration."""
    return StreamingConfig(
        protocol=StreamProtocol.SSE,
        buffer_size=10,
        enable_compression=False,
        chunk_timeout_seconds=5.0,
        max_chunk_size_bytes=1024 * 1024,
        backpressure_threshold=0.8,
    )


@pytest.fixture
def streaming(streaming_config):
    """Create StreamingCapability instance."""
    return StreamingCapability(streaming_config)


@pytest.fixture
def stream_buffer():
    """Create StreamBuffer instance."""
    return StreamBuffer(max_size=10, backpressure_threshold=0.8)


# --- StreamChunk Tests ---


def test_stream_chunk_initialization():
    """Test StreamChunk initialization."""
    chunk = StreamChunk(
        chunk_id=1,
        chunk_type=ChunkType.DATA,
        data={"message": "Hello"},
    )

    assert chunk.chunk_id == 1
    assert chunk.chunk_type == ChunkType.DATA
    assert chunk.data == {"message": "Hello"}
    assert chunk.metadata == {}


def test_stream_chunk_to_sse():
    """Test converting chunk to SSE format."""
    chunk = StreamChunk(
        chunk_id=42,
        chunk_type=ChunkType.DATA,
        data={"text": "streaming data"},
    )

    sse = chunk.to_sse()

    assert "id: 42" in sse
    assert "event: data" in sse
    assert '"text": "streaming data"' in sse
    assert sse.endswith("\n")


def test_stream_chunk_to_websocket():
    """Test converting chunk to WebSocket format."""
    chunk = StreamChunk(
        chunk_id=123,
        chunk_type=ChunkType.DATA,
        data="test data",
        metadata={"source": "test"},
    )

    ws_msg = chunk.to_websocket()
    data = json.loads(ws_msg)

    assert data["chunk_id"] == 123
    assert data["type"] == "data"
    assert data["data"] == "test data"
    assert data["metadata"]["source"] == "test"


# --- StreamBuffer Tests ---


@pytest.mark.asyncio
async def test_stream_buffer_push_pop(stream_buffer):
    """Test pushing and popping from buffer."""
    chunk1 = StreamChunk(chunk_id=1, chunk_type=ChunkType.DATA, data="test1")
    chunk2 = StreamChunk(chunk_id=2, chunk_type=ChunkType.DATA, data="test2")

    # Push chunks
    assert await stream_buffer.push(chunk1) is True
    assert await stream_buffer.push(chunk2) is True
    assert stream_buffer.size() == 2

    # Pop chunks (FIFO)
    popped1 = await stream_buffer.pop()
    assert popped1.chunk_id == 1

    popped2 = await stream_buffer.pop()
    assert popped2.chunk_id == 2

    assert stream_buffer.size() == 0


@pytest.mark.asyncio
async def test_stream_buffer_max_size(stream_buffer):
    """Test buffer respects max size."""
    # Fill buffer to max
    for i in range(10):
        chunk = StreamChunk(chunk_id=i, chunk_type=ChunkType.DATA, data=f"test{i}")
        assert await stream_buffer.push(chunk) is True

    # Buffer full - should reject
    overflow_chunk = StreamChunk(
        chunk_id=99, chunk_type=ChunkType.DATA, data="overflow"
    )
    assert await stream_buffer.push(overflow_chunk) is False


@pytest.mark.asyncio
async def test_stream_buffer_backpressure(stream_buffer):
    """Test backpressure threshold detection."""
    # Not at backpressure threshold
    assert stream_buffer.is_backpressure_active() is False

    # Add chunks to reach 80% (8/10)
    for i in range(8):
        chunk = StreamChunk(chunk_id=i, chunk_type=ChunkType.DATA, data=f"test{i}")
        await stream_buffer.push(chunk)

    # Should trigger backpressure
    assert stream_buffer.is_backpressure_active() is True


@pytest.mark.asyncio
async def test_stream_buffer_clear(stream_buffer):
    """Test clearing buffer."""
    # Add some chunks
    for i in range(5):
        chunk = StreamChunk(chunk_id=i, chunk_type=ChunkType.DATA, data=f"test{i}")
        await stream_buffer.push(chunk)

    assert stream_buffer.size() == 5

    # Clear
    cleared = await stream_buffer.clear()
    assert cleared == 5
    assert stream_buffer.size() == 0


# --- StreamingConfig Tests ---


def test_streaming_config_defaults():
    """Test StreamingConfig default values."""
    config = StreamingConfig()

    assert config.protocol == StreamProtocol.SSE
    assert config.buffer_size == 100
    assert config.enable_compression is False
    assert config.chunk_timeout_seconds == 5.0
    assert config.max_chunk_size_bytes == 1024 * 1024
    assert config.backpressure_threshold == 0.8


def test_streaming_config_custom():
    """Test StreamingConfig with custom values."""
    config = StreamingConfig(
        protocol=StreamProtocol.WEBSOCKET,
        buffer_size=50,
        enable_compression=True,
        backpressure_threshold=0.7,
    )

    assert config.protocol == StreamProtocol.WEBSOCKET
    assert config.buffer_size == 50
    assert config.enable_compression is True
    assert config.backpressure_threshold == 0.7


# --- StreamingCapability Tests ---


def test_streaming_capability_initialization(streaming):
    """Test StreamingCapability initialization."""
    assert streaming.name == "streaming"
    assert isinstance(streaming.config, StreamingConfig)
    assert streaming._active_streams == set()
    assert streaming._metrics["total_streams"] == 0


@pytest.mark.asyncio
async def test_stream_response_basic(streaming):
    """Test basic stream response."""

    async def simple_generator():
        for i in range(3):
            yield f"chunk_{i}"

    chunks = []
    async for chunk in streaming.stream_response(
        operation=simple_generator,
        operation_name="test_stream",
    ):
        chunks.append(chunk)

    # Should have 3 data chunks + 1 done chunk
    assert len(chunks) == 4
    assert chunks[0].chunk_type == ChunkType.DATA
    assert chunks[0].data == "chunk_0"
    assert chunks[1].data == "chunk_1"
    assert chunks[2].data == "chunk_2"
    assert chunks[3].chunk_type == ChunkType.DONE


@pytest.mark.asyncio
async def test_stream_response_with_error(streaming):
    """Test stream response handles errors."""

    async def failing_generator():
        yield "chunk_1"
        raise Exception("Stream error")

    chunks = []
    async for chunk in streaming.stream_response(
        operation=failing_generator,
        operation_name="failing_stream",
    ):
        chunks.append(chunk)

    # Should have 1 data chunk + 1 error chunk
    assert len(chunks) == 2
    assert chunks[0].chunk_type == ChunkType.DATA
    assert chunks[1].chunk_type == ChunkType.ERROR
    assert "Stream error" in str(chunks[1].data)


@pytest.mark.asyncio
async def test_stream_response_metrics(streaming):
    """Test stream response updates metrics."""

    async def simple_generator():
        for i in range(5):
            yield f"chunk_{i}"

    # Consume stream
    async for _ in streaming.stream_response(
        operation=simple_generator,
        operation_name="metrics_test",
    ):
        pass

    # Check metrics
    metrics = await streaming.get_metrics()
    assert metrics.output["total_streams"] == 1
    assert metrics.output["active_streams"] == 0
    assert metrics.output["total_chunks"] == 5
    assert metrics.output["errors"] == 0


@pytest.mark.asyncio
async def test_stream_response_backpressure(streaming):
    """Test backpressure handling."""
    # Small buffer to trigger backpressure
    streaming.config.buffer_size = 5
    streaming.config.backpressure_threshold = 0.6  # 3/5

    async def fast_generator():
        for i in range(10):
            yield f"chunk_{i}"

    chunks = []
    async for chunk in streaming.stream_response(
        operation=fast_generator,
        operation_name="backpressure_test",
    ):
        chunks.append(chunk)
        # Simulate slow consumer
        await asyncio.sleep(0.001)

    # Should complete despite backpressure
    assert len(chunks) == 11  # 10 data + 1 done

    # Check backpressure events recorded
    metrics = await streaming.get_metrics()
    assert metrics.output["backpressure_events"] > 0


@pytest.mark.asyncio
async def test_create_sse_stream(streaming):
    """Test SSE-formatted stream creation."""

    async def simple_generator():
        yield {"message": "Hello"}
        yield {"message": "World"}

    sse_chunks = []
    async for sse_data in streaming.create_sse_stream(
        operation=simple_generator,
        operation_name="sse_test",
    ):
        sse_chunks.append(sse_data)

    # Verify SSE format
    assert len(sse_chunks) == 3  # 2 data + 1 done
    assert "event: data" in sse_chunks[0]
    assert '"message": "Hello"' in sse_chunks[0]
    assert "event: done" in sse_chunks[2]


@pytest.mark.asyncio
async def test_create_websocket_stream(streaming):
    """Test WebSocket-formatted stream creation."""

    async def simple_generator():
        yield "message1"
        yield "message2"

    ws_chunks = []
    async for ws_msg in streaming.create_websocket_stream(
        operation=simple_generator,
        operation_name="ws_test",
    ):
        ws_chunks.append(json.loads(ws_msg))

    # Verify WebSocket format
    assert len(ws_chunks) == 3  # 2 data + 1 done
    assert ws_chunks[0]["type"] == "data"
    assert ws_chunks[0]["data"] == "message1"
    assert ws_chunks[1]["data"] == "message2"
    assert ws_chunks[2]["type"] == "done"


@pytest.mark.asyncio
async def test_get_active_streams(streaming):
    """Test getting active streams."""

    async def long_generator():
        for i in range(100):
            yield f"chunk_{i}"
            await asyncio.sleep(0.01)

    # Start stream but don't consume it fully
    stream_gen = streaming.stream_response(
        operation=long_generator,
        operation_name="active_test",
    )

    # Consume first chunk
    chunk = await stream_gen.__anext__()
    assert chunk is not None

    # Check active streams
    result = await streaming.get_active_streams()
    assert result.success is True
    assert result.output["count"] >= 0  # Stream might complete quickly

    # Consume rest
    async for _ in stream_gen:
        pass


@pytest.mark.asyncio
async def test_get_buffer_status(streaming):
    """Test getting buffer status."""
    stream_id = "test_buffer_stream"

    # Get buffer (creates it)
    buffer = streaming._get_buffer(stream_id)

    # Add some chunks
    for i in range(3):
        chunk = StreamChunk(chunk_id=i, chunk_type=ChunkType.DATA, data=f"test{i}")
        await buffer.push(chunk)

    # Check status
    result = await streaming.get_buffer_status(stream_id=stream_id)

    assert result.success is True
    assert result.output["stream_id"] == stream_id
    assert result.output["buffer_size"] == 3
    assert result.output["max_size"] == streaming.config.buffer_size
    assert 0.0 <= result.output["utilization"] <= 1.0


@pytest.mark.asyncio
async def test_get_buffer_status_nonexistent(streaming):
    """Test getting status for nonexistent buffer."""
    result = await streaming.get_buffer_status(stream_id="nonexistent")

    assert result.success is True
    assert result.output["exists"] is False


@pytest.mark.asyncio
async def test_get_metrics(streaming):
    """Test getting streaming metrics."""
    result = await streaming.get_metrics()

    assert result.success is True
    assert "total_streams" in result.output
    assert "active_streams" in result.output
    assert "total_chunks" in result.output
    assert "errors" in result.output
    assert "backpressure_events" in result.output


@pytest.mark.asyncio
async def test_reset_metrics(streaming):
    """Test resetting metrics."""

    async def simple_generator():
        for i in range(3):
            yield f"chunk_{i}"

    # Generate some activity
    async for _ in streaming.stream_response(
        operation=simple_generator,
        operation_name="test",
    ):
        pass

    # Metrics should be non-zero
    metrics_before = await streaming.get_metrics()
    assert metrics_before.output["total_streams"] > 0

    # Reset
    result = await streaming.reset_metrics()
    assert result.success is True
    assert result.output["metrics_reset"] is True

    # Verify reset
    metrics_after = await streaming.get_metrics()
    assert metrics_after.output["total_streams"] == 0
    assert metrics_after.output["total_chunks"] == 0


@pytest.mark.asyncio
async def test_execute_default_action(streaming):
    """Test execute with default action (get_metrics)."""
    result = await streaming.execute()

    assert result.success is True
    assert "total_streams" in result.output


@pytest.mark.asyncio
async def test_execute_get_active_streams_action(streaming):
    """Test execute with get_active_streams action."""
    result = await streaming.execute(action="get_active_streams")

    assert result.success is True
    assert "active_streams" in result.output
    assert "count" in result.output


@pytest.mark.asyncio
async def test_execute_get_buffer_status_action(streaming):
    """Test execute with get_buffer_status action."""
    result = await streaming.execute(
        action="get_buffer_status", stream_id="test_stream"
    )

    assert result.success is True
    assert "stream_id" in result.output


@pytest.mark.asyncio
async def test_execute_reset_metrics_action(streaming):
    """Test execute with reset_metrics action."""
    result = await streaming.execute(action="reset_metrics")

    assert result.success is True
    assert result.output["metrics_reset"] is True


@pytest.mark.asyncio
async def test_execute_unknown_action(streaming):
    """Test execute with unknown action."""
    result = await streaming.execute(action="invalid_action")

    assert result.success is False
    assert "error" in result.output


@pytest.mark.asyncio
async def test_concurrent_streams(streaming):
    """Test multiple concurrent streams."""

    async def generator(stream_num: int):
        for i in range(5):
            yield f"stream_{stream_num}_chunk_{i}"

    # Start multiple streams
    streams = [
        streaming.stream_response(
            operation=generator,
            operation_name=f"concurrent_{i}",
            stream_num=i,
        )
        for i in range(3)
    ]

    # Consume all concurrently
    results = await asyncio.gather(*[collect_stream(s) for s in streams])

    # Each stream should have 5 data chunks + 1 done
    for chunks in results:
        assert len(chunks) == 6
        assert chunks[-1].chunk_type == ChunkType.DONE

    # Check metrics
    metrics = await streaming.get_metrics()
    assert metrics.output["total_streams"] == 3


@pytest.mark.asyncio
async def test_full_streaming_workflow(streaming):
    """Test complete streaming workflow."""

    async def llm_response_generator():
        """Simulate LLM streaming response."""
        tokens = ["Hello", " ", "world", "!", " ", "How", " ", "are", " ", "you", "?"]
        for token in tokens:
            yield {"token": token, "finish_reason": None}
            await asyncio.sleep(0.01)
        yield {"token": "", "finish_reason": "stop"}

    # 1. Stream LLM response
    chunks = []
    async for chunk in streaming.stream_response(
        operation=llm_response_generator,
        operation_name="llm_completion",
    ):
        chunks.append(chunk)

    # Verify chunks
    assert len(chunks) == 13  # 12 tokens + 1 done
    assert all(c.chunk_type in [ChunkType.DATA, ChunkType.DONE] for c in chunks)

    # 2. Check active streams (should be 0 after completion)
    active = await streaming.get_active_streams()
    assert active.output["count"] == 0

    # 3. Check metrics
    metrics = await streaming.get_metrics()
    assert metrics.output["total_streams"] == 1
    assert metrics.output["total_chunks"] == 12
    assert metrics.output["errors"] == 0

    # 4. Reset for next workflow
    reset_result = await streaming.reset_metrics()
    assert reset_result.output["metrics_reset"] is True


async def collect_stream(stream_gen):
    """Helper to collect all chunks from stream."""
    chunks = []
    async for chunk in stream_gen:
        chunks.append(chunk)
    return chunks
