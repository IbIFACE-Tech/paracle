# API-First CLI Architecture

## Overview

Paracle CLI follows an **API-first architecture** with **local fallback**:

1. **Primary Mode**: API endpoints via `paracle serve`
2. **Fallback Mode**: Local execution when API unavailable

## Architecture Diagram

```
┌─────────────────────────────────────────────────────────────┐
│                      PARACLE CLI                            │
│                  (packages/paracle_cli)                     │
└─────────────────────┬───────────────────────────────────────┘
                      │
                      ├─→ Try API First
                      │   │
                      │   ├─→ Success → Use API
                      │   │    (api_client.py → httpx → FastAPI)
                      │   │
                      │   └─→ Fail → Check Local Fallback
                      │        │
                      │        ├─→ Available → Use Local
                      │        │    (Direct import orchestration)
                      │        │
                      │        └─→ Unavailable → Error
                      │             (User must start API)
                      │
                      ▼
┌─────────────────────────────────────────────────────────────┐
│                   EXECUTION LAYER                           │
│                                                             │
│  API Mode (Preferred)          Local Mode (Fallback)       │
│  ─────────────────────         ─────────────────────       │
│  • REST API (uvicorn)          • Direct imports            │
│  • Multi-client support        • Single process            │
│  • Async execution             • Sync execution only       │
│  • Remote workflows            • Local workflows           │
│  • Full monitoring             • Basic monitoring          │
└─────────────────────────────────────────────────────────────┘
```

## Command Behavior

### Workflow Commands

#### `paracle workflow list`

**API Mode** (preferred):
```bash
$ paracle serve &  # Start API in background
$ paracle workflow list
# → Uses GET /workflows endpoint
# → Full pagination, filtering, status tracking
```

**Local Mode** (fallback):
```bash
# No API running
$ paracle workflow list
⚠️  API server unavailable, using local execution
# → Uses WorkflowRepository directly
# → Basic listing from local storage
# → Limited features
```

#### `paracle workflow run`

**API Mode** (preferred):
```bash
$ paracle serve &
$ paracle workflow run my-workflow -i key=value
# → Uses POST /workflows/{id}/execute
# → Async execution with execution_id
# → Progress tracking with --watch
# → Full monitoring and status checks
```

**Local Mode** (fallback):
```bash
# No API running
$ paracle workflow run my-workflow -i key=value --sync
⚠️  API server unavailable, using local execution
# → Uses WorkflowEngine directly
# → Synchronous execution only
# → Basic output, no execution_id
# → No progress tracking
```

### Tools Commands

Tools commands are **always local** (no API dependency):
```bash
$ paracle tools list
# → Uses BuiltinToolRegistry directly
# → No API required
# → Works offline
```

### Providers Commands

Providers commands are **always local** (no API dependency):
```bash
$ paracle providers list
# → Uses ProviderRegistry directly
# → No API required
# → Configuration from local files
```

## Detection Logic

```python
def _is_api_available() -> bool:
    """Check if API server is reachable."""
    try:
        client = get_client()
        response = client.get("/health", timeout=2.0)
        return response.status_code == 200
    except Exception:
        return False

def _use_local_fallback() -> bool:
    """Determine execution mode."""
    if not _is_api_available():
        if LOCAL_EXECUTION_AVAILABLE:
            console.print("⚠️  API unavailable, using local execution")
            return True
        else:
            console.print("✗ API unavailable and local fallback not available")
            console.print("Start API: paracle serve")
            raise click.Abort()
    return False
```

## Local Fallback Requirements

For local fallback to work, you need **full package installation**:

```toml
# pyproject.toml
[project.dependencies]
paracle-orchestration = "*"  # Required for WorkflowEngine
paracle-store = "*"          # Required for repositories
paracle-events = "*"         # Required for event bus
```

**Minimal installation** (CLI only):
```bash
pip install paracle-cli
# → Tools and providers work
# → Workflows require API
```

**Full installation** (with fallback):
```bash
pip install paracle[full]
# → All features work
# → Local fallback available
```

## API-First Benefits

### 1. **Scalability**
- Multiple CLI clients can share one API server
- Centralized execution and monitoring
- Resource pooling and management

### 2. **Consistency**
- Single source of truth (API state)
- Consistent behavior across clients
- Unified logging and tracing

### 3. **Features**
- Async execution with tracking
- Progress monitoring (--watch mode)
- Remote workflow execution
- Multi-user workflows

### 4. **Separation of Concerns**
- CLI: User interface and commands
- API: Business logic and execution
- Core: Domain models and workflows

## Local Fallback Benefits

### 1. **Offline Operation**
- Works without network
- No API server required
- Simple deployments

### 2. **Development**
- Quick prototyping
- No setup overhead
- Direct debugging

### 3. **Simplicity**
- Single process
- Easier troubleshooting
- Lower resource usage

## Best Practices

### For Development
```bash
# Start API for full features
paracle serve --port 8000 &

# Use CLI with all features
paracle workflow run my-workflow --watch
paracle workflow status exec_123
```

### For Production
```bash
# Run API as service (systemd, Docker, etc.)
systemctl start paracle-api

# CLI connects automatically
paracle workflow list
```

### For Offline/Minimal
```bash
# Use tools and providers (always local)
paracle tools list
paracle providers add anthropic --api-key sk-xxx

# Workflows need API or full installation
pip install paracle[full]
paracle workflow run my-workflow --sync  # Local fallback
```

## Error Messages

### API Unavailable (with fallback)
```
⚠️  API server unavailable, using local execution
Executing workflow locally...
✓ Workflow completed
```

### API Unavailable (no fallback)
```
✗ API server unavailable and local fallback not available
Start API: paracle serve or install full packages
```

### API Available
```
# No warning, normal execution
✓ Workflow execution started
Execution ID: exec_abc123
Status: running
```

## Configuration

### API Client Config
```yaml
# .parac/config.yaml
api:
  base_url: http://localhost:8000
  timeout: 30
  retry: 3

fallback:
  enabled: true
  prefer_local: false  # Always try API first
```

### Health Check Settings
```python
# packages/paracle_cli/api_client.py
HEALTH_CHECK_TIMEOUT = 2.0  # seconds
HEALTH_CHECK_ENDPOINT = "/health"
```

## Monitoring

### Check API Status
```bash
# Manual health check
curl http://localhost:8000/health

# CLI detects automatically
paracle workflow list
# → Uses API if available
# → Falls back if not
```

### Debug API Connection
```bash
# Enable debug logging
export PARACLE_LOG_LEVEL=DEBUG
paracle workflow list
# → Shows API detection attempts
# → Shows fallback decisions
```

## Roadmap

### Phase 4 (Current)
- ✅ API-first workflow commands
- ✅ Local fallback detection
- ✅ Health check implementation
- ⏳ Async local execution

### Phase 5 (Future)
- Remote API servers
- API authentication
- Distributed workflows
- Load balancing

### Phase 6 (Future)
- API caching
- Offline queue
- Smart fallback strategies
- Performance optimization

## Related Documentation

- [API Reference](api-reference.md)
- [Workflow Management](workflow-management.md)
- [Architecture Overview](architecture.md)
- [Deployment Guide](deployment.md)
