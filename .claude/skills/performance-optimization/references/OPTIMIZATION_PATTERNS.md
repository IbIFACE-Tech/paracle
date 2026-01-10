# Performance Optimization Patterns

Advanced patterns for optimizing API and database performance.

## Database Optimization Patterns

### N+1 Query Problem

**Bad: N+1 queries**
```python
# Query 1: Get all agents
agents = await session.execute(select(Agent))

for agent in agents:
    # Query N: Get tools for each agent (N additional queries!)
    tools = await session.execute(
        select(Tool).where(Tool.agent_id == agent.id)
    )
```

**Good: Eager loading**
```python
from sqlalchemy.orm import selectinload

# Single query with join
agents = await session.execute(
    select(Agent).options(selectinload(Agent.tools))
)

for agent in agents:
    # No additional queries - tools already loaded
    tools = agent.tools
```

### Index Optimization

```python
# Add indexes for common queries
class Agent(Base):
    __tablename__ = "agents"

    id = Column(String, primary_key=True)
    name = Column(String, index=True)  # Index for name lookups
    status = Column(String, index=True)  # Index for filtering
    created_at = Column(DateTime, index=True)  # Index for sorting

    # Composite index for common query pattern
    __table_args__ = (
        Index('ix_agent_status_created', 'status', 'created_at'),
    )
```

### Query Analysis

```python
# Analyze slow queries
from sqlalchemy import text

query = select(Agent).where(Agent.status == "active")

# Log query execution time
import time
start = time.time()
result = await session.execute(query)
duration = time.time() - start

if duration > 0.1:  # Log slow queries (>100ms)
    logger.warning(f"Slow query ({duration:.2f}s): {query}")

# Use EXPLAIN to analyze query plan
explain = await session.execute(
    text(f"EXPLAIN ANALYZE {query}")
)
print(explain.fetchall())
```

## Caching Patterns

### LRU Cache (In-Memory)

```python
from functools import lru_cache

@lru_cache(maxsize=128)
def get_agent_spec(agent_id: str) -> AgentSpec:
    """Cache agent specs (immutable data)."""
    return load_spec_from_disk(agent_id)

# Clear cache when specs change
get_agent_spec.cache_clear()
```

### Redis Cache (Distributed)

```python
import redis
import pickle
import asyncio

class CacheService:
    def __init__(self):
        self.redis = redis.Redis(host='localhost', port=6379)

    async def get(self, key: str):
        """Get from cache."""
        data = self.redis.get(key)
        if data:
            return pickle.loads(data)
        return None

    async def set(self, key: str, value, ttl: int = 300):
        """Set in cache with TTL."""
        self.redis.setex(key, ttl, pickle.dumps(value))

    async def delete(self, key: str):
        """Delete from cache."""
        self.redis.delete(key)

    async def get_or_fetch(self, key: str, fetch_fn, ttl: int = 300):
        """Get from cache or fetch and cache."""
        # Try cache first
        cached = await self.get(key)
        if cached is not None:
            return cached

        # Fetch if not in cache
        value = await fetch_fn()
        await self.set(key, value, ttl)
        return value

# Usage
cache = CacheService()

async def get_agent_cached(agent_id: str) -> Agent:
    return await cache.get_or_fetch(
        f"agent:{agent_id}",
        lambda: fetch_agent_from_db(agent_id),
        ttl=300,  # 5 minutes
    )
```

### Cache Invalidation

```python
# Pattern 1: TTL-based (time-based expiration)
await cache.set("key", value, ttl=300)  # Expires after 5 minutes

# Pattern 2: Event-based (invalidate on update)
async def update_agent(agent_id: str, updates: dict):
    agent = await update_agent_in_db(agent_id, updates)
    await cache.delete(f"agent:{agent_id}")  # Invalidate
    return agent

# Pattern 3: Cache-aside (lazy loading)
async def get_agent(agent_id: str):
    cached = await cache.get(f"agent:{agent_id}")
    if cached:
        return cached

    agent = await fetch_from_db(agent_id)
    await cache.set(f"agent:{agent_id}", agent)
    return agent
```

## Async Optimization

### Parallel Execution

```python
import asyncio

# Bad: Sequential
async def process_agents_sequential(agent_ids: list[str]):
    results = []
    for agent_id in agent_ids:
        result = await process_agent(agent_id)  # Wait for each
        results.append(result)
    return results

# Good: Parallel
async def process_agents_parallel(agent_ids: list[str]):
    tasks = [process_agent(agent_id) for agent_id in agent_ids]
    results = await asyncio.gather(*tasks)  # All at once
    return results
```

