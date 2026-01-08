# paracle_api

> REST API server for the Paracle framework

## Purpose

The `paracle_api` module provides a production-ready REST API server built with FastAPI. It exposes all Paracle functionality through HTTP endpoints with comprehensive OpenAPI documentation, authentication, rate limiting, and WebSocket support for real-time updates.

**Key Features**:
- RESTful API with OpenAPI/Swagger
- WebSocket streaming for agent execution
- JWT authentication
- Rate limiting and security
- Cost tracking and monitoring
- Health checks and metrics

## Key Components

### 1. Main Application

**FastAPI Application**

```python
from paracle_api.main import app

# Run with uvicorn
# uvicorn paracle_api.main:app --reload
```

**Base Configuration**:
- **Title**: Paracle API
- **Version**: 0.0.1
- **Docs**: `/docs` (Swagger UI)
- **ReDoc**: `/redoc`
- **OpenAPI**: `/openapi.json`

### 2. Endpoints

#### Agent Endpoints

**List Agents**
```http
GET /api/v1/agents
Query Parameters:
  - parent: Filter by parent agent
  - status: Filter by status
  - limit: Max results (default: 100)
  - offset: Pagination offset
Response: 200 OK
{
  "agents": [
    {
      "id": "agent_01HQZYX...",
      "name": "coder",
      "provider": "openai",
      "model": "gpt-4",
      "status": "active",
      "created_at": "2026-01-07T10:00:00Z"
    }
  ],
  "total": 42,
  "limit": 100,
  "offset": 0
}
```

**Get Agent**
```http
GET /api/v1/agents/{agent_id}
Response: 200 OK
{
  "id": "agent_01HQZYX...",
  "name": "coder",
  "provider": "openai",
  "model": "gpt-4",
  "temperature": 0.7,
  "instructions": "You are a helpful coding assistant",
  "tools": ["filesystem_read", "filesystem_write"],
  "parent": null,
  "created_at": "2026-01-07T10:00:00Z",
  "updated_at": "2026-01-07T10:00:00Z"
}
```

**Create Agent**
```http
POST /api/v1/agents
Content-Type: application/json
{
  "name": "python-expert",
  "provider": "openai",
  "model": "gpt-4",
  "temperature": 0.5,
  "instructions": "You are a Python expert",
  "tools": ["python_ast_parser"],
  "parent": "coder"
}
Response: 201 Created
{
  "id": "agent_01HQZYX...",
  "name": "python-expert",
  ...
}
```

**Update Agent**
```http
PATCH /api/v1/agents/{agent_id}
Content-Type: application/json
{
  "temperature": 0.3,
  "instructions": "Updated instructions"
}
Response: 200 OK
```

**Delete Agent**
```http
DELETE /api/v1/agents/{agent_id}
Response: 204 No Content
```

**Execute Agent**
```http
POST /api/v1/agents/{agent_id}/execute
Content-Type: application/json
{
  "task": "Review this code for bugs",
  "mode": "safe",
  "inputs": {
    "file": "api.py",
    "focus": "security"
  },
  "cost_limit": 5.0,
  "timeout": 300
}
Response: 200 OK
{
  "execution_id": "exec_01HQZYX...",
  "status": "running",
  "created_at": "2026-01-07T10:30:00Z"
}
```

**Stream Agent Execution (WebSocket)**
```javascript
// Connect to WebSocket
const ws = new WebSocket('ws://localhost:8000/api/v1/agents/{agent_id}/stream');

// Send task
ws.send(JSON.stringify({
  "task": "Implement feature X",
  "mode": "safe"
}));

// Receive streaming updates
ws.onmessage = (event) => {
  const data = JSON.parse(event.data);
  console.log(data);
  // { "type": "token", "content": "I'll implement..." }
  // { "type": "tool_call", "tool": "filesystem_write", "args": {...} }
  // { "type": "complete", "result": {...}, "cost": 0.05 }
};
```

#### Workflow Endpoints

**List Workflows**
```http
GET /api/v1/workflows
Response: 200 OK
{
  "workflows": [
    {
      "id": "workflow_01HQZYX...",
      "name": "code-review",
      "status": "active",
      "steps": 4
    }
  ]
}
```

