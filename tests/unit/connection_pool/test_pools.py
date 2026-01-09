"""Tests for connection pooling.

Phase 8 - Performance & Scale: Connection Pooling
"""

from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest

from paracle_connection_pool import (
    HTTPPool,
    PoolMonitor,
    PoolStats,
    get_pool_monitor,
)
from paracle_connection_pool.db_pool import DatabasePoolConfig, SQLALCHEMY_AVAILABLE
from paracle_connection_pool.http_pool import HTTPPoolConfig

# Conditional import for DatabasePool
if SQLALCHEMY_AVAILABLE:
    from paracle_connection_pool import DatabasePool


class TestHTTPPoolConfig:
    """Tests for HTTPPoolConfig."""

    def test_default_values(self):
        """Test default configuration values."""
        config = HTTPPoolConfig()

        assert config.max_connections == 100
        assert config.max_keepalive_connections == 20
        assert config.keepalive_expiry == 30.0
        assert config.timeout == 30.0
        assert config.max_retries == 3
        assert config.verify_ssl is True

    def test_from_env(self):
        """Test configuration from environment variables."""
        with patch.dict(
            "os.environ",
            {
                "PARACLE_HTTP_MAX_CONNECTIONS": "200",
                "PARACLE_HTTP_MAX_KEEPALIVE": "50",
                "PARACLE_HTTP_TIMEOUT": "60.0",
            },
        ):
            config = HTTPPoolConfig.from_env()

            assert config.max_connections == 200
            assert config.max_keepalive_connections == 50
            assert config.timeout == 60.0


class TestDatabasePoolConfig:
    """Tests for DatabasePoolConfig."""

    def test_default_values(self):
        """Test default configuration values."""
        config = DatabasePoolConfig()

        assert config.pool_size == 5
        assert config.max_overflow == 10
        assert config.pool_timeout == 30.0
        assert config.pool_recycle == 3600
        assert config.echo is False
        assert config.pool_pre_ping is True

    def test_from_env(self):
        """Test configuration from environment variables."""
        with patch.dict(
            "os.environ",
            {
                "PARACLE_DB_POOL_SIZE": "10",
                "PARACLE_DB_MAX_OVERFLOW": "20",
                "PARACLE_DB_ECHO": "true",
            },
        ):
            config = DatabasePoolConfig.from_env()

            assert config.pool_size == 10
            assert config.max_overflow == 20
            assert config.echo is True


class TestHTTPPool:
    """Tests for HTTPPool."""

    def test_init_without_httpx(self):
        """Test initialization fails without httpx."""
        with patch.dict("sys.modules", {"httpx": None}):
            with patch("paracle_connection_pool.http_pool.HTTPX_AVAILABLE", False):
                with pytest.raises(ImportError):
                    HTTPPool()

    def test_stats_initial(self):
        """Test initial stats are zero."""
        pool = HTTPPool()

        stats = pool.stats()

        assert stats["requests"] == 0
        assert stats["errors"] == 0
        assert stats["error_rate"] == 0.0
        assert "config" in stats

    @pytest.mark.asyncio
    async def test_close(self):
        """Test pool can be closed."""
        pool = HTTPPool()

        # Close before any client is created
        await pool.close()

        assert pool._client is None


@pytest.mark.skipif(not SQLALCHEMY_AVAILABLE, reason="SQLAlchemy not installed")
class TestDatabasePool:
    """Tests for DatabasePool."""

    def test_init_with_sqlite(self, tmp_path: Path):
        """Test initialization with SQLite."""
        db_path = tmp_path / "test.db"
        pool = DatabasePool(f"sqlite:///{db_path}")

        assert pool.engine is not None
        assert pool.SessionLocal is not None

        pool.close()

    def test_stats_initial(self, tmp_path: Path):
        """Test initial stats are zero."""
        db_path = tmp_path / "test.db"
        pool = DatabasePool(f"sqlite:///{db_path}")

        stats = pool.stats()

        assert stats["queries"] == 0
        assert stats["errors"] == 0
        assert stats["error_rate"] == 0.0
        assert "config" in stats
        assert "pool_status" in stats

        pool.close()

    def test_get_session(self, tmp_path: Path):
        """Test getting a session."""
        db_path = tmp_path / "test.db"
        pool = DatabasePool(f"sqlite:///{db_path}")

        session = pool.get_session()

        assert session is not None
        assert pool._query_count == 1

        session.close()
        pool.close()

    def test_session_context(self, tmp_path: Path):
        """Test session context manager."""
        db_path = tmp_path / "test.db"
        pool = DatabasePool(f"sqlite:///{db_path}")

        with pool.session_context() as session:
            assert session is not None

        assert pool._query_count == 1

        pool.close()


