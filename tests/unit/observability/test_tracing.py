"""Tests for distributed tracing."""

import time

import pytest
from paracle_observability.tracing import (
    SpanKind,
    SpanStatus,
    TracingProvider,
    get_tracer,
    trace_async,
    trace_span,
)


def test_span_creation():
    """Test span creation."""
    tracer = TracingProvider("test-service")
    span = tracer.start_trace("test-operation")

    assert span.name == "test-operation"
    assert span.kind == SpanKind.INTERNAL
    assert span.status == SpanStatus.UNSET
    assert span.attributes["service.name"] == "test-service"


def test_span_hierarchy():
    """Test parent-child span relationship."""
    tracer = TracingProvider("test-service")

    parent = tracer.start_trace("parent-operation")
    child = tracer.start_span("child-operation", parent)

    assert child.trace_id == parent.trace_id
    assert child.parent_span_id == parent.span_id


def test_span_attributes():
    """Test span attributes."""
    tracer = TracingProvider("test-service")
    span = tracer.start_trace("test-operation")

    span.set_attribute("user.id", "123")
    span.set_attribute("request.method", "POST")

    assert span.attributes["user.id"] == "123"
    assert span.attributes["request.method"] == "POST"


def test_span_events():
    """Test span events."""
    tracer = TracingProvider("test-service")
    span = tracer.start_trace("test-operation")

    span.add_event("cache_hit", {"key": "user:123"})
    span.add_event("database_query", {"table": "users", "duration_ms": 15})

    assert len(span.events) == 2
    assert span.events[0]["name"] == "cache_hit"
    assert span.events[1]["attributes"]["table"] == "users"


def test_span_status():
    """Test span status."""
    tracer = TracingProvider("test-service")
    span = tracer.start_trace("test-operation")

    span.set_status(SpanStatus.OK)
    assert span.status == SpanStatus.OK

    span.set_status(SpanStatus.ERROR, "Database connection failed")
    assert span.status == SpanStatus.ERROR
    assert span.attributes["status.description"] == "Database connection failed"


def test_span_duration():
    """Test span duration calculation."""
    tracer = TracingProvider("test-service")
    span = tracer.start_trace("test-operation")

    time.sleep(0.01)
    span.end()

    assert span.duration_ms >= 10.0  # At least 10ms


def test_trace_context_manager():
    """Test tracing context manager."""
    tracer = TracingProvider("test-service")

    with tracer.trace("test-operation") as span:
        span.set_attribute("test", "value")
        time.sleep(0.01)

    completed = tracer.get_completed_spans()
    assert len(completed) == 1
    assert completed[0].name == "test-operation"
    assert completed[0].status == SpanStatus.OK


def test_trace_context_manager_error():
    """Test tracing context manager with error."""
    tracer = TracingProvider("test-service")

    with pytest.raises(ValueError):
        with tracer.trace("test-operation") as span:
            raise ValueError("Test error")

    completed = tracer.get_completed_spans()
    assert len(completed) == 1
    assert completed[0].status == SpanStatus.ERROR
    assert len(completed[0].events) > 0
    assert "exception.message" in completed[0].events[0]["attributes"]


def test_trace_decorator():
    """Test trace decorator."""

    @trace_span("decorated-function")
    def test_function(x, y):
        return x + y

    result = test_function(2, 3)
    assert result == 5

    tracer = get_tracer()
    completed = tracer.get_completed_spans()
    assert len(completed) > 0
    assert completed[-1].name == "decorated-function"
    assert completed[-1].attributes["function"] == "test_function"


@pytest.mark.asyncio
async def test_trace_async_decorator():
    """Test async trace decorator."""

    @trace_async("async-function")
    async def async_function(x):
        await asyncio.sleep(0.01)
        return x * 2

    import asyncio

    result = await async_function(5)
    assert result == 10

    tracer = get_tracer()
    completed = tracer.get_completed_spans()
    assert len(completed) > 0
    assert completed[-1].name == "async-function"


def test_jaeger_export():
    """Test Jaeger format export."""
    tracer = TracingProvider("test-service")

    with tracer.trace("parent") as parent:
        parent.set_attribute("http.method", "GET")
        with tracer.trace("child") as child:
            child.set_attribute("db.query", "SELECT * FROM users")

    export_data = tracer.export_jaeger()

    assert "data" in export_data
    assert len(export_data["data"]) > 0
    assert "spans" in export_data["data"][0]
    assert len(export_data["data"][0]["spans"]) == 2


def test_multiple_traces():
    """Test multiple independent traces."""
    tracer = TracingProvider("test-service")

    # Trace 1
    with tracer.trace("operation-1"):
        pass

    trace1_id = tracer._current_trace_id

    # Trace 2
    with tracer.trace("operation-2"):
        pass

    completed = tracer.get_completed_spans()
    assert len(completed) == 2

    # Different trace IDs
    trace_ids = {span.trace_id for span in completed}
    assert len(trace_ids) == 2
