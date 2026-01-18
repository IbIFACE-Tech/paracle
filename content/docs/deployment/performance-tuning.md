# Performance Tuning Guide

**Last Updated**: 2026-01-18
**Version**: 1.0
**Target**: 1000+ req/s, p95 < 500ms, p99 < 1s

---

## Overview

Comprehensive performance optimization guide for Paracle production deployments.

**Optimization Areas**:

- Database query optimization
- Connection pooling
- Redis caching strategies
- LLM provider optimization
- Application-level tuning
- Network optimization

---

## Database Optimization

### Query Performance Analysis

```sql
-- Enable pg_stat_statements
CREATE EXTENSION IF NOT EXISTS pg_stat_statements;

-- Find slow queries
SELECT
    calls,
    mean_exec_time,
    max_exec_time,
    stddev_exec_time,
    query
FROM pg_stat_statements
WHERE mean_exec_time > 100  -- Queries averaging > 100ms
ORDER BY mean_exec_time DESC
LIMIT 20;

-- Find queries with high total time
SELECT
    calls,
    total_exec_time,
    mean_exec_time,
    query
FROM pg_stat_statements
ORDER BY total_exec_time DESC
LIMIT 20;
```

### Index Optimization

```sql
-- Find missing indexes
SELECT
    schemaname,
    tablename,
    attname,
    n_distinct,
    correlation
FROM pg_stats
WHERE schemaname = 'public'
  AND n_distinct > 100
  AND correlation < 0.1
ORDER BY n_distinct DESC;

-- Create indexes for common queries
CREATE INDEX CONCURRENTLY idx_agents_created_at ON agents(created_at);
CREATE INDEX CONCURRENTLY idx_executions_agent_status ON executions(agent_id, status);
CREATE INDEX CONCURRENTLY idx_workflows_name ON workflows(name);

-- Analyze index usage
SELECT
    schemaname,
    tablename,
    indexname,
    idx_scan,
    idx_tup_read,
    idx_tup_fetch
FROM pg_stat_user_indexes
WHERE idx_scan = 0
  AND schemaname = 'public'
ORDER BY pg_relation_size(indexrelid) DESC;

-- Drop unused indexes
DROP INDEX CONCURRENTLY idx_unused_index;
```

### Table Partitioning

```sql
-- Partition executions table by date
CREATE TABLE executions_2026_01 PARTITION OF executions
    FOR VALUES FROM ('2026-01-01') TO ('2026-02-01');

CREATE TABLE executions_2026_02 PARTITION OF executions
    FOR VALUES FROM ('2026-02-01') TO ('2026-03-01');

-- Automatic partition creation
CREATE OR REPLACE FUNCTION create_monthly_partition()
RETURNS void AS $$
DECLARE
    partition_name text;
    start_date date;
    end_date date;
BEGIN
    start_date := date_trunc('month', CURRENT_DATE);
    end_date := start_date + interval '1 month';
    partition_name := 'executions_' || to_char(start_date, 'YYYY_MM');

    EXECUTE format(
        'CREATE TABLE IF NOT EXISTS %I PARTITION OF executions FOR VALUES FROM (%L) TO (%L)',
        partition_name, start_date, end_date
    );
END;
$$ LANGUAGE plpgsql;

-- Schedule monthly (cron)
SELECT cron.schedule('create-partition', '0 0 1 * *', 'SELECT create_monthly_partition()');
```

### VACUUM and ANALYZE

```sql
-- Manual VACUUM
VACUUM ANALYZE agents;
VACUUM ANALYZE executions;
VACUUM ANALYZE workflows;

-- Auto-vacuum tuning (postgresql.conf)
autovacuum = on
autovacuum_max_workers = 4
autovacuum_naptime = 10s
autovacuum_vacuum_threshold = 50
autovacuum_vacuum_scale_factor = 0.1
autovacuum_analyze_threshold = 50
autovacuum_analyze_scale_factor = 0.05

-- Check table bloat
SELECT
    schemaname,
    tablename,
    pg_size_pretty(pg_total_relation_size(schemaname||'.'||tablename)) AS size,
    n_dead_tup,
    n_live_tup,
    round(n_dead_tup * 100.0 / NULLIF(n_live_tup + n_dead_tup, 0), 2) AS dead_ratio
FROM pg_stat_user_tables
WHERE n_dead_tup > 1000
ORDER BY dead_ratio DESC;
```

---

## Connection Pooling

### PgBouncer Configuration

