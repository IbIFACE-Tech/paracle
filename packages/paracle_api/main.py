"""Paracle API - FastAPI Application.

Main entry point for the Paracle REST API.
Run with: uvicorn paracle_api.main:app --reload
"""

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from paracle_api.routers import health_router, parac_router

app = FastAPI(
    title="Paracle API",
    description="User-driven multi-agent framework API",
    version="0.0.1",
    docs_url="/docs",
    redoc_url="/redoc",
    openapi_url="/openapi.json",
)

# CORS middleware for development
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Configure appropriately for production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Register routers
app.include_router(health_router)
app.include_router(parac_router)


@app.get("/", tags=["root"])
async def root() -> dict[str, str]:
    """Root endpoint.

    Redirects to API documentation.
    """
    return {
        "message": "Welcome to Paracle API",
        "docs": "/docs",
        "version": "0.0.1",
    }
