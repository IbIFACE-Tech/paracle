"""StreamingCapability Demo - Real-time SSE and WebSocket Streaming.

This example demonstrates how to use StreamingCapability for real-time
LLM response streaming with SSE and WebSocket protocols.

Key Benefits:
- Real-time streaming for LLM responses
- SSE for unidirectional streaming
- WebSocket for bidirectional streaming
- Backpressure handling for flow control
- Chunk buffering and lifecycle management

Usage:
    python examples/streaming_demo.py
"""

import asyncio

from paracle_meta.capabilities import (
    ChunkType,
    StreamingCapability,
    StreamingConfig,
    StreamProtocol,
)


async def simulate_llm_streaming(prompt: str):
    """Simulate LLM streaming response.

    Args:
        prompt: User prompt.

    Yields:
        Token chunks.
    """
    # Simulate streaming tokens
    response = (
        "Hello! I'm a simulated LLM response. "
        "This demonstrates real-time streaming of tokens "
        "as they are generated, just like ChatGPT or Claude."
    )

    words = response.split()
    for word in words:
        await asyncio.sleep(0.05)  # Simulate generation delay
        yield {"token": word + " ", "finish_reason": None}

    # Final token
    yield {"token": "", "finish_reason": "stop"}


async def simulate_slow_consumer_stream():
    """Simulate stream with slow consumer (backpressure test).

    Yields:
        Data chunks.
    """
    for i in range(20):
        await asyncio.sleep(0.01)  # Fast producer
        yield f"chunk_{i}"


async def simulate_error_stream():
    """Simulate stream with error.

    Yields:
        Data chunks.

    Raises:
        Exception: Simulated error.
    """
    yield "chunk_1"
    yield "chunk_2"
    raise Exception("Simulated stream error")


