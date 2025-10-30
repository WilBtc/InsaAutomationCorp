"""
Synchronous database connection for authentication
(Authentication needs synchronous queries for simplicity)
"""

import psycopg2
from psycopg2.extras import RealDictCursor
from contextlib import contextmanager
from .config import settings


def get_sync_db_connection():
    """Get a synchronous database connection for authentication"""
    # Parse DATABASE_URL (postgresql://user:pass@host:port/db)
    db_url = settings.DATABASE_URL

    return psycopg2.connect(db_url, cursor_factory=RealDictCursor)


@contextmanager
def get_auth_db():
    """Context manager for auth database connection"""
    conn = get_sync_db_connection()
    try:
        yield conn
    finally:
        conn.close()
