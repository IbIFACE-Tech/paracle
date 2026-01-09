"""OpenTelemetry distributed tracing integration.

Provides distributed tracing capabilities using OpenTelemetry:
- Span creation and context propagation
- Trace correlation across services
- Integration with Jaeger
- Automatic instrumentation decorators
"""

import time
import uuid
from collections.abc import Callable
from contextlib import contextmanager
from dataclasses import dataclass, field
from functools import wraps
from typing import Any


class SpanKind:
    """OpenTelemetry span kinds."""

    INTERNAL = "internal"
    SERVER = "server"
    CLIENT = "client"
    PRODUCER = "producer"
    CONSUMER = "consumer"


class SpanStatus:
    """Span status codes."""

    UNSET = "unset"
    OK = "ok"
    ERROR = "error"


@dataclass
class Span:
    """Distributed tracing span."""

    trace_id: str
    span_id: str
    parent_span_id: str | None
    name: str
    kind: str
    start_time: float
    end_time: float | None = None
    status: str = SpanStatus.UNSET
    attributes: dict[str, Any] = field(default_factory=dict)
    events: list[dict[str, Any]] = field(default_factory=list)
    links: list[str] = field(default_factory=list)

    def set_attribute(self, key: str, value: Any):
        """Add attribute to span."""
        self.attributes[key] = value

    def add_event(self, name: str, attributes: dict[str, Any] | None = None):
        """Add event to span."""
        self.events.append(
            {
                "name": name,
                "timestamp": time.time(),
                "attributes": attributes or {},
            }
        )

    def set_status(self, status: str, description: str = ""):
        """Set span status."""
        self.status = status
        if description:
            self.attributes["status.description"] = description

    def end(self, status: str | None = None):
        """End span."""
        self.end_time = time.time()
        if status:
            self.status = status

    @property
    def duration_ms(self) -> float:
        """Get span duration in milliseconds."""
        if self.end_time:
            return (self.end_time - self.start_time) * 1000
        return 0.0

    def to_jaeger_format(self) -> dict[str, Any]:
        """Export span in Jaeger format."""
        return {
            "traceID": self.trace_id,
            "spanID": self.span_id,
            "operationName": self.name,
            "references": (
                [
                    {
                        "refType": "CHILD_OF",
                        "traceID": self.trace_id,
                        "spanID": self.parent_span_id,
                    }
                ]
                if self.parent_span_id
                else []
            ),
            "startTime": int(self.start_time * 1_000_000),  # microseconds
            "duration": int(self.duration_ms * 1000),  # microseconds
            "tags": [
                {"key": k, "type": "string", "value": str(v)}
                for k, v in self.attributes.items()
            ],
            "logs": [
                {
                    "timestamp": int(event["timestamp"] * 1_000_000),
                    "fields": [
                        {"key": k, "value": v} for k, v in event["attributes"].items()
                    ],
                }
                for event in self.events
            ],
        }