async def main():
    """Run streaming capability demo."""
    print("=" * 70)
    print("StreamingCapability Demo")
    print("=" * 70)
    print()

    # Initialize capability
    print("1. Initializing StreamingCapability...")
    config = StreamingConfig(
        protocol=StreamProtocol.SSE,
        buffer_size=10,
        enable_compression=False,
        chunk_timeout_seconds=5.0,
        backpressure_threshold=0.8,
    )
    streaming = StreamingCapability(config)
    print("   [OK] Protocol: SSE")
    print("   [OK] Buffer size: 10 chunks")
    print("   [OK] Backpressure threshold: 80%")
    print()

    # Demo 1: Basic streaming
    print("=" * 70)
    print("2. Demo 1: Basic LLM Token Streaming")
    print("=" * 70)
    print()

    print("Prompt: 'Hello, how are you?'")
    print("\nStreaming response:")
    print("-" * 70)

    tokens_received = 0
    async for chunk in streaming.stream_response(
        operation=simulate_llm_streaming,
        operation_name="llm_completion",
        prompt="Hello, how are you?",
    ):
        if chunk.chunk_type == ChunkType.DATA:
            token = chunk.data.get("token", "")
            if token:
                print(token, end="", flush=True)
                tokens_received += 1
        elif chunk.chunk_type == ChunkType.DONE:
            print("\n" + "-" * 70)
            print(f"[DONE] Received {tokens_received} tokens")

    print()

    # Demo 2: SSE-formatted stream
    print("=" * 70)
    print("3. Demo 2: SSE-Formatted Stream")
    print("=" * 70)
    print()

    print("Streaming in SSE format (first 3 events):")
    print("-" * 70)

    count = 0
    async for sse_event in streaming.create_sse_stream(
        operation=simulate_llm_streaming,
        operation_name="sse_stream",
        prompt="SSE test",
    ):
        if count < 3:
            print(sse_event)
            count += 1
        else:
            break  # Only show first 3

    print("-" * 70)
    print(f"[INFO] Showing {count} SSE events (stream continues...)")
    print()

    # Demo 3: WebSocket-formatted stream
    print("=" * 70)
    print("4. Demo 3: WebSocket-Formatted Stream")
    print("=" * 70)
    print()

    print("Streaming in WebSocket JSON format (first 3 messages):")
    print("-" * 70)

    count = 0
    async for ws_msg in streaming.create_websocket_stream(
        operation=simulate_llm_streaming,
        operation_name="websocket_stream",
        prompt="WebSocket test",
    ):
        if count < 3:
            print(ws_msg)
            count += 1
        else:
            break

    print("-" * 70)
    print(f"[INFO] Showing {count} WebSocket messages (stream continues...)")
    print()

    # Demo 4: Backpressure handling
    print("=" * 70)
    print("5. Demo 4: Backpressure Handling")
    print("=" * 70)
    print()

    # Configure small buffer
    streaming.config.buffer_size = 5
    streaming.config.backpressure_threshold = 0.6  # 3/5

    print("Fast producer, slow consumer (buffer size: 5):")
    chunks_received = 0

    async for chunk in streaming.stream_response(
        operation=simulate_slow_consumer_stream,
        operation_name="backpressure_test",
    ):
        if chunk.chunk_type == ChunkType.DATA:
            chunks_received += 1
            # Simulate slow consumer
            await asyncio.sleep(0.02)

            if chunks_received % 5 == 0:
                print(f"  Processed {chunks_received} chunks...")

    print(f"\n[RESULT] All {chunks_received} chunks processed")

    # Check metrics
    metrics = await streaming.get_metrics()
    backpressure_events = metrics.output["backpressure_events"]
    print(f"[METRICS] Backpressure events: {backpressure_events}")
    print()

    # Demo 5: Error handling
    print("=" * 70)
    print("6. Demo 5: Error Handling in Streams")
    print("=" * 70)
    print()

    print("Stream with error:")
    error_received = False

    async for chunk in streaming.stream_response(
        operation=simulate_error_stream,
        operation_name="error_stream",
    ):
        if chunk.chunk_type == ChunkType.DATA:
            print(f"  [DATA] {chunk.data}")
        elif chunk.chunk_type == ChunkType.ERROR:
            print(f"  [ERROR] {chunk.data['error']}")
            error_received = True

    print(f"\n[RESULT] Error gracefully handled: {error_received}")
    print()

    # Demo 6: Concurrent streams
    print("=" * 70)
    print("7. Demo 6: Concurrent Streams")
    print("=" * 70)
    print()

    async def stream_generator(stream_num: int):
        for i in range(5):
            await asyncio.sleep(0.01)
            yield f"Stream {stream_num}: chunk {i}"

    print("Starting 3 concurrent streams...")

    # Start multiple streams concurrently
    async def consume_stream(stream_num: int):
        chunks = 0
        async for chunk in streaming.stream_response(
            operation=stream_generator,
            operation_name=f"concurrent_{stream_num}",
            stream_num=stream_num,
        ):
            if chunk.chunk_type == ChunkType.DATA:
                chunks += 1
        return chunks

    results = await asyncio.gather(
        consume_stream(1), consume_stream(2), consume_stream(3)
    )

    for i, chunk_count in enumerate(results, 1):
        print(f"  Stream {i}: {chunk_count} chunks received")

    # Check active streams
    active = await streaming.get_active_streams()
    print(f"\n[ACTIVE] Current active streams: {active.output['count']}")
    print()

    # Demo 7: Metrics
    print("=" * 70)
    print("8. Metrics Summary")
    print("=" * 70)
    print()

    metrics = await streaming.get_metrics()
    print("Overall Metrics:")
    print(f"  - Total streams: {metrics.output['total_streams']}")
    print(f"  - Active streams: {metrics.output['active_streams']}")
    print(f"  - Total chunks: {metrics.output['total_chunks']}")
    print(f"  - Errors: {metrics.output['errors']}")
    print(f"  - Backpressure events: {metrics.output['backpressure_events']}")
    print()

    # Demo 8: Buffer status
    print("=" * 70)
    print("9. Buffer Status Check")
    print("=" * 70)
    print()

    # Create a stream and check its buffer
    stream_id = "buffer_test_stream"
    buffer = streaming._get_buffer(stream_id)

    # Simulate adding chunks
    from paracle_meta.capabilities.streaming import StreamChunk

    for i in range(3):
        chunk = StreamChunk(chunk_id=i, chunk_type=ChunkType.DATA, data=f"test{i}")
        await buffer.push(chunk)

    # Check status
    status = await streaming.get_buffer_status(stream_id=stream_id)
    print(f"Buffer Status for '{stream_id}':")
    print(f"  - Size: {status.output['buffer_size']} / {status.output['max_size']}")
    print(
        f"  - Utilization: {status.output['utilization']:.1%}"
    )
    print(
        f"  - Backpressure: {status.output['backpressure_active']}"
    )
    print()

    print("=" * 70)
    print("Demo Complete!")
    print("=" * 70)
    print()
    print("Key Takeaways:")
    print("  1. Stream LLM responses in real-time as tokens arrive")
    print("  2. SSE for unidirectional streaming (web apps)")
    print("  3. WebSocket for bidirectional streaming (chat apps)")
    print("  4. Automatic backpressure handling prevents buffer overflow")
    print("  5. Graceful error handling with error chunks")
    print("  6. Support for concurrent streams with independent buffers")
    print()


if __name__ == "__main__":
    asyncio.run(main())
