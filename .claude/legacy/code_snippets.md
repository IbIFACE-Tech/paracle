# Paracle Code Snippets for Claude

## Agent Creation

### Basic Agent
```python
from paracle_domain.models import AgentSpec, Agent

# Create agent specification
spec = AgentSpec(
    name="my-agent",
    model="gpt-4",
    temperature=0.7,
    system_prompt="You are a helpful AI assistant specialized in Python development.",
    tools=["code_reader", "code_executor"],
    metadata={"category": "development"}
)

# Instantiate agent
agent = Agent(spec=spec)
print(f"Created agent: {agent.id}")
```

### Agent with Inheritance
```python
# Parent agent
base_spec = AgentSpec(
    name="base-coder",
    model="gpt-4",
    temperature=0.5,
    system_prompt="You are a software developer."
)

# Child agent inheriting from parent
specialized_spec = AgentSpec(
    name="python-expert",
    parent="base-coder",  # Inherits from base-coder
    temperature=0.3,      # Override temperature
    system_prompt="You are a Python expert developer with deep knowledge of best practices."
)
```

## Workflow Definition

### Simple Sequential Workflow
```python
from paracle_domain.models import WorkflowSpec, WorkflowStep

workflow = WorkflowSpec(
    name="code_review",
    description="Automated code review workflow",
    steps=[
        WorkflowStep(
            name="analyze",
            agent="code-analyzer",
            inputs={"file_path": "src/main.py"},
            outputs=["analysis_report"]
        ),
        WorkflowStep(
            name="review",
            agent="security-reviewer",
            depends_on=["analyze"],
            inputs={"analysis": "{{ steps.analyze.outputs.analysis_report }}"},
            outputs=["security_report"]
        ),
        WorkflowStep(
            name="summarize",
            agent="documenter",
            depends_on=["review"],
            inputs={
                "analysis": "{{ steps.analyze.outputs.analysis_report }}",
                "security": "{{ steps.review.outputs.security_report }}"
            },
            outputs=["final_report"]
        )
    ]
)
```

## Testing Patterns

### Unit Test for Domain Model
```python
import pytest
from paracle_domain.models import AgentSpec

def test_agent_spec_creation():
    """Test basic agent spec creation."""
    # Arrange
    name = "test-agent"
    model = "gpt-4"

    # Act
    spec = AgentSpec(name=name, model=model)

    # Assert
    assert spec.name == name
    assert spec.model == model
    assert spec.temperature == 0.7  # default
    assert spec.status == "active"

def test_agent_spec_temperature_validation():
    """Test temperature must be between 0.0 and 2.0."""
    # Act & Assert
    with pytest.raises(ValueError):
        AgentSpec(name="test", model="gpt-4", temperature=3.0)
```

### Async Test
```python
import pytest
from paracle_domain.models import Agent, AgentSpec

@pytest.mark.asyncio
async def test_agent_execution():
    """Test agent can execute tasks."""
    # Arrange
    spec = AgentSpec(name="test-agent", model="gpt-4")
    agent = Agent(spec=spec)

    # Act
    result = await agent.execute({"task": "Hello"})

    # Assert
    assert result is not None
    assert agent.status == "ready"
```

## Repository Pattern

### Repository Interface
```python
from abc import ABC, abstractmethod
from typing import List, Optional
from paracle_domain.models import Agent

class AgentRepository(ABC):
    """Abstract repository for agent persistence."""

    @abstractmethod
    async def get_by_id(self, agent_id: str) -> Optional[Agent]:
        """Get agent by ID."""
        pass

    @abstractmethod
    async def get_by_name(self, name: str) -> Optional[Agent]:
        """Get agent by name."""
        pass

    @abstractmethod
    async def list_all(self) -> List[Agent]:
        """List all agents."""
        pass

    @abstractmethod
    async def save(self, agent: Agent) -> None:
        """Save or update agent."""
        pass

    @abstractmethod
    async def delete(self, agent_id: str) -> None:
        """Delete agent by ID."""
        pass
```

### SQLite Implementation
```python
import sqlite3
from typing import List, Optional
from paracle_domain.models import Agent, AgentSpec

class SQLiteAgentRepository(AgentRepository):
    """SQLite implementation of agent repository."""

    def __init__(self, db_path: str):
        self.db_path = db_path
        self._init_db()

    def _init_db(self):
        """Initialize database schema."""
        with sqlite3.connect(self.db_path) as conn:
            conn.execute("""
                CREATE TABLE IF NOT EXISTS agents (
                    id TEXT PRIMARY KEY,
                    name TEXT NOT NULL UNIQUE,
                    model TEXT NOT NULL,
                    temperature REAL,
                    system_prompt TEXT,
                    parent TEXT,
                    status TEXT,
                    created_at TEXT,
                    metadata TEXT
                )
            """)

    async def get_by_id(self, agent_id: str) -> Optional[Agent]:
        """Get agent by ID."""
        # Implementation here
        pass
```

## Event Bus Pattern

### Domain Event
```python
from datetime import datetime
from pydantic import BaseModel
from typing import Any, Dict

class DomainEvent(BaseModel):
    """Base class for domain events."""

    event_type: str
    aggregate_id: str
    timestamp: datetime = datetime.utcnow()
    data: Dict[str, Any] = {}

class AgentCreatedEvent(DomainEvent):
    """Event emitted when an agent is created."""

    event_type: str = "agent.created"

    @classmethod
    def create(cls, agent_id: str, agent_name: str):
        return cls(
            aggregate_id=agent_id,
            data={"name": agent_name}
        )
```

### Event Handler
```python
from typing import Callable, List

class EventBus:
    """Simple in-memory event bus."""

    def __init__(self):
        self._handlers: Dict[str, List[Callable]] = {}

    def subscribe(self, event_type: str, handler: Callable):
        """Subscribe handler to event type."""
        if event_type not in self._handlers:
            self._handlers[event_type] = []
        self._handlers[event_type].append(handler)

    async def publish(self, event: DomainEvent):
        """Publish event to all subscribers."""
        handlers = self._handlers.get(event.event_type, [])
        for handler in handlers:
            await handler(event)
```

## CLI Commands

### Click Command
```python
import click
from rich.console import Console

console = Console()

@click.command()
@click.argument("name")
@click.option("--model", default="gpt-4", help="Model to use")
@click.option("--temperature", default=0.7, type=float, help="Temperature setting")
def create_agent(name: str, model: str, temperature: float):
    """Create a new agent."""
    try:
        spec = AgentSpec(
            name=name,
            model=model,
            temperature=temperature
        )
        agent = Agent(spec=spec)

        console.print(f"[green]✓[/green] Agent created: {agent.id}")
        console.print(f"  Name: {agent.spec.name}")
        console.print(f"  Model: {agent.spec.model}")

    except Exception as e:
        console.print(f"[red]✗[/red] Error: {str(e)}")
        raise click.ClickException(str(e))
```

## Configuration Loading

### Load .parac Configuration
```python
import yaml
from pathlib import Path
from typing import Dict, Any

def load_project_config() -> Dict[str, Any]:
    """Load project configuration from .parac/project.yaml."""
    config_path = Path(".parac/project.yaml")

    if not config_path.exists():
        raise FileNotFoundError("Project configuration not found")

    with open(config_path, "r") as f:
        return yaml.safe_load(f)

def get_agent_manifest() -> Dict[str, Any]:
    """Load agent manifest from .parac/agents/manifest.yaml."""
    manifest_path = Path(".parac/agents/manifest.yaml")

    with open(manifest_path, "r") as f:
        return yaml.safe_load(f)
```
