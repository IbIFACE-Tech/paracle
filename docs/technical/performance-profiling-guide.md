# Performance Profiling Guide

**Phase 8: Performance & Scale - Profiling Infrastructure**

This guide explains how to use Paracle's performance profiling tools to measure, analyze, and optimize your application.

## 📦 Overview

The `paracle_profiling` package provides:

- **Function Profiling**: `@profile` and `@profile_async` decorators
- **Request Profiling**: `ProfilerMiddleware` for FastAPI
- **Performance Analysis**: `PerformanceAnalyzer` for bottleneck detection
- **Caching Layer**: `CacheManager` for response caching
- **Memory Tracking**: Optional memory profiling with psutil

## 🚀 Quick Start

### 1. Enable API Profiling

The API server automatically profiles all requests via middleware:

```python
# Already integrated in paracle_api/main.py
from paracle_profiling import ProfilerMiddleware

app.add_middleware(ProfilerMiddleware, slow_threshold=1.0)
```

**Features**:
- Automatic timing of all endpoints
- Response headers: `X-Process-Time`, `X-Request-Count`
- Slow request warnings (>1s by default)
- Per-endpoint statistics

### 2. Profile Functions

Add decorators to profile specific functions:

```python
from paracle_profiling import profile, profile_async

# Synchronous function
@profile(track_memory=True)
def load_agent_spec(agent_id: str):
    """Load agent specification from file."""
    # Function code here
    return spec

# Async function
@profile_async(track_memory=True)
async def execute_workflow(workflow_id: str, inputs: dict):
    """Execute a workflow."""
    # Async code here
    return result
```

**Options**:
- `track_memory=True`: Track memory usage (requires psutil)
- `name="custom_name"`: Override function name in stats

### 3. Cache Expensive Operations

Use caching to avoid repeated expensive operations:

```python
from paracle_profiling import cached

@cached(ttl=300)  # Cache for 5 minutes
def get_workflow_definition(workflow_id: str):
    """Load workflow definition (cached)."""
    # Expensive file I/O or parsing
    return workflow_def
```

**Benefits**:
- Reduces file I/O
- Speeds up repeated operations
- Automatic TTL expiration
- Hit/miss tracking

## 📊 Analyzing Performance

### Get Statistics

View profiling statistics for any function:

```python
from paracle_profiling import get_profile_stats

# Get stats for specific function
stats = get_profile_stats("load_agent_spec")
print(f"Calls: {stats['calls']}")
print(f"Average: {stats['avg_time']:.3f}s")
print(f"P95: {stats['p95_time']:.3f}s")
```

### Generate Bottleneck Report

Identify performance bottlenecks automatically:

```python
from paracle_profiling import PerformanceAnalyzer

analyzer = PerformanceAnalyzer()

# Generate detailed report
report = analyzer.generate_report(top_n=20, min_calls=5)
print(report)
```

**Output Example**:
```
Performance Bottleneck Analysis
Generated: 2026-01-07 10:30:00
Total Profiled Time: 45.23s
================================================================================

CRITICAL Severity (>2.0s avg)
--------------------------------------------------------------------------------
load_agent_spec
  Average: 2.45s | Max: 3.12s | P95: 2.89s | Calls: 45 | Total: 110.25s (24.4%)

HIGH Severity (>1.0s avg)
--------------------------------------------------------------------------------
execute_workflow_step
  Average: 1.23s | Max: 2.01s | P95: 1.78s | Calls: 120 | Total: 147.60s (32.6%)

MEDIUM Severity (>0.5s avg)
--------------------------------------------------------------------------------
parse_workflow_definition
  Average: 0.67s | Max: 0.89s | P95: 0.81s | Calls: 30 | Total: 20.10s (4.4%)

Recommendations:
- Focus on CRITICAL severity bottlenecks first
- Consider caching for frequently called functions
- Profile database queries if not already done
- Check for N+1 query patterns
```

### Check Performance Targets

Validate Phase 8 performance goals:

```python
analyzer = PerformanceAnalyzer()
targets = analyzer.check_targets()

print(f"P95 < 500ms: {'✅' if targets['p95_under_500ms'] else '❌'}")
print(f"P99 < 1000ms: {'✅' if targets['p99_under_1000ms'] else '❌'}")
print(f"Average < 100ms: {'✅' if targets['avg_under_100ms'] else '❌'}")
```

