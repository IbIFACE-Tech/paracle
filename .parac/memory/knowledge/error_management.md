# Paracle Error Management System

## Overview

Paracle has a **comprehensive, production-ready error management system** already implemented across multiple packages:

- **`paracle_resilience`** - Circuit breakers, fallback strategies, and fault tolerance
- **`paracle_observability`** - Error registry, tracking, analytics, and reporting
- **API-first CLI** - Automatic fallback from API to direct core access

## Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                    CLI Commands                             │
│              (board, task, parac, etc.)                     │
└───────────────────────┬─────────────────────────────────────┘
                        │
                        ↓
┌─────────────────────────────────────────────────────────────┐
│         use_api_or_fallback() with ErrorRegistry           │
│                                                             │
│  ┌──────────────┐         ┌──────────────┐                │
│  │   API Mode   │ -----→  │  Fallback    │                │
│  │  (Primary)   │  fail   │  (Direct)    │                │
│  └──────────────┘         └──────────────┘                │
│         │                        │                          │
│         └────────┬───────────────┘                          │
│                  ↓                                          │
│    paracle_observability.ErrorRegistry                     │
│         - Record all errors                                 │
│         - Deduplicate similar errors                       │
│         - Track patterns                                   │
│         - Generate analytics                               │
└─────────────────────────────────────────────────────────────┘
                        ↓
┌─────────────────────────────────────────────────────────────┐
│              paracle_resilience                             │
│                                                             │
│  CircuitBreaker      FallbackStrategy    RetryFallback    │
│  - Auto-recovery     - Cached response   - Exponential    │
│  - State management  - Default values    - backoff        │
│  - Failure tracking  - Degraded mode     - Jitter         │
└─────────────────────────────────────────────────────────────┘
```

## Existing Error Management Components

### 1. **ErrorRegistry** (`paracle_observability`)

**Purpose**: Centralized error tracking, analytics, and pattern detection

**Features**:
- ✅ Automatic error recording with context
- ✅ Deduplication (count similar errors)
- ✅ Pattern detection (cascading, high-frequency)
- ✅ Severity classification (DEBUG/INFO/WARNING/ERROR/CRITICAL)
- ✅ Component-based tracking
- ✅ Statistics and analytics
- ✅ Time-series analysis

**CLI Access**:
```bash
paracle errors stats      # View statistics
paracle errors list       # Browse errors
paracle errors patterns   # Detect patterns
paracle errors clear      # Clear registry
```

### 2. **CircuitBreaker** (`paracle_resilience`)

**Purpose**: Prevent cascading failures through automatic failure detection

**States**:
- **CLOSED**: Normal operation (requests pass through)
- **OPEN**: Too many failures (reject immediately, fast-fail)
- **HALF_OPEN**: Testing recovery (limited requests)

**Usage**:
```python
from paracle_resilience import CircuitBreaker

circuit = CircuitBreaker(
    name="api_service",
    failure_threshold=5,  # Open after 5 failures
    timeout=60.0,        # Wait 60s before half-open
)

# Automatic protection
async with circuit:
    result = await api_call()
```

### 3. **FallbackStrategy** (`paracle_resilience`)

**Purpose**: Graceful degradation when primary operations fail

**Available Strategies**:
- **CachedResponseFallback**: Return cached data
- **DefaultValueFallback**: Return safe default
- **RetryFallback**: Retry with exponential backoff
- **DegradedServiceFallback**: Use degraded service
- **FallbackChain**: Try multiple strategies sequentially

**Usage**:
```python
from paracle_resilience import FallbackChain, CachedResponseFallback

fallback = FallbackChain([
    CachedResponseFallback(cache_ttl=300),
    DefaultValueFallback(default={"status": "degraded"}),
])

try:
    result = service.call()
except Exception as e:
    result = await fallback.execute(lambda: service.call(), e)
```

### 4. **API-First with Fallback** (`paracle_cli`)

**Purpose**: Users can run Paracle WITHOUT API server

**Implementation**: `use_api_or_fallback()` in `api_client.py`

```python
def use_api_or_fallback(api_func, fallback_func, *args, **kwargs):
    """API-first with automatic fallback to direct core."""
    registry = get_error_registry()

    # Try API
    if client.is_available():
        try:
            return api_func(client, *args, **kwargs)
        except Exception as e:
            registry.record_error(e, "api_client")
            # Fall through to fallback...

    # Try direct core access
    try:
        return fallback_func(*args, **kwargs)
    except Exception as e:
        registry.record_error(e, "fallback_execution", severity=CRITICAL)
        raise  # No more fallbacks available
