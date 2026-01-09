# Code Style Guidelines

## Python Code

### Type Hints
- Always use type hints for function parameters and returns
- Use `Optional[T]` for nullable types
- Use `Union[A, B]` sparingly; prefer protocols
- Use `TypeVar` for generic functions

```python
def process_agent(agent_id: str, config: Optional[Config] = None) -> Agent:
    ...
```

### Pydantic Models
- Use Pydantic `BaseModel` for all domain models
- Use `Field()` with descriptions for documentation
- Add validators using `@field_validator`
- Keep models immutable with `model_config = ConfigDict(frozen=True)`

```python
from pydantic import BaseModel, Field, field_validator

class AgentSpec(BaseModel):
    name: str = Field(..., description="Unique agent name")
    temperature: float = Field(default=0.7, ge=0.0, le=2.0)

    @field_validator('name')
    @classmethod
    def validate_name(cls, v: str) -> str:
        if not v.strip():
            raise ValueError("Name cannot be empty")
        return v.lower().strip()
```

### Formatting
- Line length: 88 characters (Black default)
- Indentation: 4 spaces
- Use Black for formatting
- Use ruff for linting

### Naming Conventions
- Variables/functions: `snake_case`
- Classes: `PascalCase`
- Constants: `UPPER_SNAKE_CASE`
- Private members: `_single_underscore`
- Avoid abbreviations; prefer descriptive names

### Imports
- Group: stdlib, third-party, local
- Sort alphabetically within groups
- Use absolute imports
- Avoid `from module import *`

```python
from datetime import datetime
from typing import List, Optional

from pydantic import BaseModel
import click

from paracle_core.config import Settings
from paracle_domain.models import Agent
```

## Documentation

### Docstrings
- Use Google-style docstrings
- Document all public functions and classes
- Include type information
- Add examples for complex functions

```python
def resolve_inheritance(agent: AgentSpec, registry: dict[str, AgentSpec]) -> AgentSpec:
    """Resolve agent inheritance chain and merge properties.

    Args:
        agent: The agent specification to resolve.
        registry: Dictionary mapping agent names to their specs.

    Returns:
        A new AgentSpec with all inherited properties merged.

    Raises:
        CircularInheritanceError: If a circular dependency is detected.
        AgentNotFoundError: If a parent agent doesn't exist.

    Example:
        >>> base = AgentSpec(name="base", model="gpt-4")
        >>> child = AgentSpec(name="child", parent="base")
        >>> resolved = resolve_inheritance(child, {"base": base})
        >>> resolved.model
        'gpt-4'
    """
```

### Comments
- Write self-documenting code; minimize comments
- Use comments for "why", not "what"
- Keep comments up-to-date with code
- Use `# TODO:` for pending work

## Error Handling

### Exceptions
- Create custom exceptions inheriting from base
- Include context in error messages
- Use specific exception types

```python
class ParacleError(Exception):
    """Base exception for Paracle."""
    pass

class AgentNotFoundError(ParacleError):
    """Raised when an agent cannot be found."""
    def __init__(self, agent_name: str):
        super().__init__(f"Agent not found: {agent_name}")
        self.agent_name = agent_name
```

### Error Handling Pattern
```python
try:
    agent = await repository.get_by_name(name)
    if agent is None:
        raise AgentNotFoundError(name)
except DatabaseError as e:
    logger.error(f"Database error: {e}")
    raise
```

## Async/Await

- Use `async/await` for I/O operations
- Prefer `asyncio.gather()` for concurrent operations
- Use `async with` for context managers
- Handle cancellation gracefully

```python
async def fetch_agents(names: list[str]) -> list[Agent]:
    tasks = [repository.get_by_name(name) for name in names]
    return await asyncio.gather(*tasks)
```

## Composition Over Inheritance

- Prefer composition for code reuse
- Exception: Agent inheritance is a domain concept
- Use protocols for interface definitions
- Keep class hierarchies shallow
