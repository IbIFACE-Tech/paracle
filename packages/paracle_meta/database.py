"""Database abstraction layer for paracle_meta.

Provides PostgreSQL + pgvector support with system-level storage.
Follows patterns from paracle_store/database.py.

System-level storage locations (NOT in .parac/):
- Linux: ~/.local/share/paracle/meta.db
- Windows: %LOCALAPPDATA%/Paracle/meta.db
- macOS: ~/Library/Application Support/Paracle/meta.db
- PostgreSQL: External server (recommended for production)

Usage:
    from paracle_meta.database import MetaDatabase, MetaDatabaseConfig

    # PostgreSQL with pgvector (production)
    config = MetaDatabaseConfig(
        postgres_url="postgresql://user:pass@localhost/paracle_meta",
        enable_vectors=True,
        embedding_provider="openai",
    )
    db = MetaDatabase(config)
    await db.connect()

    # Use sessions
    async with db.session() as session:
        session.add(record)
"""

from __future__ import annotations

import os
import platform
import threading
from contextlib import asynccontextmanager, contextmanager
from datetime import datetime
from enum import Enum
from pathlib import Path
from typing import TYPE_CHECKING, Any

from paracle_core.logging import get_logger
from pydantic import BaseModel, Field, field_validator
from sqlalchemy import (
    Column,
    DateTime,
    Float,
    ForeignKey,
    Index,
    Integer,
    MetaData,
    String,
    Text,
    create_engine,
    event,
)
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine
from sqlalchemy.orm import Session, declarative_base, relationship, sessionmaker
from sqlalchemy.types import JSON, TypeDecorator

if TYPE_CHECKING:
    from collections.abc import AsyncIterator, Iterator

    from sqlalchemy import Engine
    from sqlalchemy.ext.asyncio import AsyncEngine

logger = get_logger(__name__)

# Naming convention for constraints
convention = {
    "ix": "ix_%(column_0_label)s",
    "uq": "uq_%(table_name)s_%(column_0_name)s",
    "ck": "ck_%(table_name)s_%(constraint_name)s",
    "fk": "fk_%(table_name)s_%(column_0_name)s_%(referred_table_name)s",
    "pk": "pk_%(table_name)s",
}

metadata = MetaData(naming_convention=convention)
Base = declarative_base(metadata=metadata)


# Custom JSON type that uses JSONB for PostgreSQL
class JSONType(TypeDecorator):
    """JSON type that uses JSONB for PostgreSQL, JSON for SQLite."""

    impl = JSON
    cache_ok = True

    def load_dialect_impl(self, dialect: Any) -> Any:
        if dialect.name == "postgresql":
            return dialect.type_descriptor(JSONB())
        return dialect.type_descriptor(JSON())


class EmbeddingProvider(str, Enum):
    """Supported embedding providers."""

    OPENAI = "openai"
    OLLAMA = "ollama"


