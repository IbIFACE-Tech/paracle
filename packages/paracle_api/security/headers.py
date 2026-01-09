"""Security Headers Middleware for Paracle API.

Implements security headers following OWASP recommendations:
- Strict-Transport-Security (HSTS)
- Content-Security-Policy (CSP)
- X-Content-Type-Options
- X-Frame-Options
- X-XSS-Protection
- Referrer-Policy
- Permissions-Policy
"""

from __future__ import annotations

from collections.abc import Callable

from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request
from starlette.responses import Response

from paracle_api.security.config import SecurityConfig, get_security_config


class SecurityHeadersMiddleware(BaseHTTPMiddleware):
    """Middleware to add security headers to all responses.

    Implements OWASP security header recommendations for
    protection against common web vulnerabilities.
    """

    def __init__(
        self,
        app,
        config: SecurityConfig | None = None,
    ):
        """Initialize the middleware.

        Args:
            app: ASGI application
            config: Security configuration (uses default if not provided)
        """
        super().__init__(app)
        self.config = config or get_security_config()

    async def dispatch(
        self,
        request: Request,
        call_next: Callable,
    ) -> Response:
        """Process request and add security headers to response.

        Args:
            request: Incoming request
            call_next: Next middleware/handler

        Returns:
            Response with security headers
        """
        response = await call_next(request)

        # =======================================================================
        # X-Content-Type-Options
        # Prevents MIME type sniffing attacks
        # =======================================================================
        response.headers["X-Content-Type-Options"] = "nosniff"

        # =======================================================================
        # X-Frame-Options
        # Prevents clickjacking by disabling iframe embedding
        # =======================================================================
        response.headers["X-Frame-Options"] = "DENY"

        # =======================================================================
        # X-XSS-Protection
        # Legacy XSS protection (modern browsers use CSP instead)
        # =======================================================================
        response.headers["X-XSS-Protection"] = "1; mode=block"

        # =======================================================================
        # Referrer-Policy
        # Controls referrer information sent with requests
        # =======================================================================
        response.headers["Referrer-Policy"] = "strict-origin-when-cross-origin"

        # =======================================================================
        # Permissions-Policy (formerly Feature-Policy)
        # Restricts browser features
        # =======================================================================
        response.headers["Permissions-Policy"] = (
            "accelerometer=(), "
            "camera=(), "
            "geolocation=(), "
            "gyroscope=(), "
            "magnetometer=(), "
            "microphone=(), "
            "payment=(), "
            "usb=()"
        )

        # =======================================================================
        # Strict-Transport-Security (HSTS)
        # Forces HTTPS connections
        # =======================================================================
        if self.config.enable_hsts:
            response.headers["Strict-Transport-Security"] = (
                f"max-age={self.config.hsts_max_age}; includeSubDomains"
            )

        # =======================================================================
        # Content-Security-Policy (CSP)
        # Prevents XSS and data injection attacks
        # =======================================================================
        if self.config.enable_csp:
            response.headers["Content-Security-Policy"] = self.config.csp_policy

        # =======================================================================
        # Cache-Control for API responses
        # Prevents caching of sensitive data
        # =======================================================================
        if request.url.path.startswith("/api/"):
            response.headers["Cache-Control"] = "no-store, no-cache, must-revalidate"
            response.headers["Pragma"] = "no-cache"

        return response


def get_security_headers_middleware(config: SecurityConfig | None = None):
    """Factory function to create security headers middleware.

    Args:
        config: Security configuration

    Returns:
        SecurityHeadersMiddleware class configured with settings
    """

    def middleware_factory(app):
        return SecurityHeadersMiddleware(app, config=config)

    return middleware_factory
