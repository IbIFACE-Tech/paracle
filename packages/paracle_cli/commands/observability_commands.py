"""CLI commands for observability features.

Follows API-first pattern: CLI -> API -> Core
Falls back to direct core access when API unavailable.

Provides commands for:
- Exporting metrics (Prometheus/JSON)
- Viewing traces
- Managing alerts
- Exporting observability data
"""

import json
from pathlib import Path

import click
from paracle_observability import (
    AlertSeverity,
    MetricsExporter,
    get_alert_manager,
    get_metrics_registry,
    get_tracer,
)
from rich.console import Console
from rich.table import Table

from paracle_cli.api_client import APIClient, use_api_or_fallback

console = Console()


# =============================================================================
# Metrics API Functions
# =============================================================================


def _api_metrics_list(client: APIClient) -> dict:
    """List metrics via API."""
    return client.metrics_list()


def _api_metrics_export(client: APIClient, format: str) -> dict:
    """Export metrics via API."""
    return client.metrics_export(format=format)


def _api_metrics_reset(client: APIClient) -> dict:
    """Reset metrics via API."""
    return client.metrics_reset()  # noqa: E501


# =============================================================================
# Metrics Fallback Functions
# =============================================================================


def _fallback_metrics_list() -> dict:
    """List metrics directly from core."""
    registry = get_metrics_registry()
    metrics = []

    # Counters
    for key, value in registry._counters.items():
        name, labels = _parse_metric_key(key)
        metrics.append(
            {"name": name, "type": "counter", "labels": labels, "value": value}
        )

    # Gauges
    for key, value in registry._gauges.items():
        name, labels = _parse_metric_key(key)
        metrics.append(
            {"name": name, "type": "gauge", "labels": labels, "value": value}
        )

    # Histograms
    for key, observations in registry._histograms.items():
        name, labels = _parse_metric_key(key)
        metrics.append(
            {
                "name": name,
                "type": "histogram",
                "labels": labels,
                "value": list(observations),
            }
        )

    return {"metrics": metrics, "total": len(metrics)}


def _fallback_metrics_export(format: str) -> dict:
    """Export metrics directly from core."""
    registry = get_metrics_registry()
    exporter = MetricsExporter(registry)

    if format == "prometheus":
        content = exporter.export_prometheus()
    elif format == "json":
        content = json.dumps(exporter.export_json(), indent=2)
    else:
        raise ValueError(f"Invalid format: {format}. Use prometheus or json.")

    return {"format": format, "content": content}


def _fallback_metrics_reset() -> dict:
    """Reset metrics directly via core."""
    registry = get_metrics_registry()
    registry._counters.clear()
    registry._gauges.clear()
    registry._histograms.clear()
    return {"message": "All metrics reset"}


# =============================================================================
# Trace API Functions
# =============================================================================


def _api_traces_list(client: APIClient, limit: int) -> dict:
    """List traces via API."""
    return client.traces_list(limit=limit)


def _api_traces_get(client: APIClient, trace_id: str) -> dict:
    """Get trace via API."""
    return client.traces_get(trace_id)


def _api_traces_export(client: APIClient) -> dict:
    """Export traces via API."""
    return client.traces_export()


def _api_traces_clear(client: APIClient) -> dict:
    """Clear traces via API."""
    return client.traces_clear()


# =============================================================================
# Trace Fallback Functions
# =============================================================================


def _fallback_traces_list(limit: int) -> dict:
    """List traces directly from core."""
    tracer = get_tracer()
    spans = tracer.get_completed_spans()[-limit:]

    return {
        "spans": [
            {
                "trace_id": s.trace_id,
                "span_id": s.span_id,
                "parent_span_id": s.parent_span_id,
                "name": s.name,
                "status": (
                    s.status.value if hasattr(s.status, "value") else str(s.status)
                ),
                "duration_ms": s.duration_ms,
                "attributes": s.attributes or {},
                "events": s.events or [],
            }
            for s in spans
        ],
        "total": len(spans),
    }


