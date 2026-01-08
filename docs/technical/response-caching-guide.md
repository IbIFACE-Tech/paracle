# Response Caching - Implementation Guide

## Overview

The `paracle_cache` package provides LLM response caching to reduce API costs and improve response times. It supports Redis/Valkey for production and in-memory caching for development.

## Quick Start

### 1. Installation

The caching package is included with Paracle. For Redis support:

```bash
pip install redis
# or
pip install valkey
```

### 2. Configuration

Configure via environment variables:

```bash
# Enable caching (default: true)
export PARACLE_CACHE_ENABLED=true

# Backend: "redis", "valkey", or "memory" (default: memory)
export PARACLE_CACHE_BACKEND=redis

# Redis connection (default: redis://localhost:6379/0)
export PARACLE_CACHE_REDIS_URL=redis://localhost:6379/0

# Default TTL in seconds (default: 3600 = 1 hour)
export PARACLE_CACHE_TTL=3600

# Max in-memory cache size (default: 1000)
export PARACLE_CACHE_MAX_SIZE=1000
```

### 3. Basic Usage

**Automatic caching with decorator:**

```python
from paracle_cache.decorators import cached_llm_call

@cached_llm_call(ttl=1800)  # 30 minutes
async def call_openai(
    provider: str,
    model: str,
    messages: list[dict],
    temperature: float = 0.7,
    max_tokens: int | None = None,
) -> dict:
    # Your LLM call implementation
    response = await openai_client.chat.completions.create(
        model=model,
        messages=messages,
        temperature=temperature,
    )
    return response.dict()
```

**Manual caching:**

```python
from paracle_cache.llm_cache import CacheKey, get_llm_cache

# Get cache instance
cache = get_llm_cache(ttl=3600)

# Create cache key
key = CacheKey(
    provider="openai",
    model="gpt-4",
    messages=[{"role": "user", "content": "Hello!"}],
    temperature=0.7,
)

# Check cache
cached_response = cache.get(key)
if cached_response is None:
    # Cache miss - call LLM
    response = await call_llm(...)
    cache.set(key, response)
else:
    # Cache hit - use cached response
    response = cached_response
```

## Architecture

### Components

```
┌──────────────────────────────────┐
│  @cached_llm_call(ttl=1800)      │ ← Decorator Layer (decorators.py)
└──────────────┬───────────────────┘
               │
┌──────────────▼───────────────────┐
│  LLMCache + CacheKey             │ ← LLM Layer (llm_cache.py)
│  - Semantic key generation       │
│  - Hit/miss tracking             │
└──────────────┬───────────────────┘
               │
┌──────────────▼───────────────────┐
│  CacheManager                    │ ← Infrastructure Layer
│  - Redis/Valkey backend          │   (cache_manager.py)
│  - In-memory fallback            │
│  - TTL & eviction                │
└──────────────────────────────────┘
```

### Modules

**1. `cache_manager.py`** - Infrastructure layer
- `CacheConfig`: Configuration from environment
- `CacheEntry`: Value + metadata (TTL, hit count)
- `CacheManager`: Dual backend (Redis + memory)
- `get_cache_manager()`: Global instance

**2. `llm_cache.py`** - LLM-specific layer
- `CacheKey`: Semantic key generation (hash of prompt + params)
- `LLMCache`: LLM cache with hit/miss tracking
- `get_llm_cache()`: Global instance

**3. `decorators.py`** - Integration layer
- `@cached_llm_call(ttl)`: Automatic caching decorator
- Supports async and sync functions
- Transparent caching (no code changes needed)

**4. `stats.py`** - Statistics tracking
- `CacheStats`: Metrics snapshot (hit rate, speedup, cost)
- `CacheStatsTracker`: Performance tracking over time
- `get_stats_tracker()`: Global instance

## CLI Commands

### View Statistics

```bash
# Text output
paracle cache stats

# JSON output
paracle cache stats --format json
```

Output:
```
Cache Statistics:
  Requests: 100 (70 hits, 30 misses)
  Hit Rate: 70.0%
  Speedup: 100.0x faster (cached)
  Cost Saved: $0.0120
  Utilization: 7.0% (70/1000)
```

### Clear Cache

```bash
paracle cache clear
```

Requires confirmation. Removes all cached responses and resets statistics.

### View Configuration

```bash
paracle cache config
```

Shows current cache backend, TTL, and other settings.

### Benchmark Performance

```bash
paracle cache benchmark --requests 1000
```

Runs performance test and reports:
- Total time
- Average time per request
- Requests per second

### Health Check

```bash
paracle cache health
```

Verifies cache backend connectivity and functionality.

## Integration with Providers