class TestPoolStats:
    """Tests for PoolStats dataclass."""

    def test_default_values(self):
        """Test default stats are zero."""
        stats = PoolStats()

        assert stats.http_requests == 0
        assert stats.http_errors == 0
        assert stats.db_queries == 0
        assert stats.db_errors == 0

    def test_to_dict(self):
        """Test conversion to dictionary."""
        stats = PoolStats(
            http_requests=100,
            http_errors=5,
            http_error_rate=0.05,
            db_queries=200,
            db_errors=10,
            db_error_rate=0.05,
        )

        data = stats.to_dict()

        assert data["http"]["requests"] == 100
        assert data["http"]["errors"] == 5
        assert data["database"]["queries"] == 200
        assert data["database"]["errors"] == 10
        assert "timestamp" in data


class TestPoolMonitor:
    """Tests for PoolMonitor."""

    def test_record_http_stats(self):
        """Test recording HTTP stats."""
        monitor = PoolMonitor()

        monitor.record_http_stats({"requests": 100, "errors": 5})

        assert len(monitor._http_stats_history) == 1
        assert monitor._http_stats_history[0]["requests"] == 100

    def test_record_db_stats(self):
        """Test recording database stats."""
        monitor = PoolMonitor()

        monitor.record_db_stats({"queries": 200, "errors": 10})

        assert len(monitor._db_stats_history) == 1
        assert monitor._db_stats_history[0]["queries"] == 200

    def test_max_history_limit(self):
        """Test history is limited to max size."""
        monitor = PoolMonitor()
        monitor._max_history = 10

        for i in range(20):
            monitor.record_http_stats({"requests": i})

        assert len(monitor._http_stats_history) == 10
        # Should have the most recent entries
        assert monitor._http_stats_history[0]["requests"] == 10

    def test_get_current_stats_no_pools(self):
        """Test getting stats with no pools."""
        monitor = PoolMonitor()

        stats = monitor.get_current_stats()

        assert stats.http_requests == 0
        assert stats.db_queries == 0

    def test_get_current_stats_with_http_pool(self):
        """Test getting stats with mock HTTP pool."""
        monitor = PoolMonitor()

        mock_pool = MagicMock()
        mock_pool.stats.return_value = {
            "requests": 100,
            "errors": 5,
            "error_rate": 0.05,
            "config": {"max_connections": 100},
        }

        stats = monitor.get_current_stats(http_pool=mock_pool)

        assert stats.http_requests == 100
        assert stats.http_errors == 5
        assert stats.http_error_rate == 0.05

    def test_health_check_healthy(self):
        """Test health check returns healthy."""
        monitor = PoolMonitor()

        mock_pool = MagicMock()
        mock_pool.stats.return_value = {"error_rate": 0.01}

        results = monitor.health_check(http_pool=mock_pool)

        assert results["healthy"] is True
        assert len(results["issues"]) == 0

    def test_health_check_high_error_rate(self):
        """Test health check with high error rate."""
        monitor = PoolMonitor()

        mock_pool = MagicMock()
        mock_pool.stats.return_value = {"error_rate": 0.15}  # 15%

        results = monitor.health_check(http_pool=mock_pool)

        assert results["healthy"] is False
        assert len(results["issues"]) == 1
        assert "error rate" in results["issues"][0].lower()

    def test_health_check_warning_error_rate(self):
        """Test health check with warning error rate."""
        monitor = PoolMonitor()

        mock_pool = MagicMock()
        mock_pool.stats.return_value = {"error_rate": 0.07}  # 7%

        results = monitor.health_check(http_pool=mock_pool)

        assert results["healthy"] is True
        assert len(results["warnings"]) == 1
        assert "elevated" in results["warnings"][0].lower()

    def test_summary(self):
        """Test generating summary."""
        monitor = PoolMonitor()

        mock_http_pool = MagicMock()
        mock_http_pool.stats.return_value = {
            "requests": 100,
            "errors": 5,
            "error_rate": 0.05,
            "config": {"max_connections": 100},
        }

        summary = monitor.summary(http_pool=mock_http_pool)

        assert "Connection Pool Statistics" in summary
        assert "HTTP Pool" in summary
        assert "Requests: 100" in summary


class TestGlobalPoolMonitor:
    """Tests for global pool monitor."""

    def test_get_pool_monitor_singleton(self):
        """Test get_pool_monitor returns singleton."""
        monitor1 = get_pool_monitor()
        monitor2 = get_pool_monitor()

        assert monitor1 is monitor2
