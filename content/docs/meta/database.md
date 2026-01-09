# Database Guide

Persistent storage and vector search for `paracle_meta`.

## Overview

`paracle_meta` supports two database backends:

| Backend | Use Case | Features |
|---------|----------|----------|
| **SQLite** | Development, single-user | Zero config, local file |
| **PostgreSQL + pgvector** | Production, multi-user | Vector search, scaling |

## SQLite (Default)

No configuration needed. Data is stored locally:

| Platform | Location |
|----------|----------|
| Linux | `~/.local/share/paracle/meta/` |
| macOS | `~/Library/Application Support/Paracle/meta/` |
| Windows | `%LOCALAPPDATA%\Paracle\meta\` |

**Files:**
- `generations.db` - Generation history
- `templates.db` - Template library
- `feedback.db` - User feedback
- `costs.db` - Cost tracking
- `memory.db` - Session memory
- `best_practices.db` - Knowledge base

## PostgreSQL + pgvector

For production with vector similarity search.

### Setup

1. **Install PostgreSQL with pgvector:**

```bash
# Ubuntu/Debian
sudo apt install postgresql postgresql-contrib
sudo apt install postgresql-14-pgvector

# macOS
brew install postgresql pgvector

# Docker (recommended)
docker run -d \
  --name paracle-postgres \
  -e POSTGRES_USER=paracle \
  -e POSTGRES_PASSWORD=secret \
  -e POSTGRES_DB=paracle_meta \
  -p 5432:5432 \
  pgvector/pgvector:pg16
```

2. **Enable pgvector extension:**

```sql
CREATE EXTENSION IF NOT EXISTS vector;
```

3. **Configure connection:**

```yaml
# .parac/config/meta_agent.yaml
meta_agent:
  database:
    postgres_url: "postgresql://paracle:secret@localhost:5432/paracle_meta"
    pool_size: 10
    pool_recycle: 3600
    enable_vectors: true
```

Or via environment:

```bash
PARACLE_META_POSTGRES_URL=postgresql://paracle:secret@localhost:5432/paracle_meta
```

### Schema

Tables are created automatically on first run:

```sql
-- Generations table
CREATE TABLE generations (
    id VARCHAR PRIMARY KEY,
    artifact_type VARCHAR NOT NULL,
    name VARCHAR NOT NULL,
    description TEXT,
    content TEXT NOT NULL,
    quality_score FLOAT,
    provider VARCHAR,
    model VARCHAR,
    tokens_used INTEGER,
    cost FLOAT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    metadata JSONB
);

-- Templates table (with vector)
CREATE TABLE templates (
    id VARCHAR PRIMARY KEY,
    artifact_type VARCHAR NOT NULL,
    name VARCHAR NOT NULL,
    pattern VARCHAR,
    content TEXT NOT NULL,
    quality_score FLOAT,
    usage_count INTEGER DEFAULT 0,
    source VARCHAR,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    embedding vector(1536)  -- pgvector column
);

-- Create vector index
CREATE INDEX templates_embedding_idx
ON templates USING ivfflat (embedding vector_cosine_ops);

