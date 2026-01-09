# Configuration Guide

This guide covers all configuration options for `paracle_meta`.

## Configuration Sources

Configuration is loaded from multiple sources (in order of precedence):

1. **Environment variables** (highest priority) - `PARACLE_META_*` prefix
2. **`.env` file** - Local environment file
3. **System config** - Platform-specific location
4. **Project config** - `.parac/config/meta_agent.yaml`
5. **Default values** (lowest priority)

## Configuration File Locations

### System-Level Config

Platform-specific paths:

| Platform | Path |
|----------|------|
| Linux | `~/.config/paracle/meta.yaml` |
| macOS | `~/Library/Application Support/Paracle/meta.yaml` |
| Windows | `%APPDATA%\Paracle\meta.yaml` |

### Project-Level Config

```
.parac/config/meta_agent.yaml
```

## Complete Configuration Example

```yaml
# meta_agent.yaml
meta_agent:
  # Database Configuration
  database:
    # PostgreSQL with pgvector (recommended for production)
    postgres_url: "postgresql://user:pass@localhost/paracle_meta"
    pool_size: 10
    pool_recycle: 3600
    enable_vectors: true
    vector_dimensions: 1536

    # Embedding settings
    embedding_provider: openai  # or "ollama" for local
    openai_model: text-embedding-3-small
    ollama_model: nomic-embed-text
    ollama_url: "http://localhost:11434"

  # Provider Configuration
  providers:
    - name: anthropic
      model: claude-sonnet-4-20250514
      api_key: ${ANTHROPIC_API_KEY}  # Use env var
      use_for: [agents, security, code]
      max_tokens: 4096
      temperature: 0.7

    - name: openai
      model: gpt-4o
      api_key: ${OPENAI_API_KEY}
      use_for: [documentation, embeddings]

    - name: ollama
      model: llama3.1
      base_url: "http://localhost:11434"
      use_for: [quick-tasks]

  default_provider: anthropic

  # Learning Configuration
  learning:
    enabled: true
    feedback_collection: true
    min_feedback_for_promotion: 3
    min_rating_for_promotion: 4.0
    min_quality_for_promotion: 8.0

  # Cost Configuration
  cost:
    enabled: true
    max_daily_budget: 10.0
    max_monthly_budget: 100.0
    warning_threshold: 0.8
    fallback_on_limit: true

  # Quality Configuration
  quality:
    min_quality_score: 7.0
    auto_retry_on_low_quality: true
    max_retries: 2

  # Retry Configuration
  retry:
    max_attempts: 3
    base_delay: 1.0
    max_delay: 30.0
    exponential_base: 2.0
    jitter: true

  # Circuit Breaker Configuration
  circuit_breaker:
    enabled: true
    failure_threshold: 5
    reset_timeout: 60.0
    half_open_max_calls: 3

  # Feature Flags
  enable_web_capabilities: false
  enable_code_execution: false
  enable_mcp_integration: false
  enable_agent_spawning: false
```

## Environment Variables

All configuration can be set via environment variables with `PARACLE_META_` prefix:

```bash
# Database
PARACLE_META_POSTGRES_URL=postgresql://user:pass@localhost/paracle_meta

# Default provider
PARACLE_META_DEFAULT_PROVIDER=anthropic

# Cost limits
PARACLE_META_MAX_DAILY_BUDGET=10.0
PARACLE_META_MAX_MONTHLY_BUDGET=100.0

# Learning
PARACLE_META_LEARNING_ENABLED=true
PARACLE_META_MIN_RATING_FOR_PROMOTION=4.0

# Feature flags
PARACLE_META_ENABLE_WEB_CAPABILITIES=false
PARACLE_META_ENABLE_CODE_EXECUTION=false

# Nested values use double underscore
PARACLE_META_DATABASE__POOL_SIZE=10
PARACLE_META_COST__WARNING_THRESHOLD=0.8
```

## Configuration Classes

### MetaEngineConfig

Main configuration class:

```python
from paracle_meta.config import MetaEngineConfig, load_config

# Load from all sources
config = load_config()

# Or create with specific values
config = MetaEngineConfig(
    default_provider="anthropic",
    cost=CostConfig(max_daily_budget=10.0),
)

# Access nested config
print(config.database.postgres_url)
print(config.learning.min_rating_for_promotion)
```

### ProviderConfig

Per-provider settings:

```python
from paracle_meta.config import ProviderConfig

provider = ProviderConfig(
    name="anthropic",
    model="claude-sonnet-4-20250514",
    api_key="sk-ant-...",
    use_for=["agents", "security"],
    max_tokens=4096,
    temperature=0.7,
)
```

### LearningConfig

Learning engine settings:

```python
from paracle_meta.config import LearningConfig

learning = LearningConfig(
    enabled=True,
    feedback_collection=True,
    min_feedback_for_promotion=3,
    min_rating_for_promotion=4.0,
    min_quality_for_promotion=8.0,
)
```

### CostConfig

Cost optimization settings:

```python
from paracle_meta.config import CostConfig

cost = CostConfig(
    enabled=True,
    max_daily_budget=10.0,
    max_monthly_budget=100.0,
    warning_threshold=0.8,
    fallback_on_limit=True,
)
```

## Validation

Configuration is validated automatically using Pydantic:

```python
from paracle_meta.config import validate_config, load_config

config = load_config()
warnings = validate_config(config)

for warning in warnings:
    print(f"Warning: {warning}")
```

Common validation warnings:

- "PostgreSQL URL is empty"
- "Vector search not available in SQLite mode"
- "No providers configured"
- "No API key for default provider"
- "High daily budget: $100. Consider setting a lower limit."

## Provider Selection

Providers can be selected based on task type:

```python
config = load_config()

# Get provider for specific task
agent_provider = config.get_provider_for_task("agents")
doc_provider = config.get_provider_for_task("documentation")

# Get specific provider by name
anthropic = config.get_provider_config("anthropic")
```

## Feature Flags

Control experimental features:

| Flag | Description | Default |
|------|-------------|---------|
| `enable_web_capabilities` | Web search and crawling | `false` |
| `enable_code_execution` | Execute code in sandbox | `false` |
| `enable_mcp_integration` | MCP tool integration | `false` |
| `enable_agent_spawning` | Spawn sub-agents | `false` |

## Database Configuration

### SQLite (Default)

No configuration needed - uses local file storage:

```
~/.local/share/paracle/meta/  # Linux
%LOCALAPPDATA%\Paracle\meta\  # Windows
~/Library/Application Support/Paracle/meta/  # macOS
```

### PostgreSQL with pgvector

For production with vector search:

```yaml
database:
  postgres_url: "postgresql://user:pass@localhost/paracle_meta"
  pool_size: 10
  enable_vectors: true
  embedding_provider: openai
```

Required PostgreSQL extensions:

```sql
CREATE EXTENSION IF NOT EXISTS vector;
```

## Best Practices

1. **Use environment variables for secrets** - Never commit API keys
2. **Start with SQLite** - Upgrade to PostgreSQL for production
3. **Set cost limits** - Prevent runaway spending
4. **Enable learning gradually** - Start with feedback collection
5. **Use provider fallback** - Configure multiple providers for resilience