## 🔧 Advanced Usage

### Middleware Statistics

Get per-endpoint statistics from middleware:

```python
from paracle_profiling import ProfilerMiddleware

# Access middleware instance (attached to app)
middleware = app.user_middleware[0].cls
stats = middleware.get_stats()

for endpoint, metrics in stats.items():
    print(f"{endpoint}:")
    print(f"  Average: {metrics['avg']:.3f}s")
    print(f"  P95: {metrics['p95']:.3f}s")
    print(f"  Requests: {metrics['count']}")
```

### Custom Cache Keys

Control cache key generation:

```python
from paracle_profiling import cached

def cache_key_generator(agent_id: str, include_disabled: bool = False):
    """Generate custom cache key."""
    return f"agents:{agent_id}:{include_disabled}"

@cached(ttl=60, key_func=cache_key_generator)
def list_agent_tools(agent_id: str, include_disabled: bool = False):
    """List agent tools with custom caching."""
    return tools
```

### Manual Cache Management

Direct cache access for fine-grained control:

```python
from paracle_profiling import CacheManager

cache = CacheManager(max_size=1000, default_ttl=300)

# Set value
cache.set("my_key", {"data": "value"}, ttl=60)

# Get value
value = cache.get("my_key")

# Delete value
cache.delete("my_key")

# Get statistics
stats = cache.get_stats()
print(f"Hit rate: {stats['hit_rate']}")
print(f"Size: {stats['size']}/{stats['max_size']}")
```

### Memory Profiling

Track memory usage in critical functions:

```python
from paracle_profiling import profile

@profile(track_memory=True)
def process_large_dataset(data: list):
    """Process large dataset with memory tracking."""
    results = []
    for item in data:
        results.append(expensive_operation(item))
    return results

# Check memory stats
stats = get_profile_stats("process_large_dataset")
print(f"Avg memory: {stats['memory_avg_mb']:.1f} MB")
print(f"Max memory: {stats['memory_max_mb']:.1f} MB")
```

## 📈 Performance Optimization Workflow

### Step 1: Enable Profiling

Add decorators to functions you want to profile:

```python
# Key functions to profile:
# - Agent loading/execution
# - Workflow execution
# - Provider API calls
# - Database queries
# - File I/O operations
```

### Step 2: Run Load Tests

Execute typical operations to gather data:

```bash
# Run agent execution
paracle agents run coder --task "Sample task"

# Execute workflows
paracle workflows run feature_development

# Make API requests
curl http://localhost:8000/api/agents/list
```

### Step 3: Analyze Bottlenecks

Generate performance report:

```python
from paracle_profiling import PerformanceAnalyzer

analyzer = PerformanceAnalyzer()
report = analyzer.generate_report(top_n=20)
print(report)
```

### Step 4: Optimize

Focus on highest impact optimizations:

1. **CRITICAL/HIGH** bottlenecks first
2. Functions called frequently
3. Functions consuming most total time

**Common Optimizations**:
- Add `@cached()` for repeated operations
- Optimize database queries (add indexes, batch operations)
- Use async I/O where possible
- Reduce unnecessary file operations
- Pre-compute expensive values

### Step 5: Validate

Re-run profiling and check improvements:

```python
# Check if targets are met
targets = analyzer.check_targets()

# Compare before/after metrics
print(f"Before P95: 750ms")
print(f"After P95: {stats['p95_time']*1000:.0f}ms")
print(f"Improvement: {((750 - stats['p95_time']*1000) / 750 * 100):.1f}%")
```

## 🎯 Phase 8 Performance Targets

| Metric           | Target   | Check Method                          |
| ---------------- | -------- | ------------------------------------- |
| API P95          | < 500ms  | `check_targets()['p95_under_500ms']`  |
| API P99          | < 1000ms | `check_targets()['p99_under_1000ms']` |
| Average Response | < 100ms  | `check_targets()['avg_under_100ms']`  |

## 🛠️ Troubleshooting

### Profiling Not Working

