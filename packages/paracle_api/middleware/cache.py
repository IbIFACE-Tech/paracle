"""Response caching middleware for API performance.

Phase 8 - Performance & Scale deliverable: Response Caching Middleware
Integrates with multi-level cache system for API response caching.

Target: 50% latency reduction on cacheable GET requests.
"""

import hashlib
import json
import logging
import time
from collections.abc import Callable

from paracle_profiling import CacheLayer, get_multi_level_cache
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request
from starlette.responses import JSONResponse, Response

logger = logging.getLogger(__name__)


class ResponseCacheMiddleware(BaseHTTPMiddleware):
    """Middleware for caching API responses.

    Features:
    - Caches GET responses by default
    - Configurable cache TTL per endpoint pattern
    - Cache-Control header support
    - Bypass cache via headers (Cache-Control: no-cache)
    - Cache statistics tracking
    - Selective caching by path patterns

    Example:
        app.add_middleware(
            ResponseCacheMiddleware,
            default_ttl=60,
            cache_paths=["/api/agents", "/api/specs"],
        )
    """

    def __init__(
        self,
        app,
        default_ttl: int = 60,
        cache_paths: list[str] | None = None,
        exclude_paths: list[str] | None = None,
        cache_methods: list[str] | None = None,
    ):
        """Initialize response cache middleware.

        Args:
            app: FastAPI application
            default_ttl: Default TTL in seconds for cached responses
            cache_paths: List of path prefixes to cache (None = all GET)
            exclude_paths: List of path prefixes to exclude from caching
            cache_methods: HTTP methods to cache (default: ["GET"])
        """
        super().__init__(app)
        self.default_ttl = default_ttl
        self.cache_paths = cache_paths or []
        self.exclude_paths = exclude_paths or [
            "/health",
            "/docs",
            "/redoc",
            "/openapi.json",
            "/auth",
        ]
        self.cache_methods = cache_methods or ["GET"]
        self._cache = get_multi_level_cache()

        # Statistics
        self._cache_hits = 0
        self._cache_misses = 0
        self._cache_bypasses = 0
        self._latency_savings_ms = 0.0

    def _should_cache(self, request: Request) -> bool:
        """Determine if request should be cached."""
        # Only cache specified methods
        if request.method not in self.cache_methods:
            return False

        path = request.url.path

        # Check exclusions first
        for exclude in self.exclude_paths:
            if path.startswith(exclude):
                return False

        # If specific paths configured, check if request matches
        if self.cache_paths:
            for cache_path in self.cache_paths:
                if path.startswith(cache_path):
                    return True
            return False

        # Default: cache all GET requests not excluded
        return True

    def _make_cache_key(self, request: Request) -> str:
        """Generate cache key from request."""
        # Include method, path, and query string
        key_parts = [
            request.method,
            request.url.path,
            str(sorted(request.query_params.items())),
        ]
        key_str = "|".join(key_parts)
        return f"response:{hashlib.md5(key_str.encode()).hexdigest()}"

    def _should_bypass_cache(self, request: Request) -> bool:
        """Check if request should bypass cache."""
        # Check Cache-Control header
        cache_control = request.headers.get("cache-control", "").lower()
        if "no-cache" in cache_control or "no-store" in cache_control:
            return True

        # Check custom bypass header
        if request.headers.get("x-bypass-cache", "").lower() == "true":
            return True

        return False

    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        """Process request with caching."""
        # Check if caching should be applied
        if not self._should_cache(request):
            return await call_next(request)

        # Check for cache bypass
        if self._should_bypass_cache(request):
            self._cache_bypasses += 1
            response = await call_next(request)
            response.headers["X-Cache-Status"] = "BYPASS"
            return response

        # Generate cache key
        cache_key = self._make_cache_key(request)

        # Try to get from cache
        start_time = time.perf_counter()
        cached_data = self._cache.get(CacheLayer.RESPONSE, cache_key)

        if cached_data is not None:
            # Cache hit
            self._cache_hits += 1
            elapsed = time.perf_counter() - start_time

            # Reconstruct response from cached data
            response = JSONResponse(
                content=cached_data["body"],
                status_code=cached_data["status_code"],
                headers=cached_data.get("headers", {}),
            )
            response.headers["X-Cache-Status"] = "HIT"
            response.headers["X-Cache-Key"] = cache_key[:16]
            response.headers["X-Cache-Time-Ms"] = f"{elapsed * 1000:.2f}"

            # Track latency savings (estimate based on original time)
            original_time = cached_data.get("original_time_ms", 0)
            if original_time > 0:
                self._latency_savings_ms += original_time - (elapsed * 1000)

            logger.debug(f"Cache HIT: {request.url.path} ({elapsed*1000:.2f}ms)")
            return response

        # Cache miss - call actual endpoint
        self._cache_misses += 1
        response = await call_next(request)
        elapsed = time.perf_counter() - start_time

        # Only cache successful JSON responses
        if response.status_code == 200 and "application/json" in response.headers.get(
            "content-type", ""
        ):
            # Read response body
            body = b""
            async for chunk in response.body_iterator:
                body += chunk

            try:
                body_json = json.loads(body)

                # Store in cache
                cache_data = {
                    "body": body_json,
                    "status_code": response.status_code,
                    "headers": dict(response.headers),
                    "original_time_ms": elapsed * 1000,
                    "cached_at": time.time(),
                }
                self._cache.set(
                    CacheLayer.RESPONSE,
                    cache_key,
                    cache_data,
                    ttl=self.default_ttl,
                )

                # Return new response with body
                new_response = JSONResponse(
                    content=body_json,
                    status_code=response.status_code,
                )
                new_response.headers["X-Cache-Status"] = "MISS"
                new_response.headers["X-Cache-Key"] = cache_key[:16]
                new_response.headers["X-Cache-Time-Ms"] = f"{elapsed * 1000:.2f}"

                logger.debug(f"Cache MISS: {request.url.path} ({elapsed*1000:.2f}ms)")
                return new_response

            except json.JSONDecodeError:
                # Not valid JSON, return original response
                pass

        # Add cache status header for non-cached response
        response.headers["X-Cache-Status"] = "SKIP"
        return response

    def get_stats(self) -> dict:
        """Get cache middleware statistics."""
        total_requests = self._cache_hits + self._cache_misses + self._cache_bypasses
        hit_rate = (
            (self._cache_hits / total_requests * 100) if total_requests > 0 else 0
        )

        # Get underlying cache stats
        cache_stats = self._cache.get_layer_stats(CacheLayer.RESPONSE)

        return {
            "middleware_stats": {
                "hits": self._cache_hits,
                "misses": self._cache_misses,
                "bypasses": self._cache_bypasses,
                "total_requests": total_requests,
                "hit_rate": f"{hit_rate:.1f}%",
                "latency_savings_ms": round(self._latency_savings_ms, 2),
            },
            "cache_layer_stats": cache_stats,
            "config": {
                "default_ttl": self.default_ttl,
                "cache_paths": self.cache_paths,
                "exclude_paths": self.exclude_paths,
                "cache_methods": self.cache_methods,
            },
        }

    def clear_stats(self) -> None:
        """Clear middleware statistics."""
        self._cache_hits = 0
        self._cache_misses = 0
        self._cache_bypasses = 0
        self._latency_savings_ms = 0.0
