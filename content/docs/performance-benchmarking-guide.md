# Paracle Performance Benchmarking Guide

**Version**: 1.0 | **Status**: Phase 10 | **Date**: 2026-01-10

Complete guide to performance benchmarking and regression testing in Paracle.

---

## Table of Contents

1. [Overview](#overview)
2. [Quick Start](#quick-start)
3. [Architecture](#architecture)
4. [Creating Benchmarks](#creating-benchmarks)
5. [Running Benchmarks](#running-benchmarks)
6. [Baseline Management](#baseline-management)
7. [Regression Detection](#regression-detection)
8. [CI/CD Integration](#cicd-integration)
9. [Performance Targets](#performance-targets)
10. [Best Practices](#best-practices)
11. [Troubleshooting](#troubleshooting)
12. [FAQ](#faq)

---

## Overview

Paracle's benchmarking system provides:

- **Automated Performance Testing** - Run reproducible benchmarks
- **Regression Detection** - Detect performance degradations automatically
- **Baseline Comparison** - Compare against saved baselines
- **CI/CD Integration** - Block PRs with performance regressions
- **Statistical Analysis** - Mean, median, P95, P99 metrics
- **JSON Output** - Machine-readable results for automation

### Key Features

- ✅ Decorator-based benchmark definitions
- ✅ Warmup iterations for JIT optimization
- ✅ Configurable regression thresholds (default: 15%)
- ✅ Timeout protection
- ✅ Memory usage tracking (optional)
- ✅ Suite organization (grouping related benchmarks)
- ✅ Filtering by pattern matching
- ✅ Verbose mode for detailed statistics

---

## Quick Start

### 1. Run Core Benchmarks

```bash
# Run all benchmarks
paracle benchmark run

# Run with baseline comparison
paracle benchmark run --baseline .benchmarks/baseline.json

# Run and fail if regression detected
paracle benchmark run --fail-on-regression

# Run with verbose output
paracle benchmark run --verbose
```

### 2. List Available Benchmarks

```bash
paracle benchmark list
```

### 3. Save as Baseline

```bash
paracle benchmark save --input .benchmarks/results.json --output .benchmarks/baseline.json
```

### 4. Compare Results

```bash
paracle benchmark compare .benchmarks/baseline.json .benchmarks/results.json
```

---

## Architecture

### Components

```
┌──────────────────────────────────────────────────────────────┐
│                    Benchmark System                           │
│                                                              │
│  ┌────────────┐  ┌────────────┐  ┌────────────────────────┐ │
│  │ Benchmark  │  │  Suite     │  │  CLI Commands          │ │
│  │ (Decorator)│  │  (Group)   │  │  (run/list/compare)    │ │
│  └─────┬──────┘  └─────┬──────┘  └──────────┬─────────────┘ │
│        │               │                    │               │
│        └───────────────┴────────────────────┘               │
│                        │                                    │
│               ┌────────▼──────────┐                         │
│               │  BenchmarkResult   │                         │
│               │  (Statistics)      │                         │
│               └────────┬──────────┘                         │
│                        │                                    │
│               ┌────────▼──────────┐                         │
│               │  Baseline Comparison│                        │
│               │  (Regression Check)│                         │
│               └───────────────────┘                         │
└──────────────────────────────────────────────────────────────┘
```

### Data Model

```python
@dataclass
class BenchmarkResult:
    name: str
    iterations: int
    mean_ms: float
    median_ms: float
    min_ms: float
    max_ms: float
    p50_ms: float
    p95_ms: float
    p99_ms: float
    status: BenchmarkStatus  # PASSED, FAILED, REGRESSION, etc.
    timestamp: str
    baseline_mean_ms: float | None
    regression_percent: float | None
    error: str | None

class BenchmarkStatus(Enum):
    PASSED = "passed"
    FAILED = "failed"
    REGRESSION = "regression"
    IMPROVEMENT = "improvement"
    NO_BASELINE = "no_baseline"
```

---

## Creating Benchmarks

### Basic Benchmark

```python
from paracle_profiling.benchmark import BenchmarkSuite

suite = BenchmarkSuite("my-benchmarks")

@suite.benchmark(iterations=1000)
def bench_simple_operation():
    # Operation to benchmark
    result = 2 + 2
```

### With Configuration

```python
@suite.benchmark(
    iterations=1000,
    warmup=10,
    description="Test agent creation",
    timeout_seconds=30,
)
def bench_agent_creation():
    from paracle_domain.agent import AgentSpec

    spec = AgentSpec(
        agent_id="test",
        name="Test Agent",
        model="gpt-4",
    )
```

### Suite Organization

```python
# Group related benchmarks
suite_api = BenchmarkSuite("api-benchmarks", regression_threshold=0.15)
suite_core = BenchmarkSuite("core-benchmarks", regression_threshold=0.10)

@suite_api.benchmark(iterations=100)
def bench_api_endpoint():
    # Test API endpoint
    pass

@suite_core.benchmark(iterations=5000)
def bench_core_function():
    # Test core function
    pass
```

### Complex Example

```python
from paracle_profiling.benchmark import BenchmarkSuite

suite = BenchmarkSuite("workflow-benchmarks")

# Setup data
test_workflow = create_test_workflow()

@suite.benchmark(
    iterations=50,
    warmup=5,
    description="Workflow execution end-to-end",
)
def bench_workflow_execution():
    result = execute_workflow(test_workflow)
    assert result.status == "completed"

@suite.benchmark(
    iterations=200,
    warmup=10,
    description="Agent resolution with inheritance",
)
def bench_agent_inheritance():
    from paracle_core.parac.agent_discovery import AgentDiscovery
    discovery = AgentDiscovery(parac_root)
    agent = discovery.resolve_agent("specialized-agent")
```

---

## Running Benchmarks

### CLI Commands

#### 1. Run All Benchmarks

```bash
paracle benchmark run
```

**Output**:
```
Running 8 benchmarks...

✓ bench_agent_spec_creation    1000 iterations in 125.45ms
  Mean: 0.13ms | Median: 0.12ms | P95: 0.18ms | P99: 0.25ms

✓ bench_cache_set              5000 iterations in 89.32ms
  Mean: 0.02ms | Median: 0.01ms | P95: 0.04ms | P99: 0.06ms

...

Results saved to .benchmarks/results.json
```

#### 2. With Baseline Comparison

```bash
paracle benchmark run --baseline .benchmarks/baseline.json
```

**Output**:
```
✓ bench_agent_spec_creation    Mean: 0.13ms (baseline: 0.12ms, +8.3%)
⚠ bench_cache_set               Mean: 0.03ms (baseline: 0.02ms, +50.0%) REGRESSION!
```

#### 3. Filter Benchmarks

```bash
# Run only benchmarks matching pattern
paracle benchmark run --filter "cache"

# This will run:
# - bench_cache_set
# - bench_cache_get
# - bench_cache_cycle
```

#### 4. Verbose Output

```bash
paracle benchmark run --verbose
```

**Shows**:
- All percentiles (P50, P75, P90, P95, P99)
- Warmup statistics
- Memory usage (if available)
- Standard deviation

#### 5. JSON Output

```bash
paracle benchmark run --json-output > results.json
```

**Output Format**:
```json
{
  "suite_name": "paracle-core",
  "total_benchmarks": 8,
  "passed": 7,
  "failed": 0,
  "regressions": 1,
  "timestamp": "2026-01-10T10:30:00Z",
  "results": [
    {
      "name": "bench_agent_spec_creation",
      "iterations": 1000,
      "mean_ms": 0.125,
      "median_ms": 0.120,
      "p95_ms": 0.180,
      "status": "passed"
    }
  ]
}
```

#### 6. Fail on Regression

```bash
paracle benchmark run --fail-on-regression
```

Exits with code `1` if any regression detected (for CI/CD).

---

## Baseline Management

### Creating a Baseline

```bash
# Run benchmarks first
paracle benchmark run --output .benchmarks/results.json

# Save as baseline
paracle benchmark save --input .benchmarks/results.json --output .benchmarks/baseline.json
```

### Updating Baseline

```bash
# After verifying new performance is acceptable
paracle benchmark save --input .benchmarks/results.json --output .benchmarks/baseline.json --overwrite
```

### Baseline File Format

```json
{
  "suite_name": "paracle-core",
  "timestamp": "2026-01-10T10:00:00Z",
  "results": [
    {
      "name": "bench_agent_spec_creation",
      "mean_ms": 0.125,
      "median_ms": 0.120,
      "p95_ms": 0.180
    }
  ]
}
```

### Multiple Baselines

```bash
# Branch-specific baselines
paracle benchmark run --baseline .benchmarks/baseline-main.json
paracle benchmark run --baseline .benchmarks/baseline-develop.json

# Environment-specific
paracle benchmark run --baseline .benchmarks/baseline-macos.json
paracle benchmark run --baseline .benchmarks/baseline-linux.json
```

---

## Regression Detection

### How It Works

1. **Run Benchmark** - Execute benchmark and measure performance
2. **Load Baseline** - Load baseline from file (if provided)
3. **Calculate Delta** - Compare current vs baseline
4. **Check Threshold** - Flag if regression > threshold (default: 15%)
5. **Report Status** - `REGRESSION` or `PASSED`

### Regression Formula

```
regression_percent = ((current_mean - baseline_mean) / baseline_mean) * 100

if regression_percent > threshold:
    status = REGRESSION
```

### Configuring Thresholds

#### Per Suite

```python
# Strict suite (10% threshold)
suite = BenchmarkSuite("critical-ops", regression_threshold=0.10)

# Lenient suite (25% threshold)
suite = BenchmarkSuite("ui-ops", regression_threshold=0.25)
```

#### Per Benchmark

```python
@suite.benchmark(
    iterations=1000,
    regression_threshold=0.05,  # 5% threshold for this benchmark only
)
def bench_critical_operation():
    pass
```

### Example Output

```
✓ bench_agent_spec_creation    Mean: 0.13ms (baseline: 0.12ms, +8.3%) PASSED
⚠ bench_cache_set               Mean: 0.03ms (baseline: 0.02ms, +50.0%) REGRESSION!
↗ bench_cache_get               Mean: 0.01ms (baseline: 0.02ms, -50.0%) IMPROVEMENT!
? bench_new_feature             Mean: 0.15ms NO BASELINE
```

---

## CI/CD Integration

### GitHub Actions Example

```yaml
name: Performance Benchmarks

on:
  pull_request:
    branches: [main, develop]
  push:
    branches: [main]

jobs:
  benchmark:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4

      - name: Set up Python
        uses: actions/setup-python@v5
        with:
          python-version: '3.10'

      - name: Install dependencies
        run: |
          pip install uv
          uv sync --all-extras

      - name: Download baseline
        uses: actions/download-artifact@v3
        with:
          name: benchmark-baseline
          path: .benchmarks/
        continue-on-error: true

      - name: Run benchmarks
        run: |
          uv run paracle benchmark run \
            --baseline .benchmarks/baseline.json \
            --output .benchmarks/results.json \
            --fail-on-regression \
            --verbose

      - name: Upload results
        uses: actions/upload-artifact@v3
        with:
          name: benchmark-results
          path: .benchmarks/results.json

      - name: Comment PR
        if: github.event_name == 'pull_request'
        uses: actions/github-script@v7
        with:
          script: |
            const fs = require('fs');
            const results = JSON.parse(fs.readFileSync('.benchmarks/results.json'));

            let comment = `## 📊 Benchmark Results\n\n`;
            comment += `Total: ${results.total_benchmarks} | Passed: ${results.passed} | Regressions: ${results.regressions}\n\n`;

            if (results.regressions > 0) {
              comment += `⚠️ **Performance regressions detected!**\n\n`;
              comment += `| Benchmark | Current | Baseline | Change |\n`;
              comment += `|-----------|---------|----------|--------|\n`;
              results.results.filter(r => r.status === 'regression').forEach(r => {
                comment += `| ${r.name} | ${r.mean_ms}ms | ${r.baseline_mean_ms}ms | +${r.regression_percent.toFixed(1)}% |\n`;
              });
            } else {
              comment += `✅ All benchmarks passed!\n`;
            }

            github.rest.issues.createComment({
              issue_number: context.issue.number,
              owner: context.repo.owner,
              repo: context.repo.repo,
              body: comment
            });

      - name: Update baseline (main only)
        if: github.ref == 'refs/heads/main'
        run: |
          uv run paracle benchmark save \
            --input .benchmarks/results.json \
            --output .benchmarks/baseline.json \
            --overwrite

      - name: Upload new baseline
        if: github.ref == 'refs/heads/main'
        uses: actions/upload-artifact@v3
        with:
          name: benchmark-baseline
          path: .benchmarks/baseline.json
```

### GitLab CI Example

```yaml
benchmark:
  stage: test
  script:
    - pip install uv
    - uv sync --all-extras
    - uv run paracle benchmark run --baseline baseline.json --fail-on-regression
  artifacts:
    reports:
      junit: .benchmarks/results.xml
    paths:
      - .benchmarks/results.json
  only:
    - merge_requests
    - main
```

### Pre-commit Hook

```bash
# .git/hooks/pre-push
#!/bin/bash
echo "Running performance benchmarks..."
uv run paracle benchmark run --baseline .benchmarks/baseline.json --fail-on-regression

if [ $? -ne 0 ]; then
    echo "❌ Performance regression detected! Push blocked."
    exit 1
fi
```

---

## Performance Targets

### Core Operations (v1.0.0)

| Operation             | Target (mean) | P95     | Baseline |
| --------------------- | ------------- | ------- | -------- |
| Agent spec creation   | < 0.2ms       | < 0.5ms | 0.13ms ✅ |
| Config load           | < 2ms         | < 5ms   | 1.85ms ✅ |
| Cache set             | < 0.05ms      | < 0.1ms | 0.02ms ✅ |
| Cache get             | < 0.05ms      | < 0.1ms | 0.01ms ✅ |
| Cache cycle (set+get) | < 0.1ms       | < 0.2ms | 0.06ms ✅ |
| Agent discovery       | < 50ms        | < 100ms | 42ms ✅   |

### API Operations (v1.0.0)

| Endpoint                | Target (P95) | Status  |
| ----------------------- | ------------ | ------- |
| GET /health             | < 10ms       | ✅ 5ms   |
| GET /agents             | < 50ms       | ✅ 38ms  |
| POST /agents            | < 100ms      | ✅ 87ms  |
| POST /workflows/execute | < 500ms      | ✅ 420ms |
| GET /workflows/status   | < 50ms       | ✅ 42ms  |

### Workflow Operations (v1.0.0)

| Operation                     | Target | Status |
| ----------------------------- | ------ | ------ |
| Simple workflow (1 step)      | < 2s   | ✅ 1.5s |
| Complex workflow (5 steps)    | < 10s  | ✅ 8.2s |
| Parallel execution (3 agents) | < 5s   | ✅ 4.1s |

---

## Best Practices

### 1. Benchmark Design

✅ **DO**:
- Focus on critical paths (hot code)
- Use realistic data sizes
- Include warmup iterations (10-100)
- Test both cold and warm paths
- Benchmark atomic operations

❌ **DON'T**:
- Benchmark I/O-heavy operations (use mocks)
- Include external API calls (flaky)
- Benchmark trivial operations (noise)
- Mix setup/teardown with measurement

### 2. Iteration Count

```python
# Fast operations: Many iterations
@suite.benchmark(iterations=5000)  # < 1ms each
def bench_fast_operation():
    cache.get("key")

# Slow operations: Fewer iterations
@suite.benchmark(iterations=50)    # > 10ms each
def bench_slow_operation():
    execute_workflow(complex_workflow)

# Medium operations: Balanced
@suite.benchmark(iterations=500)   # 1-10ms each
def bench_medium_operation():
    agent_discovery.resolve_agent("agent")
```

### 3. Warmup

```python
# JIT warmup for hot code
@suite.benchmark(iterations=1000, warmup=100)  # 10% warmup
def bench_hot_path():
    # Critical code path
    pass

# Minimal warmup for I/O
@suite.benchmark(iterations=100, warmup=5)     # 5% warmup
def bench_io_operation():
    # I/O bound operation
    pass
```

### 4. Baseline Strategy

```bash
# 1. Create initial baseline
paracle benchmark run --output baseline_v1.0.0.json

# 2. Run against baseline on each PR
paracle benchmark run --baseline baseline_v1.0.0.json --fail-on-regression

# 3. Update baseline after major refactoring (with approval)
paracle benchmark run --output new_baseline.json
# Review changes, then:
mv new_baseline.json baseline_v1.0.0.json
```

### 5. CI/CD Integration

```yaml
# Run on every PR
on: pull_request

# Fail on regression (blocks merge)
run: paracle benchmark run --fail-on-regression

# Update baseline only on main
if: github.ref == 'refs/heads/main'
run: paracle benchmark save --overwrite
```

---

## Troubleshooting

### Issue: Benchmarks are flaky (results vary)

**Causes**:
- Shared system resources (CPU contention)
- Garbage collection interference
- Thermal throttling
- Background processes

**Solutions**:
```python
# 1. Increase iterations
@suite.benchmark(iterations=10000)  # More samples = less noise

# 2. Add warmup
@suite.benchmark(iterations=1000, warmup=100)

# 3. Use median instead of mean (less affected by outliers)
# Already reported by default

# 4. Run on dedicated CI runner
# GitHub Actions: ubuntu-latest-4core
```

### Issue: Regression threshold too strict

**Solution**:
```python
# Increase threshold for noisy benchmarks
@suite.benchmark(
    iterations=1000,
    regression_threshold=0.25,  # 25% tolerance
)
def bench_noisy_operation():
    pass
```

### Issue: Benchmarks timeout

**Solution**:
```python
# Increase timeout
@suite.benchmark(
    iterations=100,
    timeout_seconds=60,  # 1 minute
)
def bench_slow_operation():
    pass

# Or reduce iterations
@suite.benchmark(iterations=10)  # Fewer iterations
```

### Issue: Out of memory

**Solution**:
```python
# 1. Reduce iterations
@suite.benchmark(iterations=10)

# 2. Add teardown to free memory
@suite.benchmark(iterations=100)
def bench_memory_intensive():
    data = allocate_large_dataset()
    process(data)
    del data  # Free memory
    gc.collect()  # Force collection
```

### Issue: Import errors in benchmarks

**Solution**:
```python
# Wrap imports in try/except
try:
    from paracle_domain.agent import AgentSpec

    @suite.benchmark(iterations=1000)
    def bench_agent_creation():
        AgentSpec(name="test", model="gpt-4")
except ImportError:
    pass  # Skip if package not installed
```

---

## FAQ

### Q: What is a good regression threshold?

**A**: Depends on the operation:
- **Critical paths** (agent execution, API): 10-15%
- **Normal operations** (parsing, validation): 15-20%
- **Noisy operations** (filesystem, network mocks): 20-30%

### Q: How many iterations should I use?

**A**: Rule of thumb:
- **< 1ms per iteration**: 5000-10000 iterations
- **1-10ms per iteration**: 500-1000 iterations
- **10-100ms per iteration**: 50-200 iterations
- **> 100ms per iteration**: 10-50 iterations

Target: Total benchmark time of 1-10 seconds.

### Q: Should I benchmark I/O operations?

**A**: No, benchmark logic only:
```python
# ❌ BAD - includes network latency
@suite.benchmark(iterations=100)
def bench_api_call():
    response = requests.get("https://api.example.com")

# ✅ GOOD - mocked I/O
@suite.benchmark(iterations=100)
def bench_api_parsing(mocker):
    mocker.patch("requests.get", return_value=mock_response)
    response = requests.get("https://api.example.com")
    parse_response(response)
```

### Q: Can I benchmark async code?

**A**: Not directly, but you can:
```python
import asyncio

@suite.benchmark(iterations=100)
def bench_async_operation():
    asyncio.run(async_function())
```

### Q: How do I exclude benchmarks from CI?

**A**: Use filtering:
```bash
# Run only core benchmarks
paracle benchmark run --filter "core"

# Exclude slow benchmarks
paracle benchmark run --filter "^((?!slow).)*$"
```

### Q: What if performance varies by OS?

**A**: Use OS-specific baselines:
```bash
# macOS baseline
paracle benchmark run --baseline .benchmarks/baseline-macos.json

# Linux baseline
paracle benchmark run --baseline .benchmarks/baseline-linux.json

# Windows baseline
paracle benchmark run --baseline .benchmarks/baseline-windows.json
```

---

## Related Documentation

- [Profiling Guide](technical/profiling-guide.md) - Function-level profiling
- [Performance Optimization](technical/performance-optimization.md) - Optimization techniques
- [CI/CD Pipeline](../content/docs/cicd-pipeline.md) - CI/CD configuration
- [Test Coverage](../content/docs/testing-guide.md) - Unit/integration testing

---

**Status**: Phase 10 Complete ✅ | **Version**: 1.0.0 | **Date**: 2026-01-10

