"""Paracle API Routers."""

from paracle_api.routers.agent_crud import router as agent_crud_router
from paracle_api.routers.agents import router as agents_router
from paracle_api.routers.health import router as health_router
from paracle_api.routers.logs import router as logs_router
from paracle_api.routers.parac import router as parac_router
from paracle_api.routers.tool_crud import router as tool_crud_router
from paracle_api.routers.workflow_crud import router as workflow_crud_router

__all__ = [
    "agents_router",
    "health_router",
    "logs_router",
    "parac_router",
    "agent_crud_router",
    "workflow_crud_router",
    "tool_crud_router",
]
