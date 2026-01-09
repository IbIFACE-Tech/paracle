"""Persistent Event Store with SQLite backend.

Provides durable event storage with:
- SQLite persistence (file or in-memory)
- Event replay for state reconstruction
- Event querying by type, source, time range
- Automatic schema migration
- Rollback support via event sourcing

This enables true event sourcing patterns in Paracle.
"""

from __future__ import annotations

import json
import sqlite3
import threading
from collections.abc import Iterator
from contextlib import contextmanager
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from paracle_events.events import Event, EventType


def _utcnow() -> datetime:
    """Return current UTC time."""
    return datetime.now(timezone.utc)


# SQL Schema
SCHEMA_VERSION = 1

CREATE_EVENTS_TABLE = """
CREATE TABLE IF NOT EXISTS events (
    id TEXT PRIMARY KEY,
    type TEXT NOT NULL,
    timestamp TEXT NOT NULL,
    source TEXT NOT NULL,
    payload TEXT NOT NULL,
    metadata TEXT NOT NULL,
    sequence INTEGER NOT NULL
);
"""

CREATE_EVENTS_INDEXES = """
CREATE INDEX IF NOT EXISTS idx_events_type ON events(type);
CREATE INDEX IF NOT EXISTS idx_events_source ON events(source);
CREATE INDEX IF NOT EXISTS idx_events_timestamp ON events(timestamp);
CREATE INDEX IF NOT EXISTS idx_events_sequence ON events(sequence);
"""

CREATE_SCHEMA_VERSION_TABLE = """
CREATE TABLE IF NOT EXISTS schema_version (
    version INTEGER PRIMARY KEY,
    applied_at TEXT NOT NULL
);
"""

CREATE_CHECKPOINTS_TABLE = """
CREATE TABLE IF NOT EXISTS checkpoints (
    id TEXT PRIMARY KEY,
    aggregate_id TEXT NOT NULL,
    aggregate_type TEXT NOT NULL,
    event_sequence INTEGER NOT NULL,
    state TEXT NOT NULL,
    created_at TEXT NOT NULL,
    metadata TEXT
);
"""

CREATE_CHECKPOINTS_INDEXES = """
CREATE INDEX IF NOT EXISTS idx_checkpoints_aggregate ON checkpoints(aggregate_id);
"""


