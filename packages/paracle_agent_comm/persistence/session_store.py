"""Session Storage.

Provides persistence for group collaboration sessions.
"""

from abc import ABC, abstractmethod

from paracle_agent_comm.exceptions import SessionNotFoundError
from paracle_agent_comm.models import AgentGroup, GroupSession, GroupSessionStatus


class SessionStore(ABC):
    """Abstract base class for session storage."""

    @abstractmethod
    async def save_session(self, session: GroupSession) -> None:
        """Save a session to storage.

        Args:
            session: The session to save
        """
        pass

    @abstractmethod
    async def get_session(self, session_id: str) -> GroupSession:
        """Get a session by ID.

        Args:
            session_id: The session identifier

        Returns:
            The session

        Raises:
            SessionNotFoundError: If session not found
        """
        pass

    @abstractmethod
    async def list_sessions(
        self,
        group_id: str | None = None,
        status: GroupSessionStatus | None = None,
        limit: int = 100,
    ) -> list[GroupSession]:
        """List sessions with optional filters.

        Args:
            group_id: Filter by group ID
            status: Filter by status
            limit: Maximum number of results

        Returns:
            List of sessions matching criteria
        """
        pass

    @abstractmethod
    async def delete_session(self, session_id: str) -> None:
        """Delete a session.

        Args:
            session_id: The session to delete
        """
        pass

    @abstractmethod
    async def save_group(self, group: AgentGroup) -> None:
        """Save a group definition.

        Args:
            group: The group to save
        """
        pass

    @abstractmethod
    async def get_group(self, group_id: str) -> AgentGroup:
        """Get a group by ID.

        Args:
            group_id: The group identifier

        Returns:
            The group

        Raises:
            GroupNotFoundError: If group not found
        """
        pass

    @abstractmethod
    async def list_groups(self) -> list[AgentGroup]:
        """List all groups.

        Returns:
            List of all groups
        """
        pass


class InMemorySessionStore(SessionStore):
    """In-memory implementation of session storage.

    Useful for testing and development.
    """

    def __init__(self):
        """Initialize the in-memory store."""
        self._sessions: dict[str, GroupSession] = {}
        self._groups: dict[str, AgentGroup] = {}

    async def save_session(self, session: GroupSession) -> None:
        """Save a session to memory."""
        self._sessions[session.id] = session

    async def get_session(self, session_id: str) -> GroupSession:
        """Get a session by ID."""
        if session_id not in self._sessions:
            raise SessionNotFoundError(session_id)
        return self._sessions[session_id]

    async def list_sessions(
        self,
        group_id: str | None = None,
        status: GroupSessionStatus | None = None,
        limit: int = 100,
    ) -> list[GroupSession]:
        """List sessions with optional filters."""
        sessions = list(self._sessions.values())

        if group_id:
            sessions = [s for s in sessions if s.group_id == group_id]

        if status:
            sessions = [s for s in sessions if s.status == status]

        # Sort by started_at descending
        sessions.sort(key=lambda s: s.started_at, reverse=True)

        return sessions[:limit]

    async def delete_session(self, session_id: str) -> None:
        """Delete a session."""
        if session_id in self._sessions:
            del self._sessions[session_id]

    async def save_group(self, group: AgentGroup) -> None:
        """Save a group to memory."""
        self._groups[group.id] = group

    async def get_group(self, group_id: str) -> AgentGroup:
        """Get a group by ID."""
        from paracle_agent_comm.exceptions import GroupNotFoundError

        if group_id not in self._groups:
            raise GroupNotFoundError(group_id)
        return self._groups[group_id]

    async def list_groups(self) -> list[AgentGroup]:
        """List all groups."""
        return list(self._groups.values())

    def clear(self) -> None:
        """Clear all stored data (useful for testing)."""
        self._sessions.clear()
        self._groups.clear()
