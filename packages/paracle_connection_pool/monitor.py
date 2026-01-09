"""Connection pool monitoring and statistics."""

from dataclasses import dataclass, field
from datetime import datetime
from typing import Any


@dataclass
class PoolStats:
    """Connection pool statistics snapshot."""

    # HTTP pool stats
    http_requests: int = 0
    http_errors: int = 0
    http_error_rate: float = 0.0
    http_pool_size: int = 0
    http_active_connections: int = 0

    # Database pool stats
    db_queries: int = 0
    db_errors: int = 0
    db_error_rate: float = 0.0
    db_pool_size: int = 0
    db_active_connections: int = 0
    db_overflow: int = 0

    # Temporal
    timestamp: datetime = field(default_factory=datetime.now)

    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary."""
        return {
            "http": {
                "requests": self.http_requests,
                "errors": self.http_errors,
                "error_rate": self.http_error_rate,
                "pool_size": self.http_pool_size,
                "active_connections": self.http_active_connections,
            },
            "database": {
                "queries": self.db_queries,
                "errors": self.db_errors,
                "error_rate": self.db_error_rate,
                "pool_size": self.db_pool_size,
                "active_connections": self.db_active_connections,
                "overflow": self.db_overflow,
            },
            "timestamp": self.timestamp.isoformat(),
        }


class PoolMonitor:
    """Monitor connection pool health and performance."""

    def __init__(self):
        """Initialize pool monitor."""
        self._http_stats_history: list[dict[str, Any]] = []
        self._db_stats_history: list[dict[str, Any]] = []
        self._max_history = 100

    def record_http_stats(self, stats: dict[str, Any]) -> None:
        """Record HTTP pool statistics.

        Args:
            stats: HTTP pool stats from HTTPPool.stats()
        """
        self._http_stats_history.append(
            {
                "timestamp": datetime.now(),
                **stats,
            }
        )

        # Keep only recent history
        if len(self._http_stats_history) > self._max_history:
            self._http_stats_history = self._http_stats_history[-self._max_history :]

    def record_db_stats(self, stats: dict[str, Any]) -> None:
        """Record database pool statistics.

        Args:
            stats: Database pool stats from DatabasePool.stats()
        """
        self._db_stats_history.append(
            {
                "timestamp": datetime.now(),
                **stats,
            }
        )

        # Keep only recent history
        if len(self._db_stats_history) > self._max_history:
            self._db_stats_history = self._db_stats_history[-self._max_history :]

    def get_current_stats(
        self,
        http_pool: Any | None = None,
        db_pool: Any | None = None,
    ) -> PoolStats:
        """Get current pool statistics snapshot.

        Args:
            http_pool: HTTPPool instance (optional)
            db_pool: DatabasePool instance (optional)

        Returns:
            Current pool statistics
        """
        stats = PoolStats()

        # HTTP pool stats
        if http_pool is not None:
            http_stats = http_pool.stats()
            stats.http_requests = http_stats.get("requests", 0)
            stats.http_errors = http_stats.get("errors", 0)
            stats.http_error_rate = http_stats.get("error_rate", 0.0)
            stats.http_pool_size = http_stats.get("config", {}).get(
                "max_connections", 0
            )

        # Database pool stats
        if db_pool is not None:
            db_stats = db_pool.stats()
            stats.db_queries = db_stats.get("queries", 0)
            stats.db_errors = db_stats.get("errors", 0)
            stats.db_error_rate = db_stats.get("error_rate", 0.0)

            # Parse pool status
            pool_status = db_stats.get("pool_status", "")
            # Format: "Pool size: 5  Connections in pool: 0  Current Overflow: 0  Current Checked out connections: 0"
            if "Pool size:" in pool_status:
                parts = pool_status.split("  ")
                for part in parts:
                    if "Pool size:" in part:
                        stats.db_pool_size = int(part.split(": ")[1])
                    elif "Current Checked out connections:" in part:
                        stats.db_active_connections = int(part.split(": ")[1])
                    elif "Current Overflow:" in part:
                        stats.db_overflow = int(part.split(": ")[1])

        return stats

    def health_check(
        self,
        http_pool: Any | None = None,
        db_pool: Any | None = None,
    ) -> dict[str, Any]:
        """Check pool health.

        Args:
            http_pool: HTTPPool instance (optional)
            db_pool: DatabasePool instance (optional)

        Returns:
            Health check results
        """
        results = {
            "healthy": True,
            "issues": [],
            "warnings": [],
        }

        # Check HTTP pool
        if http_pool is not None:
            http_stats = http_pool.stats()
            error_rate = http_stats.get("error_rate", 0.0)

            if error_rate > 0.1:  # >10% error rate
                results["healthy"] = False
                results["issues"].append(
                    f"HTTP pool error rate too high: {error_rate * 100:.1f}%"
                )
            elif error_rate > 0.05:  # >5% error rate
                results["warnings"].append(
                    f"HTTP pool elevated error rate: {error_rate * 100:.1f}%"
                )

        # Check database pool
        if db_pool is not None:
            try:
                is_healthy = db_pool.health_check()
                if not is_healthy:
                    results["healthy"] = False
                    results["issues"].append("Database connection failed")
            except Exception as e:
                results["healthy"] = False
                results["issues"].append(f"Database health check error: {e}")

            db_stats = db_pool.stats()
            error_rate = db_stats.get("error_rate", 0.0)

            if error_rate > 0.1:  # >10% error rate
                results["healthy"] = False
                results["issues"].append(
                    f"Database pool error rate too high: {error_rate * 100:.1f}%"
                )
            elif error_rate > 0.05:  # >5% error rate
                results["warnings"].append(
                    f"Database pool elevated error rate: {error_rate * 100:.1f}%"
                )

        return results

    def summary(
        self,
        http_pool: Any | None = None,
        db_pool: Any | None = None,
    ) -> str:
        """Generate human-readable summary.

        Args:
            http_pool: HTTPPool instance (optional)
            db_pool: DatabasePool instance (optional)

        Returns:
            Formatted summary
        """
        stats = self.get_current_stats(http_pool, db_pool)

        lines = ["Connection Pool Statistics:"]

        # HTTP pool
        if http_pool is not None:
            lines.append("\nHTTP Pool:")
            lines.append(f"  Requests: {stats.http_requests}")
            lines.append(f"  Errors: {stats.http_errors}")
            lines.append(f"  Error Rate: {stats.http_error_rate * 100:.1f}%")
            lines.append(f"  Pool Size: {stats.http_pool_size}")

        # Database pool
        if db_pool is not None:
            lines.append("\nDatabase Pool:")
            lines.append(f"  Queries: {stats.db_queries}")
            lines.append(f"  Errors: {stats.db_errors}")
            lines.append(f"  Error Rate: {stats.db_error_rate * 100:.1f}%")
            lines.append(f"  Pool Size: {stats.db_pool_size}")
            lines.append(f"  Active: {stats.db_active_connections}")
            lines.append(f"  Overflow: {stats.db_overflow}")

        return "\n".join(lines)


# Global pool monitor
_pool_monitor: PoolMonitor | None = None


def get_pool_monitor() -> PoolMonitor:
    """Get global pool monitor instance.

    Returns:
        Global PoolMonitor instance
    """
    global _pool_monitor
    if _pool_monitor is None:
        _pool_monitor = PoolMonitor()
    return _pool_monitor
