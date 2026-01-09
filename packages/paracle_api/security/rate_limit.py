"""Rate Limiting for Paracle API.

Provides rate limiting to prevent abuse and DoS attacks.
Uses in-memory storage by default, can be extended to Redis for distributed deployments.
"""

from __future__ import annotations

import asyncio
import time
from collections import defaultdict
from collections.abc import Callable
from dataclasses import dataclass, field
from functools import wraps

from fastapi import HTTPException, Request, status

from paracle_api.security.config import SecurityConfig, get_security_config


@dataclass
class RateLimitInfo:
    """Information about rate limit status for a client."""

    requests: int = 0
    window_start: float = field(default_factory=time.time)
    blocked_until: float = 0


class RateLimiter:
    """In-memory rate limiter with sliding window.

    Tracks request counts per client IP and enforces rate limits.
    Thread-safe for async operations.

    Example:
        >>> limiter = RateLimiter(requests_per_window=100, window_seconds=60)
        >>> if limiter.is_allowed("192.168.1.1"):
        ...     # Process request
        ... else:
        ...     # Return 429 Too Many Requests
    """

    def __init__(
        self,
        requests_per_window: int = 100,
        window_seconds: int = 60,
        burst_limit: int = 20,
        block_duration_seconds: int = 300,
    ):
        """Initialize the rate limiter.

        Args:
            requests_per_window: Maximum requests allowed per window
            window_seconds: Time window in seconds
            burst_limit: Maximum burst requests allowed
            block_duration_seconds: How long to block after exceeding limits
        """
        self.requests_per_window = requests_per_window
        self.window_seconds = window_seconds
        self.burst_limit = burst_limit
        self.block_duration_seconds = block_duration_seconds

        self._clients: dict[str, RateLimitInfo] = defaultdict(RateLimitInfo)
        self._lock = asyncio.Lock()

    async def is_allowed(self, client_id: str) -> tuple[bool, dict[str, int]]:
        """Check if a request from client is allowed.

        Args:
            client_id: Unique client identifier (usually IP address)

        Returns:
            Tuple of (allowed: bool, headers: dict with rate limit info)
        """
        async with self._lock:
            now = time.time()
            info = self._clients[client_id]

            # Check if client is blocked
            if info.blocked_until > now:
                remaining_block = int(info.blocked_until - now)
                return False, {
                    "X-RateLimit-Limit": self.requests_per_window,
                    "X-RateLimit-Remaining": 0,
                    "X-RateLimit-Reset": int(info.blocked_until),
                    "Retry-After": remaining_block,
                }

            # Check if we need to reset the window
            if now - info.window_start >= self.window_seconds:
                info.requests = 0
                info.window_start = now

            # Check rate limit
            if info.requests >= self.requests_per_window:
                # Block the client
                info.blocked_until = now + self.block_duration_seconds
                return False, {
                    "X-RateLimit-Limit": self.requests_per_window,
                    "X-RateLimit-Remaining": 0,
                    "X-RateLimit-Reset": int(info.blocked_until),
                    "Retry-After": self.block_duration_seconds,
                }

            # Increment request count
            info.requests += 1
            remaining = max(0, self.requests_per_window - info.requests)
            reset_time = int(info.window_start + self.window_seconds)

            return True, {
                "X-RateLimit-Limit": self.requests_per_window,
                "X-RateLimit-Remaining": remaining,
                "X-RateLimit-Reset": reset_time,
            }

    async def reset(self, client_id: str) -> None:
        """Reset rate limit for a client.

        Args:
            client_id: Client identifier to reset
        """
        async with self._lock:
            if client_id in self._clients:
                del self._clients[client_id]

    async def cleanup_expired(self) -> int:
        """Remove expired client entries to free memory.

        Returns:
            Number of entries removed
        """
        async with self._lock:
            now = time.time()
            expired = [
                cid
                for cid, info in self._clients.items()
                if now - info.window_start > self.window_seconds * 2
                and info.blocked_until < now
            ]
            for cid in expired:
                del self._clients[cid]
            return len(expired)

    def get_client_status(self, client_id: str) -> dict:
        """Get current rate limit status for a client.

        Args:
            client_id: Client identifier

        Returns:
            Dictionary with rate limit status
        """
        info = self._clients.get(client_id)
        if not info:
            return {
                "requests": 0,
                "limit": self.requests_per_window,
                "window_seconds": self.window_seconds,
                "blocked": False,
            }

        now = time.time()
        return {
            "requests": info.requests,
            "limit": self.requests_per_window,
            "window_seconds": self.window_seconds,
            "blocked": info.blocked_until > now,
            "blocked_until": info.blocked_until if info.blocked_until > now else None,
        }