def _fallback_traces_get(trace_id: str) -> dict:
    """Get trace directly from core."""
    tracer = get_tracer()
    spans = [s for s in tracer.get_completed_spans() if s.trace_id.startswith(trace_id)]

    if not spans:
        raise ValueError(f"Trace '{trace_id}' not found")

    return {
        "spans": [
            {
                "trace_id": s.trace_id,
                "span_id": s.span_id,
                "parent_span_id": s.parent_span_id,
                "name": s.name,
                "status": (
                    s.status.value if hasattr(s.status, "value") else str(s.status)
                ),
                "duration_ms": s.duration_ms,
                "attributes": s.attributes or {},
                "events": s.events or [],
            }
            for s in spans
        ],
        "total": len(spans),
    }


def _fallback_traces_export() -> dict:
    """Export traces directly from core."""
    tracer = get_tracer()
    data = tracer.export_jaeger()
    return {"format": "jaeger", "data": data}  # noqa: E501


def _fallback_traces_clear() -> dict:
    """Clear traces directly via core."""
    tracer = get_tracer()
    tracer.clear()
    return {"message": "All traces cleared successfully"}


# =============================================================================
# Alert API Functions
# =============================================================================


def _api_alerts_list(
    client: APIClient, severity: str | None, active_only: bool, limit: int
) -> dict:
    """List alerts via API."""
    return client.alerts_list(severity=severity, active_only=active_only, limit=limit)


def _api_alerts_rules(client: APIClient) -> dict:
    """List alert rules via API."""
    return client.alerts_rules()


def _api_alerts_evaluate(client: APIClient) -> dict:
    """Evaluate alerts via API."""
    return client.alerts_evaluate()


def _api_alerts_silence(client: APIClient, fingerprint: str, duration: int) -> dict:
    """Silence alert via API."""
    return client.alerts_silence(fingerprint, duration)


# =============================================================================
# Alert Fallback Functions
# =============================================================================


def _fallback_alerts_list(severity: str | None, active_only: bool, limit: int) -> dict:
    """List alerts directly from core."""
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

    return {
        "alerts": [
            {
                "fingerprint": a.fingerprint,
                "rule_name": a.rule_name,
                "severity": a.severity.value,
                "state": a.state.value,
                "message": a.message,
                "started_at": a.started_at.isoformat() if a.started_at else None,
                "resolved_at": a.resolved_at.isoformat() if a.resolved_at else None,
                "duration_seconds": a.duration_seconds,
                "labels": a.labels or {},
            }
            for a in alerts
        ],
        "total": len(alerts),
    }


def _fallback_alerts_rules() -> dict:
    """List alert rules directly from core."""
    manager = get_alert_manager()
    rules = manager._rules

    return {
        "rules": [
            {
                "name": r.name,
                "severity": r.severity.value,
                "for_duration": r.for_duration,
                "labels": r.labels,
            }
            for r in rules
        ],
        "total": len(rules),
    }


def _fallback_alerts_evaluate() -> dict:
    """Evaluate alerts directly via core."""
    manager = get_alert_manager()
    new_alerts = manager.evaluate_rules()

    return {
        "new_alerts": [
            {
                "fingerprint": a.fingerprint,
                "rule_name": a.rule_name,
                "severity": a.severity.value,
                "message": a.message,
            }
            for a in new_alerts
        ],
        "total_rules_evaluated": len(manager._rules),
    }


def _fallback_alerts_silence(fingerprint: str, duration: int) -> dict:
    """Silence alert directly via core."""
    manager = get_alert_manager()
    manager.silence(fingerprint, duration)
    return {
        "fingerprint": fingerprint,
        "duration": duration,
        "message": f"Alert silenced for {duration} seconds",
    }


# ============================================================================
# CLI Commands - Observability Group
# ============================================================================


@click.group()
def observability():
    """Observability commands (metrics, tracing, alerts)."""
    pass


# =============================================================================
# Metrics Commands
# =============================================================================


@observability.group()
def metrics():
    """Prometheus metrics management."""
    pass


