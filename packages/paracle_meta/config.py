"""Configuration validation for paracle_meta.

Provides Pydantic-based configuration with validation,
environment variable support, and YAML file loading.

Configuration sources (in order of precedence):
1. Environment variables (PARACLE_META_*)
2. .env file
3. System config file (~/.config/paracle/meta.yaml)
4. Project config file (.parac/config/meta_agent.yaml)
5. Default values

Usage:
    from paracle_meta.config import MetaEngineConfig, load_config

    # Load from all sources
    config = load_config()

    # Or create with specific values
    config = MetaEngineConfig(
        default_provider="anthropic",
        max_daily_budget=10.0,
    )

    # Access validated values
    print(config.database.postgres_url)
    print(config.learning.min_rating_for_promotion)
"""

from __future__ import annotations

import os
import platform
from enum import Enum
from pathlib import Path
from typing import Any

import yaml
from pydantic import BaseModel, Field, field_validator, model_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


# Embedding provider enum - define locally to avoid circular imports
class EmbeddingProvider(str, Enum):
    """Supported embedding providers."""

    OPENAI = "openai"
    OLLAMA = "ollama"


# Database config - define minimal version here, full version in database.py
class MinimalDatabaseConfig(BaseModel):
    """Minimal database config when sqlalchemy is not available."""

    postgres_url: str | None = None
    enable_vectors: bool = False
    embedding_provider: EmbeddingProvider = EmbeddingProvider.OPENAI


# Try to import full MetaDatabaseConfig, fallback to minimal
try:
    from paracle_meta.database import MetaDatabaseConfig

    _HAS_DATABASE = True
except ImportError:
    _HAS_DATABASE = False
    MetaDatabaseConfig = MinimalDatabaseConfig  # type: ignore


class ProviderConfig(BaseModel):
    """Configuration for an LLM provider."""

    name: str = Field(..., description="Provider name (anthropic, openai, ollama)")
    model: str = Field(..., description="Model identifier")
    api_key: str | None = Field(default=None, description="API key (can use env var)")
    base_url: str | None = Field(default=None, description="Custom API base URL")
    use_for: list[str] = Field(
        default_factory=list,
        description="Task types this provider is preferred for",
    )
    max_tokens: int = Field(default=4096, ge=1, le=128000)
    temperature: float = Field(default=0.7, ge=0.0, le=2.0)

    @field_validator("name")
    @classmethod
    def validate_provider_name(cls, v: str) -> str:
        valid_providers = {"anthropic", "openai", "ollama", "azure", "groq", "mistral"}
        if v.lower() not in valid_providers:
            raise ValueError(f"Unknown provider: {v}. Valid: {valid_providers}")
        return v.lower()


class LearningConfig(BaseModel):
    """Configuration for the learning engine."""

    enabled: bool = Field(default=True, description="Enable learning engine")
    feedback_collection: bool = Field(default=True, description="Collect user feedback")
    min_feedback_for_promotion: int = Field(
        default=3,
        ge=1,
        description="Minimum feedback samples before template promotion",
    )
    min_rating_for_promotion: float = Field(
        default=4.0,
        ge=1.0,
        le=5.0,
        description="Minimum average rating for template promotion",
    )
    min_quality_for_promotion: float = Field(
        default=8.0,
        ge=0.0,
        le=10.0,
        description="Minimum quality score for template promotion",
    )


class CostConfig(BaseModel):
    """Configuration for cost optimization."""

    enabled: bool = Field(default=True, description="Enable cost tracking")
    max_daily_budget: float = Field(
        default=10.0,
        gt=0,
        description="Maximum daily budget in USD",
    )
    max_monthly_budget: float = Field(
        default=100.0,
        gt=0,
        description="Maximum monthly budget in USD",
    )
    warning_threshold: float = Field(
        default=0.8,
        ge=0.0,
        le=1.0,
        description="Percentage of budget to trigger warning",
    )
    fallback_on_limit: bool = Field(
        default=True,
        description="Use cheaper models when approaching limit",
    )

    @model_validator(mode="after")
    def validate_budgets(self) -> CostConfig:
        if self.max_daily_budget > self.max_monthly_budget:
            raise ValueError("Daily budget cannot exceed monthly budget")
        return self


class QualityConfig(BaseModel):
    """Configuration for quality thresholds."""

    min_quality_score: float = Field(
        default=7.0,
        ge=0.0,
        le=10.0,
        description="Minimum acceptable quality score",
    )
    auto_retry_on_low_quality: bool = Field(
        default=True,
        description="Automatically retry if quality is below threshold",
    )
    max_retries: int = Field(
        default=2,
        ge=0,
        le=5,
        description="Maximum retry attempts for low quality",
    )


