# API-First CLI Architecture

Paracle CLI follows an API-first design pattern with graceful fallback to direct core access.

## Overview

The CLI acts as a thin client that communicates with the Paracle API server. When the API is unavailable, it falls back to direct core access for offline functionality.

```
┌─────────────────────────────────────────────────────────────────┐
│                         User                                     │
└────────────────────────────┬────────────────────────────────────┘
                             │
                             ▼
┌─────────────────────────────────────────────────────────────────┐
│                    Paracle CLI                                   │
│  ┌─────────────────────────────────────────────────────────────┐│
│  │                   Command Layer                              ││
│  │  paracle agents list | paracle workflow run | paracle sync   ││
│  └──────────────────────────┬──────────────────────────────────┘│
│                             │                                    │
│  ┌──────────────────────────▼──────────────────────────────────┐│
│  │                  API Client Layer                            ││
│  │           use_api_or_fallback() function                     ││
│  └──────────────────────────┬──────────────────────────────────┘│
└─────────────────────────────┼───────────────────────────────────┘
                              │
            ┌─────────────────┴─────────────────┐
            │                                   │
            ▼                                   ▼
┌───────────────────────┐           ┌───────────────────────┐
│     API Available     │           │    API Unavailable    │
│                       │           │                       │
│  ┌─────────────────┐  │           │  ┌─────────────────┐  │
│  │  HTTP Request   │  │           │  │  Direct Core    │  │
│  │  to API Server  │  │           │  │  Function Call  │  │
│  └────────┬────────┘  │           │  └────────┬────────┘  │
│           │           │           │           │           │
│           ▼           │           │           ▼           │
│  ┌─────────────────┐  │           │  ┌─────────────────┐  │
│  │  Paracle API    │  │           │  │  paracle_core   │  │
│  │  (FastAPI)      │  │           │  │  paracle_domain │  │
│  └─────────────────┘  │           │  │  paracle_store  │  │
└───────────────────────┘           │  └─────────────────┘  │
                                    └───────────────────────┘
```

## Design Principles

### 1. API-First

All functionality is exposed through REST APIs first:

```python
# CLI command calls API endpoint
def agents_list():
    client = get_client()
    response = client.agents_list()  # HTTP GET /agents
    display_agents(response)
```

### 2. Graceful Fallback

When API is unavailable, fall back to direct access:

```python
from paracle_cli.api_client import use_api_or_fallback

def list_agents():
    return use_api_or_fallback(
        api_func=lambda client: client.agents_list(),
        fallback_func=direct_list_agents,
    )
```

### 3. Consistent Interface

Users get the same experience regardless of API availability:

```bash
# Works the same whether API is running or not
paracle agents list
paracle status
paracle sync
```

## API Client

The `APIClient` class provides typed methods for all API endpoints:

```python
from paracle_cli.api_client import APIClient, get_client

# Get client instance
client = get_client()  # Defaults to http://localhost:8000

# Custom URL
client = APIClient(base_url="http://api.example.com:8080")

# Check availability
if client.is_available():
    response = client.agents_list()
```

### Available Endpoints

```python
class APIClient:
    # Health
    def health(self) -> dict[str, Any]
    def is_available(self) -> bool

    # Parac/Governance
    def parac_status(self) -> dict[str, Any]
    def parac_sync(self, update_git, update_metrics) -> dict[str, Any]
    def parac_validate(self) -> dict[str, Any]
    def parac_session_start(self) -> dict[str, Any]
    def parac_session_end(self, progress, completed, in_progress) -> dict[str, Any]

    # Agents
    def agents_list(self) -> dict[str, Any]
    def agents_get(self, agent_id: str) -> dict[str, Any]
    def agents_get_spec(self, agent_id: str) -> dict[str, Any]

    # Workflows
    def workflow_list(self, limit, offset, status) -> dict[str, Any]
    def workflow_get(self, workflow_id: str) -> dict[str, Any]
    def workflow_execute(self, workflow_id, inputs, async_execution) -> dict[str, Any]
    def workflow_execution_status(self, execution_id: str) -> dict[str, Any]

    # IDE Integration
    def ide_list(self) -> dict[str, Any]
    def ide_init(self, ides, force, copy) -> dict[str, Any]
    def ide_sync(self, copy: bool) -> dict[str, Any]

    # Approvals (Human-in-the-Loop)
    def approvals_list_pending(self) -> dict[str, Any]
    def approvals_approve(self, approval_id, approver, reason) -> dict[str, Any]
    def approvals_reject(self, approval_id, approver, reason) -> dict[str, Any]

    # Kanban Board
    def boards_list(self, include_archived) -> dict[str, Any]
    def boards_create(self, name, description, columns) -> dict[str, Any]
    def tasks_list(self, board_id, status, assigned_to) -> dict[str, Any]
    def tasks_move(self, task_id, status, reason) -> dict[str, Any]

    # Observability
    def metrics_list(self) -> dict[str, Any]
    def metrics_export(self, format) -> dict[str, Any]
    def traces_list(self, limit) -> dict[str, Any]
    def alerts_list(self, severity, active_only) -> dict[str, Any]
```