@metrics.command("export")
@click.option(
    "--format",
    type=click.Choice(["prometheus", "json"]),
    default="prometheus",
    help="Export format",
)
@click.option("--output", "-o", type=click.Path(), help="Output file (default: stdout)")
def metrics_export(format: str, output: str | None):
    """Export current metrics.

    Examples:
        paracle metrics export --format prometheus
        paracle metrics export --format json -o metrics.json
    """
    try:
        result = use_api_or_fallback(
            _api_metrics_export,
            _fallback_metrics_export,
            format,
        )

        content = result.get("content", "")

        if output:
            Path(output).write_text(content)
            console.print(f"[green]Metrics exported to {output}[/green]")
        else:
            console.print(content)

    except Exception as e:
        console.print(f"[red]Error: {e}[/red]")
        raise SystemExit(1)


@metrics.command("list")
@click.option("--json", "as_json", is_flag=True, help="Output as JSON")
def metrics_list(as_json: bool):
    """List all registered metrics."""
    try:
        result = use_api_or_fallback(
            _api_metrics_list,
            _fallback_metrics_list,
        )

        if as_json:
            click.echo(json.dumps(result, indent=2, default=str))
        else:
            metrics_data = result.get("metrics", [])

            if not metrics_data:
                console.print("[yellow]No metrics registered[/yellow]")
                return

            table = Table(title="Registered Metrics")
            table.add_column("Name", style="cyan")
            table.add_column("Type", style="magenta")
            table.add_column("Labels", style="yellow")
            table.add_column("Value", style="green")

            for m in metrics_data:
                labels_str = (
                    ", ".join(f"{k}={v}" for k, v in m.get("labels", {}).items())
                    if isinstance(m.get("labels"), dict)
                    else str(m.get("labels", "-"))
                )
                value = m.get("value", "")
                if isinstance(value, list):
                    value = f"{len(value)} obs"
                table.add_row(m["name"], m["type"], labels_str or "-", str(value))

            console.print(table)

    except Exception as e:
        console.print(f"[red]Error: {e}[/red]")
        raise SystemExit(1)


@metrics.command("reset")
@click.confirmation_option(prompt="Are you sure you want to reset all metrics?")
def metrics_reset():
    """Reset all metrics to zero."""
    try:
        result = use_api_or_fallback(
            _api_metrics_reset,
            _fallback_metrics_reset,
        )

        console.print(f"[green]{result.get('message', 'All metrics reset')}[/green]")

    except Exception as e:
        console.print(f"[red]Error: {e}[/red]")
        raise SystemExit(1)


# =============================================================================
# Tracing Commands
# =============================================================================


@observability.group()
def trace():
    """Distributed tracing management."""
    pass


@trace.command("list")
@click.option("--limit", "-n", default=20, help="Number of traces to show")
@click.option("--json", "as_json", is_flag=True, help="Output as JSON")
def trace_list(limit: int, as_json: bool):
    """List completed traces."""
    try:
        result = use_api_or_fallback(
            _api_traces_list,
            _fallback_traces_list,
            limit,
        )

        if as_json:
            click.echo(json.dumps(result, indent=2, default=str))
        else:
            spans = result.get("spans", [])

            if not spans:
                console.print("[yellow]No traces found[/yellow]")
                return

            table = Table(title=f"Recent Traces (last {limit})")
            table.add_column("Trace ID", style="cyan")
            table.add_column("Span ID", style="magenta")
            table.add_column("Name", style="white")
            table.add_column("Duration (ms)", style="green")
            table.add_column("Status", style="yellow")

            for span in spans:
                status = span.get("status", "unknown")
                status_style = "green" if status == "ok" else "red"
                table.add_row(
                    span["trace_id"][:16] + "...",
                    span["span_id"][:16] + "...",
                    span["name"],
                    f"{span.get('duration_ms', 0):.2f}",
                    f"[{status_style}]{status}[/]",
                )

            console.print(table)

    except Exception as e:
        console.print(f"[red]Error: {e}[/red]")
        raise SystemExit(1)