# Global rate limiter instance
_rate_limiter: RateLimiter | None = None


def get_rate_limiter(config: SecurityConfig | None = None) -> RateLimiter:
    """Get the global rate limiter instance.

    Args:
        config: Security configuration

    Returns:
        RateLimiter instance
    """
    global _rate_limiter
    if _rate_limiter is None:
        if config is None:
            config = get_security_config()
        _rate_limiter = RateLimiter(
            requests_per_window=config.rate_limit_requests,
            window_seconds=config.rate_limit_window_seconds,
            burst_limit=config.rate_limit_burst,
        )
    return _rate_limiter


def reset_rate_limiter() -> None:
    """Reset the global rate limiter (for testing)."""
    global _rate_limiter
    _rate_limiter = None


def get_client_ip(request: Request) -> str:
    """Extract client IP from request.

    Handles X-Forwarded-For header for proxied requests.

    Args:
        request: FastAPI request

    Returns:
        Client IP address
    """
    # Check for proxy headers
    forwarded = request.headers.get("X-Forwarded-For")
    if forwarded:
        # Take the first IP (original client)
        return forwarded.split(",")[0].strip()

    real_ip = request.headers.get("X-Real-IP")
    if real_ip:
        return real_ip.strip()

    # Fallback to direct client
    if request.client:
        return request.client.host

    return "unknown"


async def check_rate_limit(request: Request) -> None:
    """FastAPI dependency to check rate limit.

    Args:
        request: FastAPI request

    Raises:
        HTTPException: 429 if rate limit exceeded
    """
    config = get_security_config()

    if not config.rate_limit_enabled:
        return

    limiter = get_rate_limiter(config)
    client_ip = get_client_ip(request)

    allowed, headers = await limiter.is_allowed(client_ip)

    # Always add rate limit headers to response
    # (This requires response middleware, simplified here)

    if not allowed:
        raise HTTPException(
            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
            detail="Rate limit exceeded. Please try again later.",
            headers={str(k): str(v) for k, v in headers.items()},
        )


def rate_limit(
    requests: int | None = None,
    window: int | None = None,
):
    """Decorator for custom rate limiting on specific endpoints.

    Args:
        requests: Max requests per window (uses config default if None)
        window: Window in seconds (uses config default if None)

    Returns:
        Decorator function

    Example:
        @router.post("/expensive-operation")
        @rate_limit(requests=5, window=60)
        async def expensive_operation():
            ...
    """

    def decorator(func: Callable) -> Callable:
        # Create endpoint-specific limiter
        _endpoint_limiter: RateLimiter | None = None

        @wraps(func)
        async def wrapper(*args, **kwargs):
            nonlocal _endpoint_limiter

            # Get request from kwargs or args
            request = kwargs.get("request")
            if not request:
                for arg in args:
                    if isinstance(arg, Request):
                        request = arg
                        break

            if not request:
                # No request found, skip rate limiting
                return await func(*args, **kwargs)

            config = get_security_config()

            if not config.rate_limit_enabled:
                return await func(*args, **kwargs)

            # Initialize endpoint limiter
            if _endpoint_limiter is None:
                _endpoint_limiter = RateLimiter(
                    requests_per_window=requests or config.rate_limit_requests,
                    window_seconds=window or config.rate_limit_window_seconds,
                )

            client_ip = get_client_ip(request)
            allowed, headers = await _endpoint_limiter.is_allowed(client_ip)

            if not allowed:
                raise HTTPException(
                    status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                    detail="Rate limit exceeded for this endpoint.",
                    headers={str(k): str(v) for k, v in headers.items()},
                )

            return await func(*args, **kwargs)

        return wrapper

    return decorator