**Execute Workflow**
```http
POST /api/v1/workflows/{workflow_id}/execute
Content-Type: application/json
{
  "inputs": {
    "file": "api.py",
    "priority": "high"
  }
}
Response: 200 OK
{
  "execution_id": "wf_exec_01HQZYX...",
  "status": "running",
  "steps_completed": 0,
  "steps_total": 4
}
```

**Get Workflow Execution Status**
```http
GET /api/v1/workflows/executions/{execution_id}
Response: 200 OK
{
  "id": "wf_exec_01HQZYX...",
  "workflow_id": "workflow_01HQZYX...",
  "status": "completed",
  "steps_completed": 4,
  "steps_total": 4,
  "started_at": "2026-01-07T10:30:00Z",
  "completed_at": "2026-01-07T10:35:00Z",
  "results": {
    "analyze": { ... },
    "review": { ... },
    "test": { ... },
    "report": { ... }
  },
  "total_cost": 0.25
}
```

#### Tool Endpoints

**List Tools**
```http
GET /api/v1/tools
Query Parameters:
  - category: Filter by category
Response: 200 OK
{
  "tools": [
    {
      "name": "filesystem_read",
      "description": "Read file contents",
      "category": "filesystem",
      "parameters": [...]
    }
  ]
}
```

**Execute Tool**
```http
POST /api/v1/tools/{tool_name}/execute
Content-Type: application/json
{
  "args": {
    "path": "test.txt",
    "encoding": "utf-8"
  }
}
Response: 200 OK
{
  "result": {
    "content": "File contents...",
    "size": 1024
  }
}
```

#### Cost Endpoints

**Get Costs**
```http
GET /api/v1/costs
Query Parameters:
  - since: ISO date filter
  - agent_id: Filter by agent
  - limit: Max results
Response: 200 OK
{
  "costs": [
    {
      "id": "cost_01HQZYX...",
      "agent_id": "agent_01HQZYX...",
      "execution_id": "exec_01HQZYX...",
      "provider": "openai",
      "model": "gpt-4",
      "prompt_tokens": 100,
      "completion_tokens": 50,
      "total_tokens": 150,
      "cost_usd": 0.0045,
      "timestamp": "2026-01-07T10:30:00Z"
    }
  ],
  "total_cost": 12.50
}
```

**Get Cost Summary**
```http
GET /api/v1/costs/summary
Query Parameters:
  - period: day, week, month
Response: 200 OK
{
  "period": "week",
  "total_cost": 45.20,
  "by_agent": {
    "coder": 25.50,
    "reviewer": 12.30,
    "tester": 7.40
  },
  "by_provider": {
    "openai": 30.00,
    "anthropic": 15.20
  },
  "by_model": {
    "gpt-4": 30.00,
    "claude-3-opus": 15.20
  }
}
```

#### Health & Status Endpoints

**Health Check**
```http
GET /health
Response: 200 OK
{
  "status": "healthy",
  "version": "0.0.1",
  "timestamp": "2026-01-07T10:30:00Z",
  "services": {
    "database": "healthy",
    "redis": "healthy",
    "workers": "healthy"
  }
}
```

**Metrics**
```http
GET /metrics
Response: 200 OK (Prometheus format)
# HELP paracle_requests_total Total HTTP requests
# TYPE paracle_requests_total counter
paracle_requests_total{method="GET",endpoint="/api/v1/agents"} 1234
...
```

### 3. Authentication

**JWT Authentication**

```http
POST /api/v1/auth/login
Content-Type: application/json
{
  "username": "user@example.com",
  "password": "secure_password"
}
Response: 200 OK
{
  "access_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
  "refresh_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
  "token_type": "bearer",
  "expires_in": 3600
}
```

**Using Token**
```http
GET /api/v1/agents
Authorization: Bearer eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...
```

**Refresh Token**
```http
POST /api/v1/auth/refresh
Content-Type: application/json
{
  "refresh_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9..."
}
Response: 200 OK
{
  "access_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
  "token_type": "bearer",
  "expires_in": 3600
}
```

