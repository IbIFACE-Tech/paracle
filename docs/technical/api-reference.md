# Paracle API Reference

Complete REST API documentation for Paracle v0.0.1.

## Overview

Paracle provides a RESTful API built with FastAPI. The API follows an API-first architecture where the CLI uses these endpoints.

**Base URL:** `http://localhost:8000` (default)

**Start the API server:**
```bash
paracle serve
# or
paracle serve --port 8080 --host 0.0.0.0
```

## Authentication

### JWT Authentication (Production)

```bash
# Get token
curl -X POST http://localhost:8000/auth/token \
  -H "Content-Type: application/x-www-form-urlencoded" \
  -d "username=user&password=pass"

# Use token
curl -X GET http://localhost:8000/agents \
  -H "Authorization: Bearer <token>"
```

### Development Mode

Authentication can be disabled for development:
```bash
PARACLE_AUTH_ENABLED=false paracle serve
```

## Endpoints

### Health

#### GET /health
Health check endpoint.

**Response:**
```json
{
  "status": "healthy",
  "version": "0.0.1",
  "timestamp": "2026-01-05T12:00:00Z"
}
```

---

### Agents

#### GET /agents
List all agents from `.parac/agents/specs/`.

**Query Parameters:**
- `skip` (int): Pagination offset (default: 0)
- `limit` (int): Max results (default: 100)

**Response:**
```json
{
  "agents": [
    {
      "name": "code-reviewer",
      "description": "Reviews code for quality",
      "provider": "openai",
      "model": "gpt-4",
      "parent": "base-agent"
    }
  ],
  "total": 5
}
```

#### GET /agents/{name}
Get agent details by name.

**Response:**
```json
{
  "name": "code-reviewer",
  "description": "Reviews code for quality",
  "provider": "openai",
  "model": "gpt-4",
  "temperature": 0.7,
  "system_prompt": "You are an expert code reviewer...",
  "tools": ["read_file", "analyze_code"],
  "parent": "base-agent",
  "metadata": {}
}
```

#### POST /agents
Create a new agent.

**Request:**
```json
{
  "name": "my-agent",
  "description": "My custom agent",
  "provider": "openai",
  "model": "gpt-4",
  "temperature": 0.7,
  "system_prompt": "You are a helpful assistant."
}
```

#### PUT /agents/{name}
Update an existing agent.

#### DELETE /agents/{name}
Delete an agent.

---

### Workflows

#### GET /workflows
List all workflows.

**Response:**
```json
{
  "workflows": [
    {
      "id": "code-review-pipeline",
      "name": "Code Review Pipeline",
      "description": "Automated code review",
      "steps": 3,
      "status": "active"
    }
  ],
  "total": 2
}
```

#### GET /workflows/{id}
Get workflow details.

#### POST /workflows
Create a new workflow.

**Request:**
```json
{
  "id": "my-workflow",
  "name": "My Workflow",
  "description": "Custom workflow",
  "steps": [
    {
      "id": "step1",
      "name": "Analyze",
      "agent_id": "analyzer",
      "prompt": "Analyze the input"
    },
    {
      "id": "step2",
      "name": "Review",
      "agent_id": "reviewer",
      "prompt": "Review the analysis",
      "dependencies": ["step1"]
    }
  ]
}
```

#### PUT /workflows/{id}
Update a workflow.

#### DELETE /workflows/{id}
Delete a workflow.

---

### Workflow Execution

#### POST /workflows/execute
Execute a workflow with optional dry-run mode.

**Request:**
```json
{
  "workflow_id": "code-review-pipeline",
  "inputs": {
    "code": "def hello(): pass",
    "language": "python"
  },
  "async_execution": true,
  "auto_approve": false,
  "dry_run": false,
  "mock_strategy": "fixed"
}
```

**Parameters:**
- `workflow_id` (string, required): Workflow identifier
- `inputs` (object): Input parameters for the workflow
- `async_execution` (boolean, default: true): Run in background
- `auto_approve` (boolean, default: false): YOLO mode - auto-approve all gates
- `dry_run` (boolean, default: false): Mock LLM calls for testing
- `mock_strategy` (string, default: "fixed"): Mock strategy (fixed/random/file/echo)

