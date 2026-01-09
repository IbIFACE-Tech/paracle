---
name: api-development
description: Design and implement REST APIs using FastAPI. Use when creating endpoints, request/response schemas, middleware, error handling, or API documentation.
license: Apache-2.0
compatibility: FastAPI, Pydantic v2, Python 3.10+
metadata:
  author: paracle-core-team
  version: "1.0.0"
  category: creation
  level: advanced
  display_name: "API Development with FastAPI"
  tags:
    - api
    - fastapi
    - rest
    - http
    - openapi
  capabilities:
    - endpoint_creation
    - schema_design
    - middleware_implementation
    - error_handling
    - api_documentation
  requirements:
    - skill_name: code-generation
      min_level: advanced
    - skill_name: paracle-development
      min_level: intermediate
allowed-tools: Read Write Bash(python:*) Bash(pytest:*)
---

# API Development Skill

## When to use this skill

Use this skill when:

- Creating new REST API endpoints
- Designing request/response schemas with Pydantic
- Implementing middleware or dependencies
- Adding error handling and validation
- Documenting APIs with OpenAPI/Swagger
- Testing API endpoints
- Adding authentication/authorization

## Paracle API Architecture

### Structure

```
packages/paracle_api/
├── __init__.py
├── main.py                  # FastAPI application
├── routers/                 # Endpoint routers
│   ├── agents.py
│   ├── workflows.py
│   └── tools.py
├── schemas/                 # Pydantic models
│   ├── agent.py
│   ├── workflow.py
│   └── common.py
├── dependencies.py          # Shared dependencies
├── middleware.py            # Custom middleware
└── errors.py               # Error handlers
```

## API Development Patterns

### Pattern 1: Creating a New Endpoint

```python
# packages/paracle_api/routers/agents.py
from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel, Field

router = APIRouter(prefix="/api/v1/agents", tags=["agents"])

# Request schema
class CreateAgentRequest(BaseModel):
    """Request to create a new agent."""
    name: str = Field(..., min_length=1, max_length=100, description="Agent name")
    model: str = Field(default="gpt-4", description="LLM model to use")
    temperature: float = Field(default=0.7, ge=0.0, le=2.0)
    system_prompt: str | None = Field(default=None, description="Custom system prompt")

# Response schema
class AgentResponse(BaseModel):
    """Agent response."""
    id: str = Field(..., description="Unique agent ID")
    name: str
    model: str
    temperature: float
    created_at: str

    class Config:
        from_attributes = True  # For SQLAlchemy models

# Endpoint
@router.post(
    "/",
    response_model=AgentResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Create a new agent",
    description="Create a new agent with the specified configuration",
)
async def create_agent(
    request: CreateAgentRequest,
    repo: AgentRepository = Depends(get_agent_repository),
) -> AgentResponse:
    """
    Create a new agent.

    Args:
        request: Agent creation request
        repo: Agent repository (injected)

    Returns:
        Created agent

    Raises:
        HTTPException: If agent creation fails
    """
    try:
        agent = await repo.create(
            name=request.name,
            model=request.model,
            temperature=request.temperature,
            system_prompt=request.system_prompt,
        )
        return AgentResponse.from_orm(agent)
    except ValidationError as e:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=str(e),
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to create agent",
        )
```

### Pattern 2: Dependency Injection

```python
# packages/paracle_api/dependencies.py
from typing import Annotated
from fastapi import Depends, Header, HTTPException
from paracle_store import AgentRepository, get_session

async def get_agent_repository() -> AgentRepository:
    """Get agent repository instance."""
    session = get_session()
    return AgentRepository(session)

async def verify_api_key(
    x_api_key: Annotated[str, Header()] = None,
) -> str:
    """Verify API key from header."""
    if not x_api_key or x_api_key != settings.API_KEY:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid API key",
        )
    return x_api_key

# Usage in endpoint
@router.get("/agents/{agent_id}")
async def get_agent(
    agent_id: str,
    repo: AgentRepository = Depends(get_agent_repository),
    api_key: str = Depends(verify_api_key),
):
    ...
```

