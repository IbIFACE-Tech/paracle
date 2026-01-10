"""Database capability for MetaAgent.

Provides database operations:
- SQL databases (PostgreSQL, MySQL, SQLite)
- NoSQL databases (MongoDB, Redis)
- Query execution and result handling
- Schema inspection
- Connection management

Requires optional dependencies:
- asyncpg: For PostgreSQL
- aiomysql: For MySQL
- aiosqlite: For SQLite
- motor: For MongoDB
- redis: For Redis
"""

import json
import os
import time
from abc import ABC, abstractmethod
from enum import Enum
from pathlib import Path
from typing import Any

from pydantic import Field

from paracle_meta.capabilities.base import (
    BaseCapability,
    CapabilityConfig,
    CapabilityResult,
)

# Optional imports
try:
    import aiosqlite

    SQLITE_AVAILABLE = True
except ImportError:
    SQLITE_AVAILABLE = False
    aiosqlite = None  # type: ignore

try:
    import asyncpg

    POSTGRES_AVAILABLE = True
except ImportError:
    POSTGRES_AVAILABLE = False
    asyncpg = None  # type: ignore

try:
    import aiomysql

    MYSQL_AVAILABLE = True
except ImportError:
    MYSQL_AVAILABLE = False
    aiomysql = None  # type: ignore

try:
    import motor.motor_asyncio as motor

    MONGO_AVAILABLE = True
except ImportError:
    MONGO_AVAILABLE = False
    motor = None  # type: ignore

try:
    import redis.asyncio as aioredis

    REDIS_AVAILABLE = True
except ImportError:
    REDIS_AVAILABLE = False
    aioredis = None  # type: ignore


class DatabaseType(str, Enum):
    """Supported database types."""

    SQLITE = "sqlite"
    POSTGRESQL = "postgresql"
    MYSQL = "mysql"
    MONGODB = "mongodb"
    REDIS = "redis"


class DatabaseConfig(CapabilityConfig):
    """Configuration for database capability."""

    # Default database type
    default_database: str = Field(
        default="sqlite",
        description="Default database type",
    )

    # SQLite settings
    sqlite_path: str = Field(
        default=":memory:",
        description="SQLite database path",
    )

    # PostgreSQL settings
    postgres_host: str = Field(default="localhost", description="PostgreSQL host")
    postgres_port: int = Field(default=5432, description="PostgreSQL port")
    postgres_database: str = Field(default="paracle", description="PostgreSQL database")
    postgres_user: str | None = Field(default=None, description="PostgreSQL user")
    postgres_password: str | None = Field(default=None, description="PostgreSQL password")

    # MySQL settings
    mysql_host: str = Field(default="localhost", description="MySQL host")
    mysql_port: int = Field(default=3306, description="MySQL port")
    mysql_database: str = Field(default="paracle", description="MySQL database")
    mysql_user: str | None = Field(default=None, description="MySQL user")
    mysql_password: str | None = Field(default=None, description="MySQL password")

    # MongoDB settings
    mongodb_uri: str = Field(
        default="mongodb://localhost:27017",
        description="MongoDB connection URI",
    )
    mongodb_database: str = Field(default="paracle", description="MongoDB database")

    # Redis settings
    redis_url: str = Field(
        default="redis://localhost:6379",
        description="Redis connection URL",
    )

    # Query settings
    max_results: int = Field(default=1000, description="Max results per query")
    timeout: float = Field(default=30.0, description="Query timeout in seconds")