### 4. Rate Limiting

**Default Limits**:
- **Anonymous**: 100 requests/hour
- **Authenticated**: 1000 requests/hour
- **Premium**: 10000 requests/hour

**Rate Limit Headers**:
```http
X-RateLimit-Limit: 1000
X-RateLimit-Remaining: 995
X-RateLimit-Reset: 1704628800
```

**Rate Limit Exceeded**:
```http
Response: 429 Too Many Requests
{
  "error": "rate_limit_exceeded",
  "message": "Rate limit exceeded. Try again in 3600 seconds.",
  "retry_after": 3600
}
```

### 5. Error Responses

**Standard Error Format**:
```json
{
  "error": "error_code",
  "message": "Human-readable error message",
  "details": {
    "field": "Additional context"
  },
  "request_id": "req_01HQZYX..."
}
```

**HTTP Status Codes**:
- `200 OK` - Success
- `201 Created` - Resource created
- `204 No Content` - Success with no body
- `400 Bad Request` - Validation error
- `401 Unauthorized` - Authentication required
- `403 Forbidden` - Insufficient permissions
- `404 Not Found` - Resource not found
- `409 Conflict` - Resource conflict
- `422 Unprocessable Entity` - Invalid data
- `429 Too Many Requests` - Rate limit exceeded
- `500 Internal Server Error` - Server error
- `503 Service Unavailable` - Service down

## Module Structure

```
paracle_api/
├── __init__.py              # Package exports
├── main.py                  # FastAPI application
├── routers/                 # API routers
│   ├── __init__.py
│   ├── agents.py           # Agent endpoints
│   ├── workflows.py        # Workflow endpoints
│   ├── tools.py            # Tool endpoints
│   ├── costs.py            # Cost endpoints
│   ├── auth.py             # Authentication
│   └── health.py           # Health checks
├── models/                  # Request/response models
│   ├── __init__.py
│   ├── requests.py         # Request schemas
│   ├── responses.py        # Response schemas
│   └── errors.py           # Error schemas
├── middleware/              # Middleware
│   ├── __init__.py
│   ├── auth.py             # Authentication
│   ├── rate_limit.py       # Rate limiting
│   ├── cors.py             # CORS
│   └── logging.py          # Request logging
├── dependencies/            # FastAPI dependencies
│   ├── __init__.py
│   ├── auth.py             # Auth dependencies
│   └── database.py         # DB session
└── websockets/              # WebSocket handlers
    ├── __init__.py
    └── agents.py           # Agent streaming
```

## Usage Examples

### Starting the Server

```bash
# Development
uvicorn paracle_api.main:app --reload --port 8000

# Production
uvicorn paracle_api.main:app --host 0.0.0.0 --port 8000 --workers 4

# With Gunicorn
gunicorn paracle_api.main:app -w 4 -k uvicorn.workers.UvicornWorker
```

### Python Client

```python
import httpx

# Create client
client = httpx.AsyncClient(base_url="http://localhost:8000")

# Login
response = await client.post("/api/v1/auth/login", json={
    "username": "user@example.com",
    "password": "password"
})
token = response.json()["access_token"]

# Set auth header
client.headers["Authorization"] = f"Bearer {token}"

# List agents
response = await client.get("/api/v1/agents")
agents = response.json()["agents"]

# Execute agent
response = await client.post("/api/v1/agents/coder/execute", json={
    "task": "Implement feature X",
    "mode": "safe"
})
execution_id = response.json()["execution_id"]

# Check status
response = await client.get(f"/api/v1/agents/executions/{execution_id}")
status = response.json()["status"]
```

### JavaScript Client