### Pattern 3: Error Handling

```python
# packages/paracle_api/errors.py
from fastapi import Request, status
from fastapi.responses import JSONResponse
from paracle_domain import AgentNotFoundError, ValidationError

async def agent_not_found_handler(
    request: Request,
    exc: AgentNotFoundError,
) -> JSONResponse:
    """Handle agent not found errors."""
    return JSONResponse(
        status_code=status.HTTP_404_NOT_FOUND,
        content={
            "error": "agent_not_found",
            "message": str(exc),
            "agent_id": exc.agent_id,
        },
    )

# Register in main.py
app.add_exception_handler(AgentNotFoundError, agent_not_found_handler)
```

### Pattern 4: Middleware

```python
# packages/paracle_api/middleware.py
from fastapi import Request
from time import time
import logging

logger = logging.getLogger(__name__)

async def logging_middleware(request: Request, call_next):
    """Log all requests with timing."""
    start_time = time()

    # Log request
    logger.info(
        f"Request: {request.method} {request.url.path}",
        extra={
            "method": request.method,
            "path": request.url.path,
            "client": request.client.host if request.client else None,
        },
    )

    # Process request
    response = await call_next(request)

    # Log response
    duration = time() - start_time
    logger.info(
        f"Response: {response.status_code} ({duration:.3f}s)",
        extra={
            "status_code": response.status_code,
            "duration_ms": int(duration * 1000),
        },
    )

    response.headers["X-Process-Time"] = str(duration)
    return response

# Register in main.py
app.middleware("http")(logging_middleware)
```

### Pattern 5: API Testing

```python
# tests/integration/test_api_agents.py
import pytest
from fastapi.testclient import TestClient
from paracle_api.main import app

client = TestClient(app)

def test_create_agent():
    """Test creating an agent via API."""
    response = client.post(
        "/api/v1/agents/",
        json={
            "name": "test-agent",
            "model": "gpt-4",
            "temperature": 0.7,
        },
    )

    assert response.status_code == 201
    data = response.json()
    assert data["name"] == "test-agent"
    assert "id" in data
    assert "created_at" in data

def test_create_agent_validation_error():
    """Test validation error handling."""
    response = client.post(
        "/api/v1/agents/",
        json={
            "name": "",  # Invalid: empty name
            "temperature": 3.0,  # Invalid: too high
        },
    )

    assert response.status_code == 422
    assert "detail" in response.json()

@pytest.mark.asyncio
async def test_get_agent_not_found():
    """Test 404 handling."""
    response = client.get("/api/v1/agents/nonexistent")

    assert response.status_code == 404
    data = response.json()
    assert data["error"] == "agent_not_found"
```

## API Design Standards

### 1. URL Structure

```
# Resources (plural nouns)
GET    /api/v1/agents              # List all agents
POST   /api/v1/agents              # Create agent
GET    /api/v1/agents/{id}         # Get specific agent
PUT    /api/v1/agents/{id}         # Update agent
DELETE /api/v1/agents/{id}         # Delete agent

# Sub-resources
GET    /api/v1/agents/{id}/skills  # List agent's skills
POST   /api/v1/agents/{id}/run     # Execute agent action

# Query parameters for filtering/pagination
GET    /api/v1/agents?model=gpt-4&limit=10&offset=0
```

### 2. Status Codes

```python
# Success
200 OK                  # GET, PUT, PATCH success
201 Created             # POST success
204 No Content          # DELETE success

# Client Errors
400 Bad Request         # Invalid request format
401 Unauthorized        # Missing/invalid authentication
403 Forbidden           # Valid auth but no permission
404 Not Found           # Resource doesn't exist
422 Unprocessable Entity # Validation error

# Server Errors
500 Internal Server Error # Unexpected server error
503 Service Unavailable   # Temporary service issue
```

### 3. Response Format

