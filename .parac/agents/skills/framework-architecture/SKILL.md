---
name: framework-architecture
description: Design and evolve the architecture of the Paracle multi-agent framework. Use when discussing system design, architecture decisions, component structure, or technical debt.
license: Apache-2.0
compatibility: Requires understanding of Python, FastAPI, SQLAlchemy, event-driven architecture
metadata:
  author: paracle-core-team
  version: "1.0.0"
  category: creation
  level: expert
  display_name: "Framework Architecture Design"
  tags:
    - architecture
    - design
    - framework
    - system-design
    - patterns
  capabilities:
    - architecture_design
    - pattern_selection
    - component_design
    - integration_planning
    - scalability_analysis
  requirements:
    - skill_name: code-generation
      min_level: advanced
    - skill_name: data-analysis
      min_level: intermediate
allowed-tools: Read Write Bash(git:*) Bash(python:*)
---

# Framework Architecture Design Skill

## When to use this skill

Use this skill when:
- Designing new framework components or subsystems
- Evaluating architecture decisions and trade-offs
- Refactoring existing framework code
- Planning integration between modules
- Addressing scalability or performance concerns
- Resolving technical debt
- Creating ADRs (Architecture Decision Records)

## Paracle Framework Context

### Core Principles

1. **User-Driven Philosophy**
   - Users control agent behavior via .parac/ configuration
   - Declarative over imperative configuration
   - Progressive disclosure of complexity

2. **Modular Architecture**
   - Clear separation of concerns
   - Domain-driven design
   - Pluggable components

3. **Multi-Agent Coordination**
   - Agent inheritance system
   - Skill-based capabilities
   - Workflow orchestration

### Architecture Layers

```
┌─────────────────────────────────────────────┐
│           User Configuration                │
│              (.parac/)                      │
├─────────────────────────────────────────────┤
│         Application Layer                   │
│    (CLI, API, Orchestrator)                │
├─────────────────────────────────────────────┤
│           Domain Layer                      │
│  (Agents, Workflows, Tools, Skills)        │
├─────────────────────────────────────────────┤
│        Infrastructure Layer                 │
│   (Events, Storage, Providers)             │
├─────────────────────────────────────────────┤
│           Adapters Layer                    │
│  (OpenAI, Anthropic, Azure, MCP)           │
└─────────────────────────────────────────────┘
```

## Design Patterns for Paracle

### Pattern 1: Plugin Architecture

For adding new capabilities (LLM providers, tools, orchestrators):

```python
# Base interface
class Provider(Protocol):
    """Base protocol for LLM providers."""

    def generate(self, prompt: str, **kwargs) -> str:
        """Generate completion from prompt."""
        ...

    def stream(self, prompt: str, **kwargs) -> Iterator[str]:
        """Stream completion tokens."""
        ...

# Implementation
class OpenAIProvider:
    """OpenAI implementation."""

    def __init__(self, api_key: str, model: str):
        self.client = OpenAI(api_key=api_key)
        self.model = model

    def generate(self, prompt: str, **kwargs) -> str:
        response = self.client.chat.completions.create(
            model=self.model,
            messages=[{"role": "user", "content": prompt}],
            **kwargs
        )
        return response.choices[0].message.content

# Registry
class ProviderRegistry:
    _providers: Dict[str, Type[Provider]] = {}

    @classmethod
    def register(cls, name: str, provider_class: Type[Provider]):
        cls._providers[name] = provider_class

    @classmethod
    def get(cls, name: str) -> Type[Provider]:
        return cls._providers[name]

# Usage
ProviderRegistry.register("openai", OpenAIProvider)
```

### Pattern 2: Event-Driven Communication

For decoupling components:

```python
from dataclasses import dataclass
from typing import Callable, List
from enum import Enum

class EventType(str, Enum):
    AGENT_STARTED = "agent.started"
    AGENT_COMPLETED = "agent.completed"
    TOOL_EXECUTED = "tool.executed"
    ERROR_OCCURRED = "error.occurred"

@dataclass
class Event:
    """Base event class."""
    type: EventType
    agent_id: str
    timestamp: datetime
    payload: dict

class EventBus:
    """Simple in-memory event bus."""

    def __init__(self):
        self._handlers: Dict[EventType, List[Callable]] = {}

    def subscribe(self, event_type: EventType, handler: Callable):
        """Subscribe to an event type."""
        if event_type not in self._handlers:
            self._handlers[event_type] = []
        self._handlers[event_type].append(handler)

    def publish(self, event: Event):
        """Publish an event to all subscribers."""
        if event.type in self._handlers:
            for handler in self._handlers[event.type]:
                handler(event)

# Usage
event_bus = EventBus()

def log_agent_completion(event: Event):
    print(f"Agent {event.agent_id} completed")

event_bus.subscribe(EventType.AGENT_COMPLETED, log_agent_completion)
```

### Pattern 3: Configuration-Driven Behavior

Load behavior from YAML configs:

```python
from pathlib import Path
import yaml
from pydantic import BaseModel

class AgentConfig(BaseModel):
    """Agent configuration from .parac/agents/specs/"""
    name: str
    provider: str
    model: str
    temperature: float
    system_prompt: str
    skills: List[str]
    tools: List[str]

class ConfigLoader:
    """Load and validate configurations."""

    @staticmethod
    def load_agent(path: Path) -> AgentConfig:
        """Load agent configuration from YAML."""
        with open(path) as f:
            data = yaml.safe_load(f)

        # Validate with Pydantic
        config = AgentConfig(**data)
        return config

    @staticmethod
    def load_all_agents(base_path: Path) -> Dict[str, AgentConfig]:
        """Load all agent configurations."""
        agents = {}
        specs_dir = base_path / "agents" / "specs"

        for yaml_file in specs_dir.glob("*.yaml"):
            config = ConfigLoader.load_agent(yaml_file)
            agents[config.name] = config

        return agents
```

## Architecture Decision Process

### Step 1: Understand Requirements

Questions to ask:
- What problem are we solving?
- Who are the users (framework developers vs end users)?
- What are the constraints (performance, compatibility)?
- What are the failure modes?

### Step 2: Explore Options

Consider multiple approaches:
- List 3-5 potential solutions
- Document pros/cons for each
- Consider existing patterns in codebase

### Step 3: Evaluate Trade-offs

| Criteria        | Option A  | Option B  | Option C  |
| --------------- | --------- | --------- | --------- |
| Complexity      | Low       | Medium    | High      |
| Performance     | Good      | Excellent | Fair      |
| Maintainability | Excellent | Good      | Fair      |
| Extensibility   | Fair      | Good      | Excellent |

### Step 4: Document Decision (ADR)

```markdown
# ADR-XXX: [Short Title]

## Status
Proposed | Accepted | Deprecated | Superseded

## Context
What is the issue that we're seeing that is motivating this decision?

## Decision
What is the change that we're proposing and/or doing?

## Consequences
What becomes easier or more difficult because of this change?

### Positive
- Pro 1
- Pro 2

### Negative
- Con 1
- Con 2

### Neutral
- Note 1

## Alternatives Considered
- Alternative 1: [Brief description and why rejected]
- Alternative 2: [Brief description and why rejected]
```

## Key Design Principles

### 1. Separation of Concerns

```python
# ❌ Bad: Mixed responsibilities
class Agent:
    def execute(self, task: str):
        # Load config
        config = yaml.load(...)

        # Call LLM
        response = openai.create(...)

        # Store result
        db.insert(...)

        # Send event
        event_bus.publish(...)

# ✓ Good: Clear responsibilities
class Agent:
    def __init__(self, config: AgentConfig, provider: Provider, storage: Storage):
        self.config = config
        self.provider = provider
        self.storage = storage

    def execute(self, task: str):
        response = self.provider.generate(task)
        self.storage.save(response)
        return response
```

### 2. Dependency Injection

```python
# ✓ Good: Dependencies injected
class AgentOrchestrator:
    def __init__(
        self,
        event_bus: EventBus,
        provider_registry: ProviderRegistry,
        storage: Storage
    ):
        self.event_bus = event_bus
        self.provider_registry = provider_registry
        self.storage = storage

    def run_agent(self, agent_config: AgentConfig):
        provider = self.provider_registry.get(agent_config.provider)
        agent = Agent(agent_config, provider, self.storage)
        return agent.execute()
```

