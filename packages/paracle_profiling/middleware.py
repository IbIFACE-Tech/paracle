"""FastAPI middleware for request profiling."""

import logging
import time
from collections.abc import Callable

from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request
from starlette.responses import Response

logger = logging.getLogger(__name__)


class ProfilerMiddleware(BaseHTTPMiddleware):
    """Middleware to profile API requests.

    Tracks:
    - Request duration
    - Endpoint-specific timing
    - Slow request warnings
    - Response status codes

    Example:
        app.add_middleware(ProfilerMiddleware, slow_threshold=0.5)
    """

    def __init__(self, app, slow_threshold: float = 1.0):
        """Initialize profiler middleware.

        Args:
            app: FastAPI application
            slow_threshold: Threshold in seconds for slow request warnings
        """
        super().__init__(app)
        self.slow_threshold = slow_threshold
        self._request_counts = {}
        self._request_times = {}

    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        """Process request and collect metrics."""
        # Extract endpoint info
        method = request.method
        path = request.url.path
        endpoint = f"{method} {path}"

        # Start timing
        start_time = time.perf_counter()
        response = None
        status_code = 500  # Default for exceptions

        # Process request
        try:
            response = await call_next(request)
            status_code = response.status_code
        except Exception:
            logger.exception(f"Request failed: {endpoint}")
            raise
        finally:
            # Calculate duration
            end_time = time.perf_counter()
            duration = end_time - start_time

            # Update stats
            if endpoint not in self._request_counts:
                self._request_counts[endpoint] = 0
                self._request_times[endpoint] = []

            self._request_counts[endpoint] += 1
            self._request_times[endpoint].append(duration)

            # Keep only last 100 timings per endpoint
            if len(self._request_times[endpoint]) > 100:
                self._request_times[endpoint] = self._request_times[endpoint][-100:]

            # Log slow requests
            if duration > self.slow_threshold:
                logger.warning(
                    f"Slow request: {endpoint} took {duration:.3f}s "
                    f"(status: {status_code})"
                )

            # Add timing headers (only if we have a response)
            if response is not None:
                response.headers["X-Process-Time"] = f"{duration:.6f}"
                response.headers["X-Request-Count"] = str(
                    self._request_counts[endpoint]
                )

        return response

    def get_stats(self) -> dict:
        """Get profiling statistics for all endpoints."""
        stats = {}
        for endpoint, times in self._request_times.items():
            if not times:
                continue

            sorted_times = sorted(times)
            n = len(sorted_times)

            stats[endpoint] = {
                "count": self._request_counts[endpoint],
                "avg": sum(times) / n,
                "min": min(times),
                "max": max(times),
                "p50": sorted_times[n // 2],
                "p95": sorted_times[int(n * 0.95)] if n > 1 else sorted_times[0],
                "p99": sorted_times[int(n * 0.99)] if n > 1 else sorted_times[0],
            }

        return stats

    def clear_stats(self) -> None:
        """Clear profiling statistics."""
        self._request_counts.clear()
        self._request_times.clear()