### Integrating into Provider Adapters

Add caching to your LLM provider adapter:

```python
from paracle_cache.decorators import cached_llm_call

class OpenAIProvider:
    @cached_llm_call(ttl=3600)
    async def chat_completion(
        self,
        model: str,
        messages: list[dict],
        temperature: float = 0.7,
        max_tokens: int | None = None,
        **kwargs,
    ) -> dict:
        # Existing implementation
        response = await self.client.chat.completions.create(
            model=model,
            messages=messages,
            temperature=temperature,
            max_tokens=max_tokens,
            **kwargs,
        )
        return response.dict()
```

**Key Points**:
1. Decorator must receive `provider`, `model`, `messages`, `temperature`, `max_tokens`
2. These parameters create the cache key
3. Additional kwargs are passed through but not cached

### Provider-Specific Considerations

**OpenAI**:
- Cache by model + messages + temperature
- Different temperatures = different cache entries
- max_tokens doesn't affect response content (can cache)

**Anthropic**:
- Similar to OpenAI
- Cache by model + messages + temperature

**Google (Gemini)**:
- Same pattern
- Consider safety_settings in cache key if varying

## Statistics Tracking

### Using CacheStatsTracker

```python
from paracle_cache.stats import get_stats_tracker

# Get tracker
tracker = get_stats_tracker()

# Record cache hit
tracker.record_hit(response_time_ms=5.0, tokens=20)

# Record cache miss
tracker.record_miss(
    response_time_ms=500.0,
    tokens=20,
    cost=0.0004,  # $0.0004
)

# Get statistics
stats = tracker.get_stats()
print(f"Hit Rate: {stats.hit_rate * 100:.1f}%")
print(f"Speedup: {stats.speedup_factor:.1f}x")
print(f"Cost Saved: ${stats.estimated_cost_saved:.4f}")

# Human-readable summary
print(tracker.summary())
```

### Metrics Tracked

**Hit/Miss Metrics**:
- Total hits
- Total misses
- Hit rate (0.0-1.0)
- Miss rate (0.0-1.0)

**Performance Metrics**:
- Average cached response time (ms)
- Average uncached response time (ms)
- Speedup factor (Nx faster)

**Cost Metrics**:
- Cached tokens
- Uncached tokens
- Estimated cost saved ($)

**Capacity Metrics**:
- Current cache size
- Max cache size
- Cache utilization (0.0-1.0)
- Evictions count

## Cache Key Generation

### Semantic Keys

Cache keys are generated from:
1. Provider name (e.g., "openai")
2. Model name (e.g., "gpt-4")
3. Messages (full conversation history)
4. Temperature (rounded to 2 decimals)
5. max_tokens (if specified)

**Example**:

```python
key = CacheKey(
    provider="openai",
    model="gpt-4",
    messages=[
        {"role": "system", "content": "You are a helpful assistant."},
        {"role": "user", "content": "What is 2+2?"}
    ],
    temperature=0.7,
    max_tokens=100,
)

key_string = key.to_string()
# Returns SHA-256 hash: "a3d2f8e1..."
```

### Key Properties

**Deterministic**: Same inputs always produce same key

**Compact**: SHA-256 hash (64 characters)

**Collision-resistant**: Cryptographic hash prevents collisions

**Parameter-sensitive**:
- Different temperatures = different keys
- Different models = different keys
- Different message order = different keys

## Performance Targets

### Phase 8 Goals

| Metric                  | Target     | Current |
| ----------------------- | ---------- | ------- |
| Cache hit rate          | >40%       | TBD*    |
| Cached response speedup | >2x faster | 100x+   |
| Cost reduction          | >30%       | TBD*    |
| Memory overhead         | <100MB     | <10MB   |

*To be measured in production usage

### Expected Performance

**Cache Hit (in-memory)**:
- Response time: ~0.025ms
- Speedup: 40,000x vs 1000ms LLM call
- Cost: $0.00 (no API call)

**Cache Hit (Redis)**:
- Response time: ~5-10ms
- Speedup: 100-200x vs 1000ms LLM call
- Cost: $0.00 (no API call)

**Cache Miss**:
- Response time: Same as LLM call
- Overhead: <1ms (key generation + storage)
- Cost: Normal LLM pricing

## Production Deployment

### Redis/Valkey Setup

**Docker Compose**:

```yaml
services:
  redis:
    image: redis:7-alpine
    ports:
      - "6379:6379"
    volumes:
      - redis_data:/data
    command: redis-server --appendonly yes

volumes:
  redis_data:
```

**Environment**:

