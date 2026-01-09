"""Observability API schemas.

Provides request/response models for metrics, tracing, and alerts endpoints.
"""

from datetime import datetime

from pydantic import BaseModel, Field

# =============================================================================
# Metrics Schemas
# =============================================================================


class MetricValue(BaseModel):
    """Single metric value."""

    name: str = Field(..., description="Metric name")
    type: str = Field(..., description="Metric type (counter, gauge, histogram)")
    labels: dict[str, str] = Field(default_factory=dict, description="Metric labels")
    value: float | list[float] = Field(..., description="Metric value(s)")


class MetricsListResponse(BaseModel):
    """List of metrics response."""

    metrics: list[MetricValue] = Field(..., description="List of metrics")
    total: int = Field(..., description="Total count")


class MetricsExportResponse(BaseModel):
    """Metrics export response."""

    format: str = Field(..., description="Export format")
    content: str = Field(..., description="Exported content")


# =============================================================================
# Tracing Schemas
# =============================================================================


class SpanEvent(BaseModel):
    """Span event."""

    name: str = Field(..., description="Event name")
    timestamp: datetime = Field(..., description="Event timestamp")
    attributes: dict[str, str] = Field(
        default_factory=dict, description="Event attributes"
    )


class SpanResponse(BaseModel):
    """Span details response."""

    trace_id: str = Field(..., description="Trace ID")
    span_id: str = Field(..., description="Span ID")
    parent_span_id: str | None = Field(None, description="Parent span ID")
    name: str = Field(..., description="Span name")
    status: str = Field(..., description="Span status")
    start_time: datetime = Field(..., description="Start timestamp")
    end_time: datetime | None = Field(None, description="End timestamp")
    duration_ms: float = Field(..., description="Duration in milliseconds")
    attributes: dict[str, str] = Field(
        default_factory=dict, description="Span attributes"
    )
    events: list[SpanEvent] = Field(default_factory=list, description="Span events")


class TraceListResponse(BaseModel):
    """List of traces response."""

    spans: list[SpanResponse] = Field(..., description="List of spans")
    total: int = Field(..., description="Total count")


class TraceExportResponse(BaseModel):
    """Trace export response."""

    format: str = Field(..., description="Export format (jaeger)")
    data: dict = Field(..., description="Exported trace data")


# =============================================================================
# Alert Schemas
# =============================================================================


class AlertRuleResponse(BaseModel):
    """Alert rule details."""

    name: str = Field(..., description="Rule name")
    severity: str = Field(..., description="Alert severity")
    for_duration: int = Field(..., description="Duration before firing (seconds)")
    labels: dict[str, str] = Field(default_factory=dict, description="Rule labels")


class AlertRuleListResponse(BaseModel):
    """List of alert rules response."""

    rules: list[AlertRuleResponse] = Field(..., description="List of rules")
    total: int = Field(..., description="Total count")


class AlertResponse(BaseModel):
    """Alert details response."""

    fingerprint: str = Field(..., description="Alert fingerprint")
    rule_name: str = Field(..., description="Rule name")
    severity: str = Field(..., description="Alert severity")
    state: str = Field(..., description="Alert state")
    message: str = Field(..., description="Alert message")
    started_at: datetime = Field(..., description="Alert start time")
    resolved_at: datetime | None = Field(None, description="Resolution time")
    duration_seconds: float = Field(..., description="Alert duration")
    labels: dict[str, str] = Field(default_factory=dict, description="Alert labels")


class AlertListResponse(BaseModel):
    """List of alerts response."""

    alerts: list[AlertResponse] = Field(..., description="List of alerts")
    total: int = Field(..., description="Total count")


class AlertSilenceRequest(BaseModel):
    """Request to silence an alert."""

    duration: int = Field(default=3600, description="Silence duration in seconds")


class AlertSilenceResponse(BaseModel):
    """Alert silence response."""

    fingerprint: str = Field(..., description="Silenced alert fingerprint")
    duration: int = Field(..., description="Silence duration")
    message: str = Field(..., description="Status message")


class AlertEvaluateResponse(BaseModel):
    """Alert evaluation response."""

    new_alerts: list[AlertResponse] = Field(
        default_factory=list, description="New alerts fired"
    )
    total_rules_evaluated: int = Field(..., description="Total rules evaluated")
