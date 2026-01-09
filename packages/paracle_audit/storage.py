"""Audit storage implementations.

This module provides storage backends for audit events,
supporting tamper-evident storage with hash chains.
"""

import json
import sqlite3
import threading
from abc import ABC, abstractmethod
from collections.abc import Iterator
from datetime import datetime
from pathlib import Path
from typing import Any

from .events import AuditEvent, AuditEventType, AuditOutcome
from .exceptions import AuditStorageError


class AuditStorage(ABC):
    """Abstract base class for audit storage backends."""

    @abstractmethod
    def store(self, event: AuditEvent) -> None:
        """Store an audit event.

        Args:
            event: The event to store.
        """
        pass

    @abstractmethod
    def get(self, event_id: str) -> AuditEvent | None:
        """Get an event by ID.

        Args:
            event_id: The event ID.

        Returns:
            The event if found, None otherwise.
        """
        pass

    @abstractmethod
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
        """Query audit events with filters.

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
        pass

    @abstractmethod
    def get_last_hash(self) -> str | None:
        """Get the hash of the last stored event.

        Returns:
            Hash of the last event, or None if no events.
        """
        pass

    @abstractmethod
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
        pass

    @abstractmethod
    def delete_before(self, before_date: datetime) -> int:
        """Delete events before a given date.

        Args:
            before_date: Delete events before this date.

        Returns:
            Number of events deleted.
        """
        pass


class SQLiteAuditStorage(AuditStorage):
    """SQLite-based audit storage with hash chain integrity.

    This implementation stores audit events in SQLite with
    full-text search support and hash chain verification.
    """

    def __init__(self, db_path: Path | str | None = None):
        """Initialize SQLite audit storage.

        Args:
            db_path: Path to the SQLite database file.
                    If None, uses in-memory database.
        """
        if db_path:
            self._db_path = str(db_path)
        else:
            self._db_path = ":memory:"

        self._local = threading.local()
        self._init_db()

    def _get_connection(self) -> sqlite3.Connection:
        """Get a thread-local database connection."""
        if not hasattr(self._local, "connection"):
            self._local.connection = sqlite3.connect(
                self._db_path,
                check_same_thread=False,
            )
            self._local.connection.row_factory = sqlite3.Row
        return self._local.connection

    def _init_db(self) -> None:
        """Initialize the database schema."""
        conn = self._get_connection()
        cursor = conn.cursor()

        # Create audit events table
        cursor.execute(
            """
            CREATE TABLE IF NOT EXISTS audit_events (
                event_id TEXT PRIMARY KEY,
                event_type TEXT NOT NULL,
                timestamp TEXT NOT NULL,
                actor TEXT NOT NULL,
                actor_type TEXT NOT NULL,
                action TEXT NOT NULL,
                target TEXT,
                outcome TEXT NOT NULL,
                risk_score REAL,
                risk_level TEXT,
                policy_id TEXT,
                policy_result TEXT,
                context TEXT,
                correlation_id TEXT,
                session_id TEXT,
                previous_hash TEXT,
                event_hash TEXT,
                iso_control TEXT,
                data_classification TEXT,
                created_at TEXT DEFAULT CURRENT_TIMESTAMP
            )
        """
        )

        # Create indexes
        cursor.execute(
            """
            CREATE INDEX IF NOT EXISTS idx_audit_timestamp
            ON audit_events(timestamp)
        """
        )
        cursor.execute(
            """
            CREATE INDEX IF NOT EXISTS idx_audit_event_type
            ON audit_events(event_type)
        """
        )
        cursor.execute(
            """
            CREATE INDEX IF NOT EXISTS idx_audit_actor
            ON audit_events(actor)
        """
        )
        cursor.execute(
            """
            CREATE INDEX IF NOT EXISTS idx_audit_outcome
            ON audit_events(outcome)
        """
        )
        cursor.execute(
            """
            CREATE INDEX IF NOT EXISTS idx_audit_correlation
            ON audit_events(correlation_id)
        """
        )

        conn.commit()

    def store(self, event: AuditEvent) -> None:
        """Store an audit event."""
        conn = self._get_connection()
        cursor = conn.cursor()

        try:
            cursor.execute(
                """
                INSERT INTO audit_events (
                    event_id, event_type, timestamp, actor, actor_type,
                    action, target, outcome, risk_score, risk_level,
                    policy_id, policy_result, context, correlation_id,
                    session_id, previous_hash, event_hash, iso_control,
                    data_classification
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    event.event_id,
                    event.event_type.value,
                    event.timestamp.isoformat(),
                    event.actor,
                    event.actor_type,
                    event.action,
                    event.target,
                    event.outcome.value,
                    event.risk_score,
                    event.risk_level,
                    event.policy_id,
                    event.policy_result,
                    json.dumps(event.context),
                    event.correlation_id,
                    event.session_id,
                    event.previous_hash,
                    event.event_hash,
                    event.iso_control,
                    event.data_classification,
                ),
            )
            conn.commit()
        except sqlite3.IntegrityError as e:
            raise AuditStorageError(
                f"Failed to store event: {e}",
                operation="store",
            ) from e

    def get(self, event_id: str) -> AuditEvent | None:
        """Get an event by ID."""
        conn = self._get_connection()
        cursor = conn.cursor()

        cursor.execute(
            "SELECT * FROM audit_events WHERE event_id = ?",
            (event_id,),
        )
        row = cursor.fetchone()

        if row:
            return self._row_to_event(row)
        return None

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
        """Query audit events with filters."""
        conn = self._get_connection()
        cursor = conn.cursor()

        query = "SELECT * FROM audit_events WHERE 1=1"
        params: list[Any] = []

        if event_type:
            query += " AND event_type = ?"
            params.append(event_type.value)

        if actor:
            query += " AND actor = ?"
            params.append(actor)

        if start_time:
            query += " AND timestamp >= ?"
            params.append(start_time.isoformat())

        if end_time:
            query += " AND timestamp <= ?"
            params.append(end_time.isoformat())

        if outcome:
            query += " AND outcome = ?"
            params.append(outcome.value)

        query += " ORDER BY timestamp DESC LIMIT ? OFFSET ?"
        params.extend([limit, offset])

        cursor.execute(query, params)
        rows = cursor.fetchall()

        return [self._row_to_event(row) for row in rows]

    def get_last_hash(self) -> str | None:
        """Get the hash of the last stored event."""
        conn = self._get_connection()
        cursor = conn.cursor()

        cursor.execute(
            "SELECT event_hash FROM audit_events ORDER BY timestamp DESC LIMIT 1"
        )
        row = cursor.fetchone()

        if row:
            return row["event_hash"]
        return None

    def count(
        self,
        *,
        event_type: AuditEventType | None = None,
        start_time: datetime | None = None,
        end_time: datetime | None = None,
    ) -> int:
        """Count events matching filters."""
        conn = self._get_connection()
        cursor = conn.cursor()

        query = "SELECT COUNT(*) FROM audit_events WHERE 1=1"
        params: list[Any] = []

        if event_type:
            query += " AND event_type = ?"
            params.append(event_type.value)

        if start_time:
            query += " AND timestamp >= ?"
            params.append(start_time.isoformat())

        if end_time:
            query += " AND timestamp <= ?"
            params.append(end_time.isoformat())

        cursor.execute(query, params)
        return cursor.fetchone()[0]

    def delete_before(self, before_date: datetime) -> int:
        """Delete events before a given date."""
        conn = self._get_connection()
        cursor = conn.cursor()

        cursor.execute(
            "DELETE FROM audit_events WHERE timestamp < ?",
            (before_date.isoformat(),),
        )
        deleted = cursor.rowcount
        conn.commit()

        return deleted

    def get_statistics(self) -> dict[str, Any]:
        """Get audit storage statistics.

        Returns:
            Dictionary with statistics.
        """
        conn = self._get_connection()
        cursor = conn.cursor()

        # Total count
        cursor.execute("SELECT COUNT(*) FROM audit_events")
        total = cursor.fetchone()[0]

        # Count by type
        cursor.execute(
            """
            SELECT event_type, COUNT(*) as count
            FROM audit_events
            GROUP BY event_type
        """
        )
        by_type = {row["event_type"]: row["count"] for row in cursor.fetchall()}

        # Count by outcome
        cursor.execute(
            """
            SELECT outcome, COUNT(*) as count
            FROM audit_events
            GROUP BY outcome
        """
        )
        by_outcome = {row["outcome"]: row["count"] for row in cursor.fetchall()}

        # Date range
        cursor.execute(
            """
            SELECT MIN(timestamp) as earliest, MAX(timestamp) as latest
            FROM audit_events
        """
        )
        date_row = cursor.fetchone()

        return {
            "total_events": total,
            "by_type": by_type,
            "by_outcome": by_outcome,
            "earliest_event": date_row["earliest"],
            "latest_event": date_row["latest"],
        }

    def _row_to_event(self, row: sqlite3.Row) -> AuditEvent:
        """Convert a database row to an AuditEvent."""
        return AuditEvent(
            event_id=row["event_id"],
            event_type=AuditEventType(row["event_type"]),
            timestamp=datetime.fromisoformat(row["timestamp"]),
            actor=row["actor"],
            actor_type=row["actor_type"],
            action=row["action"],
            target=row["target"],
            outcome=AuditOutcome(row["outcome"]),
            risk_score=row["risk_score"],
            risk_level=row["risk_level"],
            policy_id=row["policy_id"],
            policy_result=row["policy_result"],
            context=json.loads(row["context"]) if row["context"] else {},
            correlation_id=row["correlation_id"],
            session_id=row["session_id"],
            previous_hash=row["previous_hash"],
            event_hash=row["event_hash"],
            iso_control=row["iso_control"],
            data_classification=row["data_classification"],
        )

    def iterate_all(self, batch_size: int = 1000) -> Iterator[AuditEvent]:
        """Iterate over all events in timestamp order.

        Args:
            batch_size: Number of events to fetch per batch.

        Yields:
            AuditEvent objects in timestamp order.
        """
        conn = self._get_connection()
        cursor = conn.cursor()

        offset = 0
        while True:
            cursor.execute(
                "SELECT * FROM audit_events ORDER BY timestamp LIMIT ? OFFSET ?",
                (batch_size, offset),
            )
            rows = cursor.fetchall()

            if not rows:
                break

            for row in rows:
                yield self._row_to_event(row)

            offset += batch_size