```ini
# /etc/pgbouncer/pgbouncer.ini

[databases]
paracle = host=postgres-primary.internal port=5432 dbname=paracle

[pgbouncer]
listen_port = 6432
listen_addr = *
auth_type = scram-sha-256
auth_file = /etc/pgbouncer/userlist.txt

# Pool mode
pool_mode = transaction  # Most efficient
max_client_conn = 10000  # Max client connections
default_pool_size = 25   # Connections per user/database
reserve_pool_size = 5    # Emergency pool
reserve_pool_timeout = 3 # Wait time for reserve pool

# Timeouts
server_idle_timeout = 600      # Close idle server connections after 10min
server_connect_timeout = 15    # Server connection timeout
query_wait_timeout = 120       # Max time queries can wait for connection
idle_transaction_timeout = 300 # Close idle transactions after 5min

# Limits
max_db_connections = 100       # Max connections to database
max_user_connections = 100     # Max connections per user

# Logging
log_connections = 1
log_disconnections = 1
log_pooler_errors = 1
```

### Application-Level Pooling (SQLAlchemy)

```python
# packages/paracle_store/pool.py
from sqlalchemy import create_engine, event
from sqlalchemy.pool import QueuePool

def create_optimized_engine(database_url: str):
    """Create engine with optimized pool settings"""
    engine = create_engine(
        database_url,

        # Pool configuration
        poolclass=QueuePool,
        pool_size=20,              # Persistent connections
        max_overflow=10,           # Burst capacity
        pool_timeout=30,           # Wait timeout
        pool_recycle=3600,         # Recycle connections every hour
        pool_pre_ping=True,        # Test connection before use

        # Statement compilation cache
        query_cache_size=1200,

        # Execution options
        execution_options={
            "isolation_level": "READ COMMITTED",
            "postgresql_readonly": False,
            "postgresql_deferrable": False,
        },

        # Echo for debugging (disable in prod)
        echo=False,
        echo_pool=False,
    )

    # Monitor pool usage
    @event.listens_for(engine, "connect")
    def receive_connect(dbapi_conn, connection_record):
        connection_record.info['pid'] = dbapi_conn.get_backend_pid()

    @event.listens_for(engine, "checkout")
    def receive_checkout(dbapi_conn, connection_record, connection_proxy):
        # Log checkout (optional)
        pass

    return engine

# Usage
engine = create_optimized_engine("postgresql://user:pass@pgbouncer:6432/paracle")
```

---

## Redis Optimization

### Memory Optimization

```bash
# redis.conf
maxmemory 4gb
maxmemory-policy allkeys-lru  # Evict least recently used keys

# Disable persistence (if cache-only)
save ""
appendonly no

# Enable compression
list-compress-depth 1
```

### Connection Pooling

```python
# packages/paracle_cache/redis_pool.py
import redis
from redis.connection import ConnectionPool

class RedisConnectionPool:
    def __init__(self):
        self.pool = ConnectionPool(
            host='redis-cluster',
            port=6379,
            max_connections=50,     # Pool size
            socket_keepalive=True,
            socket_connect_timeout=5,
            socket_timeout=5,
            retry_on_timeout=True,
            health_check_interval=30,
        )
        self.client = redis.Redis(
            connection_pool=self.pool,
            decode_responses=True
        )

    def get_client(self):
        return self.client

# Usage
pool = RedisConnectionPool()
redis_client = pool.get_client()
```

### Caching Strategies

```python
# packages/paracle_cache/strategies.py
from functools import wraps
import pickle
import hashlib

class CacheStrategy:
    def __init__(self, redis_client):
        self.redis = redis_client

    def cache_aside(self, key: str, ttl: int = 3600):
        """Cache-aside (lazy loading)"""
        def decorator(func):
            @wraps(func)
            def wrapper(*args, **kwargs):
                # Try cache
                cached = self.redis.get(key)
                if cached:
                    return pickle.loads(cached)

                # Cache miss - load from source
                result = func(*args, **kwargs)

                # Store in cache
                self.redis.setex(key, ttl, pickle.dumps(result))
                return result
            return wrapper
        return decorator

    def write_through(self, key: str, ttl: int = 3600):
        """Write-through (update cache on write)"""
        def decorator(func):
            @wraps(func)
            def wrapper(*args, **kwargs):
                # Write to source
                result = func(*args, **kwargs)

                # Update cache immediately
                self.redis.setex(key, ttl, pickle.dumps(result))
                return result
            return wrapper
        return decorator

    def write_behind(self, key: str, batch_size: int = 100):
        """Write-behind (async write to source)"""
        def decorator(func):
            @wraps(func)
            def wrapper(*args, **kwargs):
                # Add to write queue
                self.redis.lpush(f"write_queue:{key}", pickle.dumps((args, kwargs)))

                # Process batch if queue full
                queue_size = self.redis.llen(f"write_queue:{key}")
                if queue_size >= batch_size:
                    self._process_write_queue(key, func)

                return True
            return wrapper
        return decorator

# Usage
cache = CacheStrategy(redis_client)

@cache.cache_aside("agent:{agent_id}", ttl=600)
def get_agent(agent_id: str):
    return db.query(Agent).filter(Agent.id == agent_id).first()
```

