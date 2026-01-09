"""Observability API router.

Provides REST endpoints for metrics, tracing, and alerts:
- GET /api/metrics - List metrics
- GET /api/metrics/export - Export metrics (prometheus/json)
- POST /api/metrics/reset - Reset all metrics
- GET /api/traces - List traces
- GET /api/traces/{trace_id} - Get trace details
- GET /api/traces/export - Export traces (jaeger format)
- POST /api/traces/clear - Clear all traces
- GET /api/alerts - List alerts
- GET /api/alerts/rules - List alert rules
- POST /api/alerts/evaluate - Evaluate alert rules
- POST /api/alerts/{fingerprint}/silence - Silence an alert
"""

from datetime import datetime

from fastapi import APIRouter, HTTPException, Query
from paracle_observability import (
    AlertSeverity,
    MetricsExporter,
    get_alert_manager,
    get_metrics_registry,
    get_tracer,
)

from paracle_api.schemas.observability import (
    AlertEvaluateResponse,
    AlertListResponse,
    AlertResponse,
    AlertRuleListResponse,
    AlertRuleResponse,
    AlertSilenceRequest,
    AlertSilenceResponse,
    MetricsExportResponse,
    MetricsListResponse,
    MetricValue,
    SpanEvent,
    SpanResponse,
    TraceExportResponse,
    TraceListResponse,
)

router = APIRouter(prefix="/api", tags=["observability"])


# =============================================================================
# Metrics Endpoints
# =============================================================================


@router.get(
    "/metrics",
    response_model=MetricsListResponse,
    operation_id="listMetrics",
    summary="List all registered metrics",
)
async def list_metrics() -> MetricsListResponse:
    """List all registered metrics.

    Returns:
        List of metrics with their values
    """
    registry = get_metrics_registry()
    metrics = []

    # Counters
    for key, value in registry._counters.items():
        name, labels = _parse_metric_key(key)
        metrics.append(
            MetricValue(name=name, type="counter", labels=labels, value=value)
        )

    # Gauges
    for key, value in registry._gauges.items():
        name, labels = _parse_metric_key(key)
        metrics.append(MetricValue(name=name, type="gauge", labels=labels, value=value))

    # Histograms
    for key, observations in registry._histograms.items():
        name, labels = _parse_metric_key(key)
        metrics.append(
            MetricValue(
                name=name, type="histogram", labels=labels, value=list(observations)
            )
        )

    return MetricsListResponse(metrics=metrics, total=len(metrics))


@router.get(
    "/metrics/export",
    response_model=MetricsExportResponse,
    operation_id="exportMetrics",
    summary="Export metrics in specified format",
)
async def export_metrics(
    format: str = Query("prometheus", description="Export format (prometheus, json)"),
) -> MetricsExportResponse:
    """Export metrics in specified format.

    Args:
        format: Export format (prometheus or json)

    Returns:
        Exported metrics content
    """
    registry = get_metrics_registry()
    exporter = MetricsExporter(registry)

    if format == "prometheus":
        content = exporter.export_prometheus()
    elif format == "json":
        import json

        content = json.dumps(exporter.export_json(), indent=2)
    else:
        raise HTTPException(
            status_code=400, detail=f"Invalid format: {format}. Use prometheus or json."
        )

    return MetricsExportResponse(format=format, content=content)


@router.post(
    "/metrics/reset",
    operation_id="resetMetrics",
    summary="Reset all metrics",
)
async def reset_metrics() -> dict:
    """Reset all metrics to zero.

    Returns:
        Confirmation message
    """
    registry = get_metrics_registry()
    registry._counters.clear()
    registry._gauges.clear()
    registry._histograms.clear()

    return {"message": "All metrics reset successfully"}


# =============================================================================
# Tracing Endpoints
# =============================================================================


@router.get(
    "/traces",
    response_model=TraceListResponse,
    operation_id="listTraces",
    summary="List completed traces",
)
async def list_traces(
    limit: int = Query(20, ge=1, le=1000, description="Maximum traces to return"),
) -> TraceListResponse:
    """List completed traces.

    Args:
        limit: Maximum traces to return

    Returns:
        List of trace spans
    """
    tracer = get_tracer()
    spans = tracer.get_completed_spans()[-limit:]

    return TraceListResponse(
        spans=[_span_to_response(s) for s in spans],
        total=len(spans),
    )


@router.get(
    "/traces/{trace_id}",
    response_model=TraceListResponse,
    operation_id="getTrace",
    summary="Get trace details",
)
async def get_trace(trace_id: str) -> TraceListResponse:
    """Get all spans for a trace.

    Args:
        trace_id: Trace identifier (prefix match)

    Returns:
        List of spans in the trace

    Raises:
        HTTPException: 404 if trace not found
    """
    tracer = get_tracer()
    spans = [s for s in tracer.get_completed_spans() if s.trace_id.startswith(trace_id)]

    if not spans:
        raise HTTPException(status_code=404, detail=f"Trace '{trace_id}' not found")

    return TraceListResponse(
        spans=[_span_to_response(s) for s in spans],
        total=len(spans),
    )