class TracingProvider:
    """Distributed tracing provider."""

    def __init__(self, service_name: str = "paracle"):
        self.service_name = service_name
        self._active_spans: dict[str, Span] = {}
        self._completed_spans: list[Span] = []
        self._current_trace_id: str | None = None
        self._current_span_id: str | None = None

    def start_trace(self, name: str, kind: str = SpanKind.INTERNAL) -> Span:
        """Start new trace."""
        trace_id = str(uuid.uuid4())
        span_id = str(uuid.uuid4())

        span = Span(
            trace_id=trace_id,
            span_id=span_id,
            parent_span_id=None,
            name=name,
            kind=kind,
            start_time=time.time(),
        )

        span.set_attribute("service.name", self.service_name)
        self._active_spans[span_id] = span
        self._current_trace_id = trace_id
        self._current_span_id = span_id

        return span

    def start_span(
        self,
        name: str,
        parent_span: Span | None = None,
        kind: str = SpanKind.INTERNAL,
    ) -> Span:
        """Start child span."""
        if parent_span:
            trace_id = parent_span.trace_id
            parent_span_id = parent_span.span_id
        else:
            # Use current context if available
            trace_id = self._current_trace_id or str(uuid.uuid4())
            parent_span_id = self._current_span_id

        span_id = str(uuid.uuid4())

        span = Span(
            trace_id=trace_id,
            span_id=span_id,
            parent_span_id=parent_span_id,
            name=name,
            kind=kind,
            start_time=time.time(),
        )

        span.set_attribute("service.name", self.service_name)
        self._active_spans[span_id] = span
        self._current_span_id = span_id

        return span

    def end_span(self, span: Span, status: str | None = None):
        """End span and move to completed."""
        span.end(status)
        if span.span_id in self._active_spans:
            del self._active_spans[span.span_id]
        self._completed_spans.append(span)

        # Reset current span to parent
        if span.parent_span_id:
            self._current_span_id = span.parent_span_id
        else:
            self._current_span_id = None
            self._current_trace_id = None

    @contextmanager
    def trace(self, name: str, kind: str = SpanKind.INTERNAL):
        """Context manager for tracing."""
        span = self.start_span(name, kind=kind)
        try:
            yield span
            span.set_status(SpanStatus.OK)
        except Exception as e:
            span.set_status(SpanStatus.ERROR, str(e))
            span.add_event(
                "exception",
                {
                    "exception.message": str(e),
                    "exception.type": type(e).__name__,
                },
            )
            raise
        finally:
            # Don't pass status - keep what was already set
            self.end_span(span)

    def get_completed_spans(self, trace_id: str | None = None) -> list[Span]:
        """Get completed spans, optionally filtered by trace ID."""
        if trace_id:
            return [s for s in self._completed_spans if s.trace_id == trace_id]
        return self._completed_spans.copy()

    def export_jaeger(self, trace_id: str | None = None) -> dict[str, Any]:
        """Export spans in Jaeger format."""
        spans = self.get_completed_spans(trace_id)
        return {
            "data": [
                {
                    "traceID": trace_id or (spans[0].trace_id if spans else ""),
                    "spans": [span.to_jaeger_format() for span in spans],
                    "processes": {
                        "p1": {
                            "serviceName": self.service_name,
                            "tags": [],
                        }
                    },
                }
            ]
        }

    def clear(self):
        """Clear all spans."""
        self._active_spans.clear()
        self._completed_spans.clear()
        self._current_trace_id = None
        self._current_span_id = None


# Global tracer
_global_tracer: TracingProvider | None = None


def get_tracer(service_name: str = "paracle") -> TracingProvider:
    """Get global tracer."""
    global _global_tracer
    if _global_tracer is None:
        _global_tracer = TracingProvider(service_name)
    return _global_tracer


def trace_span(name: str, kind: str = SpanKind.INTERNAL):
    """Decorator to trace a function."""

    def decorator(func: Callable) -> Callable:
        @wraps(func)
        def wrapper(*args, **kwargs):
            tracer = get_tracer()
            with tracer.trace(name, kind=kind) as span:
                span.set_attribute("function", func.__name__)
                span.set_attribute("module", func.__module__)
                try:
                    result = func(*args, **kwargs)
                    return result
                except Exception as e:
                    span.add_event("error", {"error": str(e)})
                    raise

        return wrapper

    return decorator


def trace_async(name: str, kind: str = SpanKind.INTERNAL):
    """Decorator to trace an async function."""

    def decorator(func: Callable) -> Callable:
        @wraps(func)
        async def wrapper(*args, **kwargs):
            tracer = get_tracer()
            with tracer.trace(name, kind=kind) as span:
                span.set_attribute("function", func.__name__)
                span.set_attribute("module", func.__module__)
                try:
                    result = await func(*args, **kwargs)
                    return result
                except Exception as e:
                    span.add_event("error", {"error": str(e)})
                    raise

        return wrapper

    return decorator
