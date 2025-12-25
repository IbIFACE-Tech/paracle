# Framework Design Guidelines

## Core Principles

### 1. Design for Decades, Not Sprints

A framework must outlive its initial implementation. Every decision should consider:

- **10-year maintenance burden**: Will this be understandable in 10 years?
- **API stability**: Can we evolve without breaking consumers?
- **Conceptual integrity**: Does this fit the overall mental model?

### 2. Invariants First

Before writing any code, define what must ALWAYS be true:

```python
# Example: Agent Invariants
AGENT_INVARIANTS = """
1. An agent MUST have a unique name within its scope
2. An agent's parent chain MUST be acyclic (no circular inheritance)
3. An agent MUST have a valid model reference
4. Temperature MUST be in range [0.0, 2.0]
5. An agent MUST be auditable (all actions logged)
6. An agent MUST respect its permission boundaries
"""
```

### 3. Layered Abstraction

```text
┌─────────────────────────────────────────┐
│           CONCEPTUAL LAYER              │
│  "What problems do we solve?"           │
│  Agents, Workflows, Tools, Policies     │
├─────────────────────────────────────────┤
│            LOGICAL LAYER                │
│  "How do concepts interact?"            │
│  Inheritance, Orchestration, Events     │
├─────────────────────────────────────────┤
│           TECHNICAL LAYER               │
│  "How do we implement?"                 │
│  Python, Pydantic, SQLite, Redis        │
├─────────────────────────────────────────┤
│          OPERATIONAL LAYER              │
│  "How do we run and observe?"           │
│  Deployment, Monitoring, Scaling        │
└─────────────────────────────────────────┘
```

---

## API Design Principles

### 1. Pit of Success

Make the right thing easy and the wrong thing hard:

```python
# GOOD: Safe by default
class AgentSpec(BaseModel):
    temperature: float = Field(default=0.7, ge=0.0, le=2.0)
    max_tokens: int = Field(default=4096, ge=1, le=128000)

# BAD: Requires discipline
class AgentSpec:
    def __init__(self, temperature=None):  # None? What's the default?
        self.temperature = temperature  # No validation
```

### 2. Progressive Disclosure

Simple things should be simple. Complex things should be possible.

```python
# Simple: 1 line
agent = Agent(name="helper", model="gpt-4")

# Intermediate: Common customization
agent = Agent(
    name="coder",
    model="gpt-4",
    temperature=0.3,
    system_prompt="You are a Python expert."
)

# Advanced: Full control
agent = Agent(
    name="enterprise-coder",
    model="gpt-4",
    temperature=0.3,
    system_prompt="...",
    parent="base-coder",
    tools=["read_file", "write_file", "execute_code"],
    policies=["iso-42001-compliant"],
    metadata={"team": "platform", "cost_center": "engineering"}
)
```

### 3. Explicit Over Implicit

Never hide important behavior:

```python
# GOOD: Explicit inheritance resolution
resolved_spec = agent_factory.resolve_inheritance(spec)
agent = Agent(spec=resolved_spec)

# BAD: Magic behind the scenes
agent = Agent(spec=spec)  # Silently resolves inheritance?
```

### 4. Composability

Design components that combine predictably:

```python
# Components compose naturally
workflow = (
    Workflow("review-pipeline")
    .add_step(Step("analyze", agent="analyzer"))
    .add_step(Step("review", agent="reviewer", depends_on=["analyze"]))
    .add_step(Step("approve", agent="approver", depends_on=["review"]))
    .with_policy(RequireHumanApproval(threshold="high-risk"))
    .with_timeout(minutes=30)
)
```

---

## Extension Points

### 1. Protocols Over Inheritance

Use Protocol (structural typing) for extension points:

```python
from typing import Protocol, runtime_checkable

@runtime_checkable
class LLMProvider(Protocol):
    """Any LLM provider must implement this interface."""

    async def complete(
        self,
        messages: list[Message],
        model: str,
        temperature: float
    ) -> CompletionResult:
        ...

    async def stream(
        self,
        messages: list[Message],
        model: str,
        temperature: float
    ) -> AsyncIterator[StreamChunk]:
        ...

# Users can implement their own providers
class MyCustomProvider:
    async def complete(self, messages, model, temperature):
        # Custom implementation
        ...
```

### 2. Hook Points

Provide explicit extension hooks:

```python
class WorkflowEngine:
    """Workflow execution with extension hooks."""

    # Lifecycle hooks
    on_workflow_start: list[Callable[[Workflow], Awaitable[None]]]
    on_step_start: list[Callable[[Step], Awaitable[None]]]
    on_step_complete: list[Callable[[Step, Result], Awaitable[None]]]
    on_workflow_complete: list[Callable[[Workflow, Result], Awaitable[None]]]
    on_error: list[Callable[[Exception], Awaitable[None]]]

    # Decision hooks
    should_continue: Callable[[Step, Result], Awaitable[bool]]
    should_retry: Callable[[Step, Exception], Awaitable[bool]]
```

### 3. Plugin Architecture

Design for third-party extensions:

```python
# Plugin registration
@paracle.register_provider("my-llm")
class MyLLMProvider:
    ...

@paracle.register_tool("custom-search")
class CustomSearchTool:
    ...

@paracle.register_policy("my-company-rules")
class MyCompanyPolicy:
    ...
```

---

## Versioning & Compatibility