class RetryConfig(BaseModel):
    """Configuration for error recovery and retries."""

    max_attempts: int = Field(default=3, ge=1, le=10)
    base_delay: float = Field(default=1.0, ge=0.1, le=60.0)
    max_delay: float = Field(default=30.0, ge=1.0, le=300.0)
    exponential_base: float = Field(default=2.0, ge=1.5, le=4.0)
    jitter: bool = Field(default=True, description="Add random jitter to delays")


class CircuitBreakerConfig(BaseModel):
    """Configuration for circuit breaker pattern."""

    enabled: bool = Field(default=True)
    failure_threshold: int = Field(
        default=5,
        ge=1,
        description="Failures before opening circuit",
    )
    reset_timeout: float = Field(
        default=60.0,
        ge=10.0,
        description="Seconds before attempting recovery",
    )
    half_open_max_calls: int = Field(
        default=3,
        ge=1,
        description="Test calls in half-open state",
    )


class MetaEngineConfig(BaseSettings):
    """Complete configuration for paracle_meta engine.

    Loads from environment variables with PARACLE_META_ prefix.
    """

    model_config = SettingsConfigDict(
        env_prefix="PARACLE_META_",
        env_file=".env",
        env_file_encoding="utf-8",
        env_nested_delimiter="__",
        extra="ignore",
    )

    # Database configuration
    database: MetaDatabaseConfig = Field(default_factory=MetaDatabaseConfig)

    # Provider configuration
    providers: list[ProviderConfig] = Field(default_factory=list)
    default_provider: str = Field(
        default="anthropic",
        description="Default LLM provider to use",
    )

    # Learning configuration
    learning: LearningConfig = Field(default_factory=LearningConfig)

    # Cost configuration
    cost: CostConfig = Field(default_factory=CostConfig)

    # Quality configuration
    quality: QualityConfig = Field(default_factory=QualityConfig)

    # Retry configuration
    retry: RetryConfig = Field(default_factory=RetryConfig)

    # Circuit breaker configuration
    circuit_breaker: CircuitBreakerConfig = Field(default_factory=CircuitBreakerConfig)

    # Feature flags
    enable_web_capabilities: bool = Field(default=False)
    enable_code_execution: bool = Field(default=False)
    enable_mcp_integration: bool = Field(default=False)
    enable_agent_spawning: bool = Field(default=False)

    @field_validator("default_provider")
    @classmethod
    def validate_default_provider(cls, v: str) -> str:
        valid_providers = {"anthropic", "openai", "ollama", "azure", "groq", "mistral"}
        if v.lower() not in valid_providers:
            raise ValueError(f"Unknown provider: {v}. Valid: {valid_providers}")
        return v.lower()

    def get_provider_config(self, name: str) -> ProviderConfig | None:
        """Get configuration for a specific provider."""
        for provider in self.providers:
            if provider.name.lower() == name.lower():
                return provider
        return None

    def get_provider_for_task(self, task_type: str) -> ProviderConfig | None:
        """Get the preferred provider for a task type."""
        for provider in self.providers:
            if task_type in provider.use_for:
                return provider

        # Fall back to default provider
        return self.get_provider_config(self.default_provider)


def get_system_config_path() -> Path:
    """Get system-level configuration path.

    Returns:
        Platform-specific config path:
        - Linux: ~/.config/paracle/meta.yaml
        - Windows: %APPDATA%/Paracle/meta.yaml
        - macOS: ~/Library/Application Support/Paracle/meta.yaml
    """
    system = platform.system()

    if system == "Linux":
        xdg_config = os.environ.get("XDG_CONFIG_HOME", "")
        if xdg_config:
            base = Path(xdg_config)
        else:
            base = Path.home() / ".config"
        return base / "paracle" / "meta.yaml"

    elif system == "Darwin":  # macOS
        return Path.home() / "Library" / "Application Support" / "Paracle" / "meta.yaml"

    elif system == "Windows":
        app_data = os.environ.get("APPDATA", "")
        if app_data:
            base = Path(app_data)
        else:
            base = Path.home() / "AppData" / "Roaming"
        return base / "Paracle" / "meta.yaml"

    else:
        return Path.home() / ".config" / "paracle" / "meta.yaml"


def get_project_config_path() -> Path:
    """Get project-level configuration path.

    Returns:
        Path to .parac/config/meta_agent.yaml in current directory.
    """
    return Path.cwd() / ".parac" / "config" / "meta_agent.yaml"