**Response:**
```json
{
  "execution_id": "exec_abc123",
  "workflow_id": "code-review-pipeline",
  "status": "pending",
  "message": "Workflow execution started in background",
  "async_execution": true
}
```

**Dry-Run Example:**
```bash
curl -X POST http://localhost:8000/api/workflows/execute \
  -H "Content-Type: application/json" \
  -d '{
    "workflow_id": "my-workflow",
    "inputs": {},
    "dry_run": true,
    "mock_strategy": "fixed"
  }'
```

#### POST /workflows/{workflow_id}/plan
Analyze workflow and generate execution plan without running it.

**Response:**
```json
{
  "workflow_id": "code-review-pipeline",
  "workflow_name": "Code Review Pipeline",
  "total_steps": 5,
  "execution_groups": [
    {
      "group_number": 0,
      "steps": ["step1"],
      "can_parallelize": false
    },
    {
      "group_number": 1,
      "steps": ["step2", "step3"],
      "can_parallelize": true
    }
  ],
  "estimated_cost_usd": 0.015,
  "estimated_time_seconds": 45,
  "approval_gates": [
    {
      "step_id": "step4",
      "approver": "user:admin",
      "timeout_seconds": 300
    }
  ],
  "optimization_suggestions": [
    "Steps step2, step3 can run in parallel",
    "Consider reviewing approval gate at step4"
  ]
}
```

**Example:**
```bash
curl -X POST http://localhost:8000/api/workflows/my-workflow/plan
```

**Use Cases:**
- Preview execution order before running
- Estimate costs for budget planning
- Identify parallelization opportunities
- Review approval requirements

#### GET /workflows/executions/{execution_id}
Get execution status.

**Response:**
```json
{
  "execution_id": "exec_abc123",
  "workflow_id": "code-review-pipeline",
  "status": "completed",
  "started_at": "2026-01-05T12:00:00Z",
  "completed_at": "2026-01-05T12:01:30Z",
  "steps": [
    {
      "id": "step1",
      "status": "completed",
      "output": "Analysis complete"
    }
  ],
  "result": {
    "summary": "Code review completed successfully"
  }
}
```

#### POST /workflows/executions/{execution_id}/cancel
Cancel a running execution.

---

### Tools

#### GET /tools
List all available tools.

**Response:**
```json
{
  "tools": [
    {
      "name": "read_file",
      "category": "filesystem",
      "description": "Read the contents of a file",
      "source": "builtin"
    }
  ],
  "total": 9,
  "builtin": 9,
  "mcp": 0
}
```

#### GET /tools/{name}
Get tool details.

**Response:**
```json
{
  "name": "read_file",
  "category": "filesystem",
  "description": "Read the contents of a file",
  "parameters": {
    "path": {
      "type": "string",
      "required": true,
      "description": "Path to the file to read"
    },
    "encoding": {
      "type": "string",
      "required": false,
      "default": "utf-8"
    }
  },
  "permissions": ["filesystem:read"]
}
```

#### POST /tools/{name}/execute
Execute a tool (for testing).

**Request:**
```json
{
  "parameters": {
    "path": "README.md"
  }
}
```

#### POST /tools/register
Register a custom tool.

---

### Approvals (Human-in-the-Loop)

#### GET /approvals/pending
List pending approval requests.

**Response:**
```json
{
  "approvals": [
    {
      "id": "apr_xyz789",
      "execution_id": "exec_abc123",
      "step_id": "deploy",
      "status": "pending",
      "priority": "HIGH",
      "requested_at": "2026-01-05T12:00:00Z",
      "expires_at": "2026-01-05T13:00:00Z",
      "context": {
        "changes": ["file1.py", "file2.py"]
      }
    }
  ]
}
```

#### POST /approvals/{id}/approve
Approve a request.

**Request:**
```json
{
  "approver": "admin@example.com",
  "comment": "Approved for deployment"
}
```

#### POST /approvals/{id}/reject
Reject a request.

**Request:**
```json
{
  "approver": "admin@example.com",
  "reason": "Missing tests"
}
```

#### POST /approvals/{id}/cancel
Cancel a pending request.