### 3. Interface Segregation

```python
# Define minimal interfaces
class Executable(Protocol):
    """Can be executed."""
    def execute(self) -> Any: ...

class Configurable(Protocol):
    """Can be configured."""
    def configure(self, config: dict) -> None: ...

class Observable(Protocol):
    """Can emit events."""
    def on_event(self, handler: Callable) -> None: ...

# Implement only what's needed
class SimpleAgent:
    """Agent that is executable but not observable."""
    def execute(self) -> str:
        return "result"

class ObservableAgent:
    """Agent that is both executable and observable."""
    def execute(self) -> str:
        self._notify_listeners("started")
        result = "result"
        self._notify_listeners("completed")
        return result

    def on_event(self, handler: Callable) -> None:
        self._listeners.append(handler)
```

## Framework Evolution Strategy

### Phase 0: Core Domain (✅ Complete)
- Basic project structure
- Configuration system (.parac/)
- Core domain models

### Phase 1: Core Domain Enhancement (Current)
- Agent inheritance
- Skill system (YAML + Agent Skills format)
- Tool registry
- Workflow engine

### Phase 2: Multi-Provider Support
- Provider abstraction
- OpenAI, Anthropic, Azure integration
- Streaming support
- Token management

### Phase 3: Advanced Features
- MCP (Model Context Protocol) integration
- Event-driven architecture
- Advanced orchestration
- Observability (tracing, metrics)

## Common Architecture Challenges

### Challenge 1: Circular Dependencies

**Problem**: Module A depends on B, B depends on C, C depends on A

**Solution**:
- Use dependency injection
- Create abstraction layer
- Apply dependency inversion principle

```python
# Instead of direct dependency
from paracle_agents import Agent  # Creates circular dep

# Use protocol/interface
from typing import Protocol

class IAgent(Protocol):
    def execute(self) -> str: ...

# Inject at runtime
def create_workflow(agent: IAgent):
    return Workflow(agent)
```

### Challenge 2: Configuration Complexity

**Problem**: Too many configuration options, unclear defaults

**Solution**:
- Layer configurations (defaults → user → runtime)
- Validate early with Pydantic
- Document all options

```python
class AgentConfig(BaseModel):
    # Required fields
    name: str
    provider: str

    # Optional with sensible defaults
    model: str = "gpt-4"
    temperature: float = Field(default=0.7, ge=0.0, le=2.0)
    max_tokens: int = Field(default=2000, gt=0)

    # Computed fields
    @property
    def full_name(self) -> str:
        return f"{self.provider}:{self.name}"
```

### Challenge 3: Testing Complexity

**Problem**: Hard to test components that depend on external services

**Solution**:
- Use dependency injection
- Create test doubles (mocks, fakes)
- Isolate side effects

```python
# Production
class OpenAIProvider:
    def generate(self, prompt: str) -> str:
        return self.client.chat.completions.create(...)

# Test
class FakeProvider:
    """Fake provider for testing."""
    def generate(self, prompt: str) -> str:
        return f"Mock response for: {prompt}"

# Test usage
def test_agent_execution():
    fake_provider = FakeProvider()
    agent = Agent(config, provider=fake_provider)
    result = agent.execute("test prompt")
    assert "Mock response" in result
```

## Best Practices Checklist

When designing new components:

- [ ] Clear single responsibility
- [ ] Dependencies injected, not created
- [ ] Interfaces over concrete types
- [ ] Fails fast with clear errors
- [ ] Unit testable in isolation
- [ ] Documented with examples
- [ ] Follows existing patterns
- [ ] Backward compatible (if extending)
- [ ] Performance considered
- [ ] Security reviewed

## Related Skills

- **code-generation**: For implementing designs
- **code-review**: For validating implementations
- **documentation-writing**: For ADRs and design docs

## References

- [Clean Architecture by Robert C. Martin](https://blog.cleancoder.com/uncle-bob/2012/08/13/the-clean-architecture.html)
- [Domain-Driven Design](https://martinfowler.com/bliki/DomainDrivenDesign.html)
- [ADR (Architecture Decision Records)](https://adr.github.io/)
- [Python Design Patterns](https://refactoring.guru/design-patterns/python)