class MetaDatabaseConfig(BaseModel):
    """Configuration for meta engine database.

    Supports both PostgreSQL (production) and SQLite (development).
    Vector search is enabled by default when using PostgreSQL.
    """

    # PostgreSQL connection (production)
    postgres_url: str | None = Field(
        default=None,
        description="PostgreSQL connection URL (postgresql://user:pass@host/db)",
    )

    # SQLite fallback (development)
    sqlite_path: Path | None = Field(
        default=None,
        description="SQLite database path. Auto-set to system location if not provided.",
    )

    # Connection pool settings
    pool_size: int = Field(default=5, ge=1, le=50)
    pool_recycle: int = Field(
        default=3600, description="Connection recycle time in seconds"
    )
    echo: bool = Field(default=False, description="Echo SQL statements")

    # Vector/embedding settings
    enable_vectors: bool = Field(default=True, description="Enable vector storage")
    vector_dimensions: int = Field(
        default=1536,
        description="Embedding dimensions (1536 for OpenAI, 768 for Ollama nomic-embed-text)",
    )

    # Embedding provider
    embedding_provider: EmbeddingProvider = Field(
        default=EmbeddingProvider.OPENAI,
        description="Which embedding provider to use",
    )
    ollama_model: str = Field(
        default="nomic-embed-text",
        description="Ollama model for embeddings",
    )
    ollama_url: str = Field(
        default="http://localhost:11434",
        description="Ollama server URL",
    )
    openai_model: str = Field(
        default="text-embedding-3-small",
        description="OpenAI model for embeddings",
    )

    @field_validator("vector_dimensions")
    @classmethod
    def validate_dimensions(cls, v: int, info: Any) -> int:
        """Auto-set dimensions based on provider if using default."""
        return v

    @property
    def is_postgres(self) -> bool:
        """Check if using PostgreSQL."""
        return self.postgres_url is not None

    @property
    def connection_url(self) -> str:
        """Get the database connection URL."""
        if self.postgres_url:
            return self.postgres_url
        return f"sqlite:///{self.get_sqlite_path()}"

    @property
    def async_connection_url(self) -> str:
        """Get the async database connection URL."""
        if self.postgres_url:
            return self.postgres_url.replace("postgresql://", "postgresql+asyncpg://")
        return f"sqlite+aiosqlite:///{self.get_sqlite_path()}"

    def get_sqlite_path(self) -> Path:
        """Get SQLite path, using system location if not specified."""
        if self.sqlite_path:
            return self.sqlite_path
        return get_system_data_path() / "meta.db"


def get_system_data_path() -> Path:
    """Get system-level data directory for paracle.

    Returns platform-specific paths (NOT in .parac/):
    - Linux: ~/.local/share/paracle/
    - Windows: %LOCALAPPDATA%/Paracle/
    - macOS: ~/Library/Application Support/Paracle/
    """
    system = platform.system()

    if system == "Linux":
        xdg_data = os.environ.get("XDG_DATA_HOME", "")
        if xdg_data:
            base = Path(xdg_data)
        else:
            base = Path.home() / ".local" / "share"
        return base / "paracle"

    elif system == "Darwin":  # macOS
        return Path.home() / "Library" / "Application Support" / "Paracle"

    elif system == "Windows":
        local_app_data = os.environ.get("LOCALAPPDATA", "")
        if local_app_data:
            base = Path(local_app_data)
        else:
            base = Path.home() / "AppData" / "Local"
        return base / "Paracle"

    else:
        # Fallback for unknown systems
        return Path.home() / ".paracle"


# SQLAlchemy Models for meta engine


class GenerationRecord(Base):
    """Record of a generation by the meta engine."""

    __tablename__ = "meta_generations"

    id = Column(String(64), primary_key=True)
    artifact_type = Column(String(50), nullable=False, index=True)
    name = Column(String(255), nullable=False)
    content = Column(Text, nullable=False)
    provider = Column(String(50), nullable=False)
    model = Column(String(100), nullable=False)
    quality_score = Column(Float, nullable=False, default=0.0)
    cost_usd = Column(Float, nullable=False, default=0.0)
    tokens_input = Column(Integer, nullable=False, default=0)
    tokens_output = Column(Integer, nullable=False, default=0)
    reasoning = Column(Text, nullable=True)
    extra_data = Column(JSONType, nullable=True, default=dict)  # renamed from metadata
    created_at = Column(DateTime, nullable=False, default=datetime.utcnow, index=True)

    # Relationships
    feedback = relationship(
        "FeedbackRecord", back_populates="generation", cascade="all, delete-orphan"
    )

    __table_args__ = (
        Index("ix_meta_generations_type_created", "artifact_type", "created_at"),
    )


