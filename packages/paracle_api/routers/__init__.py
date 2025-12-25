"""Paracle API Routers."""

from paracle_api.routers.health import router as health_router
from paracle_api.routers.parac import router as parac_router

__all__ = ["health_router", "parac_router"]
