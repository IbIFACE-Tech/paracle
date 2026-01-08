# paracle_core

**Core utilities and foundational components**

## Purpose

`paracle_core` provides the foundational utilities that all other Paracle modules depend on. It contains no business logic, only shared utilities.

## Key Components

### 1. Configuration Management

```python
from paracle_core.config import Settings

settings = Settings()
print(settings.database_url)  # From env or defaults
```

**Features:**
- Environment variable loading
- `.env` file support
- Type-safe settings with Pydantic
- Hierarchical configuration

**Configuration Sources (Priority Order):**
1. Environment variables
2. `.env` file
3. Default values

### 2. ID Generation

```python
from paracle_core.ids import generate_id

agent_id = generate_id("agent")
# → "agent_01HQZYX9K5P7R8S9T0V1W2X3Y4"

workflow_id = generate_id("workflow")
# → "workflow_01HQZYX9K5P7R8S9T0V1W2X3Y5"
```

**Uses ULID** (Universally Unique Lexicographically Sortable Identifier):
- 26 characters
- Sortable by creation time
- URL-safe
- Case-insensitive

### 3. Logging

```python
from paracle_core.logging import get_logger

logger = get_logger(__name__)
logger.info("Agent created", agent_id="agent_123")
```

**Features:**
- Structured logging (JSON)
- Correlation IDs
- Log levels
- Context managers

### 4. Error Handling

```python
from paracle_core.errors import (
    ParacleError,
    ValidationError,
    NotFoundError,
    ConfigurationError
)

raise NotFoundError("Agent not found", agent_id="agent_123")
```

**Error Hierarchy:**
```
ParacleError (base)
├── ValidationError
├── NotFoundError
├── ConfigurationError
├── ExecutionError
├── AuthenticationError
└── PermissionError
```

### 5. Path Utilities

```python
from paracle_core.paths import (
    find_parac_root,
    get_agents_dir,
    get_workflows_dir
)

parac_root = find_parac_root()  # Finds .parac/ directory
agents_dir = get_agents_dir()    # .parac/agents/specs/
```

### 6. Type Definitions

```python
from paracle_core.types import (
    AgentID,
    WorkflowID,
    ToolID,
    JSON,
    PathLike
)

def process_agent(agent_id: AgentID) -> None:
    ...
```

## Module Structure

```
paracle_core/
├── __init__.py
├── config.py           # Settings and configuration
├── ids.py              # ID generation (ULID)
├── logging.py          # Logging utilities
├── errors.py           # Error classes
├── paths.py            # Path helpers
├── types.py            # Type definitions
├── utils.py            # Miscellaneous utilities
└── constants.py        # Constants
```

## Usage Examples

### Configuration

```python
from paracle_core.config import Settings

# Load settings
settings = Settings()

# Access settings
print(f"Database: {settings.database_url}")
print(f"Redis: {settings.redis_url}")
print(f"Log Level: {settings.log_level}")

# Custom .env file
settings = Settings(_env_file=".env.production")
```

### ID Generation

```python
from paracle_core.ids import generate_id, is_valid_id

# Generate IDs
agent_id = generate_id("agent")
task_id = generate_id("task")
run_id = generate_id("run")

# Validate IDs
assert is_valid_id(agent_id)
assert is_valid_id("invalid") == False
```

### Logging

```python
from paracle_core.logging import get_logger

logger = get_logger(__name__)

# Structured logging
logger.info("Operation started", operation="create_agent")

try:
    # ... work
    logger.info("Operation complete", duration_ms=123)
except Exception as e:
    logger.error("Operation failed", error=str(e))
```

### Error Handling

```python
from paracle_core.errors import NotFoundError, ValidationError

# Raise errors with context
def get_agent(agent_id: str):
    agent = db.get(agent_id)
    if not agent:
        raise NotFoundError(
            f"Agent not found: {agent_id}",
            agent_id=agent_id
        )
    return agent

# Catch and handle
try:
    agent = get_agent("agent_123")
except NotFoundError as e:
    print(f"Error: {e.message}")
    print(f"Context: {e.context}")
```

## Dependencies

**External:**
- `pydantic` - Settings and validation
- `python-dotenv` - Environment variables
- `ulid-py` - ULID generation

**Internal:**
- None (this is the foundation)

## Environment Variables

| Variable               | Default          | Description                    |
| ---------------------- | ---------------- | ------------------------------ |
| `PARACLE_DATABASE_URL` | `sqlite:///...`  | Database connection string     |
| `PARACLE_REDIS_URL`    | `redis://...`    | Redis connection string        |
| `PARACLE_LOG_LEVEL`    | `INFO`           | Logging level                  |
| `PARACLE_WORKSPACE`    | `.parac/`        | Workspace directory            |

## Design Principles

1. **No Business Logic** - Only utilities
2. **Minimal Dependencies** - Keep it light
3. **Type Safety** - Full type hints
4. **Configurability** - Everything configurable
5. **Testability** - Pure functions where possible

## Testing

```python
from paracle_core.config import Settings
from paracle_core.ids import generate_id

def test_settings_from_env(monkeypatch):
    monkeypatch.setenv("PARACLE_LOG_LEVEL", "DEBUG")
    settings = Settings()
    assert settings.log_level == "DEBUG"

def test_id_generation():
    id1 = generate_id("agent")
    id2 = generate_id("agent")
    assert id1 != id2
    assert id1.startswith("agent_")
```

## Next Steps

- [paracle_domain](domain.md) - Business models
- [paracle_store](store.md) - Persistence
- [Architecture Overview](../architecture.md)
