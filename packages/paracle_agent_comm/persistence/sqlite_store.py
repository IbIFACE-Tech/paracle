"""SQLite Session Storage.

Provides persistent storage for group collaboration sessions using SQLite.
"""

import json
import sqlite3
from datetime import datetime
from pathlib import Path
from typing import Any

from paracle_agent_comm.exceptions import GroupNotFoundError, SessionNotFoundError
from paracle_agent_comm.models import (
    AgentGroup,
    CommunicationPattern,
    GroupMessage,
    GroupSession,
    GroupSessionStatus,
    GroupStatus,
    MessagePart,
    MessagePartType,
    MessageType,
)
from paracle_agent_comm.persistence.session_store import SessionStore


class SQLiteSessionStore(SessionStore):
    """SQLite implementation of session storage.

    Provides durable persistence for group sessions and agent groups.
    """

    def __init__(self, db_path: str | Path = "agent_comm.db"):
        """Initialize the SQLite store.

        Args:
            db_path: Path to the SQLite database file
        """
        self.db_path = Path(db_path)
        self._init_schema()

    def _get_connection(self) -> sqlite3.Connection:
        """Get a database connection."""
        conn = sqlite3.connect(str(self.db_path))
        conn.row_factory = sqlite3.Row
        return conn

    def _init_schema(self) -> None:
        """Initialize database schema."""
        with self._get_connection() as conn:
            conn.executescript(
                """
                -- Agent groups table
                CREATE TABLE IF NOT EXISTS agent_groups (
                    id TEXT PRIMARY KEY,
                    name TEXT NOT NULL,
                    description TEXT,
                    members TEXT NOT NULL,  -- JSON array
                    coordinator TEXT,
                    communication_pattern TEXT NOT NULL,
                    max_rounds INTEGER NOT NULL,
                    max_messages INTEGER NOT NULL,
                    timeout_seconds REAL NOT NULL,
                    status TEXT NOT NULL,
                    current_session_id TEXT,
                    default_context TEXT,  -- JSON object
                    external_members TEXT,  -- JSON array
                    created_at TEXT NOT NULL,
                    updated_at TEXT NOT NULL
                );

                -- Group sessions table
                CREATE TABLE IF NOT EXISTS group_sessions (
                    id TEXT PRIMARY KEY,
                    group_id TEXT NOT NULL,
                    goal TEXT NOT NULL,
                    status TEXT NOT NULL,
                    round_count INTEGER NOT NULL DEFAULT 0,
                    shared_context TEXT,  -- JSON object
                    outcome TEXT,
                    artifacts TEXT,  -- JSON array
                    started_at TEXT NOT NULL,
                    ended_at TEXT,
                    total_tokens INTEGER NOT NULL DEFAULT 0,
                    estimated_cost REAL NOT NULL DEFAULT 0.0,
                    FOREIGN KEY (group_id) REFERENCES agent_groups(id)
                );

                -- Group messages table
                CREATE TABLE IF NOT EXISTS group_messages (
                    id TEXT PRIMARY KEY,
                    session_id TEXT NOT NULL,
                    group_id TEXT NOT NULL,
                    sender TEXT NOT NULL,
                    recipients TEXT,  -- JSON array or NULL for broadcast
                    content TEXT NOT NULL,  -- JSON array of MessagePart
                    conversation_id TEXT NOT NULL,
                    in_reply_to TEXT,
                    message_type TEXT NOT NULL,
                    priority TEXT NOT NULL DEFAULT 'normal',
                    timestamp TEXT NOT NULL,
                    metadata TEXT,  -- JSON object
                    expects_reply INTEGER NOT NULL DEFAULT 0,
                    timeout_seconds REAL,
                    FOREIGN KEY (session_id) REFERENCES group_sessions(id)
                );

                -- Indexes for common queries
                CREATE INDEX IF NOT EXISTS idx_sessions_group_id
                    ON group_sessions(group_id);
                CREATE INDEX IF NOT EXISTS idx_sessions_status
                    ON group_sessions(status);
                CREATE INDEX IF NOT EXISTS idx_messages_session_id
                    ON group_messages(session_id);
                CREATE INDEX IF NOT EXISTS idx_messages_sender
                    ON group_messages(sender);
                """
            )
            conn.commit()

    async def save_session(self, session: GroupSession) -> None:
        """Save a session to SQLite."""
        with self._get_connection() as conn:
            # Upsert session
            conn.execute(
                """
                INSERT OR REPLACE INTO group_sessions (
                    id, group_id, goal, status, round_count,
                    shared_context, outcome, artifacts,
                    started_at, ended_at, total_tokens, estimated_cost
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    session.id,
                    session.group_id,
                    session.goal,
                    session.status.value,
                    session.round_count,
                    json.dumps(session.shared_context),
                    session.outcome,
                    json.dumps(session.artifacts),
                    session.started_at.isoformat(),
                    session.ended_at.isoformat() if session.ended_at else None,
                    session.total_tokens,
                    session.estimated_cost,
                ),
            )

            # Save messages (delete existing and re-insert)
            conn.execute(
                "DELETE FROM group_messages WHERE session_id = ?",
                (session.id,),
            )

            for msg in session.messages:
                self._insert_message(conn, session.id, msg)

            conn.commit()

    def _insert_message(
        self,
        conn: sqlite3.Connection,
        session_id: str,
        message: GroupMessage,
    ) -> None:
        """Insert a message into the database."""
        content_json = json.dumps(
            [self._message_part_to_dict(p) for p in message.content]
        )

        conn.execute(
            """
            INSERT INTO group_messages (
                id, session_id, group_id, sender, recipients,
                content, conversation_id, in_reply_to,
                message_type, priority, timestamp,
                metadata, expects_reply, timeout_seconds
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                message.id,
                session_id,
                message.group_id,
                message.sender,
                json.dumps(message.recipients) if message.recipients else None,
                content_json,
                message.conversation_id,
                message.in_reply_to,
                message.message_type.value,
                message.priority,
                message.timestamp.isoformat(),
                json.dumps(message.metadata),
                1 if message.expects_reply else 0,
                message.timeout_seconds,
            ),
        )

    def _message_part_to_dict(self, part: MessagePart) -> dict[str, Any]:
        """Convert MessagePart to dict for JSON storage."""
        return {
            "type": part.type.value,
            "content": part.content,
            "mime_type": part.mime_type,
            "metadata": part.metadata,
            "language": part.language,
            "filename": part.filename,
        }

    def _dict_to_message_part(self, data: dict[str, Any]) -> MessagePart:
        """Convert dict to MessagePart."""
        return MessagePart(
            type=MessagePartType(data["type"]),
            content=data["content"],
            mime_type=data.get("mime_type", "text/plain"),
            metadata=data.get("metadata", {}),
            language=data.get("language"),
            filename=data.get("filename"),
        )

    async def get_session(self, session_id: str) -> GroupSession:
        """Get a session by ID."""
        with self._get_connection() as conn:
            row = conn.execute(
                "SELECT * FROM group_sessions WHERE id = ?",
                (session_id,),
            ).fetchone()

            if not row:
                raise SessionNotFoundError(session_id)

            return self._row_to_session(conn, row)

    def _row_to_session(
        self,
        conn: sqlite3.Connection,
        row: sqlite3.Row,
    ) -> GroupSession:
        """Convert database row to GroupSession."""
        # Load messages for this session
        message_rows = conn.execute(
            "SELECT * FROM group_messages WHERE session_id = ? ORDER BY timestamp",
            (row["id"],),
        ).fetchall()

        messages = [self._row_to_message(r) for r in message_rows]

        return GroupSession(
            id=row["id"],
            group_id=row["group_id"],
            goal=row["goal"],
            messages=messages,
            status=GroupSessionStatus(row["status"]),
            round_count=row["round_count"],
            shared_context=json.loads(row["shared_context"] or "{}"),
            outcome=row["outcome"],
            artifacts=json.loads(row["artifacts"] or "[]"),
            started_at=datetime.fromisoformat(row["started_at"]),
            ended_at=(
                datetime.fromisoformat(row["ended_at"]) if row["ended_at"] else None
            ),
            total_tokens=row["total_tokens"],
            estimated_cost=row["estimated_cost"],
        )

    def _row_to_message(self, row: sqlite3.Row) -> GroupMessage:
        """Convert database row to GroupMessage."""
        content_data = json.loads(row["content"])
        content = [self._dict_to_message_part(p) for p in content_data]

        return GroupMessage(
            id=row["id"],
            group_id=row["group_id"],
            sender=row["sender"],
            recipients=json.loads(row["recipients"]) if row["recipients"] else None,
            content=content,
            conversation_id=row["conversation_id"],
            in_reply_to=row["in_reply_to"],
            message_type=MessageType(row["message_type"]),
            priority=row["priority"],
            timestamp=datetime.fromisoformat(row["timestamp"]),
            metadata=json.loads(row["metadata"] or "{}"),
            expects_reply=bool(row["expects_reply"]),
            timeout_seconds=row["timeout_seconds"],
        )

    async def list_sessions(
        self,
        group_id: str | None = None,
        status: GroupSessionStatus | None = None,
        limit: int = 100,
    ) -> list[GroupSession]:
        """List sessions with optional filters."""
        with self._get_connection() as conn:
            query = "SELECT * FROM group_sessions WHERE 1=1"
            params: list[Any] = []

            if group_id:
                query += " AND group_id = ?"
                params.append(group_id)

            if status:
                query += " AND status = ?"
                params.append(status.value)

            query += " ORDER BY started_at DESC LIMIT ?"
            params.append(limit)

            rows = conn.execute(query, params).fetchall()
            return [self._row_to_session(conn, row) for row in rows]

    async def delete_session(self, session_id: str) -> None:
        """Delete a session and its messages."""
        with self._get_connection() as conn:
            # Delete messages first (foreign key)
            conn.execute(
                "DELETE FROM group_messages WHERE session_id = ?",
                (session_id,),
            )
            conn.execute(
                "DELETE FROM group_sessions WHERE id = ?",
                (session_id,),
            )
            conn.commit()

    async def save_group(self, group: AgentGroup) -> None:
        """Save a group to SQLite."""
        with self._get_connection() as conn:
            conn.execute(
                """
                INSERT OR REPLACE INTO agent_groups (
                    id, name, description, members, coordinator,
                    communication_pattern, max_rounds, max_messages,
                    timeout_seconds, status, current_session_id,
                    default_context, external_members, created_at, updated_at
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    group.id,
                    group.name,
                    group.description,
                    json.dumps(group.members),
                    group.coordinator,
                    group.communication_pattern.value,
                    group.max_rounds,
                    group.max_messages,
                    group.timeout_seconds,
                    group.status.value,
                    group.current_session_id,
                    json.dumps(group.default_context),
                    json.dumps(group.external_members),
                    group.created_at.isoformat(),
                    group.updated_at.isoformat(),
                ),
            )
            conn.commit()

    async def get_group(self, group_id: str) -> AgentGroup:
        """Get a group by ID."""
        with self._get_connection() as conn:
            row = conn.execute(
                "SELECT * FROM agent_groups WHERE id = ?",
                (group_id,),
            ).fetchone()

            if not row:
                raise GroupNotFoundError(group_id)

            return self._row_to_group(row)

    def _row_to_group(self, row: sqlite3.Row) -> AgentGroup:
        """Convert database row to AgentGroup."""
        return AgentGroup(
            id=row["id"],
            name=row["name"],
            description=row["description"],
            members=json.loads(row["members"]),
            coordinator=row["coordinator"],
            communication_pattern=CommunicationPattern(row["communication_pattern"]),
            max_rounds=row["max_rounds"],
            max_messages=row["max_messages"],
            timeout_seconds=row["timeout_seconds"],
            status=GroupStatus(row["status"]),
            current_session_id=row["current_session_id"],
            default_context=json.loads(row["default_context"] or "{}"),
            external_members=json.loads(row["external_members"] or "[]"),
            created_at=datetime.fromisoformat(row["created_at"]),
            updated_at=datetime.fromisoformat(row["updated_at"]),
        )

    async def list_groups(self) -> list[AgentGroup]:
        """List all groups."""
        with self._get_connection() as conn:
            rows = conn.execute("SELECT * FROM agent_groups ORDER BY name").fetchall()
            return [self._row_to_group(row) for row in rows]

    async def get_group_by_name(self, name: str) -> AgentGroup | None:
        """Get a group by name."""
        with self._get_connection() as conn:
            row = conn.execute(
                "SELECT * FROM agent_groups WHERE name = ?",
                (name,),
            ).fetchone()

            if not row:
                return None

            return self._row_to_group(row)

    async def delete_group(self, group_id: str) -> None:
        """Delete a group and all its sessions."""
        with self._get_connection() as conn:
            # Get all sessions for this group
            sessions = conn.execute(
                "SELECT id FROM group_sessions WHERE group_id = ?",
                (group_id,),
            ).fetchall()

            # Delete messages for each session
            for session in sessions:
                conn.execute(
                    "DELETE FROM group_messages WHERE session_id = ?",
                    (session["id"],),
                )

            # Delete sessions
            conn.execute(
                "DELETE FROM group_sessions WHERE group_id = ?",
                (group_id,),
            )

            # Delete group
            conn.execute(
                "DELETE FROM agent_groups WHERE id = ?",
                (group_id,),
            )
            conn.commit()

    async def get_session_count(self, group_id: str | None = None) -> int:
        """Get the count of sessions, optionally filtered by group."""
        with self._get_connection() as conn:
            if group_id:
                result = conn.execute(
                    "SELECT COUNT(*) FROM group_sessions WHERE group_id = ?",
                    (group_id,),
                ).fetchone()
            else:
                result = conn.execute("SELECT COUNT(*) FROM group_sessions").fetchone()
            return result[0]

    async def get_message_count(self, session_id: str) -> int:
        """Get the count of messages in a session."""
        with self._get_connection() as conn:
            result = conn.execute(
                "SELECT COUNT(*) FROM group_messages WHERE session_id = ?",
                (session_id,),
            ).fetchone()
            return result[0]
