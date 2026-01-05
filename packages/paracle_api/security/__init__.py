"""Paracle API Security Module.

This module provides comprehensive security features including:
- JWT Authentication
- Rate Limiting
- Security Headers
- Input Validation
- CORS Configuration
"""

from paracle_api.security.auth import (
    Token,
    TokenData,
    User,
    authenticate_user,
    create_access_token,
    get_current_user,
    get_password_hash,
    oauth2_scheme,
    verify_password,
)
from paracle_api.security.config import SecurityConfig, get_security_config
from paracle_api.security.headers import SecurityHeadersMiddleware
from paracle_api.security.rate_limit import RateLimiter, rate_limit

__all__ = [
    # Auth
    "Token",
    "TokenData",
    "User",
    "authenticate_user",
    "create_access_token",
    "get_current_user",
    "get_password_hash",
    "verify_password",
    "oauth2_scheme",
    # Config
    "SecurityConfig",
    "get_security_config",
    # Headers
    "SecurityHeadersMiddleware",
    # Rate Limiting
    "RateLimiter",
    "rate_limit",
]
