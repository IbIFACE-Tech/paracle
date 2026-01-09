"""Audit export functionality.

This module provides export capabilities for audit data,
supporting multiple formats for compliance reporting and SIEM integration.
"""

import csv
import json
from datetime import datetime
from enum import Enum
from pathlib import Path
from typing import Any, TextIO

from .events import AuditEvent, AuditEventType, AuditOutcome
from .exceptions import AuditExportError
from .storage import AuditStorage


def _validate_export_path(output_path: Path, base_path: Path | None = None) -> Path:
    """Validate export path to prevent path traversal attacks.

    Args:
        output_path: The requested output path.
        base_path: Optional base directory to restrict exports to.

    Returns:
        Validated absolute path.

    Raises:
        AuditExportError: If path traversal is detected.
    """
    # Check for path traversal indicators BEFORE resolution
    original_path_str = str(output_path)
    if ".." in original_path_str:
        raise AuditExportError(
            "Path traversal detected in export path",
            export_format="unknown",
            output_path=original_path_str,
        )

    # Check for home directory expansion attempts
    if original_path_str.startswith("~"):
        raise AuditExportError(
            "Home directory expansion not allowed in export path",
            export_format="unknown",
            output_path=original_path_str,
        )

    # Resolve to absolute path
    output_path = output_path.resolve()
    path_str = str(output_path)

    # If base_path is specified, ensure output is within it
    if base_path is not None:
        base_path = base_path.resolve()
        try:
            output_path.relative_to(base_path)
        except ValueError:
            raise AuditExportError(
                f"Export path must be within {base_path}",
                export_format="unknown",
                output_path=str(output_path),
            )

    # Prevent writing to sensitive system directories (Unix)
    sensitive_dirs = ["/etc", "/usr", "/bin", "/sbin", "/var/log", "/root"]
    for sensitive in sensitive_dirs:
        if path_str.startswith(sensitive):
            raise AuditExportError(
                f"Cannot export to sensitive directory: {sensitive}",
                export_format="unknown",
                output_path=path_str,
            )

    # Prevent writing to sensitive Windows directories
    windows_sensitive = ["C:\\Windows", "C:\\Program Files", "C:\\System32"]
    for sensitive in windows_sensitive:
        if path_str.lower().startswith(sensitive.lower()):
            raise AuditExportError(
                f"Cannot export to sensitive directory: {sensitive}",
                export_format="unknown",
                output_path=path_str,
            )

    return output_path


class ExportFormat(str, Enum):
    """Supported export formats."""

    JSON = "json"
    """JSON format (machine-readable)."""

    CSV = "csv"
    """CSV format (spreadsheet-compatible)."""

    JSONL = "jsonl"
    """JSON Lines format (streaming, SIEM-friendly)."""

    SYSLOG = "syslog"
    """Syslog format (RFC 5424)."""