@trace.command("show")
@click.argument("trace_id")
@click.option("--json", "as_json", is_flag=True, help="Output as JSON")
def trace_show(trace_id: str, as_json: bool):
    """Show detailed trace information.

    Args:
        trace_id: Trace ID to display
    """
    try:
        result = use_api_or_fallback(
            _api_traces_get,
            _fallback_traces_get,
            trace_id,
        )

        if as_json:
            click.echo(json.dumps(result, indent=2, default=str))
        else:
            spans = result.get("spans", [])

            if not spans:
                console.print(f"[red]Trace {trace_id} not found[/red]")
                return

            console.print(f"\n[bold cyan]Trace {spans[0]['trace_id']}[/]\n")

            for span in spans:
                indent = "  " * (span.get("parent_span_id") is not None)
                console.print(f"{indent}[yellow] [/] {span['name']}")
                console.print(f"{indent}  Duration: {span.get('duration_ms', 0):.2f}ms")
                console.print(f"{indent}  Status: {span.get('status', 'unknown')}")

                if span.get("attributes"):
                    console.print(f"{indent}  Attributes:")
                    for key, value in span["attributes"].items():
                        console.print(f"{indent}    {key}: {value}")

                if span.get("events"):
                    console.print(f"{indent}  Events:")
                    for event in span["events"]:
                        event_name = (
                            event.get("name", "")
                            if isinstance(event, dict)
                            else str(event)
                        )
                        console.print(f"{indent}    [{event_name}]")

                console.print()

    except Exception as e:
        console.print(f"[red]Error: {e}[/red]")
        raise SystemExit(1)


@trace.command("export")
@click.option("--output", "-o", required=True, help="Output file (Jaeger JSON format)")
def trace_export(output: str):
    """Export traces in Jaeger JSON format.

    Example:
        paracle trace export -o traces.json
    """
    try:
        result = use_api_or_fallback(
            _api_traces_export,
            _fallback_traces_export,
        )

        data = result.get("data", {})
        Path(output).write_text(json.dumps(data, indent=2))
        console.print(f"[green]Traces exported to {output}[/green]")

    except Exception as e:
        console.print(f"[red]Error: {e}[/red]")
        raise SystemExit(1)


@trace.command("clear")
@click.confirmation_option(prompt="Are you sure you want to clear all traces?")
def trace_clear():
    """Clear all completed traces."""
    try:
        result = use_api_or_fallback(
            _api_traces_clear,
            _fallback_traces_clear,
        )

        console.print(f"[green]{result.get('message', 'All traces cleared')}[/green]")

    except Exception as e:
        console.print(f"[red]Error: {e}[/red]")
        raise SystemExit(1)


# =============================================================================
# Alert Commands
# =============================================================================


@observability.group()
def alerts():
    """Alert management."""
    pass


@alerts.command("list")
@click.option(
    "--severity",
    type=click.Choice(["info", "warning", "error", "critical"]),
    help="Filter by severity",
)
@click.option("--active-only", is_flag=True, help="Show only active alerts")
@click.option("--limit", "-n", default=50, help="Maximum alerts to return")
@click.option("--json", "as_json", is_flag=True, help="Output as JSON")
def alerts_list(severity: str | None, active_only: bool, limit: int, as_json: bool):
    """List alerts.

    Examples:
        paracle alerts list
        paracle alerts list --severity critical
        paracle alerts list --active-only
    """
    try:
        result = use_api_or_fallback(
            _api_alerts_list,
            _fallback_alerts_list,
            severity,
            active_only,
            limit,
        )

        if as_json:
            click.echo(json.dumps(result, indent=2, default=str))
        else:
            alerts_data = result.get("alerts", [])

            if not alerts_data:
                console.print("[yellow]No alerts found[/yellow]")
                return

            table = Table(title="Alerts")
            table.add_column("Rule", style="cyan")
            table.add_column("Severity", style="magenta")
            table.add_column("State", style="white")
            table.add_column("Message", style="yellow")
            table.add_column("Duration", style="green")

            for alert in alerts_data:
                sev = alert.get("severity", "")
                severity_emoji = {
                    "info": "",
                    "warning": "",
                    "error": "",
                    "critical": "",
                }.get(sev, "")

                state = alert.get("state", "")
                state_style = {
                    "pending": "yellow",
                    "firing": "red",
                    "resolved": "green",
                    "silenced": "dim",
                }.get(state, "white")

                table.add_row(
                    alert.get("rule_name", ""),
                    f"{severity_emoji} {sev}",
                    f"[{state_style}]{state}[/]",
                    alert.get("message", ""),
                    f"{alert.get('duration_seconds', 0):.0f}s",
                )

            console.print(table)

    except Exception as e:
        console.print(f"[red]Error: {e}[/red]")
        raise SystemExit(1)