class FeedbackRecord(Base):
    """User feedback for a generation."""

    __tablename__ = "meta_feedback"

    id = Column(Integer, primary_key=True, autoincrement=True)
    generation_id = Column(
        String(64), ForeignKey("meta_generations.id"), nullable=False, index=True
    )
    rating = Column(Integer, nullable=False)  # 1-5 stars
    comment = Column(Text, nullable=True)
    usage_count = Column(Integer, nullable=False, default=1)
    created_at = Column(DateTime, nullable=False, default=datetime.utcnow)

    # Relationships
    generation = relationship("GenerationRecord", back_populates="feedback")


class TemplateRecord(Base):
    """Reusable template promoted from high-quality generations."""

    __tablename__ = "meta_templates"

    id = Column(String(64), primary_key=True)
    artifact_type = Column(String(50), nullable=False, index=True)
    name = Column(String(255), nullable=False)
    description = Column(Text, nullable=True)
    content = Column(Text, nullable=False)
    pattern = Column(Text, nullable=True)
    quality_score = Column(Float, nullable=False, default=0.0)
    usage_count = Column(Integer, nullable=False, default=0)
    source = Column(String(50), nullable=False, default="manual")  # manual, promoted
    source_generation_id = Column(String(64), nullable=True)
    extra_data = Column(JSONType, nullable=True, default=dict)  # renamed from metadata
    created_at = Column(DateTime, nullable=False, default=datetime.utcnow)
    updated_at = Column(
        DateTime, nullable=False, default=datetime.utcnow, onupdate=datetime.utcnow
    )

    __table_args__ = (
        Index("ix_meta_templates_type_quality", "artifact_type", "quality_score"),
    )


class BestPracticeRecord(Base):
    """Best practices knowledge base."""

    __tablename__ = "meta_best_practices"

    id = Column(String(64), primary_key=True)
    category = Column(String(100), nullable=False, index=True)
    practice = Column(Text, nullable=False)
    rationale = Column(Text, nullable=True)
    examples = Column(JSONType, nullable=True, default=list)
    tags = Column(JSONType, nullable=True, default=list)
    priority = Column(Integer, nullable=False, default=0)
    created_at = Column(DateTime, nullable=False, default=datetime.utcnow)


class CostRecord(Base):
    """Cost tracking record."""

    __tablename__ = "meta_costs"

    id = Column(Integer, primary_key=True, autoincrement=True)
    provider = Column(String(50), nullable=False, index=True)
    model = Column(String(100), nullable=False)
    operation = Column(String(50), nullable=False)  # generation, embedding, etc.
    cost_usd = Column(Float, nullable=False)
    tokens_input = Column(Integer, nullable=False, default=0)
    tokens_output = Column(Integer, nullable=False, default=0)
    generation_id = Column(String(64), nullable=True)
    created_at = Column(DateTime, nullable=False, default=datetime.utcnow, index=True)

    __table_args__ = (
        Index("ix_meta_costs_provider_created", "provider", "created_at"),
    )


class MemoryItem(Base):
    """Persistent memory item for meta engine context."""

    __tablename__ = "meta_memory"

    id = Column(String(64), primary_key=True)
    key = Column(String(255), nullable=False, unique=True, index=True)
    value = Column(JSONType, nullable=False)
    ttl_seconds = Column(Integer, nullable=True)  # None = no expiry
    created_at = Column(DateTime, nullable=False, default=datetime.utcnow)
    expires_at = Column(DateTime, nullable=True)


class ContextHistory(Base):
    """Context history for conversations."""

    __tablename__ = "meta_context_history"

    id = Column(Integer, primary_key=True, autoincrement=True)
    session_id = Column(String(64), nullable=False, index=True)
    role = Column(String(20), nullable=False)  # user, assistant, system
    content = Column(Text, nullable=False)
    extra_data = Column(JSONType, nullable=True, default=dict)  # renamed from metadata
    created_at = Column(DateTime, nullable=False, default=datetime.utcnow)

    __table_args__ = (
        Index("ix_meta_context_session_created", "session_id", "created_at"),
    )


class MetaDatabaseError(Exception):
    """Base exception for meta database errors."""

    pass