class QueryResult:
    """Result of a database query."""

    def __init__(
        self,
        success: bool,
        operation: str,
        rows: list[dict[str, Any]] | None = None,
        affected_rows: int = 0,
        data: dict[str, Any] | None = None,
        error: str | None = None,
        duration_ms: float = 0,
    ):
        self.success = success
        self.operation = operation
        self.rows = rows or []
        self.affected_rows = affected_rows
        self.data = data or {}
        self.error = error
        self.duration_ms = duration_ms

    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary."""
        result = {
            "success": self.success,
            "operation": self.operation,
            "duration_ms": self.duration_ms,
            "row_count": len(self.rows),
            "affected_rows": self.affected_rows,
        }
        if self.rows:
            result["rows"] = self.rows
        if self.data:
            result["data"] = self.data
        if self.error:
            result["error"] = self.error
        return result


class DatabaseCapability(BaseCapability):
    """Database capability for MetaAgent.

    Provides operations for SQL and NoSQL databases:
    - Execute queries (SELECT, INSERT, UPDATE, DELETE)
    - Schema inspection (tables, columns, indexes)
    - Connection management
    - Transaction support

    Supported databases:
    - SQLite (default, in-memory or file-based)
    - PostgreSQL
    - MySQL
    - MongoDB
    - Redis

    Example:
        >>> db = DatabaseCapability()
        >>> await db.initialize()

        >>> # Execute SQL query
        >>> result = await db.query("SELECT * FROM users WHERE active = ?", [True])

        >>> # Insert data
        >>> result = await db.insert("users", {"name": "John", "email": "john@example.com"})

        >>> # Get table schema
        >>> result = await db.schema("users")

        >>> # Use Redis
        >>> result = await db.execute(
        ...     action="set",
        ...     database="redis",
        ...     key="user:1",
        ...     value={"name": "John"}
        ... )
    """

    name = "database"
    description = "SQL and NoSQL database operations"

    def __init__(self, config: DatabaseConfig | None = None):
        """Initialize database capability."""
        super().__init__(config or DatabaseConfig())
        self.config: DatabaseConfig = self.config
        self._connections: dict[str, Any] = {}

    async def initialize(self) -> None:
        """Initialize database connections."""
        await super().initialize()

    async def shutdown(self) -> None:
        """Close all database connections."""
        for db_type, conn in self._connections.items():
            try:
                if db_type == "sqlite" and conn:
                    await conn.close()
                elif db_type == "postgresql" and conn:
                    await conn.close()
                elif db_type == "mysql" and conn:
                    conn.close()
                elif db_type == "redis" and conn:
                    await conn.close()
            except Exception:
                pass

        self._connections = {}
        await super().shutdown()

    async def execute(self, **kwargs) -> CapabilityResult:
        """Execute database operation.

        Args:
            action: Operation (query, insert, update, delete, schema, connect)
            database: Database type (sqlite, postgresql, mysql, mongodb, redis)
            **kwargs: Operation-specific parameters

        Returns:
            CapabilityResult with operation outcome
        """
        if not self._initialized:
            await self.initialize()

        action = kwargs.pop("action", "query")
        database = kwargs.pop("database", self.config.default_database)
        start_time = time.time()

        try:
            if action == "query":
                result = await self._execute_query(database, **kwargs)
            elif action == "insert":
                result = await self._insert(database, **kwargs)
            elif action == "update":
                result = await self._update(database, **kwargs)
            elif action == "delete":
                result = await self._delete(database, **kwargs)
            elif action == "schema":
                result = await self._get_schema(database, **kwargs)
            elif action == "tables":
                result = await self._list_tables(database, **kwargs)
            elif action == "connect":
                result = await self._connect(database, **kwargs)
            elif action == "disconnect":
                result = await self._disconnect(database, **kwargs)
            # Redis-specific actions
            elif action == "get":
                result = await self._redis_get(**kwargs)
            elif action == "set":
                result = await self._redis_set(**kwargs)
            elif action == "keys":
                result = await self._redis_keys(**kwargs)
            # MongoDB-specific actions
            elif action == "find":
                result = await self._mongo_find(**kwargs)
            elif action == "insert_one":
                result = await self._mongo_insert(**kwargs)
            elif action == "aggregate":
                result = await self._mongo_aggregate(**kwargs)
            else:
                return CapabilityResult.error_result(
                    capability=self.name,
                    error=f"Unknown action: {action}",
                )

            duration_ms = (time.time() - start_time) * 1000
            return CapabilityResult.success_result(
                capability=self.name,
                output=result.to_dict(),
                duration_ms=duration_ms,
                action=action,
            )

        except Exception as e:
            duration_ms = (time.time() - start_time) * 1000
            return CapabilityResult.error_result(
                capability=self.name,
                error=str(e),
                duration_ms=duration_ms,
                action=action,
            )

    async def _get_connection(self, database: str) -> Any:
        """Get or create database connection."""
        if database in self._connections:
            return self._connections[database]

        if database == "sqlite":
            if not SQLITE_AVAILABLE:
                raise RuntimeError("aiosqlite required: pip install aiosqlite")
            conn = await aiosqlite.connect(self.config.sqlite_path)
            conn.row_factory = aiosqlite.Row
            self._connections[database] = conn

        elif database == "postgresql":
            if not POSTGRES_AVAILABLE:
                raise RuntimeError("asyncpg required: pip install asyncpg")
            conn = await asyncpg.connect(
                host=self.config.postgres_host,
                port=self.config.postgres_port,
                database=self.config.postgres_database,
                user=self.config.postgres_user or os.getenv("POSTGRES_USER"),
                password=self.config.postgres_password or os.getenv("POSTGRES_PASSWORD"),
            )
            self._connections[database] = conn

        elif database == "mysql":
            if not MYSQL_AVAILABLE:
                raise RuntimeError("aiomysql required: pip install aiomysql")
            conn = await aiomysql.connect(
                host=self.config.mysql_host,
                port=self.config.mysql_port,
                db=self.config.mysql_database,
                user=self.config.mysql_user or os.getenv("MYSQL_USER"),
                password=self.config.mysql_password or os.getenv("MYSQL_PASSWORD"),
            )
            self._connections[database] = conn

        elif database == "mongodb":
            if not MONGO_AVAILABLE:
                raise RuntimeError("motor required: pip install motor")
            client = motor.AsyncIOMotorClient(self.config.mongodb_uri)
            self._connections[database] = client[self.config.mongodb_database]

        elif database == "redis":
            if not REDIS_AVAILABLE:
                raise RuntimeError("redis required: pip install redis")
            conn = await aioredis.from_url(self.config.redis_url)
            self._connections[database] = conn

        else:
            raise ValueError(f"Unknown database type: {database}")

        return self._connections[database]

    async def _execute_query(
        self,
        database: str,
        sql: str,
        params: list[Any] | tuple[Any, ...] | None = None,
        **kwargs,
    ) -> QueryResult:
        """Execute a SQL query."""
        start_time = time.time()
        params = params or []

        conn = await self._get_connection(database)

        if database == "sqlite":
            async with conn.execute(sql, params) as cursor:
                rows = await cursor.fetchall()
                columns = [desc[0] for desc in cursor.description] if cursor.description else []
                result_rows = [dict(zip(columns, row)) for row in rows]

        elif database == "postgresql":
            rows = await conn.fetch(sql, *params)
            result_rows = [dict(row) for row in rows]

        elif database == "mysql":
            async with conn.cursor(aiomysql.DictCursor) as cursor:
                await cursor.execute(sql, params)
                result_rows = await cursor.fetchall()

        else:
            raise ValueError(f"SQL not supported for: {database}")

        duration_ms = (time.time() - start_time) * 1000
        return QueryResult(
            success=True,
            operation="query",
            rows=result_rows[: self.config.max_results],
            duration_ms=duration_ms,
        )

    async def _insert(
        self,
        database: str,
        table: str,
        data: dict[str, Any],
        **kwargs,
    ) -> QueryResult:
        """Insert a row into a table."""
        start_time = time.time()

        conn = await self._get_connection(database)
        columns = list(data.keys())
        values = list(data.values())

        if database == "sqlite":
            placeholders = ", ".join(["?" for _ in values])
            sql = f"INSERT INTO {table} ({', '.join(columns)}) VALUES ({placeholders})"
            async with conn.execute(sql, values) as cursor:
                await conn.commit()
                affected = cursor.rowcount

        elif database == "postgresql":
            placeholders = ", ".join([f"${i+1}" for i in range(len(values))])
            sql = f"INSERT INTO {table} ({', '.join(columns)}) VALUES ({placeholders})"
            result = await conn.execute(sql, *values)
            affected = int(result.split()[-1])

        elif database == "mysql":
            placeholders = ", ".join(["%s" for _ in values])
            sql = f"INSERT INTO {table} ({', '.join(columns)}) VALUES ({placeholders})"
            async with conn.cursor() as cursor:
                await cursor.execute(sql, values)
                await conn.commit()
                affected = cursor.rowcount

        else:
            raise ValueError(f"Insert not supported for: {database}")

        duration_ms = (time.time() - start_time) * 1000
        return QueryResult(
            success=True,
            operation="insert",
            affected_rows=affected,
            data={"table": table, "columns": columns},
            duration_ms=duration_ms,
        )

    async def _update(
        self,
        database: str,
        table: str,
        data: dict[str, Any],
        where: str,
        params: list[Any] | None = None,
        **kwargs,
    ) -> QueryResult:
        """Update rows in a table."""
        start_time = time.time()
        params = params or []

        conn = await self._get_connection(database)
        set_clause = ", ".join([f"{k} = ?" for k in data.keys()])
        values = list(data.values()) + params

        if database == "sqlite":
            sql = f"UPDATE {table} SET {set_clause} WHERE {where}"
            async with conn.execute(sql, values) as cursor:
                await conn.commit()
                affected = cursor.rowcount

        elif database == "postgresql":
            set_clause = ", ".join([f"{k} = ${i+1}" for i, k in enumerate(data.keys())])
            sql = f"UPDATE {table} SET {set_clause} WHERE {where}"
            result = await conn.execute(sql, *values)
            affected = int(result.split()[-1])

        elif database == "mysql":
            set_clause = ", ".join([f"{k} = %s" for k in data.keys()])
            sql = f"UPDATE {table} SET {set_clause} WHERE {where}"
            async with conn.cursor() as cursor:
                await cursor.execute(sql, values)
                await conn.commit()
                affected = cursor.rowcount

        else:
            raise ValueError(f"Update not supported for: {database}")

        duration_ms = (time.time() - start_time) * 1000
        return QueryResult(
            success=True,
            operation="update",
            affected_rows=affected,
            data={"table": table},
            duration_ms=duration_ms,
        )

    async def _delete(
        self,
        database: str,
        table: str,
        where: str,
        params: list[Any] | None = None,
        **kwargs,
    ) -> QueryResult:
        """Delete rows from a table."""
        start_time = time.time()
        params = params or []

        conn = await self._get_connection(database)

        if database == "sqlite":
            sql = f"DELETE FROM {table} WHERE {where}"
            async with conn.execute(sql, params) as cursor:
                await conn.commit()
                affected = cursor.rowcount

        elif database == "postgresql":
            sql = f"DELETE FROM {table} WHERE {where}"
            result = await conn.execute(sql, *params)
            affected = int(result.split()[-1])

        elif database == "mysql":
            sql = f"DELETE FROM {table} WHERE {where}"
            async with conn.cursor() as cursor:
                await cursor.execute(sql, params)
                await conn.commit()
                affected = cursor.rowcount

        else:
            raise ValueError(f"Delete not supported for: {database}")

        duration_ms = (time.time() - start_time) * 1000
        return QueryResult(
            success=True,
            operation="delete",
            affected_rows=affected,
            data={"table": table},
            duration_ms=duration_ms,
        )

    async def _get_schema(
        self,
        database: str,
        table: str,
        **kwargs,
    ) -> QueryResult:
        """Get table schema."""
        start_time = time.time()

        conn = await self._get_connection(database)

        if database == "sqlite":
            async with conn.execute(f"PRAGMA table_info({table})") as cursor:
                rows = await cursor.fetchall()
                columns = []
                for row in rows:
                    columns.append({
                        "name": row[1],
                        "type": row[2],
                        "nullable": not row[3],
                        "default": row[4],
                        "primary_key": bool(row[5]),
                    })

        elif database == "postgresql":
            sql = """
                SELECT column_name, data_type, is_nullable, column_default
                FROM information_schema.columns
                WHERE table_name = $1
            """
            rows = await conn.fetch(sql, table)
            columns = [
                {
                    "name": row["column_name"],
                    "type": row["data_type"],
                    "nullable": row["is_nullable"] == "YES",
                    "default": row["column_default"],
                }
                for row in rows
            ]

        elif database == "mysql":
            sql = f"DESCRIBE {table}"
            async with conn.cursor(aiomysql.DictCursor) as cursor:
                await cursor.execute(sql)
                rows = await cursor.fetchall()
                columns = [
                    {
                        "name": row["Field"],
                        "type": row["Type"],
                        "nullable": row["Null"] == "YES",
                        "default": row["Default"],
                        "primary_key": row["Key"] == "PRI",
                    }
                    for row in rows
                ]

        else:
            raise ValueError(f"Schema not supported for: {database}")

        duration_ms = (time.time() - start_time) * 1000
        return QueryResult(
            success=True,
            operation="schema",
            data={"table": table, "columns": columns},
            duration_ms=duration_ms,
        )

    async def _list_tables(self, database: str, **kwargs) -> QueryResult:
        """List all tables in the database."""
        start_time = time.time()

        conn = await self._get_connection(database)

        if database == "sqlite":
            sql = "SELECT name FROM sqlite_master WHERE type='table'"
            async with conn.execute(sql) as cursor:
                rows = await cursor.fetchall()
                tables = [row[0] for row in rows]

        elif database == "postgresql":
            sql = """
                SELECT table_name FROM information_schema.tables
                WHERE table_schema = 'public'
            """
            rows = await conn.fetch(sql)
            tables = [row["table_name"] for row in rows]

        elif database == "mysql":
            async with conn.cursor() as cursor:
                await cursor.execute("SHOW TABLES")
                rows = await cursor.fetchall()
                tables = [row[0] for row in rows]

        elif database == "mongodb":
            tables = await conn.list_collection_names()

        else:
            raise ValueError(f"List tables not supported for: {database}")

        duration_ms = (time.time() - start_time) * 1000
        return QueryResult(
            success=True,
            operation="tables",
            data={"tables": tables, "count": len(tables)},
            duration_ms=duration_ms,
        )

    async def _connect(self, database: str, **kwargs) -> QueryResult:
        """Explicitly connect to database."""
        start_time = time.time()
        await self._get_connection(database)
        duration_ms = (time.time() - start_time) * 1000
        return QueryResult(
            success=True,
            operation="connect",
            data={"database": database, "connected": True},
            duration_ms=duration_ms,
        )

    async def _disconnect(self, database: str, **kwargs) -> QueryResult:
        """Disconnect from database."""
        start_time = time.time()
        if database in self._connections:
            conn = self._connections.pop(database)
            if hasattr(conn, "close"):
                await conn.close() if hasattr(conn.close, "__await__") else conn.close()
        duration_ms = (time.time() - start_time) * 1000
        return QueryResult(
            success=True,
            operation="disconnect",
            data={"database": database, "disconnected": True},
            duration_ms=duration_ms,
        )

    # Redis-specific operations
    async def _redis_get(self, key: str, **kwargs) -> QueryResult:
        """Get value from Redis."""
        start_time = time.time()
        conn = await self._get_connection("redis")
        value = await conn.get(key)

        if value:
            try:
                value = json.loads(value)
            except (json.JSONDecodeError, TypeError):
                value = value.decode() if isinstance(value, bytes) else value

        duration_ms = (time.time() - start_time) * 1000
        return QueryResult(
            success=True,
            operation="get",
            data={"key": key, "value": value},
            duration_ms=duration_ms,
        )

    async def _redis_set(
        self,
        key: str,
        value: Any,
        ttl: int | None = None,
        **kwargs,
    ) -> QueryResult:
        """Set value in Redis."""
        start_time = time.time()
        conn = await self._get_connection("redis")

        if not isinstance(value, (str, bytes)):
            value = json.dumps(value)

        if ttl:
            await conn.setex(key, ttl, value)
        else:
            await conn.set(key, value)

        duration_ms = (time.time() - start_time) * 1000
        return QueryResult(
            success=True,
            operation="set",
            data={"key": key, "ttl": ttl},
            duration_ms=duration_ms,
        )

    async def _redis_keys(self, pattern: str = "*", **kwargs) -> QueryResult:
        """List Redis keys matching pattern."""
        start_time = time.time()
        conn = await self._get_connection("redis")
        keys = await conn.keys(pattern)
        keys = [k.decode() if isinstance(k, bytes) else k for k in keys]

        duration_ms = (time.time() - start_time) * 1000
        return QueryResult(
            success=True,
            operation="keys",
            data={"pattern": pattern, "keys": keys, "count": len(keys)},
            duration_ms=duration_ms,
        )

    # MongoDB-specific operations
    async def _mongo_find(
        self,
        collection: str,
        filter: dict[str, Any] | None = None,
        projection: dict[str, Any] | None = None,
        limit: int = 100,
        **kwargs,
    ) -> QueryResult:
        """Find documents in MongoDB collection."""
        start_time = time.time()
        db = await self._get_connection("mongodb")
        coll = db[collection]

        cursor = coll.find(filter or {}, projection)
        docs = await cursor.to_list(length=limit)

        # Convert ObjectId to string
        for doc in docs:
            if "_id" in doc:
                doc["_id"] = str(doc["_id"])

        duration_ms = (time.time() - start_time) * 1000
        return QueryResult(
            success=True,
            operation="find",
            rows=docs,
            data={"collection": collection, "count": len(docs)},
            duration_ms=duration_ms,
        )

    async def _mongo_insert(
        self,
        collection: str,
        document: dict[str, Any],
        **kwargs,
    ) -> QueryResult:
        """Insert document into MongoDB collection."""
        start_time = time.time()
        db = await self._get_connection("mongodb")
        coll = db[collection]

        result = await coll.insert_one(document)

        duration_ms = (time.time() - start_time) * 1000
        return QueryResult(
            success=True,
            operation="insert_one",
            affected_rows=1,
            data={"collection": collection, "inserted_id": str(result.inserted_id)},
            duration_ms=duration_ms,
        )

    async def _mongo_aggregate(
        self,
        collection: str,
        pipeline: list[dict[str, Any]],
        **kwargs,
    ) -> QueryResult:
        """Run MongoDB aggregation pipeline."""
        start_time = time.time()
        db = await self._get_connection("mongodb")
        coll = db[collection]

        cursor = coll.aggregate(pipeline)
        docs = await cursor.to_list(length=self.config.max_results)

        # Convert ObjectId to string
        for doc in docs:
            if "_id" in doc:
                doc["_id"] = str(doc["_id"])

        duration_ms = (time.time() - start_time) * 1000
        return QueryResult(
            success=True,
            operation="aggregate",
            rows=docs,
            data={"collection": collection, "count": len(docs)},
            duration_ms=duration_ms,
        )

    # Convenience methods
    async def query(self, sql: str, params: list[Any] = None, **kwargs) -> CapabilityResult:
        """Execute a SQL query."""
        return await self.execute(action="query", sql=sql, params=params, **kwargs)

    async def insert(self, table: str, data: dict[str, Any], **kwargs) -> CapabilityResult:
        """Insert a row into a table."""
        return await self.execute(action="insert", table=table, data=data, **kwargs)

    async def update(self, table: str, data: dict[str, Any], where: str, **kwargs) -> CapabilityResult:
        """Update rows in a table."""
        return await self.execute(action="update", table=table, data=data, where=where, **kwargs)

    async def delete(self, table: str, where: str, **kwargs) -> CapabilityResult:
        """Delete rows from a table."""
        return await self.execute(action="delete", table=table, where=where, **kwargs)

    async def schema(self, table: str, **kwargs) -> CapabilityResult:
        """Get table schema."""
        return await self.execute(action="schema", table=table, **kwargs)

    async def tables(self, **kwargs) -> CapabilityResult:
        """List all tables."""
        return await self.execute(action="tables", **kwargs)