@router.get(
    "/traces/export",
    response_model=TraceExportResponse,
    operation_id="exportTraces",
    summary="Export traces in Jaeger format",
)
async def export_traces() -> TraceExportResponse:
    """Export traces in Jaeger JSON format.

    Returns:
        Exported trace data
    """
    tracer = get_tracer()
    data = tracer.export_jaeger()

    return TraceExportResponse(format="jaeger", data=data)


@router.post(
    "/traces/clear",
    operation_id="clearTraces",
    summary="Clear all completed traces",
)
async def clear_traces() -> dict:
    """Clear all completed traces.

    Returns:
        Confirmation message
    """
    tracer = get_tracer()
    tracer.clear()

    return {"message": "All traces cleared successfully"}


# =============================================================================
# Alert Endpoints
# =============================================================================


@router.get(
    "/alerts",
    response_model=AlertListResponse,
    operation_id="listAlerts",
    summary="List alerts",
)
async def list_alerts(
    severity: str | None = Query(None, description="Filter by severity"),
    active_only: bool = Query(False, description="Show only active alerts"),
    limit: int = Query(50, ge=1, le=1000, description="Maximum alerts to return"),
) -> AlertListResponse:
    """List alerts with optional filters.

    Args:
        severity: Filter by severity (info, warning, error, critical)
        active_only: Show only active alerts
        limit: Maximum alerts to return

    Returns:
        List of alerts
    """
    manager = get_alert_manager()

    if active_only:
        if severity:
            alerts = manager.get_active_alerts(AlertSeverity[severity.upper()])
        else:
            alerts = manager.get_active_alerts()
    else:
        alerts = manager.get_alert_history(limit=limit)
        if severity:
            alerts = [a for a in alerts if a.severity.value == severity]

    return AlertListResponse(
        alerts=[_alert_to_response(a) for a in alerts],
        total=len(alerts),
    )


@router.get(
    "/alerts/rules",
    response_model=AlertRuleListResponse,
    operation_id="listAlertRules",
    summary="List alert rules",
)
async def list_alert_rules() -> AlertRuleListResponse:
    """List all configured alert rules.

    Returns:
        List of alert rules
    """
    manager = get_alert_manager()
    rules = manager._rules

    return AlertRuleListResponse(
        rules=[
            AlertRuleResponse(
                name=r.name,
                severity=r.severity.value,
                for_duration=r.for_duration,
                labels=r.labels,
            )
            for r in rules
        ],
        total=len(rules),
    )


@router.post(
    "/alerts/evaluate",
    response_model=AlertEvaluateResponse,
    operation_id="evaluateAlerts",
    summary="Evaluate alert rules",
)
async def evaluate_alerts() -> AlertEvaluateResponse:
    """Manually evaluate all alert rules.

    Returns:
        New alerts that were fired
    """
    manager = get_alert_manager()
    new_alerts = manager.evaluate_rules()

    return AlertEvaluateResponse(
        new_alerts=[_alert_to_response(a) for a in new_alerts],
        total_rules_evaluated=len(manager._rules),
    )


@router.post(
    "/alerts/{fingerprint}/silence",
    response_model=AlertSilenceResponse,
    operation_id="silenceAlert",
    summary="Silence an alert",
)
async def silence_alert(
    fingerprint: str, request: AlertSilenceRequest
) -> AlertSilenceResponse:
    """Silence an alert for a specified duration.

    Args:
        fingerprint: Alert fingerprint
        request: Silence request with duration

    Returns:
        Silence confirmation
    """
    manager = get_alert_manager()
    manager.silence(fingerprint, request.duration)

    return AlertSilenceResponse(
        fingerprint=fingerprint,
        duration=request.duration,
        message=f"Alert silenced for {request.duration} seconds",
    )


# =============================================================================
# Utility Functions
# =============================================================================


def _parse_metric_key(key: str) -> tuple[str, dict[str, str]]:
    """Parse metric key into name and labels dict."""
    parts = key.split("_", 1)
    if len(parts) == 2:
        name = parts[0]
        # Parse labels from key
        labels = {}
        for pair in parts[1].split("_"):
            if "=" in pair:
                k, v = pair.split("=", 1)
                labels[k] = v
        return name, labels
    return key, {}


def _span_to_response(span) -> SpanResponse:
    """Convert span to SpanResponse."""
    return SpanResponse(
        trace_id=span.trace_id,
        span_id=span.span_id,
        parent_span_id=span.parent_span_id,
        name=span.name,
        status=span.status.value if hasattr(span.status, "value") else str(span.status),
        start_time=span.start_time,
        end_time=span.end_time,
        duration_ms=span.duration_ms,
        attributes=span.attributes or {},
        events=[
            SpanEvent(
                name=e.get("name", ""),
                timestamp=datetime.fromisoformat(e.get("timestamp", "")),
                attributes=e.get("attributes", {}),
            )
            for e in (span.events or [])
        ],
    )


def _alert_to_response(alert) -> AlertResponse:
    """Convert alert to AlertResponse."""
    return AlertResponse(
        fingerprint=alert.fingerprint,
        rule_name=alert.rule_name,
        severity=alert.severity.value,
        state=alert.state.value,
        message=alert.message,
        started_at=alert.started_at,
        resolved_at=alert.resolved_at,
        duration_seconds=alert.duration_seconds,
        labels=alert.labels or {},
    )
