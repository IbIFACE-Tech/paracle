"""Security configuration for Paracle API.

Centralizes all security-related settings with secure defaults.
"""

from __future__ import annotations

import os
from functools import lru_cache

from pydantic import Field, SecretStr, field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class SecurityConfig(BaseSettings):
    """Security configuration with secure defaults.

    All sensitive values should be provided via environment variables.
    Never commit secrets to version control.
    """

    model_config = SettingsConfigDict(
        env_prefix="PARACLE_",
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )

    # ==========================================================================
    # Authentication Settings
    # ==========================================================================

    jwt_secret_key: SecretStr = Field(
        default=SecretStr("CHANGE-ME-IN-PRODUCTION-USE-SECURE-RANDOM-KEY"),
        description="Secret key for JWT token signing. MUST be changed in production.",
    )

    jwt_algorithm: str = Field(
        default="HS256",
        description="Algorithm for JWT signing",
    )

    access_token_expire_minutes: int = Field(
        default=30,
        ge=1,
        le=1440,  # Max 24 hours
        description="Access token expiration time in minutes",
    )

    refresh_token_expire_days: int = Field(
        default=7,
        ge=1,
        le=30,
        description="Refresh token expiration time in days",
    )

    # ==========================================================================
    # CORS Settings
    # ==========================================================================

    cors_allowed_origins: list[str] = Field(
        default=["http://localhost:3000", "http://localhost:8080"],
        description="List of allowed CORS origins. Use specific origins, never '*' in production.",
    )

    cors_allow_credentials: bool = Field(
        default=True,
        description="Allow credentials in CORS requests",
    )

    cors_allowed_methods: list[str] = Field(
        default=["GET", "POST", "PUT", "DELETE", "PATCH"],
        description="Allowed HTTP methods for CORS",
    )

    cors_allowed_headers: list[str] = Field(
        default=["Authorization", "Content-Type", "X-Request-ID"],
        description="Allowed headers for CORS",
    )

    # ==========================================================================
    # Rate Limiting Settings
    # ==========================================================================

    rate_limit_enabled: bool = Field(
        default=True,
        description="Enable rate limiting",
    )

    rate_limit_requests: int = Field(
        default=100,
        ge=1,
        description="Maximum requests per window",
    )

    rate_limit_window_seconds: int = Field(
        default=60,
        ge=1,
        description="Rate limit window in seconds",
    )

    rate_limit_burst: int = Field(
        default=20,
        ge=1,
        description="Burst limit for rate limiting",
    )

    # ==========================================================================
    # Security Headers Settings
    # ==========================================================================

    enable_hsts: bool = Field(
        default=True,
        description="Enable HTTP Strict Transport Security",
    )

    hsts_max_age: int = Field(
        default=31536000,  # 1 year
        description="HSTS max-age in seconds",
    )

    enable_csp: bool = Field(
        default=True,
        description="Enable Content Security Policy",
    )

    csp_policy: str = Field(
        default="default-src 'self'; script-src 'self'; style-src 'self' 'unsafe-inline'",
        description="Content Security Policy header value",
    )

    # ==========================================================================
    # Input Validation Settings
    # ==========================================================================

    max_request_size_bytes: int = Field(
        default=10 * 1024 * 1024,  # 10 MB
        ge=1024,
        description="Maximum request body size in bytes",
    )

    max_json_depth: int = Field(
        default=10,
        ge=1,
        le=50,
        description="Maximum JSON nesting depth",
    )

    max_string_length: int = Field(
        default=100000,
        ge=100,
        description="Maximum string field length",
    )

    # ==========================================================================
    # Tool Sandboxing Settings
    # ==========================================================================

    filesystem_allowed_paths: list[str] = Field(
        default_factory=list,
        description="Allowed filesystem paths for tools. Empty = no access.",
    )

    shell_allowed_commands: list[str] = Field(
        default_factory=lambda: [
            "git",
            "ls",
            "cat",
            "head",
            "tail",
            "grep",
            "find",
            "python",
            "python3",
            "pip",
            "pytest",
            "make",
        ],
        description="Allowed shell commands",
    )

    shell_enable: bool = Field(
        default=False,
        description="Enable shell command execution (dangerous, disabled by default)",
    )

    # ==========================================================================
    # API Key Settings (for service-to-service auth)
    # ==========================================================================

    api_keys: list[SecretStr] = Field(
        default_factory=list,
        description="Valid API keys for service authentication",
    )

    # ==========================================================================
    # Validation
    # ==========================================================================

    @field_validator("jwt_secret_key")
    @classmethod
    def validate_jwt_secret(cls, v: SecretStr) -> SecretStr:
        """Warn if using default secret key."""
        secret = v.get_secret_value()
        if "CHANGE-ME" in secret:
            import warnings

            warnings.warn(
                "Using default JWT secret key! Set PARACLE_JWT_SECRET_KEY in production.",
                UserWarning,
                stacklevel=2,
            )
        if len(secret) < 32:
            raise ValueError("JWT secret key must be at least 32 characters")
        return v

    @field_validator("cors_allowed_origins")
    @classmethod
    def validate_cors_origins(cls, v: list[str]) -> list[str]:
        """Validate CORS origins."""
        if "*" in v:
            import warnings

            warnings.warn(
                "CORS allows all origins ('*'). This is insecure for production.",
                UserWarning,
                stacklevel=2,
            )
        return v

    def is_production(self) -> bool:
        """Check if running in production mode."""
        env = os.getenv("PARACLE_ENV", "development").lower()
        return env in ("production", "prod")

    def validate_production_config(self) -> list[str]:
        """Validate configuration for production use.

        Returns:
            List of configuration issues (empty if valid)
        """
        issues: list[str] = []

        # Check JWT secret
        if "CHANGE-ME" in self.jwt_secret_key.get_secret_value():
            issues.append("JWT secret key must be changed from default")

        # Check CORS
        if "*" in self.cors_allowed_origins:
            issues.append("CORS must not allow all origins in production")

        # Check rate limiting
        if not self.rate_limit_enabled:
            issues.append("Rate limiting should be enabled in production")

        return issues


# Global configuration instance
_config: SecurityConfig | None = None


@lru_cache
def get_security_config() -> SecurityConfig:
    """Get the security configuration singleton.

    Returns:
        SecurityConfig instance
    """
    global _config
    if _config is None:
        _config = SecurityConfig()
    return _config


def reset_security_config() -> None:
    """Reset the security configuration (for testing)."""
    global _config
    _config = None
    get_security_config.cache_clear()
