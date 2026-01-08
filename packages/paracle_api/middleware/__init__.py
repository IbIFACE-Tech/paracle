"""Paracle API middleware package.

Provides middleware components for the FastAPI application:
- ResponseCacheMiddleware: Multi-level response caching (Phase 8)
"""

from paracle_api.middleware.cache import ResponseCacheMiddleware

__all__ = [
    "ResponseCacheMiddleware",
]
