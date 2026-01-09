# API Reference

Python API documentation for `paracle_meta`.

## Core Classes

### MetaAgent

Main entry point for the meta engine.

```python
from paracle_meta import MetaAgent

async with MetaAgent() as meta:
    # Generate artifacts
    agent = await meta.generate_agent(name="...", description="...")
    workflow = await meta.generate_workflow(name="...", description="...")
    skill = await meta.generate_skill(name="...", description="...")
    policy = await meta.generate_policy(name="...", description="...")

    # Record feedback
    await meta.record_feedback(agent.id, rating=5, comment="Great!")

    # Get statistics
    stats = await meta.get_stats()
```

**Constructor Parameters:**

| Parameter | Type | Default | Description |
| --------- | ---- | ------- | ----------- |
| `config` | `MetaEngineConfig` | `None` | Configuration (auto-loaded if None) |
| `provider` | `str` | `"anthropic"` | Default LLM provider |

**Methods:**

| Method | Returns | Description |
| ------ | ------- | ----------- |
| `generate_agent(name, description)` | `GenerationResult` | Generate agent spec |
| `generate_workflow(name, description)` | `GenerationResult` | Generate workflow |
| `generate_skill(name, description)` | `GenerationResult` | Generate skill |
| `generate_policy(name, description)` | `GenerationResult` | Generate policy |
| `record_feedback(gen_id, rating, comment)` | `None` | Submit feedback |
| `get_stats()` | `dict` | Get usage statistics |

---

### GenerationRequest

Request for artifact generation.

```python
from paracle_meta import GenerationRequest

request = GenerationRequest(
    artifact_type="agent",
    name="SecurityAuditor",
    description="Reviews code for security issues",
    requirements=["Python expertise", "OWASP knowledge"],
    constraints={"max_tokens": 4096},
    context={"project_type": "web_api"},
)
```

**Fields:**

| Field | Type | Required | Description |
| ----- | ---- | -------- | ----------- |
| `artifact_type` | `str` | Yes | Type: agent, workflow, skill, policy |
| `name` | `str` | Yes | Artifact name |
| `description` | `str` | Yes | Natural language description |
| `requirements` | `list[str]` | No | Specific requirements |
| `constraints` | `dict` | No | Generation constraints |
| `context` | `dict` | No | Additional context |

---

### GenerationResult

Result from artifact generation.

```python
result = await meta.generate_agent(...)

print(result.id)           # Unique generation ID
print(result.content)      # Generated YAML content
print(result.quality_score) # Quality score 0-10
print(result.tokens_used)  # Tokens consumed
print(result.cost)         # Cost in USD
```

**Fields:**

| Field | Type | Description |
| ----- | ---- | ----------- |
| `id` | `str` | Unique generation ID |
| `artifact_type` | `str` | Type of artifact |
| `name` | `str` | Artifact name |
| `content` | `str` | Generated content (YAML) |
| `quality_score` | `float` | Quality score (0-10) |
| `provider` | `str` | Provider used |
| `model` | `str` | Model used |
| `tokens_used` | `int` | Total tokens |
| `cost` | `float` | Cost in USD |
| `created_at` | `datetime` | Creation timestamp |
| `metadata` | `dict` | Additional metadata |

---

## Configuration

### MetaEngineConfig

Main configuration class.

```python
from paracle_meta import MetaEngineConfig, load_config

# Load from all sources
config = load_config()

# Or create manually
config = MetaEngineConfig(
    default_provider="anthropic",
    cost=CostConfig(max_daily_budget=10.0),
    learning=LearningConfig(enabled=True),
)
```

**Fields:**

| Field | Type | Default | Description |
| ----- | ---- | ------- | ----------- |
| `database` | `MetaDatabaseConfig` | `MetaDatabaseConfig()` | Database settings |
| `providers` | `list[ProviderConfig]` | `[]` | Provider configs |
| `default_provider` | `str` | `"anthropic"` | Default provider |
| `learning` | `LearningConfig` | `LearningConfig()` | Learning settings |
| `cost` | `CostConfig` | `CostConfig()` | Cost settings |
| `quality` | `QualityConfig` | `QualityConfig()` | Quality settings |
| `retry` | `RetryConfig` | `RetryConfig()` | Retry settings |
| `circuit_breaker` | `CircuitBreakerConfig` | `CircuitBreakerConfig()` | Circuit breaker |

**Methods:**

| Method | Returns | Description |
| ------ | ------- | ----------- |
| `get_provider_config(name)` | `ProviderConfig` | Get provider by name |
| `get_provider_for_task(task_type)` | `ProviderConfig` | Get provider for task |

