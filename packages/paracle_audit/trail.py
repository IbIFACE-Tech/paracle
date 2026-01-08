"""Audit Trail - Main audit interface.

This module provides the high-level AuditTrail class that orchestrates
audit event recording, storage, and verification.
"""

from collections.abc import Callable
from datetime import datetime, timedelta
from pathlib import Path
from typing import Any

from .events import AuditEvent, AuditEventType, AuditOutcome
from .export import AuditExporter, ExportFormat
from .integrity import IntegrityVerifier
from .storage import AuditStorage, SQLiteAuditStorage


class AuditTrail:
    """High-level audit trail management.

    The AuditTrail is the main interface for audit operations.
    It manages event recording with hash chains, storage, and verification.

    Features:
    - Record audit events with automatic hash chaining
    - Query and filter audit events
    - Verify audit trail integrity
    - Export audit data for compliance
    - Retention policy management

    Example:
        >>> trail = AuditTrail()
        >>> event = trail.record(
        ...     event_type=AuditEventType.AGENT_ACTION,
        ...     actor="coder",
        ...     action="write_file",
        ...     target="/app/main.py",
        ...     outcome=AuditOutcome.SUCCESS,
        ...     risk_score=45.0,
        ... )
        >>> print(event.event_id)
        >>> print(trail.verify_integrity())
    """

    def __init__(
        self,
        *,
        storage: AuditStorage | None = None,
        db_path: Path | str | None = None,
        enable_hash_chain: bool = True,
    ):
        """Initialize the audit trail.

        Args:
            storage: Custom storage backend. If None, uses SQLite.
            db_path: Path to SQLite database (if using default storage).
            enable_hash_chain: Whether to enable hash chain integrity.
        """
        if storage:
            self._storage = storage
        else:
            self._storage = SQLiteAuditStorage(db_path)

        self._enable_hash_chain = enable_hash_chain
        self._verifier = IntegrityVerifier(self._storage)
        self._exporter = AuditExporter(self._storage)
        self._event_hooks: list[Callable[[AuditEvent], None]] = []

    @property
    def storage(self) -> AuditStorage:
        """Get the underlying storage backend."""
        return self._storage

    @property
    def verifier(self) -> IntegrityVerifier:
        """Get the integrity verifier."""
        return self._verifier

    @property
    def exporter(self) -> AuditExporter:
        """Get the audit exporter."""
        return self._exporter

    def record(
        self,
        *,
        event_type: AuditEventType,
        actor: str,
        action: str,
        target: str | None = None,
        outcome: AuditOutcome = AuditOutcome.SUCCESS,
        risk_score: float | None = None,
        risk_level: str | None = None,
        policy_id: str | None = None,
        policy_result: str | None = None,
        context: dict[str, Any] | None = None,
        correlation_id: str | None = None,
        session_id: str | None = None,
        iso_control: str | None = None,
        data_classification: str | None = None,
    ) -> AuditEvent:
        """Record an audit event.

        Creates an audit event with automatic hash chaining (if enabled)
        and stores it in the audit trail.

        Args:
            event_type: Type of audit event.
            actor: Actor who performed the action.
            action: Action that was performed.
            target: Target resource (optional).
            outcome: Outcome of the action.
            risk_score: Calculated risk score.
            risk_level: Risk level (low, medium, high, critical).
            policy_id: Related policy ID.
            policy_result: Policy evaluation result.
            context: Additional event context.
            correlation_id: Correlation ID for related events.
            session_id: Session ID.
            iso_control: Related ISO 42001 control.
            data_classification: Data classification level.

        Returns:
            The recorded audit event.
        """
        # Create base event
        event = AuditEvent(
            event_type=event_type,
            actor=actor,
            action=action,
            target=target,
            outcome=outcome,
            risk_score=risk_score,
            risk_level=risk_level,
            policy_id=policy_id,
            policy_result=policy_result,
            context=context or {},
            correlation_id=correlation_id,
            session_id=session_id,
            iso_control=iso_control,
            data_classification=data_classification,
        )

        # Add hash chain if enabled
        if self._enable_hash_chain:
            previous_hash = self._storage.get_last_hash()
            event = event.with_hash(previous_hash)

        # Store the event
        self._storage.store(event)

        # Call event hooks
        for hook in self._event_hooks:
            try:
                hook(event)
            except Exception:
                pass  # Don't let hook failures affect recording

        return event

    def record_agent_action(
        self,
        agent: str,
        action: str,
        *,
        target: str | None = None,
        outcome: AuditOutcome = AuditOutcome.SUCCESS,
        risk_score: float | None = None,
        context: dict[str, Any] | None = None,
        correlation_id: str | None = None,
    ) -> AuditEvent:
        """Convenience method to record an agent action.

        Args:
            agent: Agent name.
            action: Action performed.
            target: Target resource.
            outcome: Action outcome.
            risk_score: Risk score.
            context: Additional context.
            correlation_id: Correlation ID.

        Returns:
            The recorded audit event.
        """
        return self.record(
            event_type=AuditEventType.AGENT_ACTION,
            actor=agent,
            action=action,
            target=target,
            outcome=outcome,
            risk_score=risk_score,
            context=context,
            correlation_id=correlation_id,
        )

    def record_policy_evaluation(
        self,
        actor: str,
        action: str,
        policy_id: str,
        result: str,
        *,
        allowed: bool = True,
        risk_score: float | None = None,
        context: dict[str, Any] | None = None,
    ) -> AuditEvent:
        """Record a policy evaluation event.

        Args:
            actor: Actor being evaluated.
            action: Action being evaluated.
            policy_id: Policy that was evaluated.
            result: Evaluation result description.
            allowed: Whether the action was allowed.
            risk_score: Risk score.
            context: Additional context.

        Returns:
            The recorded audit event.
        """
        event_type = (
            AuditEventType.POLICY_EVALUATED
            if allowed
            else AuditEventType.POLICY_VIOLATED
        )
        outcome = AuditOutcome.SUCCESS if allowed else AuditOutcome.DENIED

        return self.record(
            event_type=event_type,
            actor=actor,
            action=action,
            policy_id=policy_id,
            policy_result=result,
            outcome=outcome,
            risk_score=risk_score,
            context=context,
            iso_control="6.2",  # ISO 42001 - AI risk treatment
        )

    def record_approval_event(
        self,
        actor: str,
        approval_type: str,
        request_id: str,
        *,
        approver: str | None = None,
        reason: str | None = None,
        context: dict[str, Any] | None = None,
    ) -> AuditEvent:
        """Record an approval-related event.

        Args:
            actor: Actor involved in the approval.
            approval_type: Type (requested, granted, denied, escalated).
            request_id: Approval request ID.
            approver: Who approved/denied (if applicable).
            reason: Reason for the decision.
            context: Additional context.

        Returns:
            The recorded audit event.
        """
        type_map = {
            "requested": AuditEventType.APPROVAL_REQUESTED,
            "granted": AuditEventType.APPROVAL_GRANTED,
            "denied": AuditEventType.APPROVAL_DENIED,
            "escalated": AuditEventType.APPROVAL_ESCALATED,
        }
        event_type = type_map.get(
            approval_type.lower(), AuditEventType.APPROVAL_REQUESTED
        )

        outcome_map = {
            "requested": AuditOutcome.PENDING,
            "granted": AuditOutcome.SUCCESS,
            "denied": AuditOutcome.DENIED,
            "escalated": AuditOutcome.PENDING,
        }
        outcome = outcome_map.get(approval_type.lower(), AuditOutcome.PENDING)

        event_context = context or {}
        if approver:
            event_context["approver"] = approver
        if reason:
            event_context["reason"] = reason

        return self.record(
            event_type=event_type,
            actor=actor,
            action=f"approval_{approval_type.lower()}",
            target=request_id,
            outcome=outcome,
            context=event_context,
            iso_control="6.2",  # ISO 42001 - AI risk treatment
        )

    def get(self, event_id: str) -> AuditEvent | None:
        """Get an event by ID.

        Args:
            event_id: The event ID.

        Returns:
            The event if found, None otherwise.
        """
        return self._storage.get(event_id)

    def query(
        self,
        *,
        event_type: AuditEventType | None = None,
        actor: str | None = None,
        start_time: datetime | None = None,
        end_time: datetime | None = None,
        outcome: AuditOutcome | None = None,
        limit: int = 100,
        offset: int = 0,
    ) -> list[AuditEvent]:
        """Query audit events.

        Args:
            event_type: Filter by event type.
            actor: Filter by actor.
            start_time: Filter by start time.
            end_time: Filter by end time.
            outcome: Filter by outcome.
            limit: Maximum events to return.
            offset: Offset for pagination.

        Returns:
            List of matching events.
        """
        return self._storage.query(
            event_type=event_type,
            actor=actor,
            start_time=start_time,
            end_time=end_time,
            outcome=outcome,
            limit=limit,
            offset=offset,
        )

    def count(
        self,
        *,
        event_type: AuditEventType | None = None,
        start_time: datetime | None = None,
        end_time: datetime | None = None,
    ) -> int:
        """Count events matching filters.

        Args:
            event_type: Filter by event type.
            start_time: Filter by start time.
            end_time: Filter by end time.

        Returns:
            Number of matching events.
        """
        return self._storage.count(
            event_type=event_type,
            start_time=start_time,
            end_time=end_time,
        )

    def verify_integrity(self) -> dict[str, Any]:
        """Verify the integrity of the audit trail.

        Returns:
            Verification result with:
            - valid: True if chain is valid
            - events_verified: Number of events verified
            - violations: Any violations found
        """
        return self._verifier.verify_chain()

    def generate_integrity_report(self) -> dict[str, Any]:
        """Generate a comprehensive integrity report.

        Returns:
            Detailed integrity report.
        """
        return self._verifier.generate_integrity_report()

    def export(
        self,
        output_path: Path | str,
        *,
        format: ExportFormat = ExportFormat.JSON,
        event_type: AuditEventType | None = None,
        actor: str | None = None,
        start_time: datetime | None = None,
        end_time: datetime | None = None,
        limit: int | None = None,
    ) -> int:
        """Export audit events to a file.

        Args:
            output_path: Path to the output file.
            format: Export format.
            event_type: Filter by event type.
            actor: Filter by actor.
            start_time: Filter by start time.
            end_time: Filter by end time.
            limit: Maximum events to export.

        Returns:
            Number of events exported.
        """
        return self._exporter.export_to_file(
            output_path,
            format=format,
            event_type=event_type,
            actor=actor,
            start_time=start_time,
            end_time=end_time,
            limit=limit,
        )

    def generate_compliance_report(
        self,
        *,
        start_time: datetime | None = None,
        end_time: datetime | None = None,
    ) -> dict[str, Any]:
        """Generate a compliance report.

        Args:
            start_time: Report period start.
            end_time: Report period end.

        Returns:
            Compliance report dictionary.
        """
        return self._exporter.generate_compliance_report(
            start_time=start_time,
            end_time=end_time,
        )

    def apply_retention_policy(
        self,
        retention_days: int,
        *,
        archive_path: Path | str | None = None,
    ) -> dict[str, Any]:
        """Apply retention policy to audit data.

        Deletes events older than the retention period, optionally
        archiving them first.

        Args:
            retention_days: Keep events for this many days.
            archive_path: Optional path to archive deleted events.

        Returns:
            Dictionary with:
            - deleted_count: Number of events deleted
            - archived_path: Path to archive (if created)
        """
        cutoff_date = datetime.utcnow() - timedelta(days=retention_days)
        result = {
            "deleted_count": 0,
            "archived_path": None,
            "cutoff_date": cutoff_date.isoformat(),
        }

        # Archive if path provided
        if archive_path:
            archive_count = self._exporter.export_to_file(
                archive_path,
                format=ExportFormat.JSONL,
                end_time=cutoff_date,
            )
            result["archived_path"] = str(archive_path)
            result["archived_count"] = archive_count

        # Delete old events
        deleted = self._storage.delete_before(cutoff_date)
        result["deleted_count"] = deleted

        return result

    def add_event_hook(self, hook: Callable[[AuditEvent], None]) -> None:
        """Add a hook to be called when events are recorded.

        Args:
            hook: Callable that takes an AuditEvent.
        """
        self._event_hooks.append(hook)

    def remove_event_hook(self, hook: Callable[[AuditEvent], None]) -> bool:
        """Remove an event hook.

        Args:
            hook: The hook to remove.

        Returns:
            True if removed, False if not found.
        """
        if hook in self._event_hooks:
            self._event_hooks.remove(hook)
            return True
        return False

    def get_statistics(self) -> dict[str, Any]:
        """Get audit trail statistics.

        Returns:
            Dictionary with statistics.
        """
        if hasattr(self._storage, "get_statistics"):
            stats = self._storage.get_statistics()
        else:
            stats = {}

        stats["hash_chain_enabled"] = self._enable_hash_chain
        stats["event_hooks_count"] = len(self._event_hooks)

        return stats
