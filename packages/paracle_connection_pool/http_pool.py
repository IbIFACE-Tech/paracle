"""HTTP connection pooling for LLM providers."""

import asyncio
from dataclasses import dataclass
from typing import Any

try:
    import httpx

    HTTPX_AVAILABLE = True
except ImportError:
    HTTPX_AVAILABLE = False


@dataclass
class HTTPPoolConfig:
    """HTTP connection pool configuration."""

    max_connections: int = 100  # Max total connections
    max_keepalive_connections: int = 20  # Max idle connections
    keepalive_expiry: float = 30.0  # Seconds to keep idle connections
    timeout: float = 30.0  # Request timeout in seconds
    max_retries: int = 3  # Max retry attempts
    verify_ssl: bool = True  # Verify SSL certificates

    @classmethod
    def from_env(cls) -> "HTTPPoolConfig":
        """Create config from environment variables."""
        import os

        return cls(
            max_connections=int(os.getenv("PARACLE_HTTP_MAX_CONNECTIONS", "100")),
            max_keepalive_connections=int(
                os.getenv("PARACLE_HTTP_MAX_KEEPALIVE", "20")
            ),
            keepalive_expiry=float(os.getenv("PARACLE_HTTP_KEEPALIVE_EXPIRY", "30.0")),
            timeout=float(os.getenv("PARACLE_HTTP_TIMEOUT", "30.0")),
            max_retries=int(os.getenv("PARACLE_HTTP_MAX_RETRIES", "3")),
            verify_ssl=os.getenv("PARACLE_HTTP_VERIFY_SSL", "true").lower() == "true",
        )


class HTTPPool:
    """HTTP connection pool using httpx."""

    def __init__(self, config: HTTPPoolConfig | None = None):
        """Initialize HTTP connection pool.

        Args:
            config: Pool configuration (None = use defaults)
        """
        if not HTTPX_AVAILABLE:
            raise ImportError(
                "httpx is required for HTTP pooling. " "Install with: pip install httpx"
            )

        self.config = config or HTTPPoolConfig()
        self._client: httpx.AsyncClient | None = None
        self._lock = asyncio.Lock()
        self._request_count = 0
        self._error_count = 0

    async def _ensure_client(self) -> httpx.AsyncClient:
        """Ensure client is initialized."""
        if self._client is None:
            async with self._lock:
                if self._client is None:
                    limits = httpx.Limits(
                        max_connections=self.config.max_connections,
                        max_keepalive_connections=self.config.max_keepalive_connections,
                        keepalive_expiry=self.config.keepalive_expiry,
                    )

                    timeout = httpx.Timeout(self.config.timeout)

                    self._client = httpx.AsyncClient(
                        limits=limits,
                        timeout=timeout,
                        verify=self.config.verify_ssl,
                    )

        return self._client

    async def request(
        self,
        method: str,
        url: str,
        **kwargs: Any,
    ) -> httpx.Response:
        """Make HTTP request using connection pool.

        Args:
            method: HTTP method (GET, POST, etc.)
            url: Request URL
            **kwargs: Additional httpx request arguments

        Returns:
            HTTP response

        Raises:
            httpx.HTTPError: On request failure
        """
        client = await self._ensure_client()

        retries = 0
        last_error = None

        while retries <= self.config.max_retries:
            try:
                self._request_count += 1
                response = await client.request(method, url, **kwargs)
                response.raise_for_status()
                return response

            except (httpx.HTTPError, httpx.TimeoutException) as e:
                last_error = e
                retries += 1
                self._error_count += 1

                if retries <= self.config.max_retries:
                    # Exponential backoff
                    await asyncio.sleep(2**retries)
                    continue

                raise

        raise last_error  # type: ignore

    async def get(self, url: str, **kwargs: Any) -> httpx.Response:
        """Make GET request.

        Args:
            url: Request URL
            **kwargs: Additional request arguments

        Returns:
            HTTP response
        """
        return await self.request("GET", url, **kwargs)

    async def post(self, url: str, **kwargs: Any) -> httpx.Response:
        """Make POST request.

        Args:
            url: Request URL
            **kwargs: Additional request arguments

        Returns:
            HTTP response
        """
        return await self.request("POST", url, **kwargs)

    async def close(self) -> None:
        """Close connection pool."""
        if self._client is not None:
            await self._client.aclose()
            self._client = None

    async def __aenter__(self) -> "HTTPPool":
        """Context manager entry."""
        await self._ensure_client()
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb) -> None:
        """Context manager exit."""
        await self.close()

    def stats(self) -> dict[str, Any]:
        """Get pool statistics.

        Returns:
            Dictionary with pool stats
        """
        return {
            "requests": self._request_count,
            "errors": self._error_count,
            "error_rate": (
                self._error_count / self._request_count
                if self._request_count > 0
                else 0.0
            ),
            "config": {
                "max_connections": self.config.max_connections,
                "max_keepalive": self.config.max_keepalive_connections,
                "keepalive_expiry": self.config.keepalive_expiry,
                "timeout": self.config.timeout,
            },
        }


# Global HTTP pool instance
_http_pool: HTTPPool | None = None


async def get_http_pool(config: HTTPPoolConfig | None = None) -> HTTPPool:
    """Get global HTTP pool instance.

    Args:
        config: Pool configuration (only used on first call)

    Returns:
        Global HTTPPool instance
    """
    global _http_pool
    if _http_pool is None:
        _http_pool = HTTPPool(config or HTTPPoolConfig.from_env())
    return _http_pool