---

### load_config

Load configuration from all sources.

```python
from paracle_meta import load_config

# Load with defaults
config = load_config()

# Load with custom paths
config = load_config(
    project_path=Path(".parac/config/meta_agent.yaml"),
    system_path=Path("~/.config/paracle/meta.yaml"),
)
```

---

### validate_config

Validate configuration and return warnings.

```python
from paracle_meta import validate_config

warnings = validate_config(config)
for warning in warnings:
    print(f"Warning: {warning}")
```

---

## Providers

### CapabilityProvider Protocol

Interface for LLM providers.

```python
from paracle_meta import CapabilityProvider, LLMRequest, LLMResponse

class CustomProvider(CapabilityProvider):
    @property
    def name(self) -> str:
        return "custom"

    @property
    def status(self) -> ProviderStatus:
        return self._status

    async def complete(self, request: LLMRequest) -> LLMResponse:
        # Implementation
        pass

    async def stream(self, request: LLMRequest) -> AsyncIterator[StreamChunk]:
        # Implementation
        pass

    async def health_check(self) -> bool:
        return True
```

---

### AnthropicProvider

Anthropic Claude provider.

```python
from paracle_meta.capabilities.providers import AnthropicProvider

provider = AnthropicProvider(
    api_key="sk-ant-...",
    model="claude-sonnet-4-20250514",
    max_tokens=4096,
)

response = await provider.complete(LLMRequest(
    messages=[LLMMessage(role="user", content="Hello!")],
    temperature=0.7,
))
```

---

### OpenAIProvider

OpenAI GPT provider.

```python
from paracle_meta.capabilities.providers import OpenAIProvider

provider = OpenAIProvider(
    api_key="sk-...",
    model="gpt-4o",
)
```

---

### OllamaProvider

Local Ollama provider.

```python
from paracle_meta.capabilities.providers import OllamaProvider

provider = OllamaProvider(
    model="llama3.1",
    base_url="http://localhost:11434",
)
```

---

### MockProvider

Testing provider.

```python
from paracle_meta.capabilities.providers import MockProvider

provider = MockProvider(
    responses=["Hello!", "How can I help?"],
)
```

---

## Sessions

### ChatSession

Interactive chat session.

```python
from paracle_meta import ChatSession, ChatConfig

config = ChatConfig(
    max_history=100,
    save_history=True,
    tools_enabled=True,
)

async with ChatSession(provider, config) as chat:
    response = await chat.send("Hello!")
    print(response.content)

    # Save session
    session_id = await chat.save()

# Resume session
async with ChatSession.resume(session_id, provider) as chat:
    response = await chat.send("Continue...")
```

---

### PlanSession

Task planning session.

```python
from paracle_meta import PlanSession, PlanConfig

config = PlanConfig(
    max_steps=10,
    require_approval=True,
)

async with PlanSession(provider, config) as planner:
    plan = await planner.create_plan("Build a REST API")

    for step in plan.steps:
        print(f"- {step.title}")

    await planner.approve(plan)
    result = await planner.execute(plan)
```

---

### EditSession

File editing session.

```python
from paracle_meta import EditSession, EditConfig, EditOperation, EditType

config = EditConfig(
    auto_apply=False,
    create_backup=True,
)

async with EditSession(provider, config) as editor:
    editor.add_operation(EditOperation(
        file_path="src/main.py",
        edit_type=EditType.REPLACE,
        old_text="old_function",
        new_text="new_function",
    ))

    preview = await editor.preview()
    result = await editor.apply()
```

---

## Database

### MetaDatabase

Database connection manager.

```python
from paracle_meta import MetaDatabase, MetaDatabaseConfig

config = MetaDatabaseConfig(
    postgres_url="postgresql://user:pass@localhost/db",
    pool_size=10,
    enable_vectors=True,
)

db = MetaDatabase(config)

async with db.session() as session:
    result = await session.execute("SELECT 1")
```

---

### get_meta_database

Get configured database instance.

```python
from paracle_meta import get_meta_database

db = get_meta_database(config.database)
```

---

## Repositories

### GenerationRepository

```python
from paracle_meta import GenerationRepository

repo = GenerationRepository(db)

# Add generation
await repo.add(result)

# Get by ID
gen = await repo.get("gen-123")

# List recent
recent = await repo.list_recent(limit=10)

# Get with feedback
gen, feedback = await repo.get_with_feedback("gen-123")
```

---

### TemplateRepository

```python
from paracle_meta import TemplateRepository

repo = TemplateRepository(db)

# Find similar templates
templates = await repo.find_similar("security audit", top_k=5)

# Promote from generation
template = await repo.promote_from_generation("gen-123")
```