```

## Recent Improvements (2026-01-09)

### Fixed Issues:

1. **✅ Warning Spam Eliminated**
   - Changed `warnings.warn()` to `logger.debug()` for defusedxml
   - Clean CLI output, no clutter

2. **✅ API Connection Errors Handled**
   - Added `httpx.ConnectError` and `OSError` catching
   - Windows connection errors (WinError 10061) properly handled
   - All errors logged to ErrorRegistry with DEBUG severity

3. **✅ Enum Value Handling Fixed**
   - Fixed `.value` access on Pydantic models with `use_enum_values = True`
   - Added defensive `hasattr()` checks
   - Works in both API and fallback modes

4. **✅ Error CLI Commands Added**
   - `paracle errors stats` - Statistics and metrics
   - `paracle errors list` - Browse error history
   - `paracle errors patterns` - Detect error patterns
   - `paracle errors clear` - Clear error registry

## Error Management Principles

### 1. **Silent Failures (Expected)**

Errors that are **expected** and **handled** should be DEBUG level only:

- API server not running → DEBUG (use fallback)
- Missing optional dependency → DEBUG (use alternative)
- Cache miss → DEBUG (fetch fresh data)

**User sees**: Clean operation, no warnings

### 2. **Graceful Degradation (Warning)**

Errors that cause **degraded functionality** but allow continued operation:

- API error with fallback available → WARNING
- Slow response time → WARNING
- Partial data returned → WARNING

**User sees**: Brief warning + successful result

### 3. **Operation Failure (Error)**

Errors that **prevent** the requested operation but system continues:

- Invalid input → ERROR
- Resource not found → ERROR
- Permission denied → ERROR

**User sees**: Clear error message

### 4. **System Failure (Critical)**

Errors with **no fallback** available:

- Database corruption → CRITICAL
- Out of memory → CRITICAL
- Fallback execution failed → CRITICAL

**User sees**: Error message + system exits

## Integration Example

Here's how all components work together:

```python
from paracle_resilience import CircuitBreaker, FallbackChain, CachedResponseFallback
from paracle_observability import get_error_registry

# Setup circuit breaker
circuit = CircuitBreaker("api_service", failure_threshold=5)

# Setup fallback chain
fallback = FallbackChain([
    CachedResponseFallback(cache_ttl=300),
    DefaultValueFallback(default=[]),
])

# Get error registry
registry = get_error_registry()

async def get_boards():
    """Get boards with full error management."""
    try:
        # Try API with circuit breaker
        async with circuit:
            return await api.boards_list()

    except CircuitOpenError as e:
        # Circuit open - use fallback immediately
        registry.record_error(e, "api_circuit", severity=ErrorSeverityLevel.WARNING)
        return await fallback.execute_async(api.boards_list, e)

    except Exception as e:
        # API failed - try fallback
        registry.record_error(e, "api_call", severity=ErrorSeverityLevel.WARNING)

        try:
            return await fallback.execute_async(api.boards_list, e)
        except Exception as fallback_error:
            # Total failure
            registry.record_error(
                fallback_error,
                "fallback_execution",
                severity=ErrorSeverityLevel.CRITICAL
            )
            raise
```

## CLI Error Management Commands

### View Statistics

```bash
$ paracle errors stats

Error Registry Statistics

  Total errors: 25
  Unique errors: 8
  Error rate: 0.15 errors/min
  Recent (1h): 9
  Uptime: 2.5 hours
  Patterns detected: 2
```

### List Errors

```bash
# All errors
$ paracle errors list

# Filter by component
$ paracle errors list --component api_client

# Filter by severity
$ paracle errors list --severity error

# Limit results
$ paracle errors list --limit 50
```

### Detect Patterns

```bash
$ paracle errors patterns

Detected Error Patterns

1. Pattern Type: high_frequency
   Error type: ConnectError
   Count: 15
   Time window: 1_minute