## Fallback Pattern

### use_api_or_fallback()

The main utility for implementing API-first with fallback:

```python
from paracle_cli.api_client import use_api_or_fallback

def get_project_status():
    """Get status via API or direct access."""
    return use_api_or_fallback(
        api_func=lambda client: client.parac_status(),
        fallback_func=get_status_direct,
    )

def get_status_direct():
    """Direct access fallback."""
    from paracle_core.parac import read_current_state
    return read_current_state()
```

### Fallback Behavior

1. **Check API availability** - Quick health check
2. **Try API call** - If available, use API
3. **Handle errors** - Catch connection errors, timeouts
4. **Fall back** - Use direct core access
5. **User notification** - Optionally inform user of fallback

```python
def use_api_or_fallback(api_func, fallback_func, *args, **kwargs):
    client = get_client()

    if client.is_available():
        try:
            return api_func(client, *args, **kwargs)
        except APIError as e:
            if e.status_code == 404:
                pass  # Let fallback handle
            else:
                console.print(f"[yellow]API error:[/yellow] {e.detail}")
                console.print("[dim]Falling back to direct access...[/dim]")
        except Exception as e:
            console.print(f"[yellow]API unavailable:[/yellow] {e}")
            console.print("[dim]Falling back to direct access...[/dim]")

    return fallback_func(*args, **kwargs)
```

## Command Implementation

### Example: Status Command

```python
import click
from rich.console import Console
from paracle_cli.api_client import use_api_or_fallback, get_client

console = Console()

@click.command()
def status():
    """Show project status."""
    result = use_api_or_fallback(
        api_func=lambda client: client.parac_status(),
        fallback_func=get_status_fallback,
    )
    display_status(result)

def get_status_fallback():
    """Direct access when API unavailable."""
    from paracle_core.parac.sync import read_current_state
    from pathlib import Path

    parac_dir = Path.cwd() / ".parac"
    if not parac_dir.exists():
        return {"error": "No .parac/ folder found"}

    return read_current_state(parac_dir)

def display_status(result):
    """Format and display status."""
    if "error" in result:
        console.print(f"[red]{result['error']}[/red]")
        return

    console.print(f"[bold]Phase:[/bold] {result.get('phase', 'Unknown')}")
    console.print(f"[bold]Progress:[/bold] {result.get('progress', 0)}%")
```

### Example: Agents List Command

```python
@click.command()
@click.option("--format", type=click.Choice(["table", "json"]), default="table")
def list_agents(format):
    """List all available agents."""
    result = use_api_or_fallback(
        api_func=lambda client: client.agents_list(),
        fallback_func=list_agents_fallback,
    )

    if format == "json":
        console.print_json(data=result)
    else:
        display_agents_table(result)

def list_agents_fallback():
    """Scan .parac/agents/specs/ directly."""
    from paracle_core.agents import AgentRegistry

    registry = AgentRegistry()
    return {"agents": registry.list_all()}
```

## Authentication

The API client supports token-based authentication:

```python
client = get_client()
client.set_token("your-api-token")

# All subsequent requests include the token
response = client.agents_list()
```

Headers are automatically set:

```python
def _get_headers(self) -> dict[str, str]:
    headers = {"Content-Type": "application/json"}
    if self._token:
        headers["Authorization"] = f"Bearer {self._token}"
    return headers
```

## Error Handling

### APIError

Custom exception for API errors:

```python
class APIError(Exception):
    def __init__(self, status_code: int, detail: str):
        self.status_code = status_code
        self.detail = detail
```

### Error Response Handling

```python
def _handle_response(self, response: httpx.Response) -> dict[str, Any]:
    if response.status_code >= 400:
        try:
            detail = response.json().get("detail", response.text)
        except (ValueError, KeyError):
            detail = response.text
        raise APIError(response.status_code, detail)

    return response.json()
```

### CLI Error Display

```python
try:
    result = client.workflow_execute(workflow_id, inputs)
except APIError as e:
    if e.status_code == 404:
        console.print(f"[red]Workflow not found: {workflow_id}[/red]")
    elif e.status_code == 400:
        console.print(f"[red]Invalid request: {e.detail}[/red]")
    else:
        console.print(f"[red]API error: {e.detail}[/red]")
```

## Starting the API Server

The CLI includes a `serve` command to start the API:

```bash
# Start with defaults (localhost:8000)
paracle serve

# Custom host and port
paracle serve --host 0.0.0.0 --port 9000

# With auto-reload for development
paracle serve --reload

# Production mode
paracle serve --workers 4
```

### Server Configuration

```python
@click.command()
@click.option("--host", default="127.0.0.1")
@click.option("--port", default=8000)
@click.option("--reload", is_flag=True)
@click.option("--workers", default=1)
def serve(host, port, reload, workers):
    """Start the Paracle API server."""
    import uvicorn
    uvicorn.run(
        "paracle_api.main:app",
        host=host,
        port=port,
        reload=reload,
        workers=workers,
    )
```

## Benefits of API-First

### 1. Separation of Concerns

- CLI handles user interaction and formatting
- API handles business logic and data access
- Core provides domain models and utilities

### 2. Multiple Interfaces

Same API serves:
- CLI commands
- IDE integrations
- MCP protocol
- Web dashboard
- CI/CD pipelines

### 3. Remote Access

Run CLI commands against remote Paracle instances:

```bash
export PARACLE_API_URL=https://paracle.company.com
paracle agents list
```

### 4. Testing

API-first makes testing easier:

```python
# Test API directly
def test_agents_list(client):
    response = client.get("/agents")
    assert response.status_code == 200

# Test CLI with mocked API
def test_cli_agents_list(mocker):
    mocker.patch("paracle_cli.api_client.get_client")
    result = runner.invoke(cli, ["agents", "list"])
    assert result.exit_code == 0
```

### 5. Offline Support

Fallback ensures CLI works without API:

```bash
# Works even if API server is down
paracle status
paracle agents list
paracle sync
```

## Best Practices

### 1. Always Use use_api_or_fallback()

```python
# Good - graceful degradation
result = use_api_or_fallback(api_func, fallback_func)

# Avoid - no fallback
result = client.api_call()  # Fails if API down
```

### 2. Keep Fallbacks Simple

```python
# Good - minimal fallback logic
def fallback():
    return read_file_directly()

# Avoid - complex fallback
def fallback():
    # Don't replicate full API logic here
    pass
```

### 3. Handle Errors Gracefully

```python
# Good - specific error handling
try:
    result = client.workflow_execute(id)
except APIError as e:
    if e.status_code == 404:
        console.print("[red]Workflow not found[/red]")
    raise

# Avoid - generic error handling
try:
    result = client.workflow_execute(id)
except Exception:
    console.print("[red]Error[/red]")
```

### 4. Use Rich for Output

```python
from rich.console import Console
from rich.table import Table

console = Console()

# Good - rich formatting
table = Table(title="Agents")
table.add_column("Name")
table.add_column("Status")
console.print(table)

# Avoid - plain print
print("Agents:")
for agent in agents:
    print(f"  {agent['name']}")
```

## Related Documentation

- [Architecture Overview](architecture.md) - System design
- [Synchronization Guide](synchronization-guide.md) - Async patterns
- [CLI Reference](technical/cli-reference.md) - Command reference