---

### FeedbackRepository

```python
from paracle_meta import FeedbackRepository, Feedback

repo = FeedbackRepository(db)

# Add feedback
await repo.add(Feedback(
    generation_id="gen-123",
    rating=5,
    comment="Excellent!",
))

# Get for generation
feedback_list = await repo.get_for_generation("gen-123")
```

---

### CostRepository

```python
from paracle_meta import CostRepository

repo = CostRepository(db)

# Record cost
await repo.record(
    provider="anthropic",
    input_tokens=1000,
    output_tokens=500,
    cost=0.015,
)

# Get period cost
daily = await repo.get_period_cost("daily")
monthly = await repo.get_period_cost("monthly")
```

---

## Embeddings

### EmbeddingProvider

Abstract embedding provider.

```python
from paracle_meta import EmbeddingProvider

class CustomEmbeddings(EmbeddingProvider):
    async def embed(self, text: str) -> list[float]:
        # Implementation
        pass

    async def embed_batch(self, texts: list[str]) -> list[list[float]]:
        # Implementation
        pass

    @property
    def dimensions(self) -> int:
        return 1536
```

---

### OpenAIEmbeddings

```python
from paracle_meta import OpenAIEmbeddings

embeddings = OpenAIEmbeddings(
    api_key="sk-...",
    model="text-embedding-3-small",
)

vector = await embeddings.embed("Hello world")
# Returns: list[float] with 1536 dimensions
```

---

### OllamaEmbeddings

```python
from paracle_meta import OllamaEmbeddings

embeddings = OllamaEmbeddings(
    model="nomic-embed-text",
    base_url="http://localhost:11434",
)

vector = await embeddings.embed("Hello world")
# Returns: list[float] with 768 dimensions
```

---

## Health Checks

### check_health

Run comprehensive health check.

```python
from paracle_meta import check_health

health = await check_health(config)

print(health.status)      # HEALTHY, DEGRADED, UNHEALTHY
print(health.database)    # Database status
print(health.providers)   # Provider statuses
print(health.cost_within_budget)
```

---

### HealthChecker

Health checker class.

```python
from paracle_meta import HealthChecker

checker = HealthChecker(config)

# Full check
health = await checker.check()

# Individual checks
db_health = await checker.check_database()
provider_health = await checker.check_providers()
```

---

### format_health_report

Format health check as string.

```python
from paracle_meta import format_health_report

report = format_health_report(health)
print(report)
```

---

## Learning

### LearningEngine

Learning and improvement engine.

```python
from paracle_meta import LearningEngine

engine = LearningEngine(config.learning, db)

# Record feedback
await engine.record_feedback("gen-123", rating=5)

# Check for promotion
if await engine.should_promote("gen-123"):
    template = await engine.promote_to_template("gen-123")
```

---

### FeedbackCollector

Collect user feedback.

```python
from paracle_meta import FeedbackCollector

collector = FeedbackCollector(db)

# Collect feedback
await collector.collect(
    generation_id="gen-123",
    rating=5,
    comment="Great result!",
    tags=["accurate", "well-formatted"],
)
```

---

## Optimization

### CostOptimizer

Track and optimize costs.

```python
from paracle_meta import CostOptimizer

optimizer = CostOptimizer(config.cost, db)

# Record usage
await optimizer.record_usage(
    provider="anthropic",
    input_tokens=1000,
    output_tokens=500,
)

# Check limits
if optimizer.at_warning_threshold():
    print("Approaching budget limit!")

if optimizer.at_limit():
    print("Budget exceeded!")
```

---

### QualityScorer

Score generation quality.

```python
from paracle_meta import QualityScorer

scorer = QualityScorer()

score = await scorer.score(generation_result)
# Returns: float (0-10)

if score < config.quality.min_quality_score:
    # Retry with different parameters
    pass
```

---

## Feature Flags

Check optional features availability:

```python
from paracle_meta import _HAS_DATABASE, _HAS_EMBEDDINGS

if _HAS_DATABASE:
    # SQLAlchemy is available
    from paracle_meta import MetaDatabase
else:
    print("Database features not available")

if _HAS_EMBEDDINGS:
    # Embedding providers available
    from paracle_meta import OpenAIEmbeddings
```

---

## Exceptions

```python
from paracle_meta.exceptions import (
    MetaError,           # Base exception
    ProviderError,       # LLM provider error
    DatabaseError,       # Database error
    ConfigError,         # Configuration error
    CostLimitError,      # Budget exceeded
    QualityError,        # Quality too low
    ValidationError,     # Validation failed
)
```
