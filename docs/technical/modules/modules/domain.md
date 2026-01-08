# paracle_domain

> Business models and domain logic for the Paracle framework

## Purpose

The `paracle_domain` module contains all domain models, business logic, and validation rules for Paracle. It implements the **Domain Layer** in the hexagonal architecture, providing a clean, framework-agnostic representation of agents, workflows, tools, and other core entities.

**Key Principle**: Domain models are **pure Python** with no infrastructure dependencies, making them highly testable and portable.

## Key Components

### 1. Agent Models

**Agent Specification and Runtime**

```python
from paracle_domain.models import AgentSpec, Agent

# Agent specification (design-time)
agent_spec = AgentSpec(
    name="code-reviewer",
    role="Code quality expert",
    provider="openai",
    model="gpt-4",
    temperature=0.3,
    instructions="Review code for bugs and best practices",
    tools=["filesystem_read", "grep_search"],
    parent="base-developer"  # Inheritance
)

# Agent instance (runtime)
agent = Agent.from_spec(agent_spec)
```

**Key Fields**:

- `name` (str) - Unique identifier
- `role` (str) - Agent's purpose
- `provider` (str) - LLM provider (openai, anthropic, etc.)
- `model` (str) - Model name (gpt-4, claude-3-opus, etc.)
- `instructions` (str) - System prompt
- `tools` (List[str]) - Available tools
- `parent` (Optional[str]) - Parent agent for inheritance
- `temperature`, `max_tokens`, `top_p` - LLM parameters

### 2. Workflow Models

**Workflow Definition and Execution**

```python
from paracle_domain.models import WorkflowSpec, WorkflowStep

# Workflow specification
workflow_spec = WorkflowSpec(
    name="code-review-workflow",
    description="Multi-agent code review process",
    steps=[
        WorkflowStep(
            id="analyze",
            agent="static-analyzer",
            task="Analyze code for issues",
            inputs={"file": "${workflow.input.file}"}
        ),
        WorkflowStep(
            id="review",
            agent="code-reviewer",
            task="Review analysis results",
            depends_on=["analyze"],
            inputs={"analysis": "${steps.analyze.output}"}
        )
    ],
    inputs={"file": "str"},
    outputs={"review": "${steps.review.output}"}
)
```

**Key Features**:

- Dependency management (DAG)
- Variable interpolation
- Input/output typing
- Conditional execution
- Parallel steps

### 3. Tool Models

**Tool Definition and Schema**

```python
from paracle_domain.models import ToolSpec, ToolParameter

# Tool specification
tool_spec = ToolSpec(
    name="filesystem_read",
    description="Read file contents",
    parameters=[
        ToolParameter(
            name="path",
            type="string",
            description="File path to read",
            required=True
        ),
        ToolParameter(
            name="encoding",
            type="string",
            description="File encoding",
            default="utf-8"
        )
    ],
    returns={
        "type": "object",
        "properties": {
            "content": {"type": "string"},
            "size": {"type": "integer"}
        }
    }
)
```

**Tool Categories**:

- **Filesystem**: Read, write, list files
- **Network**: HTTP requests, API calls
- **Shell**: Execute commands
- **Search**: Grep, semantic search
- **Git**: Repository operations
- **Database**: Query, update

### 4. Provider Models

**LLM Provider Configuration**

```python
from paracle_domain.models import ProviderConfig

# Provider configuration
provider_config = ProviderConfig(
    name="openai",
    api_key="sk-...",
    base_url="https://api.openai.com/v1",
    default_model="gpt-4",
    max_retries=3,
    timeout=60.0,
    rate_limit={
        "requests_per_minute": 60,
        "tokens_per_minute": 150000
    }
)
```

**Supported Providers**:

- OpenAI (GPT-4, GPT-3.5)
- Anthropic (Claude 3)
- Google (Gemini)
- xAI (Grok)
- DeepSeek
- Groq
- Mistral
- Together
- Perplexity
- Cohere
- OpenRouter
- Fireworks
- Ollama (local)

### 5. Memory Models

**Context and History**

```python
from paracle_domain.models import Context, Message, MemoryEntry

# Conversation context
context = Context(
    id="ctx_01HQZYX...",
    agent_id="agent_01HQZYX...",
    messages=[
        Message(role="user", content="Review this code"),
        Message(role="assistant", content="I found 3 issues...")
    ],
    metadata={
        "session_id": "session_123",
        "user_id": "user_456"
    }
)

# Long-term memory
memory_entry = MemoryEntry(
    id="mem_01HQZYX...",
    agent_id="agent_01HQZYX...",
    content="User prefers type hints in all functions",
    embedding=[0.1, 0.2, ...],  # Vector representation
    metadata={"category": "coding_style"}
)
```

