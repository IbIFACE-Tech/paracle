"""A2A Protocol Configuration.

Configuration classes for A2A server and client.
"""

from typing import Any

from pydantic import BaseModel, ConfigDict, Field


class SecuritySchemeConfig(BaseModel):
    """Security scheme configuration."""

    model_config = ConfigDict(frozen=True)

    scheme: str = Field(
        default="bearer",
        description="Authentication scheme (bearer, apiKey, oauth2)",
    )
    type: str = Field(
        default="http",
        description="Security type (http, apiKey, oauth2)",
    )
    bearer_format: str | None = Field(
        default="JWT",
        description="Bearer token format",
    )
    api_key_name: str | None = Field(
        default=None,
        description="API key header name (for apiKey type)",
    )
    api_key_location: str | None = Field(
        default="header",
        description="API key location (header, query)",
    )


class A2AServerConfig(BaseModel):
    """Configuration for A2A server."""

    model_config = ConfigDict(frozen=True)

    # Server settings
    host: str = Field(
        default="0.0.0.0",
        description="Server host address",
    )
    port: int = Field(
        default=8080,
        description="Server port",
    )
    base_path: str = Field(
        default="/a2a",
        description="Base path for A2A endpoints",
    )

    # Agent settings
    agent_ids: list[str] = Field(
        default_factory=list,
        description="List of agent IDs to expose (empty = all)",
    )
    expose_all_agents: bool = Field(
        default=True,
        description="Expose all available agents",
    )

    # Provider info (for Agent Cards)
    provider_name: str = Field(
        default="Paracle Framework",
        description="Provider organization name",
    )
    provider_url: str | None = Field(
        default="https://github.com/IbIFACE-Tech/paracle-lite",
        description="Provider URL",
    )

    # Capabilities
    enable_streaming: bool = Field(
        default=True,
        description="Enable SSE streaming for task updates",
    )
    enable_push_notifications: bool = Field(
        default=False,
        description="Enable push notifications (webhooks)",
    )
    enable_state_transition_history: bool = Field(
        default=True,
        description="Track task state transition history",
    )

    # Security
    require_authentication: bool = Field(
        default=False,
        description="Require authentication for all requests",
    )
    security_schemes: list[SecuritySchemeConfig] = Field(
        default_factory=list,
        description="Supported security schemes",
    )
    api_keys: list[str] = Field(
        default_factory=list,
        description="Valid API keys (for simple auth)",
    )
    cors_origins: list[str] = Field(
        default_factory=lambda: ["*"],
        description="CORS allowed origins",
    )

    # Rate limiting
    rate_limit_enabled: bool = Field(
        default=False,
        description="Enable rate limiting",
    )
    rate_limit_requests: int = Field(
        default=100,
        description="Max requests per window",
    )
    rate_limit_window_seconds: int = Field(
        default=60,
        description="Rate limit window in seconds",
    )

    # Task settings
    task_timeout_seconds: float = Field(
        default=300.0,
        description="Default task timeout in seconds",
    )
    max_concurrent_tasks: int = Field(
        default=10,
        description="Maximum concurrent tasks per agent",
    )
    task_history_limit: int = Field(
        default=1000,
        description="Maximum tasks to keep in history",
    )

    # Paracle integration
    parac_root: str = Field(
        default=".parac",
        description="Path to .parac directory",
    )

    def to_fastapi_kwargs(self) -> dict[str, Any]:
        """Convert to FastAPI/uvicorn kwargs.

        Returns:
            Dictionary of kwargs for uvicorn.run()
        """
        return {
            "host": self.host,
            "port": self.port,
        }


class A2AClientConfig(BaseModel):
    """Configuration for A2A client."""

    model_config = ConfigDict(frozen=True)

    # Connection settings
    timeout_seconds: float = Field(
        default=30.0,
        description="Request timeout in seconds",
    )
    connect_timeout_seconds: float = Field(
        default=10.0,
        description="Connection timeout in seconds",
    )
    max_retries: int = Field(
        default=3,
        description="Maximum retry attempts",
    )
    retry_delay_seconds: float = Field(
        default=1.0,
        description="Initial retry delay in seconds",
    )
    retry_backoff_factor: float = Field(
        default=2.0,
        description="Retry backoff multiplier",
    )

    # Streaming settings
    enable_streaming: bool = Field(
        default=True,
        description="Enable SSE streaming when available",
    )
    stream_timeout_seconds: float = Field(
        default=300.0,
        description="Streaming timeout in seconds",
    )
    stream_reconnect_attempts: int = Field(
        default=3,
        description="Stream reconnection attempts",
    )

    # Authentication
    auth_type: str | None = Field(
        default=None,
        description="Authentication type (bearer, apiKey)",
    )
    auth_token: str | None = Field(
        default=None,
        description="Authentication token or API key",
    )
    auth_header: str = Field(
        default="Authorization",
        description="Authentication header name",
    )

    # Discovery settings
    cache_agent_cards: bool = Field(
        default=True,
        description="Cache discovered Agent Cards",
    )
    card_cache_ttl_seconds: int = Field(
        default=3600,
        description="Agent Card cache TTL in seconds",
    )

    # HTTP client settings
    verify_ssl: bool = Field(
        default=True,
        description="Verify SSL certificates",
    )
    user_agent: str = Field(
        default="Paracle-A2A-Client/0.1",
        description="User-Agent header value",
    )

    def get_auth_headers(self) -> dict[str, str]:
        """Get authentication headers.

        Returns:
            Dictionary of authentication headers
        """
        if not self.auth_token:
            return {}

        if self.auth_type == "bearer":
            return {self.auth_header: f"Bearer {self.auth_token}"}
        elif self.auth_type == "apiKey":
            return {self.auth_header: self.auth_token}
        else:
            return {}