```json
// Success response
{
  "id": "agent-123",
  "name": "my-agent",
  "model": "gpt-4",
  "created_at": "2026-01-04T10:30:00Z"
}

// Error response
{
  "error": "validation_error",
  "message": "Temperature must be between 0.0 and 2.0",
  "field": "temperature",
  "value": 3.0
}

// List response with pagination
{
  "items": [...],
  "total": 42,
  "limit": 10,
  "offset": 0,
  "next": "/api/v1/agents?limit=10&offset=10"
}
```

### 4. OpenAPI Documentation

```python
# main.py
app = FastAPI(
    title="Paracle API",
    description="Multi-agent orchestration framework API",
    version="0.1.0",
    docs_url="/docs",
    redoc_url="/redoc",
    openapi_tags=[
        {
            "name": "agents",
            "description": "Agent management endpoints",
        },
        {
            "name": "workflows",
            "description": "Workflow orchestration endpoints",
        },
    ],
)
```

## Testing APIs

### Unit Tests

```python
# Test schemas
def test_create_agent_request_validation():
    """Test request schema validation."""
    # Valid
    request = CreateAgentRequest(name="test", model="gpt-4")
    assert request.name == "test"

    # Invalid temperature
    with pytest.raises(ValidationError):
        CreateAgentRequest(name="test", temperature=5.0)
```

### Integration Tests

```python
# Test with test database
@pytest.fixture
def test_db():
    """Provide test database."""
    engine = create_engine("sqlite:///:memory:")
    Base.metadata.create_all(engine)
    yield engine
    Base.metadata.drop_all(engine)

def test_full_agent_lifecycle(test_db):
    """Test create -> read -> update -> delete."""
    # Create
    response = client.post("/api/v1/agents/", json={"name": "test"})
    agent_id = response.json()["id"]

    # Read
    response = client.get(f"/api/v1/agents/{agent_id}")
    assert response.status_code == 200

    # Update
    response = client.put(
        f"/api/v1/agents/{agent_id}",
        json={"temperature": 0.8},
    )
    assert response.json()["temperature"] == 0.8

    # Delete
    response = client.delete(f"/api/v1/agents/{agent_id}")
    assert response.status_code == 204
```

## Performance Considerations

### 1. Async All The Way

```python
# Good: Fully async
@router.get("/agents/{id}")
async def get_agent(
    id: str,
    repo: AgentRepository = Depends(get_async_repository),
):
    agent = await repo.get_by_id(id)
    return agent

# Bad: Blocking call in async function
async def get_agent(id: str):
    agent = repo.get_by_id_sync(id)  # Blocks event loop!
    return agent
```

### 2. Database Connection Pooling

```python
# Use async SQLAlchemy with connection pooling
from sqlalchemy.ext.asyncio import create_async_engine

engine = create_async_engine(
    "sqlite+aiosqlite:///paracle.db",
    pool_size=5,
    max_overflow=10,
)
```

### 3. Response Caching

```python
from fastapi_cache import FastAPICache
from fastapi_cache.decorator import cache

@router.get("/agents")
@cache(expire=60)  # Cache for 60 seconds
async def list_agents():
    return await repo.list_all()
```

## Security Best Practices

1. **Input Validation**: Always validate with Pydantic
2. **SQL Injection**: Use parameterized queries (SQLAlchemy)
3. **Authentication**: Implement API key or JWT
4. **Rate Limiting**: Use middleware to prevent abuse
5. **CORS**: Configure allowed origins
6. **HTTPS**: Always use in production

## Common Pitfalls

❌ **Don't:**

- Return raw database models (use Pydantic schemas)

- Block the event loop with sync code
- Return 500 for validation errors (use 422)

- Expose internal error details in production
- Skip input validation

✅ **Do:**

- Use proper HTTP status codes
- Implement comprehensive error handling
- Add request/response logging
- Write integration tests
- Document with OpenAPI tags

## Resources

- [FastAPI Documentation](https://fastapi.tiangolo.com/)
- [Pydantic V2 Documentation](https://docs.pydantic.dev/)
- [REST API Best Practices](https://restfulapi.net/)
- Paracle API: `packages/paracle_api/`