---

## LLM Provider Optimization

### Request Batching

```python
# packages/paracle_providers/batching.py
import asyncio
from collections import defaultdict

class LLMBatcher:
    def __init__(self, batch_size: int = 10, wait_time: float = 0.1):
        self.batch_size = batch_size
        self.wait_time = wait_time
        self.queue = defaultdict(list)
        self.results = {}

    async def batch_request(self, provider: str, prompt: str) -> str:
        """Add request to batch"""
        request_id = f"{provider}:{hash(prompt)}"
        future = asyncio.Future()

        self.queue[provider].append((prompt, request_id, future))

        # Trigger batch if full
        if len(self.queue[provider]) >= self.batch_size:
            await self._process_batch(provider)

        # Wait for result
        return await future

    async def _process_batch(self, provider: str):
        """Process batched requests"""
        if not self.queue[provider]:
            return

        batch = self.queue[provider][:self.batch_size]
        self.queue[provider] = self.queue[provider][self.batch_size:]

        # Create batch prompt
        prompts = [item[0] for item in batch]
        batch_prompt = "\n\n".join(f"Request {i+1}:\n{p}" for i, p in enumerate(prompts))

        # Call LLM
        response = await llm_client.complete(batch_prompt)

        # Parse responses
        responses = response.split("\n\nResponse ")

        # Set futures
        for i, (prompt, request_id, future) in enumerate(batch):
            if not future.done():
                future.set_result(responses[i] if i < len(responses) else "")

# Usage
batcher = LLMBatcher()
result = await batcher.batch_request("openai", "Generate code")
```

### Response Streaming

```python
# packages/paracle_providers/streaming.py
from typing import AsyncIterator

async def stream_llm_response(prompt: str) -> AsyncIterator[str]:
    """Stream LLM response tokens"""
    async for chunk in llm_client.stream(prompt):
        yield chunk.text

# FastAPI endpoint
@app.post("/api/v1/agents/run/stream")
async def run_agent_stream(request: AgentRequest):
    async def generate():
        async for chunk in stream_llm_response(request.prompt):
            yield f"data: {chunk}\n\n"

    return StreamingResponse(generate(), media_type="text/event-stream")
```

### Caching LLM Responses

```python
# packages/paracle_providers/llm_cache.py
import hashlib

class LLMCache:
    def __init__(self, redis_client):
        self.redis = redis_client
        self.ttl = 86400  # 24 hours

    def get_cache_key(self, provider: str, model: str, prompt: str) -> str:
        """Generate cache key"""
        content = f"{provider}:{model}:{prompt}"
        return f"llm_cache:{hashlib.sha256(content.encode()).hexdigest()}"

    async def get_or_call(self, provider: str, model: str, prompt: str, func):
        """Get cached response or call LLM"""
        cache_key = self.get_cache_key(provider, model, prompt)

        # Try cache
        cached = self.redis.get(cache_key)
        if cached:
            cache_hits.inc()
            return pickle.loads(cached)

        # Cache miss
        cache_misses.inc()
        response = await func(prompt)

        # Store in cache
        self.redis.setex(cache_key, self.ttl, pickle.dumps(response))
        return response

# Usage
cache = LLMCache(redis_client)
response = await cache.get_or_call("openai", "gpt-4", prompt, llm_client.complete)
```

---

## Application-Level Optimization

### Async I/O

```python
# packages/paracle_api/handlers.py
import asyncio
from fastapi import FastAPI

app = FastAPI()

@app.post("/api/v1/agents/run")
async def run_agent(request: AgentRequest):
    """Async endpoint"""

    # Parallel execution
    tasks = [
        load_agent_spec(request.agent_id),
        load_tools(request.agent_id),
        check_permissions(request.user_id)
    ]

    agent, tools, perms = await asyncio.gather(*tasks)

    # Execute agent
    result = await execute_agent_async(agent, request.task, tools)

    return {"result": result}
```