```bash
export PARACLE_CACHE_ENABLED=true
export PARACLE_CACHE_BACKEND=redis
export PARACLE_CACHE_REDIS_URL=redis://redis:6379/0
export PARACLE_CACHE_TTL=3600
```

### Monitoring

**Track key metrics**:

```bash
# View stats periodically
watch -n 60 paracle cache stats

# Or use JSON for monitoring tools
paracle cache stats --format json | jq .hit_rate
```

**Alert on**:
- Hit rate <30%
- Cache backend failures
- High eviction rates

### Cache Warming

Pre-populate cache with common queries:

```python
from paracle_cache.llm_cache import CacheKey, get_llm_cache

cache = get_llm_cache()

# Common queries
common_prompts = [
    "Explain Python decorators",
    "Write a hello world program",
    "What is REST API?",
]

for prompt in common_prompts:
    key = CacheKey(
        provider="openai",
        model="gpt-4",
        messages=[{"role": "user", "content": prompt}],
        temperature=0.7,
    )

    # Generate and cache response
    response = await call_llm(prompt)
    cache.set(key, response, ttl=7200)  # 2 hours
```

## Best Practices

### 1. Choose Appropriate TTL

- **Short-lived (300s)**: Time-sensitive data
- **Medium (3600s)**: General queries
- **Long (86400s)**: Static reference data

### 2. Monitor Hit Rates

Target >40% hit rate in production:

```bash
paracle cache stats
```

If hit rate is low:
- Increase TTL
- Check if queries are unique
- Consider semantic similarity matching

### 3. Set Cache Limits

Prevent unbounded memory growth:

```bash
export PARACLE_CACHE_MAX_SIZE=10000
```

### 4. Handle Cache Failures Gracefully

Cache should degrade gracefully:
- Redis unavailable → fallback to memory
- Memory full → LRU eviction
- Never block on cache operations

### 5. Invalidate Stale Data

Clear cache when data changes:

```python
from paracle_cache.llm_cache import get_llm_cache

cache = get_llm_cache()
cache.clear()  # Clear all

# Or invalidate specific entry
cache.invalidate(key)
```

## Troubleshooting

### Cache Not Working

**Check configuration**:
```bash
paracle cache config
```

**Check health**:
```bash
paracle cache health
```

### Low Hit Rate

**Causes**:
1. Queries are unique (no repetition)
2. TTL too short (entries expire)
3. Temperature varies (creates different keys)

**Solutions**:
1. Increase TTL
2. Use consistent temperature
3. Pre-warm cache with common queries

### Redis Connection Errors

**Check Redis**:
```bash
redis-cli ping
# Should return: PONG
```

**Fallback to memory**:
```bash
export PARACLE_CACHE_BACKEND=memory
```

### High Memory Usage

**Check utilization**:
```bash
paracle cache stats
```

**Reduce max size**:
```bash
export PARACLE_CACHE_MAX_SIZE=500
```

## Examples

See [examples/14_response_caching.py](../examples/14_response_caching.py) for:
- Manual caching
- Decorator usage
- Statistics tracking
- Configuration
- CLI commands

## API Reference

### CacheManager

```python
class CacheManager:
    def __init__(self, config: CacheConfig): ...
    def get(self, key: str) -> Any | None: ...
    def set(self, key: str, value: Any, ttl: int) -> bool: ...
    def delete(self, key: str) -> bool: ...
    def clear(self) -> int: ...
    def stats(self) -> dict: ...
```

### LLMCache

```python
class LLMCache:
    def __init__(self, ttl: int = 3600): ...
    def get(self, key: CacheKey) -> dict | None: ...
    def set(self, key: CacheKey, response: dict, ttl: int | None = None) -> bool: ...
    def invalidate(self, key: CacheKey) -> bool: ...
    def clear(self) -> int: ...
    def hit_rate(self) -> float | None: ...
    def stats(self) -> dict: ...
```

### CacheStatsTracker

```python
class CacheStatsTracker:
    def record_hit(self, response_time_ms: float, tokens: int = 0): ...
    def record_miss(self, response_time_ms: float, tokens: int = 0, cost: float = 0.0): ...
    def record_eviction(self): ...
    def update_cache_size(self, size: int): ...
    def get_stats(self) -> CacheStats: ...
    def reset(self): ...
    def summary(self) -> str: ...
```

## Next Steps

1. **Enable caching** in your environment
2. **Monitor hit rates** with `paracle cache stats`
3. **Tune TTL** based on your workload
4. **Set up Redis** for production
5. **Track cost savings** over time

Target: >40% hit rate, >30% cost reduction, 2x faster cached responses.

---

**Version**: 1.0
**Last Updated**: 2026-01-07
**Status**: Production Ready
