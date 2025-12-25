"""Paracle API Routers."""

from paracle_api.routers.agents import router as agents_router
from paracle_api.routers.health import router as health_router
from paracle_api.routers.parac import router as parac_router

__all__ = ["agents_router", "health_router", "parac_router"]