def load_yaml_config(path: Path) -> dict[str, Any]:
    """Load configuration from YAML file.

    Args:
        path: Path to YAML file.

    Returns:
        Configuration dictionary (empty if file doesn't exist).
    """
    if not path.exists():
        return {}

    try:
        with open(path, encoding="utf-8") as f:
            data = yaml.safe_load(f)
            return data if data else {}
    except Exception as e:
        import warnings

        warnings.warn(f"Failed to load config from {path}: {e}")
        return {}


def merge_configs(*configs: dict[str, Any]) -> dict[str, Any]:
    """Merge multiple configuration dictionaries.

    Later configs override earlier ones.
    Nested dicts are merged recursively.

    Args:
        *configs: Configuration dictionaries to merge.

    Returns:
        Merged configuration.
    """
    result: dict[str, Any] = {}

    for config in configs:
        for key, value in config.items():
            if (
                key in result
                and isinstance(result[key], dict)
                and isinstance(value, dict)
            ):
                result[key] = merge_configs(result[key], value)
            else:
                result[key] = value

    return result


def load_config(
    project_path: Path | None = None,
    system_path: Path | None = None,
) -> MetaEngineConfig:
    """Load configuration from all sources.

    Merges configuration from (in order of increasing precedence):
    1. Default values
    2. System config file
    3. Project config file
    4. Environment variables

    Args:
        project_path: Custom project config path.
        system_path: Custom system config path.

    Returns:
        Validated MetaEngineConfig.
    """
    # Load from YAML files
    system_config = load_yaml_config(system_path or get_system_config_path())
    project_config = load_yaml_config(project_path or get_project_config_path())

    # Merge configurations
    merged = merge_configs(system_config, project_config)

    # Create config (env vars are loaded automatically by pydantic-settings)
    if merged:
        # Handle nested config sections
        if "meta_agent" in merged:
            merged = merged["meta_agent"]

        return MetaEngineConfig(**merged)
    else:
        return MetaEngineConfig()


def validate_config(config: MetaEngineConfig) -> list[str]:
    """Validate configuration and return warnings.

    Args:
        config: Configuration to validate.

    Returns:
        List of warning messages (empty if all good).
    """
    warnings: list[str] = []

    # Check database configuration
    if config.database.is_postgres:
        if not config.database.postgres_url:
            warnings.append("PostgreSQL URL is empty")
    else:
        # SQLite mode
        if config.database.enable_vectors:
            warnings.append(
                "Vector search not available in SQLite mode. "
                "Use PostgreSQL with pgvector for vector features."
            )

    # Check provider configuration
    if not config.providers:
        warnings.append(
            "No providers configured. Add providers to use generation features."
        )

    # Check for API keys
    default_provider = config.get_provider_config(config.default_provider)
    if default_provider and not default_provider.api_key:
        env_var = f"{config.default_provider.upper()}_API_KEY"
        if not os.environ.get(env_var):
            warnings.append(
                f"No API key for default provider '{config.default_provider}'. "
                f"Set {env_var} environment variable."
            )

    # Check cost limits
    if config.cost.max_daily_budget > 100:
        warnings.append(
            f"High daily budget: ${config.cost.max_daily_budget}. "
            "Consider setting a lower limit."
        )

    return warnings


# Example configuration file content
EXAMPLE_CONFIG = """
# Paracle Meta Engine Configuration
# Place at ~/.config/paracle/meta.yaml (Linux/macOS) or %APPDATA%/Paracle/meta.yaml (Windows)

meta_agent:
  database:
    # PostgreSQL with pgvector (recommended for production)
    postgres_url: "postgresql://user:pass@localhost/paracle_meta"
    pool_size: 10
    enable_vectors: true

    # Embedding settings
    embedding_provider: openai  # or "ollama" for local
    openai_model: text-embedding-3-small
    ollama_model: nomic-embed-text
    ollama_url: "http://localhost:11434"

  providers:
    - name: anthropic
      model: claude-sonnet-4-20250514
      use_for: [agents, security, code]

    - name: openai
      model: gpt-4o
      use_for: [documentation, embeddings]

    - name: ollama
      model: llama3.1
      base_url: "http://localhost:11434"
      use_for: [quick-tasks]

  default_provider: anthropic

  learning:
    enabled: true
    min_feedback_for_promotion: 3
    min_rating_for_promotion: 4.0

  cost:
    enabled: true
    max_daily_budget: 10.0
    max_monthly_budget: 100.0
    warning_threshold: 0.8

  quality:
    min_quality_score: 7.0
    auto_retry_on_low_quality: true

  retry:
    max_attempts: 3
    base_delay: 1.0
    max_delay: 30.0
    jitter: true

  circuit_breaker:
    enabled: true
    failure_threshold: 5
    reset_timeout: 60.0

  # Feature flags
  enable_web_capabilities: false
  enable_code_execution: false
  enable_mcp_integration: false
  enable_agent_spawning: false
"""
