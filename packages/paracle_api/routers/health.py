"""Health check API router.

Provides health, version, and performance statistics endpoints.
"""

from typing import Any

from fastapi import APIRouter
from paracle_profiling import get_multi_level_cache

from paracle_api.schemas.health import HealthResponse

router = APIRouter(tags=["health"])


@router.get("/health", response_model=HealthResponse, operation_id="healthCheck")
async def health_check() -> HealthResponse:
    """Health check endpoint.

    Returns service status and version.
    """
    return HealthResponse(
        status="ok",
        version="1.0.0",
        service="paracle",
    )


@router.get("/health/cache", tags=["performance"], operation_id="getCacheStats")
async def cache_stats() -> dict[str, Any]:
    """Get cache statistics for all layers.

    Returns multi-level cache statistics including:
    - Response cache stats (short TTL)
    - Query cache stats (medium TTL)
    - LLM cache stats (long TTL)
    - Overall hit rate and summary

    Phase 8 - Performance & Scale deliverable.
    """
    cache = get_multi_level_cache()
    return {
        "status": "ok",
        "cache_stats": cache.get_stats(),
    }


@router.delete("/health/cache", tags=["performance"], operation_id="clearCache")
async def clear_cache() -> dict[str, str]:
    """Clear all cache layers.

    Use with caution - clears all cached data.

    Returns:
        Confirmation message
    """
    cache = get_multi_level_cache()
    cache.clear()
    return {
        "status": "ok",
        "message": "All cache layers cleared",
    }
