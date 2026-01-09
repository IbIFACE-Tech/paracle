"""Performance profiler with timing and metrics collection."""

import functools
import logging
import time
from collections import defaultdict
from collections.abc import Callable
from dataclasses import dataclass, field
from typing import Any

logger = logging.getLogger(__name__)


@dataclass
class ProfileEntry:
    """Single profiling entry."""

    name: str
    start_time: float
    end_time: float
    duration: float
    memory_start: int | None = None
    memory_end: int | None = None
    metadata: dict[str, Any] = field(default_factory=dict)

    @property
    def memory_delta(self) -> int | None:
        """Memory change in bytes."""
        if self.memory_start is not None and self.memory_end is not None:
            return self.memory_end - self.memory_start
        return None


class Profiler:
    """Global profiler for collecting performance metrics."""

    _stats: dict[str, list[ProfileEntry]] = defaultdict(list)
    _enabled: bool = True

    @classmethod
    def enable(cls) -> None:
        """Enable profiling."""
        cls._enabled = True
        logger.info("Profiler enabled")

    @classmethod
    def disable(cls) -> None:
        """Disable profiling."""
        cls._enabled = False
        logger.info("Profiler disabled")

    @classmethod
    def is_enabled(cls) -> bool:
        """Check if profiling is enabled."""
        return cls._enabled

    @classmethod
    def record(cls, entry: ProfileEntry) -> None:
        """Record a profile entry."""
        if cls._enabled:
            cls._stats[entry.name].append(entry)

    @classmethod
    def get_stats(cls, name: str | None = None) -> dict[str, list[ProfileEntry]]:
        """Get profiling statistics."""
        if name:
            return {name: cls._stats.get(name, [])}
        return dict(cls._stats)

    @classmethod
    def clear(cls, name: str | None = None) -> None:
        """Clear profiling statistics."""
        if name:
            cls._stats.pop(name, None)
        else:
            cls._stats.clear()

    @classmethod
    def get_summary(cls, name: str) -> dict[str, Any]:
        """Get summary statistics for a profiled function."""
        entries = cls._stats.get(name, [])
        if not entries:
            return {}

        durations = [e.duration for e in entries]
        memory_deltas = [e.memory_delta for e in entries if e.memory_delta is not None]

        return {
            "name": name,
            "calls": len(entries),
            "total_time": sum(durations),
            "avg_time": sum(durations) / len(durations),
            "min_time": min(durations),
            "max_time": max(durations),
            "p50_time": sorted(durations)[len(durations) // 2],
            "p95_time": (
                sorted(durations)[int(len(durations) * 0.95)]
                if len(durations) > 1
                else durations[0]
            ),
            "p99_time": (
                sorted(durations)[int(len(durations) * 0.99)]
                if len(durations) > 1
                else durations[0]
            ),
            "memory_avg": (
                sum(memory_deltas) / len(memory_deltas) if memory_deltas else None
            ),
            "memory_max": max(memory_deltas) if memory_deltas else None,
        }


def profile(name: str | None = None, track_memory: bool = False) -> Callable:
    """Decorator to profile a synchronous function.

    Args:
        name: Name for the profile entry (defaults to function name)
        track_memory: Whether to track memory usage

    Example:
        @profile("my_function")
        def my_function():
            ...
    """

    def decorator(func: Callable) -> Callable:
        # Use simple function name by default for easier querying
        profile_name = name or func.__name__

        @functools.wraps(func)
        def wrapper(*args, **kwargs):
            if not Profiler.is_enabled():
                return func(*args, **kwargs)

            # Track memory if requested
            memory_start = None
            if track_memory:
                try:
                    import psutil

                    process = psutil.Process()
                    memory_start = process.memory_info().rss
                except ImportError:
                    pass

            start_time = time.perf_counter()
            try:
                result = func(*args, **kwargs)
                return result
            finally:
                end_time = time.perf_counter()
                duration = end_time - start_time

                memory_end = None
                if track_memory and memory_start is not None:
                    try:
                        import psutil

                        process = psutil.Process()
                        memory_end = process.memory_info().rss
                    except ImportError:
                        pass

                entry = ProfileEntry(
                    name=profile_name,
                    start_time=start_time,
                    end_time=end_time,
                    duration=duration,
                    memory_start=memory_start,
                    memory_end=memory_end,
                    metadata={"args_count": len(args), "kwargs_count": len(kwargs)},
                )
                Profiler.record(entry)

                # Log slow operations
                if duration > 1.0:  # > 1 second
                    logger.warning(
                        f"Slow operation: {profile_name} took {duration:.2f}s"
                    )

        return wrapper

    return decorator


def profile_async(name: str | None = None, track_memory: bool = False) -> Callable:
    """Decorator to profile an asynchronous function.

    Args:
        name: Name for the profile entry (defaults to function name)
        track_memory: Whether to track memory usage

    Example:
        @profile_async("my_async_function")
        async def my_async_function():
            ...
    """

    def decorator(func: Callable) -> Callable:
        # Use simple function name by default for easier querying
        profile_name = name or func.__name__

        @functools.wraps(func)
        async def wrapper(*args, **kwargs):
            if not Profiler.is_enabled():
                return await func(*args, **kwargs)

            # Track memory if requested
            memory_start = None
            if track_memory:
                try:
                    import psutil

                    process = psutil.Process()
                    memory_start = process.memory_info().rss
                except ImportError:
                    pass

            start_time = time.perf_counter()
            try:
                result = await func(*args, **kwargs)
                return result
            finally:
                end_time = time.perf_counter()
                duration = end_time - start_time

                memory_end = None
                if track_memory and memory_start is not None:
                    try:
                        import psutil

                        process = psutil.Process()
                        memory_end = process.memory_info().rss
                    except ImportError:
                        pass

                entry = ProfileEntry(
                    name=profile_name,
                    start_time=start_time,
                    end_time=end_time,
                    duration=duration,
                    memory_start=memory_start,
                    memory_end=memory_end,
                    metadata={"args_count": len(args), "kwargs_count": len(kwargs)},
                )
                Profiler.record(entry)

                # Log slow operations
                if duration > 1.0:  # > 1 second
                    logger.warning(
                        f"Slow async operation: {profile_name} took {duration:.2f}s"
                    )

        return wrapper

    return decorator


def get_profile_stats(name: str | None = None) -> dict[str, Any]:
    """Get profiling statistics.

    Args:
        name: Optional name to filter by

    Returns:
        Dictionary of statistics
    """
    if name:
        return Profiler.get_summary(name)

    # Get all summaries
    summaries = {}
    for func_name in Profiler.get_stats().keys():
        summaries[func_name] = Profiler.get_summary(func_name)

    return summaries


def clear_profile_stats(name: str | None = None) -> None:
    """Clear profiling statistics.

    Args:
        name: Optional name to clear (clears all if not provided)
    """
    Profiler.clear(name)
