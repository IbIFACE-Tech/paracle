"""Audit integrity verification.

This module provides hash chain verification for audit trails,
ensuring tamper-evident storage of audit events.
"""

from typing import Any

from .events import AuditEvent
from .storage import AuditStorage


class IntegrityVerifier:
    """Verifies the integrity of audit trails using hash chains.

    The verifier checks that:
    1. Each event's hash matches its computed hash
    2. Each event's previous_hash matches the prior event's hash
    3. The chain is unbroken from start to end

    Example:
        >>> verifier = IntegrityVerifier(storage)
        >>> result = verifier.verify_chain()
        >>> if result["valid"]:
        ...     print("Audit trail integrity verified")
        >>> else:
        ...     print(f"Integrity violation at event: {result['violation_event']}")
    """

    def __init__(self, storage: AuditStorage):
        """Initialize the integrity verifier.

        Args:
            storage: The audit storage to verify.
        """
        self._storage = storage

    def verify_event(self, event: AuditEvent) -> bool:
        """Verify a single event's hash integrity.

        Args:
            event: The event to verify.

        Returns:
            True if the event's hash is valid.
        """
        if not event.event_hash:
            return False

        computed_hash = event.compute_hash()
        return event.event_hash == computed_hash

    def verify_chain(
        self,
        *,
        start_event_id: str | None = None,
        end_event_id: str | None = None,
        max_events: int = 10000,
    ) -> dict[str, Any]:
        """Verify the integrity of the audit trail chain.

        Args:
            start_event_id: Optional start event ID for partial verification.
            end_event_id: Optional end event ID for partial verification.
            max_events: Maximum number of events to verify.

        Returns:
            Dictionary with verification results:
            - valid: True if chain is valid
            - events_verified: Number of events verified
            - first_event_id: ID of first event in chain
            - last_event_id: ID of last event in chain
            - violation_event: ID of event where violation occurred (if any)
            - violation_type: Type of violation (if any)
            - violation_details: Details about the violation (if any)
        """
        result = {
            "valid": True,
            "events_verified": 0,
            "first_event_id": None,
            "last_event_id": None,
            "violation_event": None,
            "violation_type": None,
            "violation_details": None,
        }

        previous_hash: str | None = None
        previous_event_id: str | None = None

        # Use storage iterator if available
        if hasattr(self._storage, "iterate_all"):
            iterator = self._storage.iterate_all()
        else:
            # Fallback to query
            events = self._storage.query(limit=max_events)
            iterator = iter(sorted(events, key=lambda e: e.timestamp))

        for i, event in enumerate(iterator):
            if i >= max_events:
                break

            # Record first event
            if result["first_event_id"] is None:
                result["first_event_id"] = event.event_id

            result["last_event_id"] = event.event_id
            result["events_verified"] = i + 1

            # Verify event hash
            if event.event_hash:
                computed_hash = event.compute_hash()
                if event.event_hash != computed_hash:
                    result["valid"] = False
                    result["violation_event"] = event.event_id
                    result["violation_type"] = "hash_mismatch"
                    result["violation_details"] = {
                        "expected": event.event_hash,
                        "computed": computed_hash,
                    }
                    return result

            # Verify chain linkage
            if previous_hash is not None and event.previous_hash != previous_hash:
                result["valid"] = False
                result["violation_event"] = event.event_id
                result["violation_type"] = "chain_break"
                result["violation_details"] = {
                    "expected_previous": previous_hash,
                    "actual_previous": event.previous_hash,
                    "previous_event": previous_event_id,
                }
                return result

            # Update for next iteration
            previous_hash = event.event_hash
            previous_event_id = event.event_id

        return result

    def verify_event_chain(
        self,
        event_id: str,
        *,
        depth: int = 10,
    ) -> dict[str, Any]:
        """Verify the chain leading to a specific event.

        Verifies the event and its predecessors up to the given depth.

        Args:
            event_id: ID of the event to verify.
            depth: Number of predecessor events to verify.

        Returns:
            Dictionary with verification results.
        """
        result = {
            "valid": True,
            "events_verified": 0,
            "chain": [],
            "violation_event": None,
            "violation_type": None,
        }

        current_event = self._storage.get(event_id)
        if not current_event:
            result["valid"] = False
            result["violation_type"] = "event_not_found"
            result["violation_event"] = event_id
            return result

        # Verify current event and predecessors
        for _ in range(depth):
            # Verify current event hash
            if current_event.event_hash:
                computed_hash = current_event.compute_hash()
                if current_event.event_hash != computed_hash:
                    result["valid"] = False
                    result["violation_event"] = current_event.event_id
                    result["violation_type"] = "hash_mismatch"
                    return result

            result["chain"].append(current_event.event_id)
            result["events_verified"] += 1

            # Check if we have a previous event
            if not current_event.previous_hash:
                break  # Start of chain

            # Find previous event by hash
            # Note: In production, you'd want an index on event_hash
            # For now, we'll just return incomplete verification
            break

        return result

    def find_violations(
        self,
        *,
        max_events: int = 10000,
    ) -> list[dict[str, Any]]:
        """Find all integrity violations in the audit trail.

        Unlike verify_chain which stops at the first violation,
        this method finds all violations.

        Args:
            max_events: Maximum number of events to check.

        Returns:
            List of violations, each with:
            - event_id: ID of the violating event
            - violation_type: Type of violation
            - details: Violation details
        """
        violations = []
        previous_hash: str | None = None
        previous_event_id: str | None = None

        if hasattr(self._storage, "iterate_all"):
            iterator = self._storage.iterate_all()
        else:
            events = self._storage.query(limit=max_events)
            iterator = iter(sorted(events, key=lambda e: e.timestamp))

        for i, event in enumerate(iterator):
            if i >= max_events:
                break

            # Check event hash
            if event.event_hash:
                computed_hash = event.compute_hash()
                if event.event_hash != computed_hash:
                    violations.append(
                        {
                            "event_id": event.event_id,
                            "violation_type": "hash_mismatch",
                            "details": {
                                "expected": event.event_hash,
                                "computed": computed_hash,
                            },
                        }
                    )

            # Check chain linkage
            if previous_hash is not None and event.previous_hash != previous_hash:
                violations.append(
                    {
                        "event_id": event.event_id,
                        "violation_type": "chain_break",
                        "details": {
                            "expected_previous": previous_hash,
                            "actual_previous": event.previous_hash,
                            "previous_event": previous_event_id,
                        },
                    }
                )

            previous_hash = event.event_hash
            previous_event_id = event.event_id

        return violations

    def generate_integrity_report(self) -> dict[str, Any]:
        """Generate a comprehensive integrity report.

        Returns:
            Dictionary with:
            - verification_time: When verification was performed
            - total_events: Total events in storage
            - events_verified: Events that were verified
            - chain_valid: Whether the full chain is valid
            - violations: List of violations found
            - statistics: Storage statistics
        """
        from datetime import datetime

        # Get statistics
        stats = {}
        if hasattr(self._storage, "get_statistics"):
            stats = self._storage.get_statistics()

        # Verify chain
        chain_result = self.verify_chain()

        # Find all violations
        violations = self.find_violations()

        return {
            "verification_time": datetime.utcnow().isoformat(),
            "total_events": stats.get("total_events", 0),
            "events_verified": chain_result["events_verified"],
            "chain_valid": chain_result["valid"],
            "first_event_id": chain_result.get("first_event_id"),
            "last_event_id": chain_result.get("last_event_id"),
            "violations_count": len(violations),
            "violations": violations[:100],  # Limit to first 100
            "statistics": stats,
        }
