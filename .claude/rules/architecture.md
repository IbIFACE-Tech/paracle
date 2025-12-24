# Architecture Guidelines

## Hexagonal Architecture (Ports & Adapters)

### Layer Rules

1. **Domain Layer** (innermost)
   - Pure Python with Pydantic
   - No external dependencies
   - Contains business logic and entities
   - 100% testable without mocks

2. **Application Layer**
   - Orchestrates use cases
   - Calls domain layer
   - Defines port interfaces (abstract classes)

3. **Infrastructure Layer** (outermost)
   - Implements adapters for ports
   - Contains external integrations
   - Database, HTTP, message queues

### Dependency Direction
```
Infrastructure → Application → Domain
     ↓              ↓           ↓
  Adapters        Ports      Entities
```

Dependencies flow inward only. Domain never imports from infrastructure.

## Repository Pattern

### Interface Definition (Port)
```python
from abc import ABC, abstractmethod
from typing import Optional, List

class AgentRepository(ABC):
    """Abstract port for agent persistence."""

    @abstractmethod
    async def get_by_id(self, agent_id: str) -> Optional[Agent]:
        """Retrieve agent by ID."""
        pass

    @abstractmethod
    async def save(self, agent: Agent) -> None:
        """Persist agent."""
        pass

    @abstractmethod
    async def delete(self, agent_id: str) -> None:
        """Remove agent."""
        pass
```

### Implementation (Adapter)
```python
class SQLiteAgentRepository(AgentRepository):
    """SQLite adapter for agent persistence."""

    def __init__(self, db_path: str):
        self.db_path = db_path
        self._init_schema()

    async def get_by_id(self, agent_id: str) -> Optional[Agent]:
        # Implementation details
        pass
```

## Event-Driven Architecture

### Domain Events
```python
class DomainEvent(BaseModel):
    """Base class for all domain events."""
    event_id: str = Field(default_factory=generate_ulid)
    event_type: str
    aggregate_id: str
    timestamp: datetime = Field(default_factory=datetime.utcnow)
    data: dict = Field(default_factory=dict)

class AgentCreatedEvent(DomainEvent):
    event_type: str = "agent.created"
```

### Event Bus
```python
class EventBus(ABC):
    @abstractmethod
    async def publish(self, event: DomainEvent) -> None:
        pass

    @abstractmethod
    def subscribe(self, event_type: str, handler: Callable) -> None:
        pass
```

### Event Emission
- Emit events after state changes
- Keep events immutable
- Include all relevant context
- Handle failures gracefully

```python
async def create_agent(self, spec: AgentSpec) -> Agent:
    agent = Agent(spec=spec)
    await self.repository.save(agent)

    await self.event_bus.publish(
        AgentCreatedEvent(
            aggregate_id=agent.id,
            data={"name": spec.name, "model": spec.model}
        )
    )
    return agent
```

## Factory Pattern

### Agent Factory
```python
class AgentFactory:
    """Factory for creating agents with inheritance resolution."""

    def __init__(self, registry: AgentRegistry):
        self.registry = registry

    def create(self, spec: AgentSpec) -> Agent:
        """Create agent with resolved inheritance."""
        resolved_spec = self._resolve_inheritance(spec)
        return Agent(spec=resolved_spec)

    def _resolve_inheritance(self, spec: AgentSpec) -> AgentSpec:
        if not spec.parent:
            return spec

        parent = self.registry.get(spec.parent)
        merged = self._merge_specs(parent, spec)
        return self._resolve_inheritance(merged)
```

## Package Dependencies

### Allowed Dependencies
```
paracle_core     → (none - pure utilities)
paracle_domain   → paracle_core
paracle_store    → paracle_core, paracle_domain
paracle_events   → paracle_core, paracle_domain
paracle_providers → paracle_core, paracle_domain
paracle_orchestration → paracle_core, paracle_domain, paracle_events
paracle_api      → paracle_core, paracle_domain, paracle_orchestration
paracle_cli      → paracle_core, paracle_domain, paracle_api
```

### Forbidden Dependencies
- Domain must NEVER import from infrastructure
- Packages should not have circular dependencies
- Prefer explicit over implicit imports

## Configuration

### Settings Management
```python
from pydantic_settings import BaseSettings

class Settings(BaseSettings):
    """Application settings from environment."""

    database_url: str = "sqlite:///paracle.db"
    redis_url: str = "redis://localhost:6379"
    log_level: str = "INFO"

    model_config = ConfigDict(
        env_prefix="PARACLE_",
        env_file=".env"
    )
```

### Configuration Hierarchy
1. Environment variables (highest)
2. `.env` file
3. `.parac/project.yaml`
4. Default values (lowest)