```

### Clear Registry

```bash
$ paracle errors clear
```

## Best Practices

### ✅ DO

1. **Use ErrorRegistry for all errors**
   ```python
   registry.record_error(error, component="my_component", context={...})
   ```

2. **Use CircuitBreaker for external services**
   ```python
   async with circuit_breaker:
       await external_api.call()
   ```

3. **Use FallbackStrategy for graceful degradation**
   ```python
   fallback = FallbackChain([cached, default])
   ```

4. **Log at appropriate levels**
   - DEBUG: Expected failures with fallbacks
   - WARNING: Degraded operation
   - ERROR: Operation failed
   - CRITICAL: System failure

### ❌ DON'T

1. **Don't use warnings.warn()** → Use `logger.debug()` or ErrorRegistry
2. **Don't ignore errors** → Always record to ErrorRegistry
3. **Don't print errors** → Use proper logging + ErrorRegistry
4. **Don't create parallel error systems** → Use existing infrastructure

## Architecture Packages

| Package                   | Purpose                    | Key Components                                  |
| ------------------------- | -------------------------- | ----------------------------------------------- |
| **paracle_observability** | Error tracking & analytics | ErrorRegistry, ErrorReporter, ErrorDashboard    |
| **paracle_resilience**    | Fault tolerance            | CircuitBreaker, FallbackStrategy, RetryFallback |
| **paracle_cli**           | User interface             | use_api_or_fallback, error commands             |
| **paracle_core**          | Core exceptions            | ParacleError hierarchy                          |

## Related Documentation

- [Circuit Breaker Pattern](../packages/paracle_resilience/circuit_breaker.py)
- [Fallback Strategies](../packages/paracle_resilience/fallback.py)
- [Error Registry](../packages/paracle_observability/error_registry.py)
- [Error Reporter](../packages/paracle_observability/error_reporter.py)

---

**Status**: ✅ Fully Implemented (Production-Ready)
**Version**: 1.0.0
**Last Updated**: 2026-01-09


## Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                    CLI Commands                             │
│              (board, task, parac, etc.)                     │
└───────────────────────┬─────────────────────────────────────┘
                        │
                        ↓
┌─────────────────────────────────────────────────────────────┐
│              use_api_or_fallback()                          │
│                                                             │
│  ┌──────────────┐         ┌──────────────┐                │
│  │   API Mode   │ -----→  │  Fallback    │                │
│  └──────────────┘  fail   └──────────────┘                │
│         │                        │                          │
│         └────────┬───────────────┘                          │
│                  ↓                                          │
│          ErrorRegistry.record_error()                      │
│                  ↓                                          │
│     All errors tracked & analyzed                          │
└─────────────────────────────────────────────────────────────┘
```

## Error Management Principles

### 1. **API-First with Graceful Fallback**

```python
# All CLI commands use this pattern:
result = use_api_or_fallback(
    api_func=_api_list_boards,
    fallback_func=_fallback_list_boards,
    **params
)
```

**Benefits:**
- User can run Paracle **WITHOUT API server**
- Seamless transition between modes
- No user-facing errors for connection issues

### 2. **Centralized Error Tracking**

ALL errors go through `ErrorRegistry`:

```python
from paracle_observability import get_error_registry

registry = get_error_registry()
registry.record_error(
    error=exception,
    component="api_client",
    severity=ErrorSeverityLevel.WARNING,
    context={"additional": "info"},
)
```

### 3. **Error Classification**

Errors are classified by:
- **Component**: Where the error occurred (api_client, fallback_execution, etc.)
- **Severity**: DEBUG, INFO, WARNING, ERROR, CRITICAL
- **Context**: Additional metadata for debugging
- **Deduplication**: Similar errors are counted, not duplicated

### 4. **Proper Logging Levels**

- **DEBUG**: Expected issues (API not available, feature not used)
- **WARNING**: Degraded functionality (API error, falling back to direct)
- **ERROR**: Operation failed but system continues
- **CRITICAL**: Operation failed with no fallback available

## Error Flow Examples

### Example 1: API Unavailable (Normal Operation)

```
User: paracle board list
↓
CLI checks API → Connection refused
↓
ErrorRegistry records (DEBUG level):
  - Component: "api_health_check"
  - Error: ConnectError
  - Context: {"api_url": "http://localhost:8000"}
↓
CLI falls back to direct core access
↓
User sees clean output: boards listed ✓
```

**No user-facing warning** - this is expected behavior!

### Example 2: API Error (Fallback Available)

```
User: paracle board get board_123
↓
CLI calls API → 500 Internal Server Error
↓
ErrorRegistry records (WARNING level):
  - Component: "api_client"
  - Error: APIError(500)
  - Context: {"status_code": 500, "function": "_api_get_board"}
↓
User sees: "⚠ API error: Internal error. Falling back..."
↓
CLI falls back to direct core access
↓
User gets the board data ✓
```

### Example 3: Total Failure (No Fallback)

```
User: paracle board get nonexistent_board
↓
CLI tries API → Not available
↓
CLI tries fallback → Board not found
↓
ErrorRegistry records (CRITICAL level):
  - Component: "fallback_execution"
  - Error: ValueError("Board not found")
  - Context: {"fallback_failed": True}
↓
User sees: "❌ Error: Board 'nonexistent_board' not found"
```