```javascript
// Create client
const API_URL = 'http://localhost:8000/api/v1';

// Login
const loginResponse = await fetch(`${API_URL}/auth/login`, {
  method: 'POST',
  headers: { 'Content-Type': 'application/json' },
  body: JSON.stringify({
    username: 'user@example.com',
    password: 'password'
  })
});
const { access_token } = await loginResponse.json();

// List agents
const agentsResponse = await fetch(`${API_URL}/agents`, {
  headers: { 'Authorization': `Bearer ${access_token}` }
});
const { agents } = await agentsResponse.json();

// Execute agent
const executeResponse = await fetch(`${API_URL}/agents/coder/execute`, {
  method: 'POST',
  headers: {
    'Authorization': `Bearer ${access_token}`,
    'Content-Type': 'application/json'
  },
  body: JSON.stringify({
    task: 'Implement feature X',
    mode: 'safe'
  })
});
const { execution_id } = await executeResponse.json();
```

## Dependencies

**Required Packages**:
```toml
[project.dependencies]
fastapi = "^0.109"          # Web framework
uvicorn = {extras = ["standard"], version = "^0.27"}  # ASGI server
pydantic = "^2.5"           # Data validation
sqlalchemy = "^2.0"         # Database ORM
python-jose = "^3.3"        # JWT handling
passlib = "^1.7"            # Password hashing
python-multipart = "^0.0.6" # File uploads
```

**Optional Packages**:
```toml
[project.optional-dependencies]
api = [
    "redis ^5.0",           # Rate limiting
    "prometheus-client ^0.19",  # Metrics
    "sentry-sdk ^1.39",     # Error tracking
]
```

**Internal Dependencies**:
- `paracle_core` - Core utilities
- `paracle_domain` - Domain models
- `paracle_orchestration` - Workflow execution
- `paracle_store` - Data persistence
- `paracle_events` - Event bus

## Environment Variables

```bash
# Server
PARACLE_API_HOST=0.0.0.0
PARACLE_API_PORT=8000
PARACLE_API_WORKERS=4

# Database
PARACLE_DATABASE_URL=postgresql://user:pass@localhost/paracle

# Redis
PARACLE_REDIS_URL=redis://localhost:6379/0

# Authentication
PARACLE_SECRET_KEY=your-secret-key-here
PARACLE_JWT_ALGORITHM=HS256
PARACLE_JWT_EXPIRE_MINUTES=60

# Rate Limiting
PARACLE_RATE_LIMIT_ANONYMOUS=100
PARACLE_RATE_LIMIT_AUTHENTICATED=1000

# CORS
PARACLE_CORS_ORIGINS=http://localhost:3000,https://app.example.com

# Logging
PARACLE_LOG_LEVEL=INFO
```

## Testing

### Unit Tests

```python
from fastapi.testclient import TestClient
from paracle_api.main import app

client = TestClient(app)

def test_health():
    response = client.get("/health")
    assert response.status_code == 200
    assert response.json()["status"] == "healthy"

def test_list_agents():
    response = client.get("/api/v1/agents")
    assert response.status_code == 200
    assert "agents" in response.json()
```

### Integration Tests

```python
@pytest.mark.asyncio
async def test_agent_execution():
    async with httpx.AsyncClient(base_url="http://localhost:8000") as client:
        # Create agent
        response = await client.post("/api/v1/agents", json={
            "name": "test-agent",
            "provider": "openai",
            "model": "gpt-4"
        })
        agent_id = response.json()["id"]

        # Execute agent
        response = await client.post(f"/api/v1/agents/{agent_id}/execute", json={
            "task": "Test task",
            "mode": "sandbox"
        })
        assert response.status_code == 200
        execution_id = response.json()["execution_id"]

        # Wait for completion
        while True:
            response = await client.get(f"/api/v1/agents/executions/{execution_id}")
            status = response.json()["status"]
            if status in ["completed", "failed"]:
                break
            await asyncio.sleep(1)

        assert status == "completed"
```

## See Also

- [API Reference](../api-reference.md) - Complete API documentation
- [paracle_cli](cli.md) - Command-line interface
- [Authentication Guide](../guides/authentication.md) - Auth setup
- [Deployment Guide](../deployment/production.md) - Production deployment

---

**Module Type**: Interface (REST API)
**Dependencies**: paracle_core, paracle_domain, paracle_orchestration, paracle_store
**Port**: 8000 (default)
**Status**: Stable
**Version**: 0.0.1