### Batching

```python
# Batch database operations
async def create_agents_batch(agents: list[AgentCreate]):
    """Create multiple agents in single transaction."""
    async with session.begin():
        db_agents = [Agent(**agent.dict()) for agent in agents]
        session.add_all(db_agents)

    return db_agents

# vs creating one at a time (slow!)
async def create_agents_slow(agents: list[AgentCreate]):
    results = []
    for agent in agents:
        async with session.begin():
            db_agent = Agent(**agent.dict())
            session.add(db_agent)
            results.append(db_agent)
    return results
```

### Connection Pooling

```python
from sqlalchemy.ext.asyncio import create_async_engine

# Configure connection pool
engine = create_async_engine(
    "postgresql+asyncpg://...",
    pool_size=20,  # Max connections in pool
    max_overflow=10,  # Additional connections when needed
    pool_timeout=30,  # Wait time for connection
    pool_recycle=3600,  # Recycle connections after 1 hour
    pool_pre_ping=True,  # Verify connection before using
)
```

## API Response Optimization

### Response Model Optimization

```python
# Bad: Return full objects (includes unnecessary data)
@app.get("/agents")
async def list_agents() -> list[Agent]:
    return await session.execute(select(Agent)).all()

# Good: Return only needed fields
class AgentSummary(BaseModel):
    id: str
    name: str
    status: str

@app.get("/agents")
async def list_agents() -> list[AgentSummary]:
    # Select only needed columns
    agents = await session.execute(
        select(Agent.id, Agent.name, Agent.status)
    )
    return [AgentSummary(**a) for a in agents]
```

### Pagination

```python
# Always paginate list endpoints
@app.get("/agents")
async def list_agents(
    offset: int = 0,
    limit: int = Query(10, le=100),  # Max 100
):
    query = select(Agent).offset(offset).limit(limit)
    agents = await session.execute(query)
    total = await session.scalar(select(func.count(Agent.id)))

    return {
        "items": agents,
        "total": total,
        "offset": offset,
        "limit": limit,
    }
```

### Streaming Large Responses

```python
from fastapi.responses import StreamingResponse

@app.get("/agents/export")
async def export_agents():
    """Stream agents as NDJSON."""

    async def generate():
        query = select(Agent)
        stream = await session.stream(query)

        async for agent in stream:
            yield agent.json() + "\n"

    return StreamingResponse(
        generate(),
        media_type="application/x-ndjson",
    )
```

### Compression

```python
from starlette.middleware.gzip import GZipMiddleware

# Enable compression
app.add_middleware(
    GZipMiddleware,
    minimum_size=1000,  # Compress responses >1KB
)
```

## Profiling

### Function Profiling

```python
import cProfile
import pstats

def profile_function():
    profiler = cProfile.Profile()
    profiler.enable()

    # Code to profile
    result = expensive_function()

    profiler.disable()

    # Print stats
    stats = pstats.Stats(profiler)
    stats.sort_stats('cumulative')
    stats.print_stats(20)  # Top 20 functions

    return result
```

### Line Profiling

```python
# Using line_profiler
from line_profiler import LineProfiler

def profile_lines():
    profiler = LineProfiler()
    profiler.add_function(expensive_function)

    profiler.enable()
    result = expensive_function()
    profiler.disable()

    profiler.print_stats()
    return result
```

### Memory Profiling

```python
from memory_profiler import profile

@profile
def memory_intensive_function():
    # This will show memory usage per line
    large_list = [i for i in range(1000000)]
    processed = [x * 2 for x in large_list]
    return sum(processed)
```

## Best Practices Summary

1. **Database**: Use eager loading, add indexes, batch operations
2. **Caching**: Cache expensive operations, invalidate on updates
3. **Async**: Parallelize independent operations, use connection pooling
4. **API**: Paginate lists, select only needed fields, compress responses
5. **Profiling**: Profile before optimizing, focus on bottlenecks
6. **Monitoring**: Track p95/p99, log slow operations, set alerts

## See Also

- `SKILL.md` for quick optimization patterns
- `scripts/profile_api.py` for endpoint profiling
- `content/docs/technical/performance-guide.md` for detailed guidelines
