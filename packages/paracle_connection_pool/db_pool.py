"""Database connection pooling using SQLAlchemy."""

from dataclasses import dataclass
from typing import Any

try:
    from sqlalchemy import create_engine, pool
    from sqlalchemy.engine import Engine
    from sqlalchemy.orm import Session, sessionmaker

    SQLALCHEMY_AVAILABLE = True
except ImportError:
    SQLALCHEMY_AVAILABLE = False
    Engine = Any  # type: ignore
    Session = Any  # type: ignore


@dataclass
class DatabasePoolConfig:
    """Database connection pool configuration."""

    pool_size: int = 5  # Number of connections to maintain
    max_overflow: int = 10  # Max connections beyond pool_size
    pool_timeout: float = 30.0  # Seconds to wait for connection
    pool_recycle: int = 3600  # Seconds before recycling connection
    echo: bool = False  # Log SQL statements
    pool_pre_ping: bool = True  # Test connections before use

    @classmethod
    def from_env(cls) -> "DatabasePoolConfig":
        """Create config from environment variables."""
        import os

        return cls(
            pool_size=int(os.getenv("PARACLE_DB_POOL_SIZE", "5")),
            max_overflow=int(os.getenv("PARACLE_DB_MAX_OVERFLOW", "10")),
            pool_timeout=float(os.getenv("PARACLE_DB_POOL_TIMEOUT", "30.0")),
            pool_recycle=int(os.getenv("PARACLE_DB_POOL_RECYCLE", "3600")),
            echo=os.getenv("PARACLE_DB_ECHO", "false").lower() == "true",
            pool_pre_ping=os.getenv("PARACLE_DB_PRE_PING", "true").lower() == "true",
        )


class DatabasePool:
    """Database connection pool using SQLAlchemy."""

    def __init__(
        self,
        database_url: str,
        config: DatabasePoolConfig | None = None,
    ):
        """Initialize database connection pool.

        Args:
            database_url: Database connection URL
            config: Pool configuration (None = use defaults)
        """
        if not SQLALCHEMY_AVAILABLE:
            raise ImportError(
                "sqlalchemy is required for database pooling. "
                "Install with: pip install sqlalchemy"
            )

        self.database_url = database_url
        self.config = config or DatabasePoolConfig()

        # Create engine with pooling
        self.engine = create_engine(
            database_url,
            poolclass=pool.QueuePool,
            pool_size=self.config.pool_size,
            max_overflow=self.config.max_overflow,
            pool_timeout=self.config.pool_timeout,
            pool_recycle=self.config.pool_recycle,
            pool_pre_ping=self.config.pool_pre_ping,
            echo=self.config.echo,
        )

        # Create session factory
        self.SessionLocal = sessionmaker(
            autocommit=False,
            autoflush=False,
            bind=self.engine,
        )

        self._query_count = 0
        self._error_count = 0

    def get_session(self) -> Session:
        """Get database session from pool.

        Returns:
            SQLAlchemy session

        Example:
            ```python
            pool = DatabasePool("sqlite:///test.db")
            session = pool.get_session()
            try:
                # Use session
                results = session.query(Model).all()
            finally:
                session.close()
            ```
        """
        self._query_count += 1
        return self.SessionLocal()

    def session_context(self):
        """Get session as context manager.

        Yields:
            SQLAlchemy session that auto-closes

        Example:
            ```python
            pool = DatabasePool("sqlite:///test.db")
            with pool.session_context() as session:
                results = session.query(Model).all()
            # Session auto-closed
            ```
        """
        session = self.get_session()
        try:
            yield session
            session.commit()
        except Exception:
            session.rollback()
            self._error_count += 1
            raise
        finally:
            session.close()

    def close(self) -> None:
        """Close connection pool and all connections."""
        self.engine.dispose()

    def stats(self) -> dict[str, Any]:
        """Get pool statistics.

        Returns:
            Dictionary with pool stats
        """
        pool_status = self.engine.pool.status()

        return {
            "queries": self._query_count,
            "errors": self._error_count,
            "error_rate": (
                self._error_count / self._query_count if self._query_count > 0 else 0.0
            ),
            "pool_status": pool_status,
            "config": {
                "pool_size": self.config.pool_size,
                "max_overflow": self.config.max_overflow,
                "pool_timeout": self.config.pool_timeout,
                "pool_recycle": self.config.pool_recycle,
            },
        }

    def health_check(self) -> bool:
        """Check if database connection is healthy.

        Returns:
            True if connection is healthy
        """
        try:
            with self.session_context() as session:
                # Simple query to test connection
                session.execute("SELECT 1")
            return True
        except Exception:
            return False


# Global database pool instance
_db_pool: DatabasePool | None = None


def get_db_pool(
    database_url: str | None = None,
    config: DatabasePoolConfig | None = None,
) -> DatabasePool:
    """Get global database pool instance.

    Args:
        database_url: Database URL (only used on first call)
        config: Pool configuration (only used on first call)

    Returns:
        Global DatabasePool instance
    """
    global _db_pool
    if _db_pool is None:
        if database_url is None:
            import os

            database_url = os.getenv("PARACLE_DATABASE_URL", "sqlite:///./paracle.db")

        _db_pool = DatabasePool(database_url, config or DatabasePoolConfig.from_env())

    return _db_pool