@alerts.command("rules")
@click.option("--json", "as_json", is_flag=True, help="Output as JSON")
def alerts_rules(as_json: bool):
    """List alert rules."""
    try:
        result = use_api_or_fallback(
            _api_alerts_rules,
            _fallback_alerts_rules,
        )

        if as_json:
            click.echo(json.dumps(result, indent=2, default=str))
        else:
            rules = result.get("rules", [])

            if not rules:
                console.print("[yellow]No alert rules configured[/yellow]")
                return

            table = Table(title="Alert Rules")
            table.add_column("Name", style="cyan")
            table.add_column("Severity", style="magenta")
            table.add_column("For Duration", style="yellow")
            table.add_column("Labels", style="white")

            for rule in rules:
                labels = rule.get("labels", {})
                labels_str = ", ".join(f"{k}={v}" for k, v in labels.items())
                table.add_row(
                    rule.get("name", ""),
                    rule.get("severity", ""),
                    f"{rule.get('for_duration', 0)}s",
                    labels_str or "-",
                )

            console.print(table)

    except Exception as e:
        console.print(f"[red]Error: {e}[/red]")
        raise SystemExit(1)


@alerts.command("silence")
@click.argument("fingerprint")
@click.option("--duration", "-d", default=3600, help="Silence duration in seconds")
def alerts_silence(fingerprint: str, duration: int):
    """Silence an alert.

    Args:
        fingerprint: Alert fingerprint to silence

    Example:
        paracle alerts silence high_error_rate_env=prod --duration 7200
    """
    try:
        result = use_api_or_fallback(
            _api_alerts_silence,
            _fallback_alerts_silence,
            fingerprint,
            duration,
        )

        console.print(f"[green]{result.get('message', 'Alert silenced')}[/green]")

    except Exception as e:
        console.print(f"[red]Error: {e}[/red]")
        raise SystemExit(1)


@alerts.command("evaluate")
@click.option("--json", "as_json", is_flag=True, help="Output as JSON")
def alerts_evaluate(as_json: bool):
    """Manually evaluate alert rules."""
    try:
        result = use_api_or_fallback(
            _api_alerts_evaluate,
            _fallback_alerts_evaluate,
        )

        if as_json:
            click.echo(json.dumps(result, indent=2, default=str))
        else:
            new_alerts = result.get("new_alerts", [])

            if not new_alerts:
                console.print("[green]No new alerts[/green]")
                return

            console.print(f"[yellow]{len(new_alerts)} new alert(s) fired:[/yellow]")
            for alert in new_alerts:
                console.print(
                    f"  - {alert.get('rule_name', '')}: {alert.get('message', '')}"
                )

    except Exception as e:
        console.print(f"[red]Error: {e}[/red]")
        raise SystemExit(1)


# =============================================================================
# Utility Functions
# =============================================================================


def _parse_metric_key(key: str) -> tuple[str, dict]:
    """Parse metric key into name and labels dict."""
    parts = key.split("_", 1)
    if len(parts) == 2:
        name = parts[0]
        labels = {}
        for pair in parts[1].split("_"):
            if "=" in pair:
                k, v = pair.split("=", 1)
                labels[k] = v
        return name, labels
    return key, {}


# =============================================================================
# Register CLI
# =============================================================================


def register_cli(app):
    """Register observability commands with main CLI."""
    app.add_command(observability)