class PersistentEventStore:
    """SQLite-backed persistent event store.

    Features:
    - Durable event storage
    - Ordered event sequences
    - Event replay from any point
    - Checkpoint support for snapshots
    - Thread-safe operations

    Example:
        >>> store = PersistentEventStore("events.db")
        >>> store.append(agent_created_event)
        >>> events = store.get_by_source("agent_123")
        >>> store.replay_from(checkpoint_sequence, handler)
    """

    def __init__(
        self,
        db_path: str | Path | None = None,
        *,
        in_memory: bool = False,
    ) -> None:
        """Initialize the event store.

        Args:
            db_path: Path to SQLite database file
            in_memory: Use in-memory database (for testing)
        """
        if in_memory:
            self._db_path = ":memory:"
        elif db_path:
            self._db_path = str(db_path)
        else:
            self._db_path = "paracle_events.db"

        self._lock = threading.RLock()
        self._local = threading.local()
        self._sequence = 0

        # Initialize database
        self._init_database()

    def _get_connection(self) -> sqlite3.Connection:
        """Get thread-local database connection."""
        if not hasattr(self._local, "connection") or self._local.connection is None:
            self._local.connection = sqlite3.connect(
                self._db_path,
                check_same_thread=False,
            )
            self._local.connection.row_factory = sqlite3.Row
        return self._local.connection

    @contextmanager
    def _transaction(self) -> Iterator[sqlite3.Cursor]:
        """Context manager for database transactions."""
        conn = self._get_connection()
        cursor = conn.cursor()
        try:
            yield cursor
            conn.commit()
        except Exception:
            conn.rollback()
            raise

    def _init_database(self) -> None:
        """Initialize database schema."""
        with self._lock:
            with self._transaction() as cursor:
                # Create tables
                cursor.execute(CREATE_SCHEMA_VERSION_TABLE)
                cursor.execute(CREATE_EVENTS_TABLE)
                cursor.executescript(CREATE_EVENTS_INDEXES)
                cursor.execute(CREATE_CHECKPOINTS_TABLE)
                cursor.executescript(CREATE_CHECKPOINTS_INDEXES)

                # Check/update schema version
                cursor.execute(
                    "INSERT OR IGNORE INTO schema_version (version, applied_at) VALUES (?, ?)",
                    (SCHEMA_VERSION, _utcnow().isoformat()),
                )

                # Get current max sequence
                cursor.execute("SELECT MAX(sequence) FROM events")
                row = cursor.fetchone()
                self._sequence = (row[0] or 0) if row else 0

    def append(self, event: Event) -> int:
        """Append an event to the store.

        Args:
            event: Event to append

        Returns:
            Sequence number of the appended event
        """
        with self._lock:
            self._sequence += 1
            sequence = self._sequence

            with self._transaction() as cursor:
                cursor.execute(
                    """
                    INSERT INTO events (id, type, timestamp, source, payload, metadata, sequence)
                    VALUES (?, ?, ?, ?, ?, ?, ?)
                    """,
                    (
                        event.id,
                        event.type.value,
                        event.timestamp.isoformat(),
                        event.source,
                        json.dumps(event.payload),
                        json.dumps(event.metadata),
                        sequence,
                    ),
                )

            return sequence

    def append_batch(self, events: list[Event]) -> list[int]:
        """Append multiple events atomically.

        Args:
            events: Events to append

        Returns:
            List of sequence numbers
        """
        with self._lock:
            sequences = []

            with self._transaction() as cursor:
                for event in events:
                    self._sequence += 1
                    sequence = self._sequence
                    sequences.append(sequence)

                    cursor.execute(
                        """
                        INSERT INTO events (id, type, timestamp, source, payload, metadata, sequence)
                        VALUES (?, ?, ?, ?, ?, ?, ?)
                        """,
                        (
                            event.id,
                            event.type.value,
                            event.timestamp.isoformat(),
                            event.source,
                            json.dumps(event.payload),
                            json.dumps(event.metadata),
                            sequence,
                        ),
                    )

            return sequences

    def _row_to_event(self, row: sqlite3.Row) -> Event:
        """Convert database row to Event."""
        return Event(
            id=row["id"],
            type=EventType(row["type"]),
            timestamp=datetime.fromisoformat(row["timestamp"]),
            source=row["source"],
            payload=json.loads(row["payload"]),
            metadata=json.loads(row["metadata"]),
        )

    def get(self, event_id: str) -> Event | None:
        """Get event by ID."""
        with self._transaction() as cursor:
            cursor.execute("SELECT * FROM events WHERE id = ?", (event_id,))
            row = cursor.fetchone()
            return self._row_to_event(row) if row else None

    def get_all(self, limit: int | None = None) -> list[Event]:
        """Get all events in sequence order."""
        with self._transaction() as cursor:
            if limit:
                cursor.execute(
                    "SELECT * FROM events ORDER BY sequence ASC LIMIT ?",
                    (limit,),
                )
            else:
                cursor.execute("SELECT * FROM events ORDER BY sequence ASC")
            return [self._row_to_event(row) for row in cursor.fetchall()]

    def get_by_type(self, event_type: EventType) -> list[Event]:
        """Get events by type."""
        with self._transaction() as cursor:
            cursor.execute(
                "SELECT * FROM events WHERE type = ? ORDER BY sequence ASC",
                (event_type.value,),
            )
            return [self._row_to_event(row) for row in cursor.fetchall()]

    def get_by_source(self, source: str) -> list[Event]:
        """Get events by source."""
        with self._transaction() as cursor:
            cursor.execute(
                "SELECT * FROM events WHERE source = ? ORDER BY sequence ASC",
                (source,),
            )
            return [self._row_to_event(row) for row in cursor.fetchall()]

    def get_since(self, event_id: str) -> list[Event]:
        """Get events after a specific event."""
        with self._transaction() as cursor:
            # Get the sequence of the reference event
            cursor.execute("SELECT sequence FROM events WHERE id = ?", (event_id,))
            row = cursor.fetchone()
            if not row:
                return []

            sequence = row["sequence"]
            cursor.execute(
                "SELECT * FROM events WHERE sequence > ? ORDER BY sequence ASC",
                (sequence,),
            )
            return [self._row_to_event(row) for row in cursor.fetchall()]

    def get_since_sequence(self, sequence: int) -> list[Event]:
        """Get events after a specific sequence number."""
        with self._transaction() as cursor:
            cursor.execute(
                "SELECT * FROM events WHERE sequence > ? ORDER BY sequence ASC",
                (sequence,),
            )
            return [self._row_to_event(row) for row in cursor.fetchall()]

    def get_range(
        self,
        start_time: datetime | None = None,
        end_time: datetime | None = None,
        event_types: list[EventType] | None = None,
        sources: list[str] | None = None,
        limit: int | None = None,
    ) -> list[Event]:
        """Get events matching criteria.

        Args:
            start_time: Filter events after this time
            end_time: Filter events before this time
            event_types: Filter by event types
            sources: Filter by sources
            limit: Maximum number of events

        Returns:
            Matching events in sequence order
        """
        conditions = []
        params: list[Any] = []

        if start_time:
            conditions.append("timestamp >= ?")
            params.append(start_time.isoformat())

        if end_time:
            conditions.append("timestamp <= ?")
            params.append(end_time.isoformat())

        if event_types:
            placeholders = ",".join("?" * len(event_types))
            conditions.append(f"type IN ({placeholders})")
            params.extend(et.value for et in event_types)

        if sources:
            placeholders = ",".join("?" * len(sources))
            conditions.append(f"source IN ({placeholders})")
            params.extend(sources)

        where_clause = " AND ".join(conditions) if conditions else "1=1"
        query = f"SELECT * FROM events WHERE {where_clause} ORDER BY sequence ASC"

        if limit:
            query += " LIMIT ?"
            params.append(limit)

        with self._transaction() as cursor:
            cursor.execute(query, params)
            return [self._row_to_event(row) for row in cursor.fetchall()]

    def count(self) -> int:
        """Get total event count."""
        with self._transaction() as cursor:
            cursor.execute("SELECT COUNT(*) FROM events")
            row = cursor.fetchone()
            return row[0] if row else 0

    def get_sequence(self) -> int:
        """Get current sequence number."""
        return self._sequence

    def replay(
        self,
        handler: callable[[Event], None],
        from_sequence: int = 0,
        event_types: list[EventType] | None = None,
        sources: list[str] | None = None,
    ) -> int:
        """Replay events through a handler.

        Args:
            handler: Function to call for each event
            from_sequence: Start replaying from this sequence
            event_types: Filter by event types
            sources: Filter by sources

        Returns:
            Number of events replayed
        """
        conditions = ["sequence > ?"]
        params: list[Any] = [from_sequence]

        if event_types:
            placeholders = ",".join("?" * len(event_types))
            conditions.append(f"type IN ({placeholders})")
            params.extend(et.value for et in event_types)

        if sources:
            placeholders = ",".join("?" * len(sources))
            conditions.append(f"source IN ({placeholders})")
            params.extend(sources)

        where_clause = " AND ".join(conditions)
        query = f"SELECT * FROM events WHERE {where_clause} ORDER BY sequence ASC"

        count = 0
        with self._transaction() as cursor:
            cursor.execute(query, params)
            for row in cursor:
                event = self._row_to_event(row)
                handler(event)
                count += 1

        return count

    # ==========================================================================
    # Checkpoint support
    # ==========================================================================

    def save_checkpoint(
        self,
        checkpoint_id: str,
        aggregate_id: str,
        aggregate_type: str,
        state: dict[str, Any],
        metadata: dict[str, Any] | None = None,
    ) -> None:
        """Save a checkpoint (snapshot) at current sequence.

        Args:
            checkpoint_id: Unique checkpoint ID
            aggregate_id: ID of the aggregate being checkpointed
            aggregate_type: Type of the aggregate
            state: Serialized state to save
            metadata: Optional additional metadata
        """
        with self._lock:
            with self._transaction() as cursor:
                cursor.execute(
                    """
                    INSERT OR REPLACE INTO checkpoints
                    (id, aggregate_id, aggregate_type, event_sequence, state, created_at, metadata)
                    VALUES (?, ?, ?, ?, ?, ?, ?)
                    """,
                    (
                        checkpoint_id,
                        aggregate_id,
                        aggregate_type,
                        self._sequence,
                        json.dumps(state),
                        _utcnow().isoformat(),
                        json.dumps(metadata or {}),
                    ),
                )

    def get_checkpoint(self, checkpoint_id: str) -> dict[str, Any] | None:
        """Get a checkpoint by ID."""
        with self._transaction() as cursor:
            cursor.execute("SELECT * FROM checkpoints WHERE id = ?", (checkpoint_id,))
            row = cursor.fetchone()
            if not row:
                return None

            return {
                "id": row["id"],
                "aggregate_id": row["aggregate_id"],
                "aggregate_type": row["aggregate_type"],
                "event_sequence": row["event_sequence"],
                "state": json.loads(row["state"]),
                "created_at": datetime.fromisoformat(row["created_at"]),
                "metadata": json.loads(row["metadata"]) if row["metadata"] else {},
            }

    def get_latest_checkpoint(self, aggregate_id: str) -> dict[str, Any] | None:
        """Get the latest checkpoint for an aggregate."""
        with self._transaction() as cursor:
            cursor.execute(
                """
                SELECT * FROM checkpoints
                WHERE aggregate_id = ?
                ORDER BY event_sequence DESC
                LIMIT 1
                """,
                (aggregate_id,),
            )
            row = cursor.fetchone()
            if not row:
                return None

            return {
                "id": row["id"],
                "aggregate_id": row["aggregate_id"],
                "aggregate_type": row["aggregate_type"],
                "event_sequence": row["event_sequence"],
                "state": json.loads(row["state"]),
                "created_at": datetime.fromisoformat(row["created_at"]),
                "metadata": json.loads(row["metadata"]) if row["metadata"] else {},
            }

    def restore_from_checkpoint(
        self,
        checkpoint_id: str,
        handler: callable[[Event], None],
    ) -> dict[str, Any] | None:
        """Restore state from checkpoint and replay subsequent events.

        Args:
            checkpoint_id: Checkpoint to restore from
            handler: Handler for replaying events after checkpoint

        Returns:
            Checkpoint state dict, or None if not found
        """
        checkpoint = self.get_checkpoint(checkpoint_id)
        if not checkpoint:
            return None

        # Replay events since checkpoint
        self.replay(handler, from_sequence=checkpoint["event_sequence"])

        return checkpoint

    def delete_checkpoint(self, checkpoint_id: str) -> bool:
        """Delete a checkpoint."""
        with self._transaction() as cursor:
            cursor.execute("DELETE FROM checkpoints WHERE id = ?", (checkpoint_id,))
            return cursor.rowcount > 0

    def prune_checkpoints(
        self,
        aggregate_id: str,
        keep_count: int = 5,
    ) -> int:
        """Prune old checkpoints, keeping the N most recent.

        Returns number of checkpoints deleted.
        """
        with self._transaction() as cursor:
            # Get checkpoints to delete
            cursor.execute(
                """
                SELECT id FROM checkpoints
                WHERE aggregate_id = ?
                ORDER BY event_sequence DESC
                LIMIT -1 OFFSET ?
                """,
                (aggregate_id, keep_count),
            )
            to_delete = [row["id"] for row in cursor.fetchall()]

            if not to_delete:
                return 0

            placeholders = ",".join("?" * len(to_delete))
            cursor.execute(
                f"DELETE FROM checkpoints WHERE id IN ({placeholders})",
                to_delete,
            )
            return cursor.rowcount

    # ==========================================================================
    # Maintenance
    # ==========================================================================

    def clear(self) -> int:
        """Clear all events and checkpoints."""
        with self._lock:
            with self._transaction() as cursor:
                cursor.execute("DELETE FROM events")
                events_deleted = cursor.rowcount
                cursor.execute("DELETE FROM checkpoints")
                self._sequence = 0
                return events_deleted

    def close(self) -> None:
        """Close database connections."""
        if hasattr(self._local, "connection") and self._local.connection:
            self._local.connection.close()
            self._local.connection = None

    def export_ndjson(self) -> str:
        """Export all events as NDJSON."""
        events = self.get_all()
        lines = [json.dumps(e.to_dict()) for e in events]
        return "\n".join(lines)

    def import_ndjson(self, ndjson: str) -> int:
        """Import events from NDJSON.

        Args:
            ndjson: Newline-delimited JSON events

        Returns:
            Number of events imported
        """
        lines = ndjson.strip().split("\n")
        count = 0

        for line in lines:
            if not line.strip():
                continue

            data = json.loads(line)
            event = Event(
                id=data["id"],
                type=EventType(data["type"]),
                timestamp=datetime.fromisoformat(data["timestamp"]),
                source=data["source"],
                payload=data.get("payload", {}),
                metadata=data.get("metadata", {}),
            )
            self.append(event)
            count += 1

        return count