### 1. Semantic Versioning

```text
MAJOR.MINOR.PATCH

MAJOR: Breaking changes (removed/renamed APIs, changed behavior)
MINOR: New features (backward compatible)
PATCH: Bug fixes (backward compatible)
```

### 2. Deprecation Strategy

```python
import warnings

def old_method(self, arg):
    """Deprecated: Use new_method() instead."""
    warnings.warn(
        "old_method() is deprecated and will be removed in v2.0. "
        "Use new_method() instead.",
        DeprecationWarning,
        stacklevel=2
    )
    return self.new_method(arg)
```

### 3. Feature Flags

```python
class ParacleConfig:
    """Feature flags for gradual rollout."""

    # Experimental features (may change)
    enable_experimental_rag: bool = False
    enable_experimental_multi_agent_chat: bool = False

    # Beta features (stable API, may have bugs)
    enable_beta_workflow_visualization: bool = False

    # Deprecated features (will be removed)
    enable_legacy_agent_format: bool = True  # Remove in v2.0
```

---

## Error Handling Philosophy

### 1. Fail Fast, Fail Loud

```python
class AgentFactory:
    def create(self, spec: AgentSpec) -> Agent:
        # Validate immediately
        self._validate_spec(spec)
        self._validate_parent_exists(spec)
        self._validate_no_circular_inheritance(spec)
        self._validate_tools_available(spec)

        # Only then create
        return self._build_agent(spec)
```

### 2. Rich Error Context

```python
class ParacleError(Exception):
    """Base exception with rich context."""

    def __init__(
        self,
        message: str,
        *,
        code: str,
        context: dict[str, Any] | None = None,
        suggestion: str | None = None
    ):
        super().__init__(message)
        self.code = code
        self.context = context or {}
        self.suggestion = suggestion

class CircularInheritanceError(ParacleError):
    def __init__(self, chain: list[str]):
        super().__init__(
            f"Circular inheritance detected: {' -> '.join(chain)}",
            code="AGENT_CIRCULAR_INHERITANCE",
            context={"inheritance_chain": chain},
            suggestion="Remove the circular dependency by updating parent references"
        )
```

### 3. Recoverable vs Fatal

```python
# Recoverable: Retry or fallback possible
class ProviderTemporarilyUnavailable(ParacleError):
    """Provider is temporarily unavailable. Retry is appropriate."""
    recoverable = True

# Fatal: Cannot continue
class InvalidAgentSpecification(ParacleError):
    """Agent specification is invalid. Cannot proceed."""
    recoverable = False
```

---

## Performance Considerations

### 1. Lazy by Default

```python
class Agent:
    @cached_property
    def resolved_spec(self) -> AgentSpec:
        """Resolve inheritance only when needed."""
        return self._resolve_inheritance()

    @cached_property
    def provider(self) -> LLMProvider:
        """Initialize provider only when first used."""
        return self._create_provider()
```

### 2. Batch Operations

```python
class AgentRepository:
    # Single item
    async def get(self, id: str) -> Agent | None:
        ...

    # Batch operation (more efficient)
    async def get_many(self, ids: list[str]) -> list[Agent]:
        ...

    # Bulk operation
    async def save_many(self, agents: list[Agent]) -> None:
        ...
```

### 3. Streaming First

```python
class LLMProvider(Protocol):
    # Streaming is the primary interface
    async def stream(
        self,
        messages: list[Message],
        **kwargs
    ) -> AsyncIterator[StreamChunk]:
        ...

    # Non-streaming is built on streaming
    async def complete(
        self,
        messages: list[Message],
        **kwargs
    ) -> CompletionResult:
        chunks = []
        async for chunk in self.stream(messages, **kwargs):
            chunks.append(chunk)
        return CompletionResult.from_chunks(chunks)
```

---

## Documentation Standards

### 1. Every Public API Documented

```python
def resolve_inheritance(
    spec: AgentSpec,
    registry: AgentRegistry
) -> AgentSpec:
    """Resolve agent inheritance chain and merge properties.

    Walks the parent chain from the given spec to the root,
    merging properties at each level. Child properties override
    parent properties.

    Args:
        spec: The agent specification to resolve.
        registry: Registry containing all agent definitions.

    Returns:
        A new AgentSpec with all inherited properties merged.
        The returned spec has no parent (fully resolved).

    Raises:
        AgentNotFoundError: If a parent agent doesn't exist in registry.
        CircularInheritanceError: If a circular dependency is detected.

    Example:
        >>> base = AgentSpec(name="base", model="gpt-4", temperature=0.7)
        >>> child = AgentSpec(name="child", parent="base", temperature=0.3)
        >>> registry = AgentRegistry([base, child])
        >>> resolved = resolve_inheritance(child, registry)
        >>> resolved.model
        'gpt-4'
        >>> resolved.temperature
        0.3

    Note:
        The resolution is deterministic: given the same inputs,
        it will always produce the same output.
    """
```

### 2. Architecture Decision Records

Every significant decision gets an ADR:

```markdown
# ADR-001: Use Pydantic for Domain Models

## Status
Accepted

## Context
We need a way to define and validate domain models.

## Decision
Use Pydantic BaseModel for all domain entities.

## Consequences
- (+) Built-in validation
- (+) Automatic JSON serialization
- (+) Type hints as documentation
- (-) Runtime overhead for validation
- (-) Learning curve for team
```