class AuditExporter:
    """Exports audit data to various formats.

    Supports JSON, CSV, JSON Lines (JSONL), and Syslog formats
    for compliance reporting and SIEM integration.

    Example:
        >>> exporter = AuditExporter(storage)
        >>> exporter.export_to_file(
        ...     "audit_report.json",
        ...     format=ExportFormat.JSON,
        ...     start_time=datetime(2026, 1, 1),
        ... )
    """

    def __init__(self, storage: AuditStorage):
        """Initialize the exporter.

        Args:
            storage: The audit storage to export from.
        """
        self._storage = storage

    def export_to_file(
        self,
        output_path: Path | str,
        *,
        format: ExportFormat = ExportFormat.JSON,
        event_type: AuditEventType | None = None,
        actor: str | None = None,
        start_time: datetime | None = None,
        end_time: datetime | None = None,
        outcome: AuditOutcome | None = None,
        limit: int | None = None,
        base_path: Path | str | None = None,
    ) -> int:
        """Export audit events to a file.

        Args:
            output_path: Path to the output file.
            format: Export format.
            event_type: Filter by event type.
            actor: Filter by actor.
            start_time: Filter by start time.
            end_time: Filter by end time.
            outcome: Filter by outcome.
            limit: Maximum events to export.
            base_path: Optional base directory to restrict exports to.

        Returns:
            Number of events exported.

        Raises:
            AuditExportError: If export fails or path traversal is detected.
        """
        output_path = Path(output_path)
        base_path_obj = Path(base_path) if base_path else None

        # Validate path to prevent traversal attacks
        output_path = _validate_export_path(output_path, base_path_obj)

        # Query events
        events = self._storage.query(
            event_type=event_type,
            actor=actor,
            start_time=start_time,
            end_time=end_time,
            outcome=outcome,
            limit=limit or 100000,
        )

        try:
            output_path.parent.mkdir(parents=True, exist_ok=True)

            with open(output_path, "w", encoding="utf-8", newline="") as f:
                if format == ExportFormat.JSON:
                    self._export_json(f, events)
                elif format == ExportFormat.CSV:
                    self._export_csv(f, events)
                elif format == ExportFormat.JSONL:
                    self._export_jsonl(f, events)
                elif format == ExportFormat.SYSLOG:
                    self._export_syslog(f, events)
                else:
                    raise AuditExportError(
                        f"Unsupported format: {format}",
                        export_format=format.value,
                        output_path=str(output_path),
                    )

            return len(events)

        except Exception as e:
            raise AuditExportError(
                f"Export failed: {e}",
                export_format=format.value,
                output_path=str(output_path),
            ) from e

    def export_to_string(
        self,
        *,
        format: ExportFormat = ExportFormat.JSON,
        event_type: AuditEventType | None = None,
        actor: str | None = None,
        start_time: datetime | None = None,
        end_time: datetime | None = None,
        outcome: AuditOutcome | None = None,
        limit: int | None = None,
    ) -> str:
        """Export audit events to a string.

        Args:
            format: Export format.
            event_type: Filter by event type.
            actor: Filter by actor.
            start_time: Filter by start time.
            end_time: Filter by end time.
            outcome: Filter by outcome.
            limit: Maximum events to export.

        Returns:
            Exported data as a string.
        """
        import io

        events = self._storage.query(
            event_type=event_type,
            actor=actor,
            start_time=start_time,
            end_time=end_time,
            outcome=outcome,
            limit=limit or 10000,
        )

        buffer = io.StringIO()

        if format == ExportFormat.JSON:
            self._export_json(buffer, events)
        elif format == ExportFormat.CSV:
            self._export_csv(buffer, events)
        elif format == ExportFormat.JSONL:
            self._export_jsonl(buffer, events)
        elif format == ExportFormat.SYSLOG:
            self._export_syslog(buffer, events)

        return buffer.getvalue()

    def _export_json(self, f: TextIO, events: list[AuditEvent]) -> None:
        """Export events as JSON."""
        data = {
            "export_time": datetime.utcnow().isoformat(),
            "total_events": len(events),
            "events": [event.to_dict() for event in events],
        }
        json.dump(data, f, indent=2, default=str)

    def _export_csv(self, f: TextIO, events: list[AuditEvent]) -> None:
        """Export events as CSV."""
        fieldnames = [
            "event_id",
            "event_type",
            "timestamp",
            "actor",
            "actor_type",
            "action",
            "target",
            "outcome",
            "risk_score",
            "risk_level",
            "policy_id",
            "policy_result",
            "correlation_id",
            "session_id",
            "iso_control",
            "data_classification",
        ]

        writer = csv.DictWriter(f, fieldnames=fieldnames, extrasaction="ignore")
        writer.writeheader()

        for event in events:
            row = event.to_dict()
            # Convert nested context to string
            row.pop("context", None)
            row.pop("previous_hash", None)
            row.pop("event_hash", None)
            writer.writerow(row)

    def _export_jsonl(self, f: TextIO, events: list[AuditEvent]) -> None:
        """Export events as JSON Lines (one JSON object per line)."""
        for event in events:
            f.write(json.dumps(event.to_dict(), default=str))
            f.write("\n")

    def _export_syslog(self, f: TextIO, events: list[AuditEvent]) -> None:
        """Export events in syslog format (RFC 5424).

        Format: <priority>version timestamp hostname app-name procid msgid msg
        """
        for event in events:
            # Map outcome to syslog severity
            severity = self._outcome_to_severity(event.outcome)
            facility = 10  # Security/authorization (authpriv)
            priority = facility * 8 + severity

            # Format timestamp as RFC 5424
            timestamp = event.timestamp.strftime("%Y-%m-%dT%H:%M:%S.%fZ")

            # Build message
            msg_parts = [
                f"event_type={event.event_type.value}",
                f"actor={event.actor}",
                f"action={event.action}",
                f"outcome={event.outcome.value}",
            ]
            if event.target:
                msg_parts.append(f"target={event.target}")
            if event.risk_score is not None:
                msg_parts.append(f"risk_score={event.risk_score:.1f}")
            if event.policy_id:
                msg_parts.append(f"policy={event.policy_id}")

            msg = " ".join(msg_parts)

            # RFC 5424 format
            syslog_line = (
                f"<{priority}>1 {timestamp} paracle audit {event.event_id} " f"- {msg}"
            )
            f.write(syslog_line)
            f.write("\n")

    def _outcome_to_severity(self, outcome: AuditOutcome) -> int:
        """Map audit outcome to syslog severity."""
        severity_map = {
            AuditOutcome.SUCCESS: 6,  # Informational
            AuditOutcome.FAILURE: 3,  # Error
            AuditOutcome.DENIED: 4,  # Warning
            AuditOutcome.PENDING: 6,  # Informational
            AuditOutcome.CANCELLED: 5,  # Notice
            AuditOutcome.ERROR: 3,  # Error
        }
        return severity_map.get(outcome, 6)

    def generate_compliance_report(
        self,
        *,
        start_time: datetime | None = None,
        end_time: datetime | None = None,
    ) -> dict[str, Any]:
        """Generate a compliance-focused report.

        Returns a structured report suitable for compliance reviews.

        Args:
            start_time: Report period start.
            end_time: Report period end.

        Returns:
            Compliance report dictionary.
        """
        events = self._storage.query(
            start_time=start_time,
            end_time=end_time,
            limit=100000,
        )

        # Calculate statistics
        by_type: dict[str, int] = {}
        by_outcome: dict[str, int] = {}
        by_risk_level: dict[str, int] = {}
        by_iso_control: dict[str, int] = {}
        policy_violations: list[dict] = []
        high_risk_actions: list[dict] = []

        for event in events:
            # Count by type
            type_key = event.event_type.value
            by_type[type_key] = by_type.get(type_key, 0) + 1

            # Count by outcome
            outcome_key = event.outcome.value
            by_outcome[outcome_key] = by_outcome.get(outcome_key, 0) + 1

            # Count by risk level
            if event.risk_level:
                by_risk_level[event.risk_level] = (
                    by_risk_level.get(event.risk_level, 0) + 1
                )

            # Count by ISO control
            if event.iso_control:
                by_iso_control[event.iso_control] = (
                    by_iso_control.get(event.iso_control, 0) + 1
                )

            # Track policy violations
            if event.event_type == AuditEventType.POLICY_VIOLATED:
                policy_violations.append(
                    {
                        "event_id": event.event_id,
                        "timestamp": event.timestamp.isoformat(),
                        "actor": event.actor,
                        "action": event.action,
                        "policy_id": event.policy_id,
                    }
                )

            # Track high-risk actions
            if event.risk_score and event.risk_score >= 80:
                high_risk_actions.append(
                    {
                        "event_id": event.event_id,
                        "timestamp": event.timestamp.isoformat(),
                        "actor": event.actor,
                        "action": event.action,
                        "risk_score": event.risk_score,
                        "outcome": event.outcome.value,
                    }
                )

        return {
            "report_time": datetime.utcnow().isoformat(),
            "period": {
                "start": start_time.isoformat() if start_time else None,
                "end": end_time.isoformat() if end_time else None,
            },
            "summary": {
                "total_events": len(events),
                "by_type": by_type,
                "by_outcome": by_outcome,
                "by_risk_level": by_risk_level,
                "by_iso_control": by_iso_control,
            },
            "compliance": {
                "policy_violations_count": len(policy_violations),
                "policy_violations": policy_violations[:50],  # Top 50
                "high_risk_actions_count": len(high_risk_actions),
                "high_risk_actions": high_risk_actions[:50],  # Top 50
            },
            "recommendations": self._generate_recommendations(
                by_outcome, len(policy_violations), len(high_risk_actions)
            ),
        }

    def _generate_recommendations(
        self,
        by_outcome: dict[str, int],
        violation_count: int,
        high_risk_count: int,
    ) -> list[str]:
        """Generate compliance recommendations based on audit data."""
        recommendations = []

        # Check failure rate
        total = sum(by_outcome.values())
        failures = by_outcome.get("failure", 0) + by_outcome.get("error", 0)
        if total > 0 and failures / total > 0.1:
            recommendations.append(
                "High failure rate detected (>10%). Review agent configurations "
                "and error handling."
            )

        # Check policy violations
        if violation_count > 0:
            recommendations.append(
                f"{violation_count} policy violations detected. Review policy "
                "configurations and agent permissions."
            )

        # Check high-risk actions
        if high_risk_count > 10:
            recommendations.append(
                f"{high_risk_count} high-risk actions detected. Consider "
                "implementing additional approval workflows for critical operations."
            )

        # Check denied actions
        denied = by_outcome.get("denied", 0)
        if denied > 0:
            recommendations.append(
                f"{denied} actions were denied by policies. Review agent "
                "permissions and policy configurations."
            )

        if not recommendations:
            recommendations.append(
                "No significant compliance issues detected. Continue monitoring."
            )

        return recommendations
