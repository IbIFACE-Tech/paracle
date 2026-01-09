"""Paracle Performance Profiling Package.

Provides tools for profiling, monitoring, and optimizing performance:
- Request profiling middleware
- Function-level profiling decorators
- Multi-level caching (response, query, LLM)
- Benchmarking suite with regression detection
- Database query profiling
- Memory profiling
- Performance analysis and reporting

Phase 8 - Performance & Scale deliverables included.
"""

from paracle_profiling.analyzer import PerformanceAnalyzer
from paracle_profiling.benchmark import (
    Benchmark,
    BenchmarkResult,
    BenchmarkStatus,
    BenchmarkSuite,
    BenchmarkSuiteResult,
    benchmark,
    get_default_suite,
    run_benchmarks,
)
from paracle_profiling.cache import (
    CacheEntry,
    CacheLayer,
    CacheManager,
    MultiLevelCache,
    cache_llm,
    cache_llm_async,
    cache_query,
    cache_response,
    cached,
    get_cache,
    get_multi_level_cache,
)
from paracle_profiling.profiler import (
    Profiler,
    clear_profile_stats,
    get_profile_stats,
    profile,
    profile_async,
)

# Optional middleware - only available if starlette is installed
try:
    from paracle_profiling.middleware import ProfilerMiddleware

    __all__ = [
        # Middleware
        "ProfilerMiddleware",
        # Profiler
        "Profiler",
        "profile",
        "profile_async",
        "get_profile_stats",
        "clear_profile_stats",
        # Analyzer
        "PerformanceAnalyzer",
        # Single-level cache
        "CacheManager",
        "CacheEntry",
        "cached",
        "get_cache",
        # Multi-level cache (Phase 8)
        "CacheLayer",
        "MultiLevelCache",
        "get_multi_level_cache",
        "cache_response",
        "cache_query",
        "cache_llm",
        "cache_llm_async",
        # Benchmarking suite (Phase 8)
        "Benchmark",
        "BenchmarkResult",
        "BenchmarkStatus",
        "BenchmarkSuite",
        "BenchmarkSuiteResult",
        "benchmark",
        "get_default_suite",
        "run_benchmarks",
    ]
except ImportError:
    # Starlette not available - middleware disabled
    __all__ = [
        # Profiler
        "Profiler",
        "profile",
        "profile_async",
        "get_profile_stats",
        "clear_profile_stats",
        # Analyzer
        "PerformanceAnalyzer",
        # Single-level cache
        "CacheManager",
        "CacheEntry",
        "cached",
        "get_cache",
        # Multi-level cache (Phase 8)
        "CacheLayer",
        "MultiLevelCache",
        "get_multi_level_cache",
        "cache_response",
        "cache_query",
        "cache_llm",
        "cache_llm_async",
        # Benchmarking suite (Phase 8)
        "Benchmark",
        "BenchmarkResult",
        "BenchmarkStatus",
        "BenchmarkSuite",
        "BenchmarkSuiteResult",
        "benchmark",
        "get_default_suite",
        "run_benchmarks",
    ]

__version__ = "0.1.0"