**Issue**: No profiling data collected

**Solution**:
```python
from paracle_profiling import Profiler

# Enable profiler explicitly
Profiler.enable()

# Check if enabled
print(f"Profiler enabled: {Profiler.is_enabled()}")
```

### High Memory Usage

**Issue**: Memory tracking shows high usage

**Solution**:
1. Check for memory leaks (growing memory over time)
2. Profile with `track_memory=True` to identify culprits
3. Use generators instead of lists for large datasets
4. Clear caches periodically: `cache.clear()`

### Cache Not Hitting

**Issue**: Low cache hit rate

**Solution**:
```python
from paracle_profiling import get_cache

cache = get_cache()
stats = cache.get_stats()
print(f"Hit rate: {stats['hit_rate']}")
print(f"Hits: {stats['hits']} | Misses: {stats['misses']}")

# Check TTL settings
# Increase TTL if data rarely changes
@cached(ttl=600)  # 10 minutes instead of 5
```

### Slow Requests Not Logged

**Issue**: Expected slow request warnings not appearing

**Solution**:
```python
# Lower threshold to catch more slow requests
app.add_middleware(ProfilerMiddleware, slow_threshold=0.5)  # 500ms
```

## 📚 API Reference

### Decorators

#### `@profile(name=None, track_memory=False)`

Profile synchronous function execution.

**Args**:
- `name` (str, optional): Override function name in stats
- `track_memory` (bool): Track memory usage (requires psutil)

**Returns**: Decorated function

#### `@profile_async(name=None, track_memory=False)`

Profile asynchronous function execution.

**Args**: Same as `@profile`

**Returns**: Decorated async function

#### `@cached(ttl=300, key_func=None)`

Cache function results with TTL.

**Args**:
- `ttl` (int): Time-to-live in seconds (0 = no expiration)
- `key_func` (callable, optional): Custom cache key generator

**Returns**: Decorated function

### Classes

#### `ProfilerMiddleware(app, slow_threshold=1.0)`

FastAPI middleware for request profiling.

**Args**:
- `app`: ASGI application
- `slow_threshold` (float): Slow request threshold in seconds

**Methods**:
- `get_stats()`: Get per-endpoint statistics
- `clear_stats()`: Reset all statistics

#### `PerformanceAnalyzer()`

Analyze profiling data and identify bottlenecks.

**Methods**:
- `analyze_bottlenecks(top_n=10, min_calls=5)`: Get bottleneck reports
- `generate_report(top_n=10, min_calls=5)`: Generate formatted report
- `get_slowest_endpoints(top_n=10)`: Get slowest functions
- `check_targets()`: Validate Phase 8 performance targets

#### `CacheManager(max_size=1000, default_ttl=300)`

In-memory cache with TTL support.

**Args**:
- `max_size` (int): Maximum cache entries (LRU eviction)
- `default_ttl` (int): Default TTL in seconds

**Methods**:
- `get(key)`: Get cached value
- `set(key, value, ttl=None)`: Set cached value
- `delete(key)`: Delete cache entry
- `clear()`: Clear all entries
- `get_stats()`: Get cache statistics
- `cached(ttl=None, key_func=None)`: Decorator for caching

### Functions

#### `get_profile_stats(name=None)`

Get profiling statistics for function(s).

**Args**:
- `name` (str, optional): Function name (None = all functions)

**Returns**: dict with timing and memory statistics

#### `clear_profile_stats()`

Clear all profiling statistics.

#### `get_cache()`

Get global cache instance.

**Returns**: Global `CacheManager` instance

## 🔗 Related Documentation

- [Phase 8 Guide](phase8-guide.md) - Complete Phase 8 overview
- [Performance Optimization](performance-optimization.md) - Optimization techniques
- [API Reference](api-reference.md) - Complete API documentation
- [Architecture](architecture.md) - System architecture

## 📝 Examples

See complete examples in [`examples/`](../examples/):

- `13_phase8_profiling.py` - Complete profiling example
- `14_caching_strategies.py` - Caching patterns
- `15_performance_analysis.py` - Analysis and optimization

---

**Last Updated**: 2026-01-07
**Phase**: 8 (Performance & Scale)
**Status**: Active