### Response Compression

```python
# FastAPI middleware
from fastapi.middleware.gzip import GZipMiddleware

app.add_middleware(GZIPMiddleware, minimum_size=1000)  # Compress responses > 1KB
```

### Rate Limiting

```python
# packages/paracle_api/rate_limit.py
from slowapi import Limiter, _rate_limit_exceeded_handler
from slowapi.util import get_remote_address

limiter = Limiter(key_func=get_remote_address)

@app.post("/api/v1/agents/run")
@limiter.limit("100/minute")
async def run_agent(request: Request):
    pass
```

---

## Network Optimization

### CDN for Static Assets

```nginx
# Nginx configuration
location /static/ {
    alias /var/www/paracle/static/;
    expires 30d;
    add_header Cache-Control "public, immutable";
}
```

### HTTP/2 and HTTP/3

```nginx
server {
    listen 443 ssl http2;
    listen 443 quic reuseport;  # HTTP/3

    ssl_certificate /etc/letsencrypt/live/api.paracle.com/fullchain.pem;
    ssl_certificate_key /etc/letsencrypt/live/api.paracle.com/privkey.pem;

    # HTTP/3 headers
    add_header Alt-Svc 'h3=":443"; ma=86400';
}
```

### Connection Keep-Alive

```python
# HTTP client optimization
import httpx

client = httpx.AsyncClient(
    timeout=30.0,
    limits=httpx.Limits(max_keepalive_connections=100, max_connections=200),
    http2=True
)
```

---

## Monitoring Performance

### Key Metrics

```python
# Prometheus metrics
from prometheus_client import Histogram, Counter

# Request duration
request_duration = Histogram(
    'http_request_duration_seconds',
    'HTTP request duration',
    ['method', 'endpoint'],
    buckets=[0.01, 0.05, 0.1, 0.5, 1.0, 2.0, 5.0]
)

# Database query duration
db_query_duration = Histogram(
    'db_query_duration_seconds',
    'Database query duration',
    ['query_type'],
    buckets=[0.001, 0.01, 0.05, 0.1, 0.5, 1.0]
)

# LLM call duration
llm_call_duration = Histogram(
    'llm_call_duration_seconds',
    'LLM API call duration',
    ['provider', 'model'],
    buckets=[0.1, 0.5, 1.0, 2.0, 5.0, 10.0, 30.0]
)

# Cache hit rate
cache_hits = Counter('cache_hits_total', 'Cache hits', ['cache_type'])
cache_misses = Counter('cache_misses_total', 'Cache misses', ['cache_type'])
```

### Performance Benchmarking

```bash
# Baseline performance test
python scripts/baseline_profiling.py

# Load test
locust -f tests/load/locustfile.py --host https://api.paracle.com --users 1000 --spawn-rate 10
```

---

## Profiling

### CPU Profiling

```python
# packages/paracle_profiling/cpu.py
import cProfile
import pstats

def profile_function(func):
    def wrapper(*args, **kwargs):
        profiler = cProfile.Profile()
        profiler.enable()

        result = func(*args, **kwargs)

        profiler.disable()
        stats = pstats.Stats(profiler)
        stats.sort_stats('cumulative')
        stats.print_stats(20)

        return result
    return wrapper

# Usage
@profile_function
def slow_function():
    # ...
    pass
```

### Memory Profiling

```python
# Use memory_profiler
from memory_profiler import profile

@profile
def memory_intensive_function():
    large_list = [i for i in range(1000000)]
    return large_list
```

---

## Best Practices Checklist

### Database

- ✅ Index all foreign keys
- ✅ Use connection pooling (PgBouncer)
- ✅ Enable query caching
- ✅ Partition large tables
- ✅ Regular VACUUM ANALYZE

### Caching

- ✅ Multi-layer cache (memory + Redis)
- ✅ Cache LLM responses
- ✅ Cache-aside pattern
- ✅ Appropriate TTLs

### Application

- ✅ Async I/O throughout
- ✅ Response compression
- ✅ Request batching
- ✅ Connection pooling

### Monitoring

- ✅ Track p50/p95/p99 latency
- ✅ Monitor cache hit rates
- ✅ Alert on slow queries
- ✅ Regular performance testing

---

## Related Documentation

- [scaling-guide.md](scaling-guide.md) - Horizontal scaling
- [monitoring-setup.md](monitoring-setup.md) - Performance monitoring
- [production-deployment.md](production-deployment.md) - Deployment