## Error Monitoring Commands

### View Error Statistics

```bash
$ paracle errors stats

Error Registry Statistics

  Total errors: 25
  Unique errors: 8
  Error rate: 0.15 errors/min
  Recent (1h): 9
  Uptime: 2.5 hours
  Patterns detected: 2

Severity Breakdown:
  • debug: 18
  • warning: 5
  • error: 2

Top Error Types:
  • ConnectError: 15
  • APIError: 5
  • ValueError: 3
```

### List Recent Errors

```bash
$ paracle errors list --limit 10
$ paracle errors list --component api_client
$ paracle errors list --severity error
```

### Detect Patterns

```bash
$ paracle errors patterns

Detected Error Patterns

1. Pattern Type: high_frequency
   Error type: ConnectError
   Count: 15
   Time window: 1_minute

2. Pattern Type: cascading
   Component: api_client
   Count: 8
   Time window: 1_minute
```

### Clear Errors

```bash
$ paracle errors clear
```

## Error Registry Features

### Automatic Pattern Detection

The error registry automatically detects:

1. **High-frequency errors** - Same error type occurring many times rapidly
2. **Cascading errors** - Multiple errors in the same component
3. **Error correlation** - Related errors across components

### Deduplication

Similar errors are deduplicated and counted:

```python
# First occurrence
ErrorRecord(id="api:ConnectError:12345", count=1)

# Second occurrence (same error)
# count incremented to 2, last_seen updated
```

### Context Preservation

All error context is preserved:

```python
{
    "id": "error_abc123",
    "timestamp": 1736454321.5,
    "error_type": "APIError",
    "message": "Connection refused",
    "component": "api_client",
    "severity": "warning",
    "context": {
        "api_url": "http://localhost:8000",
        "status_code": None,
        "function": "_api_list_boards",
        "fallback_available": True
    },
    "stack_trace": "...",
    "count": 3,
    "first_seen": 1736454320.1,
    "last_seen": 1736454321.5
}
```

## Implementation Details

### 1. Warning Suppression (Best Practice)

**Before:**
```python
import warnings
warnings.warn("defusedxml not installed...", UserWarning)
# ❌ Shown to user on EVERY command!
```

**After:**
```python
import logging
logger.debug("defusedxml not installed...")
# ✓ Only visible when debugging enabled
```

### 2. Error Boundary in use_api_or_fallback

```python
def use_api_or_fallback(api_func, fallback_func, *args, **kwargs):
    """ALL errors managed here."""
    registry = get_error_registry()

    # Try API
    if client.is_available():
        try:
            return api_func(client, *args, **kwargs)
        except Exception as e:
            registry.record_error(e, "api_client")
            # Fall back...

    # Try fallback
    try:
        return fallback_func(*args, **kwargs)
    except Exception as e:
        registry.record_error(e, "fallback_execution", severity=CRITICAL)
        raise  # No more fallbacks!
```

### 3. Singleton Pattern

```python
_global_registry: ErrorRegistry | None = None

def get_error_registry() -> ErrorRegistry:
    global _global_registry
    if _global_registry is None:
        _global_registry = ErrorRegistry()
    return _global_registry
```

**Note:** Errors are in-memory per process. For persistent tracking across sessions, errors would need to be persisted to `.parac/memory/data/errors.db`.

## Benefits

✅ **User Experience**
- Clean output (no warning spam)
- Works offline (no API required)
- Graceful degradation

✅ **Developer Experience**
- Centralized error tracking
- Pattern detection
- Full error context
- Easy debugging

✅ **Production Ready**
- Proper logging levels
- Error analytics
- Pattern detection
- Security-aware (defusedxml warning only when needed)

✅ **Observability**
- Error statistics
- Component health
- Error trends
- Automated alerting (via ErrorRegistry)

## Future Enhancements

1. **Persistent Error Storage** - Save to `.parac/memory/data/errors.db`
2. **Error Alerts** - Notify on critical error patterns
3. **Error Dashboard** - Web UI for error visualization
4. **Automated Reports** - Daily/weekly error summaries
5. **Error Recovery** - Automatic retry with exponential backoff

## Related Files

- `packages/paracle_cli/api_client.py` - use_api_or_fallback implementation
- `packages/paracle_observability/error_registry.py` - ErrorRegistry
- `packages/paracle_cli/commands/errors.py` - Error monitoring CLI
- `packages/paracle_observability/error_reporter.py` - Automated reporting

---

**Status**: ✅ Implemented
**Version**: 1.0.0
**Last Updated**: 2026-01-09
