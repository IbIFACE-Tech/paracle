"""Storage configuration for Paracle.

This module provides the multi-layer storage configuration:
1. YAML/Markdown files - Configuration and definitions (.parac/)
2. SQLite/PostgreSQL - Runtime data (executions, events, audit)
3. ChromaDB/pgvector - Vector storage (future, for RAG)

Usage:
    from paracle_core.storage import StorageConfig, get_storage_config

    # Default configuration (file-based only)
    config = StorageConfig()

    # With SQLite persistence
    config = StorageConfig(
        database_url="sqlite:///paracle.db"
    )

    # Production with PostgreSQL
    config = StorageConfig(
        database_url="postgresql://user:pass@localhost/paracle"
    )
"""

from __future__ import annotations

from pathlib import Path
from typing import Literal

from pydantic import BaseModel, ConfigDict, Field, field_validator
from pydantic_settings import BaseSettings


class StorageConfig(BaseModel):
    """Multi-layer storage configuration.

    Attributes:
        workspace_path: Path to .parac/ workspace directory
        database_url: SQLite or PostgreSQL connection URL
        vector_store: Vector store type (none, chroma, pgvector)
        vector_store_path: Path for vector store data
        auto_migrate: Whether to run migrations automatically
    """

    model_config = ConfigDict(frozen=False, validate_default=True)

    # Layer 1: File-based (always available)
    workspace_path: Path = Field(
        default=Path(".parac"),
        description="Path to .parac/ workspace directory",
    )

    # Layer 2: Relational database (optional)
    database_url: str | None = Field(
        default=None,
        description="Database connection URL (sqlite:/// or postgresql://)",
    )

    # Layer 3: Vector store (optional, for RAG - future)
    vector_store: Literal["none", "chroma", "pgvector"] = Field(
        default="none",
        description="Vector store type for embeddings",
    )
    vector_store_path: str | None = Field(
        default=None,
        description="Path for vector store data",
    )

    # Migration settings
    auto_migrate: bool = Field(
        default=True,
        description="Automatically run database migrations",
    )

    @field_validator("database_url")
    @classmethod
    def validate_database_url(cls, v: str | None) -> str | None:
        """Validate database URL format."""
        if v is None:
            return v
        if not (v.startswith("sqlite:") or v.startswith("postgresql:")):
            msg = "database_url must start with 'sqlite:' or 'postgresql:'"
            raise ValueError(msg)
        return v

    @property
    def is_persistent(self) -> bool:
        """Check if persistent storage is configured."""
        return self.database_url is not None

    @property
    def is_sqlite(self) -> bool:
        """Check if using SQLite."""
        return self.database_url is not None and self.database_url.startswith("sqlite:")

    @property
    def is_postgresql(self) -> bool:
        """Check if using PostgreSQL."""
        return self.database_url is not None and self.database_url.startswith(
            "postgresql:"
        )

    @property
    def has_vector_store(self) -> bool:
        """Check if vector store is configured."""
        return self.vector_store != "none"

    @property
    def default_sqlite_path(self) -> Path:
        """Get default SQLite database path."""
        return self.workspace_path / "data" / "paracle.db"

    @property
    def default_sqlite_url(self) -> str:
        """Get default SQLite connection URL."""
        return f"sqlite:///{self.default_sqlite_path}"

    def get_database_url(self) -> str:
        """Get database URL, using default SQLite if not configured."""
        if self.database_url:
            return self.database_url
        return self.default_sqlite_url

    def ensure_directories(self) -> None:
        """Ensure all required directories exist."""
        self.workspace_path.mkdir(parents=True, exist_ok=True)
        if self.is_sqlite or self.database_url is None:
            (self.workspace_path / "data").mkdir(parents=True, exist_ok=True)


class StorageSettings(BaseSettings):
    """Storage settings from environment variables.

    Environment variables:
        PARACLE_WORKSPACE_PATH: Path to .parac/ workspace
        PARACLE_DATABASE_URL: Database connection URL
        PARACLE_VECTOR_STORE: Vector store type
        PARACLE_AUTO_MIGRATE: Whether to auto-run migrations
    """

    model_config = ConfigDict(
        env_prefix="PARACLE_",
        env_file=".env",
        extra="ignore",
    )

    workspace_path: Path = Path(".parac")
    database_url: str | None = None
    vector_store: Literal["none", "chroma", "pgvector"] = "none"
    vector_store_path: str | None = None
    auto_migrate: bool = True

    def to_storage_config(self) -> StorageConfig:
        """Convert settings to StorageConfig."""
        return StorageConfig(
            workspace_path=self.workspace_path,
            database_url=self.database_url,
            vector_store=self.vector_store,
            vector_store_path=self.vector_store_path,
            auto_migrate=self.auto_migrate,
        )


# Global storage configuration (can be overridden)
_storage_config: StorageConfig | None = None


def get_storage_config() -> StorageConfig:
    """Get the current storage configuration.

    Returns:
        Current StorageConfig, loading from environment if not set.
    """
    global _storage_config
    if _storage_config is None:
        settings = StorageSettings()
        _storage_config = settings.to_storage_config()
    return _storage_config


def set_storage_config(config: StorageConfig) -> None:
    """Set the global storage configuration.

    Args:
        config: StorageConfig to use globally.
    """
    global _storage_config
    _storage_config = config


def reset_storage_config() -> None:
    """Reset storage configuration to default (load from environment)."""
    global _storage_config
    _storage_config = None