### 6. Event Models

**Domain Events**

```python
from paracle_domain.events import (
    AgentCreated,
    AgentExecutionStarted,
    AgentExecutionCompleted,
    WorkflowStarted,
    WorkflowStepCompleted
)

# Agent execution events
event = AgentExecutionStarted(
    agent_id="agent_01HQZYX...",
    task="Review code",
    timestamp="2026-01-07T10:30:00Z"
)
```

**Event Types**:

- Agent lifecycle events
- Workflow execution events
- Tool invocation events
- Error events
- Cost tracking events

### 7. Validation Models

**Input/Output Validation**

```python
from paracle_domain.validation import (
    validate_agent_spec,
    validate_workflow_spec,
    ValidationError
)

# Validate agent specification
try:
    validate_agent_spec(agent_spec)
except ValidationError as e:
    print(f"Invalid agent: {e.errors}")
```

## Module Structure

```
paracle_domain/
├── __init__.py           # Public exports
├── models/               # Domain models
│   ├── __init__.py
│   ├── agent.py         # Agent models
│   ├── workflow.py      # Workflow models
│   ├── tool.py          # Tool models
│   ├── provider.py      # Provider models
│   ├── memory.py        # Memory models
│   └── common.py        # Shared types
├── events/              # Domain events
│   ├── __init__.py
│   ├── agent.py
│   ├── workflow.py
│   └── base.py
├── validation/          # Validation logic
│   ├── __init__.py
│   ├── agent.py
│   ├── workflow.py
│   └── errors.py
└── types.py             # Type definitions
```

## Usage Examples

### Creating an Agent with Inheritance

```python
from paracle_domain.models import AgentSpec

# Base agent
base = AgentSpec(
    name="base-developer",
    provider="openai",
    model="gpt-4",
    temperature=0.7,
    instructions="You are a helpful coding assistant",
    tools=["filesystem_read", "filesystem_write"]
)

# Specialized agent (inherits from base)
python_expert = AgentSpec(
    name="python-expert",
    parent="base-developer",
    instructions="You are a Python expert. Focus on type hints and best practices.",
    tools=["python_ast_parser"],  # Adds to inherited tools
    temperature=0.3  # Overrides base value
)
```

### Building a Workflow

```python
from paracle_domain.models import WorkflowSpec, WorkflowStep

workflow = WorkflowSpec(
    name="feature-development",
    description="Develop, test, and document a feature",
    steps=[
        WorkflowStep(
            id="architect",
            agent="system-architect",
            task="Design the feature architecture",
            inputs={"requirements": "${workflow.input.requirements}"}
        ),
        WorkflowStep(
            id="implement",
            agent="coder",
            task="Implement the feature",
            depends_on=["architect"],
            inputs={"design": "${steps.architect.output}"}
        ),
        WorkflowStep(
            id="test",
            agent="tester",
            task="Write tests for the feature",
            depends_on=["implement"],
            inputs={"code": "${steps.implement.output}"}
        ),
        WorkflowStep(
            id="document",
            agent="documenter",
            task="Write documentation",
            depends_on=["implement", "test"],
            inputs={
                "code": "${steps.implement.output}",
                "tests": "${steps.test.output}"
            }
        )
    ],
    inputs={"requirements": "str"},
    outputs={
        "code": "${steps.implement.output}",
        "tests": "${steps.test.output}",
        "docs": "${steps.document.output}"
    }
)
```

### Defining Custom Tools

```python
from paracle_domain.models import ToolSpec, ToolParameter

search_tool = ToolSpec(
    name="semantic_search",
    description="Search codebase using semantic similarity",
    parameters=[
        ToolParameter(
            name="query",
            type="string",
            description="Search query",
            required=True
        ),
        ToolParameter(
            name="max_results",
            type="integer",
            description="Maximum number of results",
            default=10
        ),
        ToolParameter(
            name="threshold",
            type="number",
            description="Similarity threshold (0-1)",
            default=0.7
        )
    ],
    returns={
        "type": "array",
        "items": {
            "type": "object",
            "properties": {
                "file": {"type": "string"},
                "line": {"type": "integer"},
                "content": {"type": "string"},
                "score": {"type": "number"}
            }
        }
    },
    metadata={
        "category": "search",
        "requires_embeddings": True
    }
)
```