-- Feedback table
CREATE TABLE feedback (
    id VARCHAR PRIMARY KEY,
    generation_id VARCHAR REFERENCES generations(id),
    rating INTEGER CHECK (rating >= 1 AND rating <= 5),
    comment TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Costs table
CREATE TABLE costs (
    id VARCHAR PRIMARY KEY,
    provider VARCHAR NOT NULL,
    model VARCHAR NOT NULL,
    input_tokens INTEGER,
    output_tokens INTEGER,
    cost FLOAT,
    period_type VARCHAR,  -- 'daily' or 'monthly'
    period_start DATE,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Memory table
CREATE TABLE memory (
    id VARCHAR PRIMARY KEY,
    session_id VARCHAR,
    key VARCHAR NOT NULL,
    value TEXT NOT NULL,
    scope VARCHAR DEFAULT 'session',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    expires_at TIMESTAMP
);

-- Best practices table (with vector)
CREATE TABLE best_practices (
    id VARCHAR PRIMARY KEY,
    category VARCHAR NOT NULL,
    title VARCHAR NOT NULL,
    content TEXT NOT NULL,
    tags TEXT[],
    quality_score FLOAT,
    usage_count INTEGER DEFAULT 0,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    embedding vector(1536)
);
```

## Vector Search

### Embeddings

Configure embedding provider:

```yaml
database:
  enable_vectors: true
  embedding_provider: openai  # or "ollama"

  # OpenAI settings
  openai_model: text-embedding-3-small  # 1536 dimensions

  # Ollama settings (for local)
  ollama_model: nomic-embed-text  # 768 dimensions
  ollama_url: "http://localhost:11434"
```

### Embedding Providers

```python
from paracle_meta.embeddings import (
    OpenAIEmbeddings,
    OllamaEmbeddings,
    get_embedding_provider,
)

# Auto-select based on config
provider = get_embedding_provider(config)

# Or explicit
openai_embed = OpenAIEmbeddings(
    api_key="sk-...",
    model="text-embedding-3-small",
)
embedding = await openai_embed.embed("Hello world")
# Returns: list[float] with 1536 dimensions

ollama_embed = OllamaEmbeddings(
    model="nomic-embed-text",
    base_url="http://localhost:11434",
)
embedding = await ollama_embed.embed("Hello world")
# Returns: list[float] with 768 dimensions
```

### Similarity Search

```python
from paracle_meta import MetaDatabase

db = MetaDatabase(config.database)

# Find similar templates
similar = await db.vector_search(
    collection="templates",
    query="security audit agent",
    top_k=5,
)

for template in similar:
    print(f"{template.name}: {template.similarity:.2f}")
```

## Repositories

Repository pattern for type-safe database access.

### GenerationRepository

```python
from paracle_meta import GenerationRepository, MetaDatabase

db = MetaDatabase(config.database)
repo = GenerationRepository(db)

# Save generation
await repo.add(generation_result)

# Get by ID
gen = await repo.get("gen-123")

# List recent
recent = await repo.list_recent(limit=10)

# Get with feedback
gen, feedback = await repo.get_with_feedback("gen-123")
```

### TemplateRepository

```python
from paracle_meta import TemplateRepository

repo = TemplateRepository(db)

# Find similar templates
templates = await repo.find_similar(
    description="Python security scanner",
    top_k=5,
)

# Promote from generation
template = await repo.promote_from_generation("gen-123")
```

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

# Get feedback for generation
feedback_list = await repo.get_for_generation("gen-123")
```

### CostRepository

```python
from paracle_meta import CostRepository

repo = CostRepository(db)

# Record cost
await repo.record(
    provider="anthropic",
    model="claude-sonnet-4-20250514",
    input_tokens=1000,
    output_tokens=500,
    cost=0.015,
)

# Get period cost
daily = await repo.get_period_cost("daily")
monthly = await repo.get_period_cost("monthly")

# Get detailed report
report = await repo.get_report("monthly")
```

## Database Access

### Direct Session Access

```python
from paracle_meta import get_meta_database

db = get_meta_database(config.database)

# Use session context manager
async with db.session() as session:
    result = await session.execute(
        "SELECT * FROM generations WHERE id = :id",
        {"id": "gen-123"}
    )
    row = result.fetchone()
```

### Connection Pool

```yaml
database:
  postgres_url: "postgresql://..."
  pool_size: 10        # Max connections
  pool_recycle: 3600   # Recycle connections after 1 hour
  pool_pre_ping: true  # Check connection health
```

## Migration

### SQLite to PostgreSQL

```bash
# Export from SQLite
paracle meta export --format sql > backup.sql

# Import to PostgreSQL
psql paracle_meta < backup.sql
```

### Schema Updates

Schema is managed automatically. For manual migrations:

```python
from paracle_meta.database import MetaDatabase

db = MetaDatabase(config.database)
await db.migrate()  # Apply any pending migrations
```

## Best Practices

1. **Start with SQLite** - Zero config for development
2. **Use PostgreSQL for production** - Reliability and scaling
3. **Enable pgvector** - Powerful similarity search
4. **Use OpenAI embeddings** - Best quality for semantic search
5. **Monitor pool size** - Adjust based on concurrent users
6. **Regular backups** - Use pg_dump for PostgreSQL
