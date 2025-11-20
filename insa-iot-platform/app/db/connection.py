"""
Database connection pooling for the Alkhorayef ESP IoT Platform.

This module provides PostgreSQL connection pooling using psycopg2
with proper error handling and retry logic.
"""

import time
from typing import Optional, Dict, Any, Generator
from contextlib import contextmanager

import psycopg2
from psycopg2 import pool, extras
from psycopg2.extensions import connection, cursor

from app.core import (
    get_config,
    get_logger,
    DatabaseError,
    ConnectionError as PlatformConnectionError,
    ConfigurationError
)


logger = get_logger(__name__)


class DatabasePool:
    """Thread-safe PostgreSQL connection pool manager."""

    def __init__(self) -> None:
        """Initialize database pool (connection created lazily)."""
        self._pool: Optional[pool.SimpleConnectionPool] = None
        self._config = get_config()
        self._max_retries = 3
        self._retry_delay_seconds = 1

    def initialize(self) -> None:
        """
        Initialize the connection pool.

        Raises:
            ConnectionError: If unable to create connection pool
            ConfigurationError: If database configuration is invalid
        """
        if self._pool is not None:
            logger.warning("Database pool already initialized")
            return

        try:
            logger.info(
                "Initializing database connection pool",
                extra={
                    "extra_fields": {
                        "host": self._config.database.host,
                        "port": self._config.database.port,
                        "database": self._config.database.database,
                        "min_connections": self._config.database.min_pool_size,
                        "max_connections": self._config.database.max_pool_size
                    }
                }
            )

            self._pool = pool.SimpleConnectionPool(
                minconn=self._config.database.min_pool_size,
                maxconn=self._config.database.max_pool_size,
                host=self._config.database.host,
                port=self._config.database.port,
                database=self._config.database.database,
                user=self._config.database.user,
                password=self._config.database.password,
                connect_timeout=self._config.database.command_timeout,
                options=f"-c statement_timeout={self._config.database.command_timeout * 1000}"
            )

            # Test the connection
            self._test_connection()

            logger.info("Database connection pool initialized successfully")

        except psycopg2.OperationalError as e:
            error_msg = f"Failed to connect to database: {str(e)}"
            logger.error(error_msg, exc_info=e)
            raise PlatformConnectionError(
                message=error_msg,
                service="PostgreSQL"
            ) from e
        except Exception as e:
            error_msg = f"Unexpected error initializing database pool: {str(e)}"
            logger.error(error_msg, exc_info=e)
            raise DatabaseError(
                message=error_msg,
                operation="INITIALIZE_POOL"
            ) from e

    def _test_connection(self) -> None:
        """
        Test database connection.

        Raises:
            ConnectionError: If connection test fails
        """
        conn = None
        try:
            conn = self._pool.getconn()
            with conn.cursor() as cur:
                cur.execute("SELECT 1")
                result = cur.fetchone()
                if result[0] != 1:
                    raise PlatformConnectionError(
                        message="Database connection test failed",
                        service="PostgreSQL"
                    )
        finally:
            if conn:
                self._pool.putconn(conn)

    @contextmanager
    def get_connection(self) -> Generator[connection, None, None]:
        """
        Get a database connection from the pool.

        Yields:
            Database connection

        Raises:
            DatabaseError: If unable to get connection from pool
        """
        # Lazy initialization - connect on first use
        if self._pool is None:
            self.initialize()

        conn = None
        try:
            conn = self._pool.getconn()
            if conn is None:
                raise DatabaseError(
                    message="Failed to get connection from pool",
                    operation="GET_CONNECTION"
                )

            # Set connection properties
            conn.autocommit = False

            yield conn

        except psycopg2.Error as e:
            logger.error(
                "Database connection error",
                exc_info=e,
                extra={"extra_fields": {"error_code": e.pgcode}}
            )
            raise DatabaseError(
                message=f"Database connection error: {str(e)}",
                operation="GET_CONNECTION",
                details={"error_code": e.pgcode}
            ) from e
        finally:
            if conn:
                self._pool.putconn(conn)

    @contextmanager
    def get_cursor(
        self,
        cursor_factory: Optional[Any] = None
    ) -> Generator[cursor, None, None]:
        """
        Get a database cursor with automatic connection management.

        Args:
            cursor_factory: psycopg2 cursor factory (e.g., RealDictCursor)

        Yields:
            Database cursor

        Raises:
            DatabaseError: If unable to create cursor
        """
        with self.get_connection() as conn:
            cur = None
            try:
                if cursor_factory:
                    cur = conn.cursor(cursor_factory=cursor_factory)
                else:
                    cur = conn.cursor()

                yield cur

                conn.commit()

            except psycopg2.Error as e:
                conn.rollback()
                logger.error(
                    "Database cursor error",
                    exc_info=e,
                    extra={"extra_fields": {"error_code": e.pgcode}}
                )
                raise DatabaseError(
                    message=f"Database cursor error: {str(e)}",
                    operation="GET_CURSOR",
                    details={"error_code": e.pgcode}
                ) from e
            finally:
                if cur:
                    cur.close()

    def execute_query(
        self,
        query: str,
        params: Optional[tuple] = None,
        fetch: bool = True,
        return_dict: bool = False
    ) -> Optional[list]:
        """
        Execute a database query with retry logic.

        Args:
            query: SQL query to execute
            params: Query parameters
            fetch: Whether to fetch results
            return_dict: Return results as dictionaries

        Returns:
            Query results or None

        Raises:
            DatabaseError: If query execution fails
        """
        cursor_factory = extras.RealDictCursor if return_dict else None

        for attempt in range(self._max_retries):
            try:
                with self.get_cursor(cursor_factory=cursor_factory) as cur:
                    cur.execute(query, params)

                    if fetch:
                        return cur.fetchall()
                    return None

            except DatabaseError as e:
                if attempt < self._max_retries - 1:
                    logger.warning(
                        f"Query execution failed, retrying ({attempt + 1}/{self._max_retries})",
                        extra={
                            "extra_fields": {
                                "query": query[:100],  # Log first 100 chars
                                "attempt": attempt + 1
                            }
                        }
                    )
                    time.sleep(self._retry_delay_seconds)
                else:
                    logger.error(
                        "Query execution failed after all retries",
                        extra={
                            "extra_fields": {
                                "query": query[:100],
                                "attempts": self._max_retries
                            }
                        }
                    )
                    raise

        return None

    def execute_many(
        self,
        query: str,
        params_list: list[tuple]
    ) -> None:
        """
        Execute a query with multiple parameter sets.

        Args:
            query: SQL query to execute
            params_list: List of parameter tuples

        Raises:
            DatabaseError: If batch execution fails
        """
        try:
            with self.get_cursor() as cur:
                extras.execute_batch(cur, query, params_list)

            logger.info(
                "Batch query executed successfully",
                extra={
                    "extra_fields": {
                        "query": query[:100],
                        "batch_size": len(params_list)
                    }
                }
            )

        except DatabaseError as e:
            logger.error(
                "Batch query execution failed",
                extra={
                    "extra_fields": {
                        "query": query[:100],
                        "batch_size": len(params_list)
                    }
                }
            )
            raise

    def close(self) -> None:
        """Close all connections in the pool."""
        if self._pool is not None:
            logger.info("Closing database connection pool")
            self._pool.closeall()
            self._pool = None
            logger.info("Database connection pool closed")

    def __enter__(self) -> "DatabasePool":
        """Context manager entry."""
        self.initialize()
        return self

    def __exit__(self, exc_type, exc_val, exc_tb) -> None:
        """Context manager exit."""
        self.close()


# Global database pool instance
_db_pool: Optional[DatabasePool] = None


def get_db_pool() -> DatabasePool:
    """
    Get or create global database pool instance.

    Note: Connection pool initialization is lazy - it will connect
    on first use, not on creation. Call initialize() explicitly
    if you need to connect immediately.

    Returns:
        DatabasePool instance
    """
    global _db_pool
    if _db_pool is None:
        _db_pool = DatabasePool()
        # Lazy initialization - don't call initialize() here
        # Pool will connect on first actual database operation
    return _db_pool


def close_db_pool() -> None:
    """Close global database pool."""
    global _db_pool
    if _db_pool is not None:
        _db_pool.close()
        _db_pool = None