## Dependencies

**Required Packages**:

```toml
[project.dependencies]
pydantic = "^2.5"           # Data validation
pydantic-settings = "^2.1"  # Settings management
typing-extensions = "^4.9"  # Type hints
```

**Internal Dependencies**:

- `paracle_core` - Utilities, IDs, configuration

**No External Infrastructure**:

- ❌ No database dependencies
- ❌ No API client dependencies
- ❌ No framework dependencies

## Design Principles

### 1. Framework-Agnostic

Domain models don't depend on FastAPI, Click, or any framework:

```python
# ✅ Good - Pure domain model
class Agent(BaseModel):
    name: str
    role: str
    provider: str

# ❌ Bad - Framework coupling
class Agent(BaseModel):
    name: str
    role: str
    request: FastAPIRequest  # Don't do this!
```

### 2. Immutability

Domain models are immutable by default:

```python
from pydantic import BaseModel

class AgentSpec(BaseModel):
    name: str

    class Config:
        frozen = True  # Immutable

# Usage
agent = AgentSpec(name="test")
agent.name = "new"  # ❌ Raises error
```

### 3. Validation

All inputs validated with Pydantic:

```python
class AgentSpec(BaseModel):
    name: str = Field(min_length=1, max_length=100)
    temperature: float = Field(ge=0.0, le=2.0)
    model: str = Field(pattern=r'^[a-z0-9-]+$')

    @field_validator('provider')
    def validate_provider(cls, v):
        if v not in SUPPORTED_PROVIDERS:
            raise ValueError(f"Unsupported provider: {v}")
        return v
```

### 4. Type Safety

Strong typing throughout:

```python
from typing import List, Optional, Dict, Any
from paracle_domain.types import AgentID, WorkflowID

class Agent:
    id: AgentID  # Not just 'str'
    parent: Optional[AgentID]
    tools: List[str]
    metadata: Dict[str, Any]
```

### 5. Business Logic in Domain

Keep business rules in domain layer:

```python
class WorkflowSpec(BaseModel):
    steps: List[WorkflowStep]

    def get_execution_order(self) -> List[str]:
        """Calculate step execution order (topological sort)."""
        # Business logic here, not in infrastructure
        return topological_sort(self.steps)

    def validate_dependencies(self) -> None:
        """Validate no circular dependencies."""
        # Domain validation
        if has_cycle(self.steps):
            raise CircularDependencyError()
```

## Testing

### Unit Tests

```python
import pytest
from paracle_domain.models import AgentSpec

def test_agent_spec_validation():
    # Valid agent
    agent = AgentSpec(
        name="test",
        provider="openai",
        model="gpt-4"
    )
    assert agent.name == "test"

def test_agent_spec_invalid_temperature():
    # Invalid temperature
    with pytest.raises(ValidationError):
        AgentSpec(
            name="test",
            provider="openai",
            model="gpt-4",
            temperature=3.0  # > 2.0
        )

def test_agent_inheritance():
    base = AgentSpec(name="base", provider="openai", model="gpt-4")
    child = AgentSpec(name="child", parent="base", temperature=0.3)

    # Test inheritance resolution
    resolved = child.resolve_inheritance(base)
    assert resolved.provider == "openai"  # Inherited
    assert resolved.temperature == 0.3     # Overridden
```

### Property-Based Tests

```python
from hypothesis import given
from hypothesis.strategies import text, floats

@given(
    name=text(min_size=1, max_size=100),
    temperature=floats(min_value=0.0, max_value=2.0)
)
def test_agent_spec_properties(name, temperature):
    agent = AgentSpec(
        name=name,
        provider="openai",
        model="gpt-4",
        temperature=temperature
    )
    assert agent.temperature >= 0.0
    assert agent.temperature <= 2.0
```

## Environment Variables

None - Domain layer doesn't read environment variables directly. Configuration comes from `paracle_core.Settings`.

## See Also

- [paracle_core](core.md) - Core utilities
- [paracle_store](store.md) - Persistence
- [paracle_orchestration](orchestration.md) - Workflow execution
- [Agent Concepts](../concepts/agents.md) - Agent guide
- [Workflow Guide](../workflow-guide.md) - Workflow patterns

---

**Module Type**: Domain (Core)
**Dependencies**: paracle_core
**Dependents**: All other modules
**Status**: Stable
**Version**: 0.0.1
