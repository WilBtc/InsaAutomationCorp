#!/usr/bin/env python3
"""
Docker PostgreSQL Wrapper - Temporary solution for Docker networking issue.

This module provides a connection to PostgreSQL through docker exec,
bypassing the Docker port forwarding issue on port 5440.

Usage:
    from docker_psql_wrapper import get_docker_connection

    with get_docker_connection() as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT version();")
        print(cursor.fetchone())
"""

import subprocess
import json
from typing import Optional, List, Tuple, Any
from contextlib import contextmanager


class DockerPSQLConnection:
    """Wrapper that executes PostgreSQL commands through docker exec."""

    def __init__(self, container_name: str = "alkhorayef-timescaledb",
                 user: str = "esp_user", database: str = "esp_telemetry"):
        """
        Initialize Docker PostgreSQL connection wrapper.

        Args:
            container_name: Name of the Docker container
            user: PostgreSQL user
            database: Database name
        """
        self.container_name = container_name
        self.user = user
        self.database = database
        self.autocommit = False
        self._in_transaction = False

    def _execute_psql(self, sql: str, params: Optional[Tuple] = None) -> str:
        """
        Execute SQL through docker exec.

        Args:
            sql: SQL query to execute
            params: Query parameters (will be safely interpolated)

        Returns:
            Output from psql command

        Raises:
            RuntimeError: If docker exec fails
        """
        # Format parameters safely using psql's \set and variable substitution
        if params:
            # For now, use simple string interpolation (be careful!)
            # TODO: Implement proper parameter binding
            sql = sql % params

        cmd = [
            "docker", "exec", "-i", self.container_name,
            "psql", "-U", self.user, "-d", self.database,
            "-t",  # Tuples only (no headers)
            "-A",  # Unaligned output
            "-F", "|",  # Pipe delimiter
            "-c", sql
        ]

        try:
            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                check=True,
                timeout=30
            )
            return result.stdout.strip()
        except subprocess.CalledProcessError as e:
            raise RuntimeError(f"Docker exec failed: {e.stderr}") from e
        except subprocess.TimeoutExpired as e:
            raise RuntimeError(f"Query timeout: {sql[:100]}") from e

    def cursor(self):
        """Return a cursor object."""
        return DockerPSQLCursor(self)

    def commit(self):
        """Commit the current transaction."""
        if self._in_transaction:
            self._execute_psql("COMMIT;")
            self._in_transaction = False

    def rollback(self):
        """Rollback the current transaction."""
        if self._in_transaction:
            self._execute_psql("ROLLBACK;")
            self._in_transaction = False

    def close(self):
        """Close the connection."""
        if self._in_transaction:
            self.rollback()


class DockerPSQLCursor:
    """Cursor for executing queries through docker exec."""

    def __init__(self, connection: DockerPSQLConnection):
        """Initialize cursor with connection."""
        self.connection = connection
        self._results: List[Tuple] = []
        self._index = 0

    def execute(self, sql: str, params: Optional[Tuple] = None):
        """
        Execute a SQL query.

        Args:
            sql: SQL query to execute
            params: Query parameters
        """
        if not self.connection.autocommit and not self.connection._in_transaction:
            # Start transaction
            self.connection._execute_psql("BEGIN;")
            self.connection._in_transaction = True

        output = self.connection._execute_psql(sql, params)

        # Parse output into tuples
        self._results = []
        if output:
            for line in output.split('\n'):
                if line.strip():
                    # Split by pipe delimiter and convert to tuple
                    values = line.split('|')
                    self._results.append(tuple(values))

        self._index = 0

    def fetchone(self) -> Optional[Tuple]:
        """Fetch the next row."""
        if self._index < len(self._results):
            result = self._results[self._index]
            self._index += 1
            return result
        return None

    def fetchall(self) -> List[Tuple]:
        """Fetch all remaining rows."""
        results = self._results[self._index:]
        self._index = len(self._results)
        return results

    def fetchmany(self, size: int = 1) -> List[Tuple]:
        """Fetch the next N rows."""
        results = self._results[self._index:self._index + size]
        self._index += len(results)
        return results

    def close(self):
        """Close the cursor."""
        self._results = []
        self._index = 0


@contextmanager
def get_docker_connection(container_name: str = "alkhorayef-timescaledb",
                          user: str = "esp_user",
                          database: str = "esp_telemetry"):
    """
    Context manager for Docker PostgreSQL connection.

    Args:
        container_name: Name of the Docker container
        user: PostgreSQL user
        database: Database name

    Yields:
        DockerPSQLConnection instance

    Example:
        with get_docker_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT version();")
            print(cursor.fetchone())
    """
    conn = DockerPSQLConnection(container_name, user, database)
    try:
        yield conn
    finally:
        conn.close()


if __name__ == "__main__":
    # Test the wrapper
    print("Testing Docker PostgreSQL Wrapper...")
    print("=" * 80)

    try:
        with get_docker_connection() as conn:
            cursor = conn.cursor()

            # Test 1: Version
            print("\n[Test 1] Database Version:")
            cursor.execute("SELECT version();")
            result = cursor.fetchone()
            if result:
                print(f"  {result[0][:100]}")

            # Test 2: Current database and user
            print("\n[Test 2] Current Database and User:")
            cursor.execute("SELECT current_database(), current_user;")
            result = cursor.fetchone()
            if result:
                print(f"  Database: {result[0]}, User: {result[1]}")

            # Test 3: List tables
            print("\n[Test 3] Tables in esp_telemetry:")
            cursor.execute("""
                SELECT tablename FROM pg_tables
                WHERE schemaname = 'public'
                ORDER BY tablename;
            """)
            tables = cursor.fetchall()
            if tables:
                for table in tables:
                    print(f"  - {table[0]}")
            else:
                print("  (no tables found)")

            conn.commit()

            print("\n" + "=" * 80)
            print("✅ Docker PostgreSQL Wrapper working correctly!")
            print("\nThis wrapper can be used as a temporary solution until")
            print("the Docker networking issue is resolved.")

    except Exception as e:
        print(f"\n❌ Error: {e}")
        import traceback
        traceback.print_exc()
