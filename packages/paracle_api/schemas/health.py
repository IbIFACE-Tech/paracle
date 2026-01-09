"""Health check schemas."""

from pydantic import BaseModel, Field


class HealthResponse(BaseModel):
    """Health check response."""

    status: str = Field(
        default="ok", description="Service status", examples=["ok", "degraded", "error"]
    )
    version: str = Field(description="API version", examples=["0.0.1", "1.0.0"])
    service: str = Field(
        default="paracle", description="Service name", examples=["paracle"]
    )