---

### Logs

#### GET /logs
List available log files.

**Response:**
```json
{
  "logs": [
    {
      "name": "actions",
      "path": "memory/logs/agent_actions.log",
      "size": "12KB",
      "modified": "2026-01-05T12:00:00Z"
    }
  ]
}
```

#### GET /logs/{name}
Get log contents.

**Query Parameters:**
- `tail` (int): Number of lines (default: 50)
- `pattern` (string): Filter pattern

---

### IDE Integration

#### GET /ide/list
List supported IDEs.

**Response:**
```json
{
  "ides": [
    {
      "name": "cursor",
      "display_name": "Cursor",
      "file_name": ".cursorrules",
      "destination": "./"
    },
    {
      "name": "claude",
      "display_name": "Claude Code",
      "file_name": "CLAUDE.md",
      "destination": ".claude/"
    }
  ]
}
```

#### GET /ide/status
Get IDE configuration status.

#### POST /ide/init
Initialize IDE configurations.

**Request:**
```json
{
  "ides": ["cursor", "claude"],
  "force": false,
  "copy": true
}
```

#### POST /ide/sync
Synchronize IDE configurations with `.parac/` state.

---

### .parac/ Management

#### GET /parac/status
Get current project state.

**Response:**
```json
{
  "phase": "phase_4",
  "phase_name": "Persistence & Production Scale",
  "progress": 95,
  "deliverables": {
    "completed": ["sqlite_persistence", "database_migrations"],
    "in_progress": ["observability"]
  }
}
```

#### POST /parac/validate
Validate `.parac/` workspace consistency.

#### POST /parac/sync
Synchronize `.parac/` with project state.

---

## Error Responses

All errors follow RFC 7807 Problem Details format:

```json
{
  "type": "https://paracle.dev/errors/not-found",
  "title": "Resource Not Found",
  "status": 404,
  "detail": "Agent 'unknown-agent' not found",
  "instance": "/agents/unknown-agent",
  "error_code": "PARACLE-API-404"
}
```

### Error Codes

| Code            | Status | Description                             |
| --------------- | ------ | --------------------------------------- |
| PARACLE-API-400 | 400    | Bad Request - Invalid input             |
| PARACLE-API-401 | 401    | Unauthorized - Missing/invalid token    |
| PARACLE-API-403 | 403    | Forbidden - Insufficient permissions    |
| PARACLE-API-404 | 404    | Not Found - Resource doesn't exist      |
| PARACLE-API-409 | 409    | Conflict - Resource already exists      |
| PARACLE-API-422 | 422    | Unprocessable Entity - Validation error |
| PARACLE-API-429 | 429    | Too Many Requests - Rate limited        |
| PARACLE-API-500 | 500    | Internal Server Error                   |

---

## Rate Limiting

Default rate limits:
- 100 requests per minute per IP
- 1000 requests per hour per IP

Rate limit headers:
```
X-RateLimit-Limit: 100
X-RateLimit-Remaining: 95
X-RateLimit-Reset: 1704456000
```

---

## Security Headers

All responses include security headers:
```
X-Content-Type-Options: nosniff
X-Frame-Options: DENY
X-XSS-Protection: 1; mode=block
Strict-Transport-Security: max-age=31536000; includeSubDomains
Content-Security-Policy: default-src 'self'
```

---

## WebSocket API

### /ws/executions/{execution_id}
Stream execution progress in real-time.

**Message Format:**
```json
{
  "type": "step_started",
  "step_id": "analyze",
  "timestamp": "2026-01-05T12:00:00Z"
}
```

**Message Types:**
- `step_started` - Step execution started
- `step_progress` - Step progress update
- `step_completed` - Step completed
- `step_failed` - Step failed
- `execution_completed` - Workflow completed
- `approval_required` - Human approval needed

---

## OpenAPI/Swagger

Interactive API documentation available at:
- Swagger UI: `http://localhost:8000/docs`
- ReDoc: `http://localhost:8000/redoc`
- OpenAPI JSON: `http://localhost:8000/openapi.json`

---

**Last Updated:** 2026-01-05
**API Version:** 0.0.1
