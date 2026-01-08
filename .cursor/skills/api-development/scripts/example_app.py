#!/usr/bin/env python3
"""Example FastAPI application demonstrating best practices.

This example shows:
- Pydantic models for validation
- Dependency injection
- Error handling
- API documentation
- Middleware
"""


from fastapi import Depends, FastAPI, HTTPException, status
from pydantic import BaseModel, Field

app = FastAPI(
    title="Paracle API Example",
    description="Example API following best practices",
    version="1.0.0",
)

# Models


class AgentCreate(BaseModel):
    """Request model for creating an agent."""
    name: str = Field(..., min_length=1, max_length=100)
    model: str = Field(default="gpt-4")
    temperature: float = Field(default=0.7, ge=0.0, le=2.0)


class AgentResponse(BaseModel):
    """Response model for agent."""
    id: str
    name: str
    model: str
    temperature: float

# Dependency injection example


async def get_current_user():
    """Dependency for authentication."""
    # In production, validate JWT token here
    return {"id": "user123", "name": "Test User"}

# Endpoints


@app.post(
    "/agents",
    response_model=AgentResponse,
    status_code=status.HTTP_201_CREATED,
)
async def create_agent(
    agent: AgentCreate,
    user=Depends(get_current_user),
):
    """Create a new agent.

    Args:
        agent: Agent creation data
        user: Current authenticated user

    Returns:
        Created agent with ID

    Raises:
        HTTPException: If agent name already exists
    """
    # Check if agent exists
    if agent.name == "existing-agent":
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Agent with this name already exists",
        )

    # Create agent (simplified)
    return AgentResponse(
        id="agent-123",
        name=agent.name,
        model=agent.model,
        temperature=agent.temperature,
    )


@app.get("/agents/{agent_id}", response_model=AgentResponse)
async def get_agent(
    agent_id: str,
    user=Depends(get_current_user),
):
    """Get agent by ID."""
    if agent_id != "agent-123":
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Agent not found",
        )

    return AgentResponse(
        id=agent_id,
        name="example-agent",
        model="gpt-4",
        temperature=0.7,
    )

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
