"""Database connection and session management.

This module provides SQLAlchemy database connection management
for the persistence layer.

Usage:
    from paracle_store.database import Database, get_database

    # Create database with default SQLite
    db = Database()
    db.connect()

    # Use with context manager
    with db.session() as session:
        session.add(entity)
        session.commit()

    # Or use get_database() for singleton
    db = get_database()
"""

from __future__ import annotations

import threading
from contextlib import contextmanager
from pathlib import Path
from typing import TYPE_CHECKING

from sqlalchemy import MetaData, create_engine, event, text
from sqlalchemy.orm import Session, declarative_base, sessionmaker

if TYPE_CHECKING:
    from collections.abc import Iterator

    from sqlalchemy import Engine

# Naming convention for constraints (helps with migrations)
convention = {
    "ix": "ix_%(column_0_label)s",
    "uq": "uq_%(table_name)s_%(column_0_name)s",
    "ck": "ck_%(table_name)s_%(constraint_name)s",
    "fk": "fk_%(table_name)s_%(column_0_name)s_%(referred_table_name)s",
    "pk": "pk_%(table_name)s",
}

metadata = MetaData(naming_convention=convention)
Base = declarative_base(metadata=metadata)


class DatabaseError(Exception):
    """Base exception for database errors."""

    pass


class ConnectionError(DatabaseError):
    """Raised when database connection fails."""

    pass


class Database:
    """Database connection manager.

    Provides thread-safe database connection and session management.
    Supports SQLite and PostgreSQL.

    Attributes:
        url: Database connection URL
        engine: SQLAlchemy engine
        session_factory: Session factory for creating sessions
    """

    def __init__(
        self,
        url: str | None = None,
        *,
        echo: bool = False,
        pool_size: int = 5,
        pool_recycle: int = 3600,
    ) -> None:
        """Initialize database connection.

        Args:
            url: Database URL. Defaults to in-memory SQLite.
            echo: Whether to echo SQL statements.
            pool_size: Connection pool size (PostgreSQL only).
            pool_recycle: Connection recycle time in seconds.
        """
        self._url = url or "sqlite:///:memory:"
        self._echo = echo
        self._pool_size = pool_size
        self._pool_recycle = pool_recycle
        self._engine: Engine | None = None
        self._session_factory: sessionmaker[Session] | None = None
        self._lock = threading.Lock()

    @property
    def url(self) -> str:
        """Get database URL."""
        return self._url

    @property
    def is_sqlite(self) -> bool:
        """Check if using SQLite."""
        return self._url.startswith("sqlite:")

    @property
    def is_connected(self) -> bool:
        """Check if connected to database."""
        return self._engine is not None

    def connect(self) -> None:
        """Connect to the database.

        Creates engine and session factory. For SQLite file databases,
        ensures the parent directory exists.

        Raises:
            ConnectionError: If connection fails.
        """
        with self._lock:
            if self._engine is not None:
                return  # Already connected

            try:
                # Ensure directory exists for SQLite file databases
                if self.is_sqlite and ":///" in self._url:
                    db_path = self._url.split("///")[1]
                    if db_path != ":memory:":
                        Path(db_path).parent.mkdir(parents=True, exist_ok=True)

                # Create engine with appropriate settings
                if self.is_sqlite:
                    self._engine = create_engine(
                        self._url,
                        echo=self._echo,
                        connect_args={"check_same_thread": False},
                    )
                    # Enable foreign keys for SQLite
                    # Note: conn is a raw DBAPI connection, use cursor directly
                    event.listen(
                        self._engine,
                        "connect",
                        lambda conn, _: conn.execute("PRAGMA foreign_keys=ON"),
                    )
                else:
                    # PostgreSQL with connection pooling
                    self._engine = create_engine(
                        self._url,
                        echo=self._echo,
                        pool_size=self._pool_size,
                        pool_recycle=self._pool_recycle,
                    )

                self._session_factory = sessionmaker(
                    bind=self._engine,
                    expire_on_commit=False,
                )

            except Exception as e:
                raise ConnectionError(f"Failed to connect to database: {e}") from e

    def disconnect(self) -> None:
        """Disconnect from the database."""
        with self._lock:
            if self._engine is not None:
                self._engine.dispose()
                self._engine = None
                self._session_factory = None

    def create_tables(self) -> None:
        """Create all tables defined in models.

        Should be called after all models are imported.
        """
        if self._engine is None:
            self.connect()
        Base.metadata.create_all(self._engine)

    def drop_tables(self) -> None:
        """Drop all tables. USE WITH CAUTION."""
        if self._engine is not None:
            Base.metadata.drop_all(self._engine)

    @contextmanager
    def session(self) -> Iterator[Session]:
        """Create a database session context.

        Usage:
            with db.session() as session:
                session.add(entity)
                session.commit()

        Yields:
            SQLAlchemy Session

        Raises:
            ConnectionError: If not connected.
        """
        if self._session_factory is None:
            self.connect()

        if self._session_factory is None:
            raise ConnectionError("Database not connected")

        session = self._session_factory()
        try:
            yield session
            session.commit()
        except Exception:
            session.rollback()
            raise
        finally:
            session.close()

    def execute(self, sql: str) -> None:
        """Execute raw SQL.

        Args:
            sql: SQL statement to execute.
        """
        with self.session() as session:
            session.execute(text(sql))


# Global database instance
_database: Database | None = None
_database_lock = threading.Lock()


def get_database(url: str | None = None) -> Database:
    """Get the global database instance.

    Creates a new instance if not exists or if URL differs.

    Args:
        url: Database URL. Uses default if not provided.

    Returns:
        Database instance.
    """
    global _database

    with _database_lock:
        if _database is None or (url is not None and _database.url != url):
            _database = Database(url)
            _database.connect()
        return _database


def reset_database() -> None:
    """Reset the global database instance."""
    global _database

    with _database_lock:
        if _database is not None:
            _database.disconnect()
            _database = None
