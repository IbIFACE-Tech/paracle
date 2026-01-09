"""Connection pooling for HTTP and database connections.

Provides efficient connection reuse for LLM providers and database access,
reducing connection overhead and improving performance.
"""

from paracle_connection_pool.db_pool import DatabasePool, get_db_pool
from paracle_connection_pool.http_pool import HTTPPool, get_http_pool
from paracle_connection_pool.monitor import PoolMonitor, PoolStats, get_pool_monitor

__all__ = [
    "HTTPPool",
    "DatabasePool",
    "PoolMonitor",
    "PoolStats",
    "get_http_pool",
    "get_db_pool",
    "get_pool_monitor",
]

__version__ = "0.1.0"