class MetaConnectionError(MetaDatabaseError):
    """Raised when database connection fails."""

    pass


class MetaDatabase:
    """Unified database interface for paracle_meta.

    Supports both sync and async operations.
    Uses system-level storage (NOT in .parac/).

    Usage:
        # Async usage (recommended for production)
        db = MetaDatabase(config)
        await db.connect_async()

        async with db.async_session() as session:
            session.add(record)

        # Sync usage (for CLI tools)
        db = MetaDatabase(config)
        db.connect()

        with db.session() as session:
            session.add(record)
    """

    def __init__(self, config: MetaDatabaseConfig | None = None) -> None:
        """Initialize meta database.

        Args:
            config: Database configuration. Uses defaults if not provided.
        """
        self.config = config or MetaDatabaseConfig()
        self._engine: Engine | None = None
        self._async_engine: AsyncEngine | None = None
        self._session_factory: sessionmaker[Session] | None = None
        self._async_session_factory: async_sessionmaker[AsyncSession] | None = None
        self._lock = threading.Lock()
        self._pgvector_enabled = False

    @property
    def is_connected(self) -> bool:
        """Check if connected to database."""
        return self._engine is not None or self._async_engine is not None

    @property
    def is_postgres(self) -> bool:
        """Check if using PostgreSQL."""
        return self.config.is_postgres

    @property
    def has_vectors(self) -> bool:
        """Check if vector support is available."""
        return self._pgvector_enabled

    def connect(self) -> None:
        """Connect to the database (sync).

        For CLI tools and sync operations.

        Raises:
            MetaConnectionError: If connection fails.
        """
        with self._lock:
            if self._engine is not None:
                return

            try:
                # Ensure data directory exists for SQLite
                if not self.config.is_postgres:
                    data_dir = self.config.get_sqlite_path().parent
                    data_dir.mkdir(parents=True, exist_ok=True)

                url = self.config.connection_url

                if self.config.is_postgres:
                    self._engine = create_engine(
                        url,
                        echo=self.config.echo,
                        pool_size=self.config.pool_size,
                        pool_recycle=self.config.pool_recycle,
                    )
                else:
                    self._engine = create_engine(
                        url,
                        echo=self.config.echo,
                        connect_args={"check_same_thread": False},
                    )
                    # Enable foreign keys for SQLite
                    event.listen(
                        self._engine,
                        "connect",
                        lambda conn, _: conn.execute("PRAGMA foreign_keys=ON"),
                    )

                self._session_factory = sessionmaker(
                    bind=self._engine,
                    expire_on_commit=False,
                )

                # Create tables
                Base.metadata.create_all(self._engine)

                # Try to enable pgvector for PostgreSQL
                if self.config.is_postgres and self.config.enable_vectors:
                    self._try_enable_pgvector_sync()

                logger.info(
                    "MetaDatabase connected",
                    extra={
                        "backend": (
                            "postgresql" if self.config.is_postgres else "sqlite"
                        ),
                        "vectors": self._pgvector_enabled,
                    },
                )

            except Exception as e:
                raise MetaConnectionError(f"Failed to connect: {e}") from e

    async def connect_async(self) -> None:
        """Connect to the database (async).

        For production async operations.

        Raises:
            MetaConnectionError: If connection fails.
        """
        if self._async_engine is not None:
            return

        try:
            # Ensure data directory exists for SQLite
            if not self.config.is_postgres:
                data_dir = self.config.get_sqlite_path().parent
                data_dir.mkdir(parents=True, exist_ok=True)

            url = self.config.async_connection_url

            if self.config.is_postgres:
                self._async_engine = create_async_engine(
                    url,
                    echo=self.config.echo,
                    pool_size=self.config.pool_size,
                    pool_recycle=self.config.pool_recycle,
                )
            else:
                self._async_engine = create_async_engine(
                    url,
                    echo=self.config.echo,
                )

            self._async_session_factory = async_sessionmaker(
                bind=self._async_engine,
                expire_on_commit=False,
            )

            # Create tables
            async with self._async_engine.begin() as conn:
                await conn.run_sync(Base.metadata.create_all)

            # Try to enable pgvector for PostgreSQL
            if self.config.is_postgres and self.config.enable_vectors:
                await self._try_enable_pgvector_async()

            logger.info(
                "MetaDatabase connected (async)",
                extra={
                    "backend": "postgresql" if self.config.is_postgres else "sqlite",
                    "vectors": self._pgvector_enabled,
                },
            )

        except Exception as e:
            raise MetaConnectionError(f"Failed to connect: {e}") from e

    def disconnect(self) -> None:
        """Disconnect from the database."""
        with self._lock:
            if self._engine is not None:
                self._engine.dispose()
                self._engine = None
                self._session_factory = None

    async def disconnect_async(self) -> None:
        """Disconnect from the database (async)."""
        if self._async_engine is not None:
            await self._async_engine.dispose()
            self._async_engine = None
            self._async_session_factory = None

    @contextmanager
    def session(self) -> Iterator[Session]:
        """Create a sync database session context.

        Usage:
            with db.session() as session:
                session.add(record)

        Yields:
            SQLAlchemy Session

        Raises:
            MetaConnectionError: If not connected.
        """
        if self._session_factory is None:
            self.connect()

        if self._session_factory is None:
            raise MetaConnectionError("Database not connected")

        session = self._session_factory()
        try:
            yield session
            session.commit()
        except Exception:
            session.rollback()
            raise
        finally:
            session.close()

    @asynccontextmanager
    async def async_session(self) -> AsyncIterator[AsyncSession]:
        """Create an async database session context.

        Usage:
            async with db.async_session() as session:
                session.add(record)

        Yields:
            SQLAlchemy AsyncSession

        Raises:
            MetaConnectionError: If not connected.
        """
        if self._async_session_factory is None:
            await self.connect_async()

        if self._async_session_factory is None:
            raise MetaConnectionError("Database not connected")

        async with self._async_session_factory() as session:
            try:
                yield session
                await session.commit()
            except Exception:
                await session.rollback()
                raise

    def _try_enable_pgvector_sync(self) -> None:
        """Try to enable pgvector extension (sync)."""
        if self._engine is None:
            return

        try:
            from sqlalchemy import text

            with self._engine.connect() as conn:
                conn.execute(text("CREATE EXTENSION IF NOT EXISTS vector"))
                conn.commit()
                self._pgvector_enabled = True
                logger.info("pgvector extension enabled")
        except Exception as e:
            logger.warning(f"pgvector not available: {e}")
            self._pgvector_enabled = False

    async def _try_enable_pgvector_async(self) -> None:
        """Try to enable pgvector extension (async)."""
        if self._async_engine is None:
            return

        try:
            from sqlalchemy import text

            async with self._async_engine.begin() as conn:
                await conn.execute(text("CREATE EXTENSION IF NOT EXISTS vector"))
                self._pgvector_enabled = True
                logger.info("pgvector extension enabled")
        except Exception as e:
            logger.warning(f"pgvector not available: {e}")
            self._pgvector_enabled = False


# Global database instance
_meta_database: MetaDatabase | None = None
_meta_database_lock = threading.Lock()


def get_meta_database(config: MetaDatabaseConfig | None = None) -> MetaDatabase:
    """Get the global meta database instance.

    Creates a new instance if not exists.

    Args:
        config: Database configuration. Uses defaults if not provided.

    Returns:
        MetaDatabase instance.
    """
    global _meta_database

    with _meta_database_lock:
        if _meta_database is None:
            _meta_database = MetaDatabase(config)
        return _meta_database


def reset_meta_database() -> None:
    """Reset the global meta database instance."""
    global _meta_database

    with _meta_database_lock:
        if _meta_database is not None:
            _meta_database.disconnect()
            _meta_database = None
